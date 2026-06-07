from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess, json
root = Path('/root/.openclaw/workspace/podcast')
feed = root / 'feed.xml'
audio = root / 'audio/ep079.mp3'
size = audio.stat().st_size
try:
    r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)], capture_output=True, text=True, check=True)
    sec = float(json.loads(r.stdout)['format']['duration'])
    dur = f"{int(sec//60)}:{int(sec%60):02d}"
except Exception:
    dur = '5:10'
ET.register_namespace('atom','http://www.w3.org/2005/Atom')
ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
for existing in channel.findall('item'):
    if (existing.findtext('title') or '').startswith('EP079:'):
        print('EP079 already in feed')
        break
else:
    item = ET.Element('item')
    ET.SubElement(item,'title').text = 'EP079: Cost per Accepted Image Is the Metric That Matters'
    ET.SubElement(item,'description').text = 'Image generation pricing is misleading if teams only compare cost per request. This episode explains cost per accepted image, why model demos are not enough, and how developers can use a repeatable test matrix across GPT Image, Imagen, Qwen Image, and FLUX-style models before choosing production routes.'
    ET.SubElement(item,'pubDate').text = 'Sun, 07 Jun 2026 09:20:00 +0000'
    enc = ET.SubElement(item,'enclosure')
    enc.set('url','https://xujfcn.github.io/podcast/audio/ep079.mp3')
    enc.set('length',str(size))
    enc.set('type','audio/mpeg')
    ET.SubElement(item,'guid').text = 'https://xujfcn.github.io/podcast/audio/ep079.mp3'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = dur
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episode').text = '79'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType').text = 'full'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'
    ET.SubElement(item,'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep079'
    items = list(channel.findall('item'))
    if items:
        channel.insert(list(channel).index(items[0]), item)
    else:
        channel.append(item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
    print('inserted EP079', size, dur)
