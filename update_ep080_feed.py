from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess, json
root = Path('/root/.openclaw/workspace/podcast')
feed = root / 'feed.xml'
audio = root / 'audio/ep080.mp3'
size = audio.stat().st_size
try:
    r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)], capture_output=True, text=True, check=True)
    sec = float(json.loads(r.stdout)['format']['duration'])
    dur = f"{int(sec//60)}:{int(sec%60):02d}"
except Exception:
    dur = '4:48'
ET.register_namespace('atom','http://www.w3.org/2005/Atom')
ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
for existing in channel.findall('item'):
    if (existing.findtext('title') or '').startswith('EP080:'):
        print('EP080 already in feed')
        break
else:
    item = ET.Element('item')
    ET.SubElement(item,'title').text = 'EP080: GPT-5 Parameters, Claude Code Setup, and API Hygiene'
    ET.SubElement(item,'description').text = 'A practical episode on why GPT-5-style reasoning models need cleaner request payloads, how to handle max_tokens versus max_completion_tokens, when to use reasoning_effort and verbosity, and why config-only Claude Code onboarding is better for users who already installed the CLI.'
    ET.SubElement(item,'pubDate').text = 'Mon, 08 Jun 2026 11:25:00 +0000'
    enc = ET.SubElement(item,'enclosure')
    enc.set('url','https://xujfcn.github.io/podcast/audio/ep080.mp3')
    enc.set('length',str(size))
    enc.set('type','audio/mpeg')
    ET.SubElement(item,'guid').text = 'https://xujfcn.github.io/podcast/audio/ep080.mp3'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = dur
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episode').text = '80'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType').text = 'full'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'
    ET.SubElement(item,'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep080'
    items = list(channel.findall('item'))
    if items:
        channel.insert(list(channel).index(items[0]), item)
    else:
        channel.append(item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
    print('inserted EP080', size, dur)
