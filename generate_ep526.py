from pathlib import Path
import json
import subprocess
import time
import xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 526
title = 'EP526: Policy Remediation Control Handover - Transfer Closed Fixes into Reliable Operations'
description = 'A practical guide to transferring verified AI gateway remediations into durable ownership, telemetry, response, change control, and steady-state operations.'
pub_date = 'Sun, 13 Sep 2026 20:50:00 +0000'
parts = [p for p in (root / f'episodes/ep{ep:03d}_script.txt').read_text().split('\n\n') if not p.startswith('METADATA_')]
(root / 'audio').mkdir(exist_ok=True)
for i, part in enumerate(parts, 1):
    output = root / f'episodes/ep{ep:03d}_chunk{i}.mp3'
    cmd = ['edge-tts', '--voice', 'en-US-GuyNeural', '--text', part, '--write-media', str(output)]
    for attempt in range(1, 6):
        try:
            subprocess.run(cmd, check=True)
            break
        except subprocess.CalledProcessError:
            if attempt == 5:
                raise
            time.sleep(attempt * 5)
concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file \'ep{ep:03d}_chunk{i}.mp3\'\n" for i in range(1, len(parts) + 1)))
audio = root / f'audio/ep{ep:03d}.mp3'
subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c:a', 'libmp3lame', '-q:a', '4', str(audio)], check=True)
seconds = float(json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True).stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
tree = ET.parse(root / 'feed.xml')
channel = tree.getroot().find('channel')
for old in list(channel.findall('item')):
    if (old.findtext('title') or '').startswith(f'EP{ep:03d}:'):
        channel.remove(old)
item = ET.Element('item')
for tag, value in [('title', title), ('description', description), ('pubDate', pub_date)]:
    ET.SubElement(item, tag).text = value
enc = ET.SubElement(item, 'enclosure')
enc.attrib.update(url=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3', length=str(audio.stat().st_size), type='audio/mpeg')
ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
for tag, value in [('duration', duration), ('episode', str(ep)), ('episodeType', 'full'), ('explicit', 'false')]:
    ET.SubElement(item, f'{{{ns}}}{tag}').text = value
ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep}'
channel.insert(0, item)
tree.write(root / 'feed.xml', encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {audio.stat().st_size} bytes {duration} {len(parts)} chunks')
