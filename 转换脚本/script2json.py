#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import json
import sys
import io
from pathlib import Path

# 强制 UTF-8 输出，防止 Windows 控制台乱码闪退
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def load_mappings():
    char_map = {}
    art_map = {}
    # 寻找同目录的 cast.json 和 art.json
    for f in os.listdir('.'):
        if f.endswith('cast.json'):
            try:
                data = json.load(open(f, 'r', encoding='utf-8'))
                for c in data.get('characters', []):
                    char_map[c['name']] = c['id']
                    for alias in c.get('aliases', []):
                        char_map[alias] = c['id']
            except: pass
        if f.endswith('art.json'):
            try:
                data = json.load(open(f, 'r', encoding='utf-8'))
                for s in data.get('scenes', []):
                    art_map[s['name']] = s['id']
            except: pass
    return char_map, art_map

def parse_script_md(md_content, char_map, art_map):
    # 截断尾部不需要的统计表
    md_content = re.split(r'\n## 场次总表', md_content)[0]
    md_content = re.split(r'\n## 台词本', md_content)[0]
    
    m_source = re.search(r'^#\s*(.*?)\s*[·—\-]', md_content, re.M)
    source = m_source.group(1).strip() if m_source else "未知剧本"
    
    result = {
        "source": source,
        "params": {
            "charsPerSecond": 4.5,
            "actionSeconds": 2.5,
            "tolerance": 0.15,
            "maxLineChars": 35
        },
        "episodes": []
    }
    
    ep_blocks = re.split(r'\n##\s*第\s*(\d+)\s*集', md_content)
    
    for i in range(1, len(ep_blocks), 2):
        ep_num = int(ep_blocks[i])
        ep_text = ep_blocks[i+1]
        
        target_m = re.search(r'目标\s*(\d+)\s*秒', ep_text)
        target = int(target_m.group(1)) if target_m else 90
        
        hook_m = re.search(r'开场钩子：(.*?)(?:（| ·|$)', ep_text)
        hook = hook_m.group(1).strip() if hook_m else ""
        
        cliff_m = re.search(r'结尾悬念：(.*)', ep_text)
        cliff = cliff_m.group(1).strip() if cliff_m else ""
        
        beats = []
        beats_m = re.search(r'认领爽点：(.*)', ep_text)
        if beats_m:
            beats = [b.strip() for b in beats_m.group(1).split('、') if b.strip()]
            
        scenes = []
        scene_blocks = re.split(r'\n###\s*第\s*\d+\s*场[\s·]+', ep_text)
        
        for s_idx in range(1, len(scene_blocks)):
            scene_text = scene_blocks[s_idx]
            
            lines = scene_text.strip().split('\n')
            if not lines: continue
            
            title_line = lines[0].strip()
            scene_name = title_line
            lighting = "白天"
            
            # 提取场景名和光照
            m_title = re.match(r'(.*?)[（\(](.*?)[）\)]', title_line)
            if m_title:
                scene_name = m_title.group(1).strip()
                lighting = m_title.group(2).strip()
            
            scene_id = art_map.get(scene_name, scene_name)
            
            # 提取人物
            chars = []
            chars_m = re.search(r'人物：(.*)', scene_text)
            if chars_m:
                raw_chars = chars_m.group(1).strip()
                for name in re.split(r'[、,，]', raw_chars):
                    name = name.strip()
                    if name:
                        chars.append(char_map.get(name, name))
                        
            # 提取台词和动作
            flow = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith('人物：') or line.startswith('---') or line.startswith('>') or line == title_line:
                    continue
                
                if line.startswith('**'):
                    m_speaker = re.match(r'^\*\*(.*?)\*\*', line)
                    if m_speaker:
                        raw_speaker = m_speaker.group(1).strip()
                        rest = line[m_speaker.end():].strip()
                        
                        if '：' in rest:
                            delivery_part, text = rest.split('：', 1)
                        elif ':' in rest:
                            delivery_part, text = rest.split(':', 1)
                        else:
                            delivery_part, text = "", rest
                        
                        # 优雅处理外层括号：比如 (（心声）张婶) -> 提取为 （心声）张婶
                        delivery = delivery_part.strip()
                        if (delivery.startswith('（') and delivery.endswith('）')) or (delivery.startswith('(') and delivery.endswith(')')):
                            delivery = delivery[1:-1].strip()
                        
                        speaker = 'VO' if '画外音' in raw_speaker else char_map.get(raw_speaker, raw_speaker)
                        
                        item = {"speaker": speaker, "line": text.strip()}
                        if delivery:
                            item["delivery"] = delivery
                        flow.append(item)
                        continue
                
                # 动作
                flow.append({"action": line})
                    
            scenes.append({
                "sceneId": scene_id,
                "lighting": lighting,
                "characters": chars,
                "props": [],
                "flow": flow
            })
            
        result["episodes"].append({
            "ep": ep_num,
            "targetSeconds": target,
            "hook": hook,
            "cliff": cliff,
            "beatsClaimed": beats,
            "hookBeat": [1, 1],
            "scenes": scenes
        })
        
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python script2json.py <input_md> [-o output_json]")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] == '-o' else md_path.with_suffix('.json')

    char_map, art_map = load_mappings()
    try:
        md_content = md_path.read_text(encoding='utf-8')
        json_data = parse_script_md(md_content, char_map, art_map)
        out_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"Success: {out_path.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()