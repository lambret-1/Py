#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""短剧角色表 Markdown -> JSON 转换器。

用法：
    python cast2json.py 八零新婚夜-cast.md
    python cast2json.py 八零新婚夜-cast.md -o cast.json
"""

import argparse
import json
import re
from pathlib import Path

def extract_prompt(section_text, keyword):
    """根据关键字提取下方的代码块内容"""
    pattern = re.escape(keyword) + r'.*?```(?:text)?\n(.*?)```'
    m = re.search(pattern, section_text, re.S)
    return m.group(1).strip() if m else ""

def parse_importance(role_str):
    """将中文身份映射为英文 importance"""
    mapping = {
        '主角': 'protagonist',
        '主要角色': 'major',
        '配角': 'supporting',
        '龙套': 'minor'
    }
    for k, v in mapping.items():
        if k in role_str:
            return v
    return 'supporting'

def parse_md_to_json(md_content):
    result = {
        "source": "",
        "lang": "zh",
        "summary": "",
        "characters": []
    }

    # 1. 提取 Source (标题)
    m_source = re.search(r'^# (.*?)\s*[—\-]\s*', md_content, re.M)
    if m_source:
        result["source"] = m_source.group(1).strip()

    # 2. 提取 故事摘要
    m_summary = re.search(r'## 故事摘要\n+(.*?)\n+---', md_content, re.S)
    if m_summary:
        result["summary"] = m_summary.group(1).strip()

    # 3. 分割角色模块 (以 ## 开头，且不是 "## 故事摘要" 的部分)
    # 使用正则按行分割，忽略 ## 故事摘要
    parts = re.split(r'\n## (?!#)', md_content)
    
    for part in parts:
        # 跳过前言/摘要部分
        if '故事摘要' in part[:20] or not part.strip():
            continue

        # 提取角色名和别名 (如：陆野（野子、陆大哥）)
        m_title = re.match(r'([^（\n]+)(?:（([^）]+)）)?', part.strip())
        if not m_title:
            continue
        
        name = m_title.group(1).strip()
        aliases_str = m_title.group(2)
        aliases = [a.strip() for a in re.split(r'[、,]', aliases_str)] if aliases_str else []

        char_data = {
            "name": name,
            "aliases": aliases,
            "importance": "supporting",
            "oneLiner": "",
            "persona": {},
            "image": {"tags": []},
            "voice": {}
        }

        # 提取 引言/一句话介绍 (> 主角 · 一米八二的糙汉...)
        m_quote = re.search(r'^> (.*?)\n', part, re.M)
        if m_quote:
            quote_parts = m_quote.group(1).split(' · ', 1)
            if len(quote_parts) == 2:
                char_data["importance"] = parse_importance(quote_parts[0])
                char_data["oneLiner"] = quote_parts[1].strip()
            else:
                char_data["oneLiner"] = m_quote.group(1).strip()

        # 切分三大区块
        persona_match = re.search(r'### 画像\n(.*?)(?=### 形象|\Z)', part, re.S)
        image_match = re.search(r'### 形象\n(.*?)(?=### 声音|\Z)', part, re.S)
        voice_match = re.search(r'### 声音\n(.*)', part, re.S)

        # --- 解析 画像 ---
        if persona_match:
            p_text = persona_match.group(1)
            persona = char_data["persona"]

            # 基本信息列表 (- **性别**：男)
            basic_info = re.findall(r'- \*\*(.*?)\*\*：(.*)', p_text)
            for k, v in basic_info:
                if k == '性别': persona['gender'] = v.strip()
                elif k == '年龄': persona['ageRange'] = v.strip()
                elif k == '身份': persona['identity'] = v.strip()

            # 性格标签 (- 沉默寡言 / 行动力极强 / ...)
            m_personality = re.search(r'^- (.*?/.*?)\n', p_text, re.M)
            if m_personality:
                persona['personality'] = [x.strip() for x in m_personality.group(1).split('/')]

            # 段落类属性 (**外貌** 文本)
            paragraphs = re.findall(r'\*\*(外貌|性情|动机|人物弧光)\*\*[　 ]*(.*)', p_text)
            key_map = {'外貌': 'appearance', '性情': 'temperament', '动机': 'motivation', '人物弧光': 'arc'}
            for k, v in paragraphs:
                persona[key_map[k]] = v.strip()

            # 关系 (**关系**)
            m_rel = re.search(r'\*\*关系\*\*\n(.*?)(?=\n\*\*|\Z)', p_text, re.S)
            if m_rel:
                rels = re.findall(r'- (.*?) — (.*)', m_rel.group(1))
                persona['relationships'] = [{"name": r[0].strip(), "relation": r[1].strip()} for r in rels]

            # 原文依据 (**原文依据**)
            m_evid = re.search(r'\*\*原文依据\*\*\n(.*?)(?=\n\*\*|\Z)', p_text, re.S)
            if m_evid:
                evidences = re.findall(r'^> (.*)', m_evid.group(1), re.M)
                persona['evidence'] = [e.strip() for e in evidences]

        # --- 解析 形象 ---
        if image_match:
            i_text = image_match.group(1)
            image = char_data["image"]
            
            # 标签 (反引号包裹)
            tags = re.findall(r'`([^`]+)`', i_text)
            image['tags'] = tags

            # 提示词
            image['prompt'] = extract_prompt(i_text, '喂出图模型用这条')
            image['promptLocal'] = extract_prompt(i_text, '豆包出图提示词')
            image['negativePrompt'] = extract_prompt(i_text, '反向提示词')
            image['sheet'] = extract_prompt(i_text, '角色设定图提示词 EN')

        # --- 解析 声音 ---
        if voice_match:
            v_text = voice_match.group(1)
            voice = char_data["voice"]

            basic_voice = re.findall(r'- \*\*(.*?)\*\*：(.*)', v_text)
            v_map = {'音色': 'timbre', '音高': 'pitch', '语速': 'pace', '口音': 'accent', '情绪': 'emotion', '类比': 'referenceHint'}
            for k, v in basic_voice:
                if k in v_map:
                    voice[v_map[k]] = v.strip()
            
            voice['prompt'] = extract_prompt(v_text, '喂 TTS 引擎用这条')

        result["characters"].append(char_data)

    return result

def main():
    parser = argparse.ArgumentParser(description='短剧角色表 Markdown → JSON')
    parser.add_argument('input', help='输入 Markdown 文件路径')
    parser.add_argument('-o', '--output', help='输出 JSON 文件路径（默认同名 .json）')
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        raise SystemExit(f'找不到文件：{md_path}')

    out_path = Path(args.output) if args.output else md_path.with_suffix('.json')
    md_content = md_path.read_text(encoding='utf-8')
    
    json_data = parse_md_to_json(md_content)
    
    out_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'成功生成角色表 JSON：{out_path}')

if __name__ == '__main__':
    main()