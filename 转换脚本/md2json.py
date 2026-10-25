#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""短剧改编大纲 Markdown -> outline.json 转换器。

用法：
    python md2json.py 北玄老六_大纲.md
    python md2json.py 北玄老六_大纲.md -o outline.json

依赖：仅标准库。
"""

import argparse
import json
import re
from pathlib import Path


# ---------- 通用工具 ----------

def parse_md_table(lines, start_idx):
    """从 start_idx 开始解析 Markdown 表格，返回行字典列表。"""
    header_cells = [c.strip() for c in lines[start_idx].strip().strip('|').split('|')]
    rows = []
    i = start_idx + 2  # 跳过表头、分隔行
    while i < len(lines) and lines[i].strip().startswith('|'):
        cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
        rows.append(dict(zip(header_cells, cells)))
        i += 1
    return rows


def find_table(lines):
    """返回该段中第一张表格的所有行。"""
    for i, line in enumerate(lines):
        if line.strip().startswith('|'):
            return parse_md_table(lines, i)
    return []


def split_sections(md_text):
    """按 ## 二级标题切分文档。返回 (标题, {章节名: 行列表})。"""
    sections = {}
    title = None
    current = None
    for line in md_text.split('\n'):
        m = re.match(r'^# (.+)$', line)
        if m and title is None:
            title = m.group(1).strip()
            continue
        m2 = re.match(r'^## (.+)$', line)
        if m2:
            current = m2.group(1).strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return title, sections


def get_section(sections, prefix):
    for k, v in sections.items():
        if k.startswith(prefix):
            return v
    return []


# ---------- 各章节解析 ----------

def parse_params(md_text):
    m = re.search(r'(\d+)\s*集\s*×\s*([\d.]+)\s*分钟', md_text)
    episodes = int(m.group(1)) if m else 36
    minutes = float(m.group(2)) if m else 1.5
    return {
        'episodes': episodes,
        'minutesPerEpisode': minutes,
        'genre': '年代重生爽文',
        'adaptMode': '抽核',
        'preferences': [],
        'thresholds': {
            'maxLeads': 5,
            'maxSupport': 10,
            'maxFunctional': 10,
            'maxBeatGap': 3,
            'maxPrimaryScenes': 8,
        },
    }


def parse_adaptation(lines):
    """解析 ## 一、改编说明：一句话核心 + 保留/砍掉/合并/风险 子表。"""
    result = {'core': '', 'keep': [], 'cut': [], 'merge': [], 'risks': []}

    subsections = {}
    current_sub = None
    for line in lines:
        m = re.match(r'^### (.+)$', line)
        if m:
            current_sub = m.group(1).strip()
            subsections[current_sub] = []
        elif current_sub is not None:
            subsections[current_sub].append(line)
        else:
            stripped = line.strip()
            if stripped.startswith('**一句话核心**'):
                result['core'] = stripped.replace('**一句话核心**', '').strip()

    for name, sub in subsections.items():
        rows = find_table(sub)
        if '保留' in name:
            for r in rows:
                result['keep'].append({
                    'what': r.get('内容', '').strip(),
                    'why': r.get('理由', '').strip(),
                    'evidence': r.get('原文依据', '').strip(),
                })
        elif '砍掉' in name:
            for r in rows:
                result['cut'].append({
                    'what': r.get('内容', '').strip(),
                    'why': r.get('理由', '').strip(),
                })
        elif '合并' in name:
            for r in rows:
                result['merge'].append({
                    'what': r.get('内容', '').strip(),
                    'why': r.get('理由', '').strip(),
                })
        elif '风险' in name:
            for r in rows:
                result['risks'].append({
                    'what': r.get('内容', '').strip(),
                    'plan': r.get('对策', '').strip(),
                })
    return result


def parse_characters(lines):
    """解析 ## 二、人物表。"""
    rows = find_table(lines)
    tier_map = {'主角组': 'lead', '重要配角': 'support', '功能性角色': 'functional'}
    chars = []
    for row in rows:
        cid = row.get('ID', '').strip()
        if not cid.startswith('C'):
            continue
        arc = row.get('人物弧', '').strip()
        from_cell = ''
        for k in row:
            if '改动记录' in k:
                from_cell = row[k]
                break
        froms = [
            s.strip() for s in re.split(r'[/、]', from_cell)
            if s.strip() and s.strip() != '—'
        ]
        char = {
            'id': cid,
            'name': row.get('角色', '').strip(),
            'role': row.get('定位', '').strip(),
            'tier': tier_map.get(row.get('层级', '').strip(), 'functional'),
        }
        if arc and arc != '—':
            char['arc'] = arc
        char['from'] = froms
        chars.append(char)
    return chars


def parse_scenes(lines):
    """解析 ## 五、资产清单 的第一张表（场景表）。"""
    rows = find_table(lines)
    scenes = []
    for row in rows:
        sid = row.get('ID', '').strip()
        if not sid.startswith('S'):
            continue
        reuse = row.get('复用方案', '').strip()
        scenes.append({
            'id': sid,
            'name': row.get('场景', '').strip(),
            'primary': row.get('主场景', '').strip() == '是',
            'reusePlan': '' if reuse in ('—', '') else reuse,
        })
    return scenes


def parse_beats(lines):
    """解析 ## 三、爽点表。"""
    rows = find_table(lines)
    weight_map = {'大爆点': 'major', '常规': 'minor'}
    beats = []
    for row in rows:
        bid = row.get('ID', '').strip()
        if not bid.startswith('B'):
            continue
        ep_cell = row.get('集', '0').strip()
        try:
            episode = int(re.sub(r'\D', '', ep_cell) or '0')
        except ValueError:
            episode = 0
        beats.append({
            'id': bid,
            'type': row.get('类型', '').strip(),
            'weight': weight_map.get(row.get('量级', '').strip(), 'minor'),
            'episode': episode,
            'setup': row.get('铺垫', '').strip(),
            'payoff': row.get('兑现', '').strip(),
        })
    return beats


def parse_episodes(lines):
    """解析 ## 四、分集梗概。"""
    blocks = []
    current = None
    for line in lines:
        m = re.match(r'^### 第\s*(\d+)\s*集', line)
        if m:
            if current is not None:
                blocks.append(current)
            current = {'ep': int(m.group(1)), 'lines': []}
        elif current is not None:
            current['lines'].append(line)
    if current is not None:
        blocks.append(current)
    return [parse_episode_block(b) for b in blocks]


def parse_episode_block(block):
    lines = block['lines']
    synopsis_parts = []
    hook = ''
    suspense = ''
    scene_ids = []
    char_ids = []
    prop_ids = []
    crowd = ''
    warnings = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('- '):
            break
        if line:
            synopsis_parts.append(line)
        i += 1

    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line.startswith('- '):
            continue
        content = line[2:].strip()

        m = re.match(r'\*\*【钩子】\*\*\s*(.*)', content)
        if m:
            hook = m.group(1).strip()
            continue

        m = re.match(r'\*\*【悬念】\*\*\s*(.*)', content)
        if m:
            suspense = m.group(1).strip()
            continue

        if content.startswith('场景：'):
            scene_ids = list(dict.fromkeys(re.findall(r'S\d+', content)))
            char_ids = list(dict.fromkeys(re.findall(r'C\d+', content)))
            prop_ids = list(dict.fromkeys(re.findall(r'P\d+', content)))
            continue

        if content.startswith('同框拆解：'):
            crowd = content[len('同框拆解：'):].strip()
            continue

        if '预警：' in content:
            warn_str = content.split('预警：')[-1].strip()
            warnings = [w.strip() for w in re.split(r'[、,，]', warn_str) if w.strip()]

    return {
        'ep': block['ep'],
        'synopsis': ' '.join(synopsis_parts).strip(),
        'hook': hook,
        'suspense': suspense,
        'sceneIds': scene_ids,
        'characterIds': char_ids,
        'propIds': prop_ids,
        'crowdPlan': crowd,
        'warnings': warnings,
    }


# ---------- 主流程 ----------

def convert(md_path, out_path):
    md_text = Path(md_path).read_text(encoding='utf-8')
    title, sections = split_sections(md_text)
    source = title.split(' · ')[0].strip() if title else ''

    result = {
        'source': source,
        'lang': 'zh',
        'params': parse_params(md_text),
        'adaptation': parse_adaptation(get_section(sections, '一、改编说明')),
        'characters': parse_characters(get_section(sections, '二、人物表')),
        'scenes': parse_scenes(get_section(sections, '五、资产清单')),
        'beats': parse_beats(get_section(sections, '三、爽点表')),
        'episodes': parse_episodes(get_section(sections, '四、分集梗概')),
    }

    Path(out_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def main():
    parser = argparse.ArgumentParser(description='短剧改编大纲 Markdown → JSON')
    parser.add_argument('input', help='输入 Markdown 文件路径')
    parser.add_argument('-o', '--output', help='输出 JSON 文件路径（默认同名 .json）')
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        raise SystemExit(f'找不到文件：{md_path}')

    out_path = Path(args.output) if args.output else md_path.with_suffix('.json')
    convert(md_path, out_path)
    print(f'已生成 {out_path}')


if __name__ == '__main__':
    main()