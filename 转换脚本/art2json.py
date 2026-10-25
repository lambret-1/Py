#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""短剧美术设定集 Markdown -> JSON 转换器。

用法：
    python art2json.py 八零新婚夜-art.md
    python art2json.py 八零新婚夜-art.md -o art.json
"""

import argparse
import json
import re
from pathlib import Path

def parse_md_table(md_text, table_title):
    """解析指定标题下的 Markdown 表格"""
    pattern = rf"## {table_title}\n\n\|(.*?)\|\n\s*\|(?:\s*[-:]+\s*\|)+\n((?:\|.*?\|\n?)+)"
    m = re.search(pattern, md_text)
    if not m:
        return []
    
    headers = [h.strip() for h in m.group(1).split('|')]
    rows = []
    for line in m.group(2).strip().split('\n'):
        if not line.strip(): continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(dict(zip(headers, cells)))
    return rows

def extract_codeblock(text, block_name):
    """提取指定名称的代码块"""
    pattern = rf"\*\*{re.escape(block_name)}\*\*.*?```(?:text)?\n(.*?)```"
    m = re.search(pattern, text, re.S)
    return m.group(1).strip() if m else ""

def parse_episodes(ep_str):
    """将 '1、2、16' 解析为整数列表"""
    if not ep_str or ep_str == '—':
        return []
    return [int(x) for x in re.findall(r'\d+', ep_str)]

def parse_art_to_json(md_content):
    result = {
        "source": "",
        "scenes": [],
        "props": [],
        "dynasty": "1980年代中国北方农村"  # 默认年代，可根据需要修改
    }

    # 1. 提取 Source
    m_source = re.search(r'^# (.*?)\s*[·—\-]\s*', md_content, re.M)
    if m_source:
        result["source"] = m_source.group(1).strip()

    # 2. 解析表格数据作为元数据
    scene_table = parse_md_table(md_content, "场景清单")
    prop_table = parse_md_table(md_content, "道具清单")
    
    # 将表格转为字典，方便按 ID 查询
    scene_meta = {r['ID']: r for r in scene_table if 'ID' in r}
    prop_meta = {r['ID']: r for r in prop_table if 'ID' in r}

    # 3. 按 ## 切分正文模块
    parts = re.split(r'\n## (?!#)', md_content)
    
    for part in parts:
        part = part.strip()
        if not part or '清单' in part[:10] or '美术设定集' in part[:10]:
            continue

        # 判断是场景还是道具
        m_title = re.match(r'([SP]\d+)\s+(.*)', part)
        if not m_title:
            continue
        
        item_id = m_title.group(1)
        item_name = m_title.group(2).strip()

        # --- 解析场景 (S) ---
        if item_id.startswith('S'):
            meta = scene_meta.get(item_id, {})
            scene_data = {
                "id": item_id,
                "name": item_name,
                "primary": meta.get('类型') == '主场景',
                "summary": "",
                "anchors": [],
                "lighting": [],
                "image": {"tags": []},
                "usage": {
                    "episodes": parse_episodes(meta.get('出现集', '')),
                    "beats": []  # 源 MD 中无直接映射，预留空数组
                }
            }

            # 提取 summary (标题下的第一段)
            summary_match = re.search(r'###[^#].*?\n\n(.*?)\n\n', part, re.S)
            if summary_match:
                scene_data["summary"] = summary_match.group(1).strip()
            
            # 提取 锚点
            anchors = re.findall(r'\d+\.\s*\*\*(.*?)\*\*\s*[—-]\s*(.*)', part)
            scene_data["anchors"] = [{"name": a[0].strip(), "desc": a[1].strip()} for a in anchors]

            # 提取 光照
            lighting = re.findall(r'-\s*\*\*(.*?)\*\*\s*：\s*`([^`]+)`', part)
            scene_data["lighting"] = [{"state": l[0].strip(), "prompt": l[1].strip()} for l in lighting]

            # 提取 提示词
            scene_data["image"]["prompt"] = extract_codeblock(part, "主视角 EN")
            scene_data["image"]["negativePrompt"] = extract_codeblock(part, "反向提示词")
            scene_data["image"]["sheet"] = extract_codeblock(part, "设定图 EN")

            # 提取变体信息
            m_variant = re.search(r'>\s*变体来源：(S\d+)[　\s]+改动：(.*)', part)
            if m_variant:
                scene_data["variantOf"] = m_variant.group(1)
                scene_data["changes"] = m_variant.group(2).strip()

            # 提取底部 tags（以反引号包围的一行）
            m_tags = re.search(r'\n\n`([^`\n]+)`(?:`, `([^`\n]+)`)+', part)
            if m_tags:
                # 直接抓取最后所有的反引号内容
                tags = re.findall(r'`([^`]+)`', part.split('### 出图提示词包')[-1])
                scene_data["image"]["tags"] = tags

            result["scenes"].append(scene_data)

        # --- 解析道具 (P) ---
        elif item_id.startswith('P'):
            meta = prop_meta.get(item_id, {})
            prop_data = {
                "id": item_id,
                "name": item_name,
                "scale": meta.get('尺度', ''),
                "summary": "",
                "anchors": [],
                "states": [],
                "relatedScenes": [s.strip() for s in meta.get('关联场景', '').split('、') if s.strip() and s != '—'],
                "carriedBy": "苏晚",  # 默认推测，如果是其他道具需要改
                "image": {"tags": []},
                "usage": {
                    "episodes": parse_episodes(meta.get('出现集', '')),
                    "beats": []  # 预留空数组
                }
            }

            # 提取 summary
            summary_match = re.search(r'###[^#].*?\n\n(.*?)\n\n', part, re.S)
            if summary_match:
                prop_data["summary"] = summary_match.group(1).strip()

            # 提取 锚点
            anchors = re.findall(r'\d+\.\s*\*\*(.*?)\*\*\s*[—-]\s*(.*)', part)
            prop_data["anchors"] = [{"name": a[0].strip(), "desc": a[1].strip()} for a in anchors]

            # 提取 状态变体
            states = re.findall(r'-\s*\*\*(.*?)\*\*\s*：\s*`([^`]+)`', part)
            prop_data["states"] = [{"state": l[0].strip(), "prompt": l[1].strip()} for l in states]

            # 提取 提示词
            prop_data["image"]["prompt"] = extract_codeblock(part, "主视角 EN")
            prop_data["image"]["negativePrompt"] = extract_codeblock(part, "反向提示词")
            prop_data["image"]["sheet"] = extract_codeblock(part, "设定图 EN")

            # 提取 tags
            m_tags = re.search(r'\n\n`([^`\n]+)`(?:`, `([^`\n]+)`)+', part)
            if m_tags:
                tags = re.findall(r'`([^`]+)`', part.split('### 出图提示词包')[-1])
                prop_data["image"]["tags"] = tags

            result["props"].append(prop_data)

    return result

def main():
    parser = argparse.ArgumentParser(description='短剧美术设定集 Markdown → JSON')
    parser.add_argument('input', help='输入 Markdown 文件路径')
    parser.add_argument('-o', '--output', help='输出 JSON 文件路径（默认同名 .json）')
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        raise SystemExit(f'找不到文件：{md_path}')

    out_path = Path(args.output) if args.output else md_path.with_suffix('.json')
    md_content = md_path.read_text(encoding='utf-8')
    
    json_data = parse_art_to_json(md_content)
    
    out_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'成功生成美术设定集 JSON：{out_path}')

if __name__ == '__main__':
    main()