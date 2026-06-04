from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess, json
root = Path('/root/.openclaw/workspace/podcast')
feed = root / 'feed.xml'
audio = root / 'audio/ep077.mp3'
size = audio.stat().st_size
try:
    r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)], capture_output=True, text=True, check=True)
    sec = float(json.loads(r.stdout)['format']['duration'])
    dur = f"{int(sec//60)}:{int(sec%60):02d}"
except Exception:
    dur = '9:56'
ET.register_namespace('atom','http://www.w3.org/2005/Atom')
ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
for existing in channel.findall('item'):
    if (existing.findtext('title') or '').startswith('EP077:'):
        print('EP077 already in feed')
        break
else:
    item = ET.Element('item')
    ET.SubElement(item,'title').text = 'EP077: Base URL Bugs Are Developer Experience Bugs'
    ET.SubElement(item,'description').text = 'API Base URL mistakes are one of the most common AI developer onboarding failures. This episode explains why missing /v1, wrong environment variables, UTM parameters in API endpoints, region endpoints, and unclear error paths turn small configuration details into support load — and how guides, generators, and troubleshooting pages convert support questions into growth assets.'
    ET.SubElement(item,'pubDate').text = 'Thu, 04 Jun 2026 09:20:00 +0000'
    enc = ET.SubElement(item,'enclosure')
    enc.set('url','https://xujfcn.github.io/podcast/audio/ep077.mp3')
    enc.set('length',str(size))
    enc.set('type','audio/mpeg')
    ET.SubElement(item,'guid').text = 'https://xujfcn.github.io/podcast/audio/ep077.mp3'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = dur
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episode').text = '77'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType').text = 'full'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'
    ET.SubElement(item,'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast'
    items = list(channel.findall('item'))
    if items:
        channel.insert(list(channel).index(items[0]), item)
    else:
        channel.append(item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
    print('inserted EP077', size, dur)
