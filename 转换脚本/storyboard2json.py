#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import json
import sys
import io
from pathlib import Path

# 强制 UTF-8 输出，防止乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def load_char_map():
    char_map = {}
    for f in os.listdir('.'):
        if f.endswith('cast.json'):
            try:
                data = json.load(open(f, 'r', encoding='utf-8'))
                for c in data.get('characters', []):
                    char_map[c['name']] = c['id']
                    for alias in c.get('aliases', []):
                        char_map[alias] = c['id']
            except: pass
    return char_map

def map_size(size_str):
    size_str = size_str.strip()
    if '特写' in size_str: return 'close'
    if '中景' in size_str: return 'medium'
    if '全景' in size_str: return 'wide'
    if '远景' in size_str: return 'extreme wide'
    if '近景' in size_str: return 'close-up'
    return 'medium'

def extract_seedance_params(seedance_text):
    """从 Seedance 文本中提取每个镜头的参数"""
    shots = {}
    # 按【镜头X】分割
    parts = re.split(r'【镜头(\d+)】', seedance_text)
    for i in range(1, len(parts), 2):
        shot_num = int(parts[i])
        block = parts[i+1]
        
        # 提取各项参数
        lens_m = re.search(r'焦距：(.*)', block)
        pos_m = re.search(r'机位：(.*)', block)
        comp_m = re.search(r'构图：(.*)', block)
        eye_m = re.search(r'视线落点：(.*)', block)
        focus_m = re.search(r'焦点：(.*)', block)
        
        shots[shot_num] = {
            "lens": lens_m.group(1).strip() if lens_m else "",
            "cameraPosition": pos_m.group(1).strip() if pos_m else "",
            "composition": comp_m.group(1).strip() if comp_m else "",
            "eyeline": eye_m.group(1).strip() if eye_m else "",
            "focus": focus_m.group(1).strip() if focus_m else "",
        }
    return shots

def parse_storyboard_md(md_content, char_map):
    md_content = re.split(r'\n## 生成批次单', md_content)[0]
    
    m_source = re.search(r'^#\s*(.*?)\s*[·—\-]', md_content, re.M)
    source = m_source.group(1).strip() if m_source else "未知剧本"
    
    result = {
        "source": source,
        "promptLang": "en",
        "params": {
            "maxSegmentSeconds": 15,
            "minCutSeconds": 2,
            "maxCutSeconds": 5,
            "maxOnScreen": 3,
            "tolerance": 0.15
        },
        "episodes": []
    }
    
    ep_blocks = re.split(r'\n##\s*E(\d+)', md_content)
    
    for i in range(1, len(ep_blocks), 2):
        ep_num = int(ep_blocks[i])
        ep_text = ep_blocks[i+1]
        
        segments = []
        # 按 ### E01-01 分割
        seg_blocks = re.split(r'\n###\s*(E\d+-\d+)\s*·\s*', ep_text)
        
        for j in range(1, len(seg_blocks), 2):
            seg_id = seg_blocks[j]
            seg_text = seg_blocks[j+1]
            
            # 提取走位
            blocking_m = re.search(r'> 走位：(.*)', seg_text)
            blocking = blocking_m.group(1).strip() if blocking_m else ""
            
            # 提取表格
            table_m = re.search(r'\| 切 \| 起点 \| 秒 \| 景别 \| 运镜 \| 配方 \| 画面 \| 人物 \|(.*?)(?=\*\*H3|\Z)', seg_text, re.S)
            cuts = []
            if table_m:
                rows = table_m.group(1).strip().split('\n')
                cut_idx = 1
                for row in rows:
                    if not row.strip() or row.startswith('| ---'): continue
                    cols = [c.strip() for c in row.strip('|').split('|')]
                    if len(cols) >= 8:
                        # 列: 切, 起点, 秒, 景别, 运镜, 配方, 画面, 人物
                        try:
                            seconds = float(cols[2])
                        except: seconds = 0
                        
                        # 解析人物
                        chars_raw = cols[7]
                        chars = []
                        if chars_raw and chars_raw != '—':
                            for name in re.split(r'[、,，]', chars_raw):
                                name = name.strip()
                                if name: chars.append(char_map.get(name, name))
                                
                        cuts.append({
                            "beats": [cut_idx, cut_idx], # 默认递增
                            "seconds": seconds,
                            "size": map_size(cols[3]),
                            "camera": cols[4],
                            "characters": chars,
                            "frame": f"{cols[3]}：{cols[6]}",
                            "shot": cols[6],
                            "lens": "",
                            "cameraPosition": "",
                            "composition": "",
                            "eyeline": "",
                            "focus": "",
                            "stability": "stable"
                        })
                        cut_idx += 1

            # 提取 H3 提示词
            h3_m = re.search(r'\*\*H3 视频提示词\*\*\s*```(?:text)?\n(.*?)```', seg_text, re.S)
            h3_prompt = h3_m.group(1).strip() if h3_m else ""
            
            # 提取 Seedance 提示词
            seedance_m = re.search(r'\*\*Seedance 视频提示词\*\*\s*```(?:text)?\n(.*?)```', seg_text, re.S)
            seedance_text = seedance_m.group(1).strip() if seedance_m else ""
            
            # 从 Seedance 提取参数并回填 cuts
            sd_shots = extract_seedance_params(seedance_text)
            for idx, cut in enumerate(cuts, 1):
                if idx in sd_shots:
                    cut.update(sd_shots[idx])
                    
            # 提取声音和音乐
            sound_m = re.search(r'<(.*?)>', seedance_text)
            soundscape = sound_m.group(1).strip() if sound_m else ""
            music_m = re.search(r'（(.*?)）', seedance_text)
            music = music_m.group(1).strip() if music_m else ""
            
            # 兼容处理：如果 Seedance 里没有，去 H3 里找
            if not soundscape:
                sound_m2 = re.search(r'overall_soundscape:\s*(.*)', h3_prompt)
                soundscape = sound_m2.group(1).strip() if sound_m2 else ""
            if not music:
                music_m2 = re.search(r'non_diegetic_music:\s*(.*)', h3_prompt)
                music = music_m2.group(1).strip() if music_m2 else ""

            segments.append({
                "id": seg_id,
                "sceneIndex": 1, # 默认值
                "blocking": blocking,
                "soundscape": soundscape,
                "music": music,
                "h3Prompt": h3_prompt,
                "cuts": cuts
            })
            
        result["episodes"].append({
            "ep": ep_num,
            "segments": segments
        })
        
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python storyboard2json.py <input_md> [-o output_json]")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] == '-o' else md_path.with_suffix('.json')

    char_map = load_char_map()
    try:
        md_content = md_path.read_text(encoding='utf-8')
        json_data = parse_storyboard_md(md_content, char_map)
        out_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"Success: {out_path.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()