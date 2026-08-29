from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 270
title = 'EP270: AI API Gateway Cancellation Contracts - Stop Work When the User Leaves'
description = 'A practical guide to cancellation contracts in AI API gateways: model operation states, propagate cancellation, stop tools and side effects, reconcile uncertain usage, and make retries safe.'
pub_date = 'Sat, 29 Aug 2026 11:15:00 +0000'
parts = (root / f'episodes/ep{ep:03d}_script.txt').read_text().split('\n\n')
(root / 'audio').mkdir(exist_ok=True)
for i, part in enumerate(parts, 1):
    subprocess.run(['edge-tts', '--voice', 'en-US-GuyNeural', '--text', part, '--write-media', str(root / f'episodes/ep{ep:03d}_chunk{i}.mp3')], check=True)
concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file 'ep{ep:03d}_chunk{i}.mp3'\n" for i in range(1, len(parts) + 1)))
audio = root / f'audio/ep{ep:03d}.mp3'
subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c:a', 'libmp3lame', '-q:a', '4', str(audio)], check=True)
seconds = float(json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True).stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
tree = ET.parse(root / 'feed.xml')
channel = tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in channel.findall('item')):
    item = ET.Element('item')
    for tag, value in [('title', title), ('description', description), ('pubDate', pub_date)]: ET.SubElement(item, tag).text = value
    enc = ET.SubElement(item, 'enclosure'); enc.attrib.update(url=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3', length=str(audio.stat().st_size), type='audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    for tag, value in [('duration', duration), ('episode', str(ep)), ('episodeType', 'full'), ('explicit', 'false')]: ET.SubElement(item, f'{{{ns}}}{tag}').text = value
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep}'
    channel.insert(0, item); tree.write(root / 'feed.xml', encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {audio.stat().st_size} bytes {duration} {len(parts)} chunks')
