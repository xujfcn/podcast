from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess, json
root = Path('/root/.openclaw/workspace/podcast')
feed = root / 'feed.xml'
audio = root / 'audio/ep081.mp3'
size = audio.stat().st_size
try:
    r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)], capture_output=True, text=True, check=True)
    sec = float(json.loads(r.stdout)['format']['duration'])
    dur = f"{int(sec//60)}:{int(sec%60):02d}"
except Exception:
    dur = '5:08'
ET.register_namespace('atom','http://www.w3.org/2005/Atom')
ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
for existing in channel.findall('item'):
    if (existing.findtext('title') or '').startswith('EP081:'):
        print('EP081 already in feed')
        break
else:
    item = ET.Element('item')
    ET.SubElement(item,'title').text = 'EP081: Turning Claude Code Guides into Developer Growth Infrastructure'
    ET.SubElement(item,'description').text = 'A practical episode on how a Claude Code guide repository can become developer growth infrastructure: correct base URL rules, UTM discipline, searchable docs, setup scripts, FAQs, and multi-platform content distribution built from validated developer onboarding.'
    ET.SubElement(item,'pubDate').text = 'Tue, 09 Jun 2026 11:20:00 +0000'
    enc = ET.SubElement(item,'enclosure')
    enc.set('url','https://xujfcn.github.io/podcast/audio/ep081.mp3')
    enc.set('length',str(size))
    enc.set('type','audio/mpeg')
    ET.SubElement(item,'guid').text = 'https://xujfcn.github.io/podcast/audio/ep081.mp3'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = dur
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episode').text = '81'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType').text = 'full'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'
    ET.SubElement(item,'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep081'
    items = list(channel.findall('item'))
    if items:
        channel.insert(list(channel).index(items[0]), item)
    else:
        channel.append(item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
    print('inserted EP081', size, dur)
