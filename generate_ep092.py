from pathlib import Path
import json
import re
import subprocess
import xml.etree.ElementTree as ET

import requests

root = Path('/root/.openclaw/workspace/podcast')
(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)

ep = 92
title = 'EP092: Model Catalogs Are Production Interfaces'
description = 'A practical episode on why AI model catalogs need operational discipline: exact aliases, access rules, pricing visibility, endpoint examples, deprecation notes, and release checks that keep developer workflows from breaking as model lists change.'
pub_date = 'Thu, 09 Jul 2026 10:20:00 +0000'

script = """EP092: Model Catalogs Are Production Interfaces

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about something that looks simple from the outside: the model catalog.

Every AI platform has some version of it. A list of model names, prices, context windows, modalities, and maybe a few tags like fast, reasoning, vision, or coding. It can look like documentation. It can look like marketing. But in production, the model catalog is much more than a list. It is an interface.

Developers build against it. They copy model strings into configuration files. They add aliases to environment variables. They build dropdowns, routing rules, allowlists, dashboards, budget checks, and fallback policies around those names. If the catalog is vague, stale, or inconsistent, the breakage does not stay on the docs page. It leaks into runtime behavior.

That is why model catalogs need operational discipline. The first rule is exact naming. If a model appears as claude-sonnet-5 in an email, claude-sonnet-five in a dashboard, and claude-5-sonnet in a code example, users will not know which one is real. Even if the gateway supports aliases, the canonical name should be obvious and stable.

The second rule is access visibility. A model can be listed and still fail for a user if their token has a restricted allowlist, their account lacks permission, or the route is temporarily disabled. A good catalog should make access state understandable. Is this model generally available? Is it beta? Does it require enabling? Does it support the same endpoint shape as the rest of the gateway?

This is especially important for API gateways because the gateway is trying to reduce provider-specific complexity. Users do not want to memorize every native provider's account setup, parameter naming, and billing rules. They want one endpoint, one key, and predictable model selection. The catalog is where that promise becomes concrete.

Pricing is another place where catalog quality matters. A price table is not just a finance artifact. It informs routing decisions. Teams choose models based on input price, output price, context length, latency, quality, and fallback behavior. If pricing is missing or stale, developers either guess or overfit to old assumptions.

But pricing should also be presented carefully. The cheapest model per million tokens is not always the cheapest model per successful task. A model that needs retries, longer prompts, or manual correction may cost more in practice. A strong catalog can show raw prices while still pushing teams toward task-level measurement.

The third rule is endpoint clarity. Every important model should have at least one clean request example. That example should use the real base URL, the real model string, and a minimal payload. Human-facing links can have UTM parameters. API base URLs inside code blocks should never have campaign tracking. Developers copy examples directly, so examples are part of the product surface.

The fourth rule is deprecation discipline. Models move quickly. Some are renamed. Some are replaced by newer versions. Some providers change availability. A catalog should not silently remove or rename models without a migration path. At minimum, users need old name, new name, effective date, and expected behavior during the transition.

For teams operating a gateway, this creates a practical release checklist. When adding a model, verify a real request. Confirm the model appears in the catalog. Confirm pricing and context limits. Confirm token allowlist behavior. Confirm the code example. Confirm observability labels. Then announce it.

The observability point is easy to miss. If the catalog says one model name but logs use another internal route name, support gets harder. When a user asks why a request failed, the support team should be able to search the same model string the user typed. Catalog names, logs, billing records, and docs should line up.

This is the unglamorous work that makes AI infrastructure feel reliable. Model launches get attention, but catalog hygiene keeps launches from turning into support load. It also helps growth because every new model page, comparison page, and tutorial becomes easier to keep consistent.

So the takeaway for today is simple. Treat your model catalog as a production interface, not a static page. Keep names canonical, access rules visible, pricing current, examples clean, deprecations explicit, and logs aligned. In a fast-moving model market, that discipline is what lets developers move quickly without breaking their own workflows.

That is it for today. Thanks for listening to AI Dev Tools — The Crazyrouter Podcast. See you in the next episode."""

script_path = root / f'episodes/ep{ep:03d}_script.txt'
script_path.write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8', errors='ignore')
m = re.search(r'Bearer\s+(sk-[A-Za-z0-9_\-]+)', tools)
if not m:
    raise SystemExit('Crazyrouter API key not found')
key = m.group(1)

paras = script.split('\n\n')
n = len(paras)
parts = [
    '\n\n'.join(paras[: n // 3]),
    '\n\n'.join(paras[n // 3 : 2 * n // 3]),
    '\n\n'.join(paras[2 * n // 3 :]),
]

for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_part{i}.mp3'
    if not out.exists() or out.stat().st_size < 1000:
        r = requests.post(
            'https://crazyrouter.com/v1/audio/speech',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
            timeout=300,
        )
        print('part', i, 'status', r.status_code, r.headers.get('content-type'), flush=True)
        if not r.ok:
            print(r.text[:500])
            r.raise_for_status()
        out.write_bytes(r.content)
    print('saved', out.name, out.stat().st_size, flush=True)

concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join([f"file 'ep{ep:03d}_part{i}.mp3'\n" for i in range(1, 4)]), encoding='utf-8')
subprocess.run(
    ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(root / f'audio/ep{ep:03d}.mp3')],
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
audio = root / f'audio/ep{ep:03d}.mp3'
size = audio.stat().st_size

try:
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)],
        capture_output=True,
        text=True,
        check=True,
    )
    sec = float(json.loads(r.stdout)['format']['duration'])
    dur = f'{int(sec // 60)}:{int(sec % 60):02d}'
except Exception:
    dur = '6:00'

feed = root / 'feed.xml'
ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
for existing in channel.findall('item'):
    if (existing.findtext('title') or '').startswith(f'EP{ep:03d}:'):
        print(f'EP{ep:03d} already in feed')
        break
else:
    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = pub_date
    enc = ET.SubElement(item, 'enclosure')
    enc.set('url', f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3')
    enc.set('length', str(size))
    enc.set('type', 'audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = dur
    ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}episode').text = str(ep)
    ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType').text = 'full'
    ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'
    items = list(channel.findall('item'))
    if items:
        channel.insert(list(channel).index(items[0]), item)
    else:
        channel.append(item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
    print('inserted', f'EP{ep:03d}', size, dur)

ET.parse(feed)
print('done', audio, size, dur)
