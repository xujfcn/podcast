from pathlib import Path
import json
import re
import subprocess
import xml.etree.ElementTree as ET

import requests

root = Path('/root/.openclaw/workspace/podcast')
(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)

ep = 93
title = 'EP093: Fallbacks Are Product Features, Not Afterthoughts'
description = 'A practical episode on designing AI API fallbacks as a first-class product feature: routing rules, compatibility checks, retry budgets, observability, cost controls, and user-visible behavior when a preferred model is unavailable.'
pub_date = 'Mon, 13 Jul 2026 16:20:00 +0000'

script = """EP093: Fallbacks Are Product Features, Not Afterthoughts

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about fallbacks.

In AI infrastructure, fallbacks are often treated like emergency plumbing. A model goes down, rate limits spike, a provider has a regional problem, and the gateway quietly sends the request somewhere else. That sounds simple, but in production a fallback is not just a technical escape hatch. It is part of the user experience.

The first design question is compatibility. Two models may both support chat completions, but that does not mean they behave the same way. They may differ in tool calling, JSON mode, image input, context limits, safety behavior, reasoning traces, latency, and output style. If a fallback ignores those differences, the request may technically succeed while the application breaks in a more subtle way.

That is why fallback rules should be explicit. A coding workload might fall back from one strong coding model to another, but not to a cheap general model. A vision workload should only fall back to another vision-capable model. A strict JSON workflow should only use models that have been tested against the schema behavior the application expects.

The second design question is budget. Fallbacks can accidentally turn an outage into a billing surprise. If the primary model is cheap and the fallback is premium, every retry can become more expensive. A good gateway should let teams define retry budgets, maximum fallback price, maximum attempts, and whether a fallback is allowed at all for a given route.

There is also a latency budget. Sometimes the right answer is not to retry forever. For an interactive product, a fast, clear failure can be better than a slow fallback that arrives too late. For a background job, waiting longer may be acceptable. Fallback policy should match the user experience, not just the infrastructure preference.

The third design question is visibility. Silent fallbacks are convenient until someone needs to debug quality, cost, or correctness. Developers should be able to see when a fallback happened, which model handled the final request, how many attempts were made, and why the original route failed. Logs, usage records, and dashboards should use names that match the public model catalog.

This is especially important for support. If a customer says, I sent this to model A but got behavior from model B, the answer should not be a mystery. The system should make the route decision explainable without exposing private provider internals.

The fourth design question is control. Some teams want maximum availability. Some want deterministic behavior. Some want the lowest cost. Some want to avoid specific providers for compliance or procurement reasons. A useful fallback system should support different policies instead of assuming one global answer.

For API gateway operators, the practical checklist is straightforward. Test fallback pairs before enabling them. Confirm endpoint compatibility. Confirm tool and JSON behavior. Confirm pricing. Confirm observability labels. Confirm user-facing documentation. Then roll out the policy gradually, starting with low-risk workloads.

One underrated pattern is declaring fallback groups by intent. Instead of saying model A falls back to model B, define groups like fast chat, coding, long context, image understanding, or premium reasoning. Then the gateway can route within a group while preserving the intent of the workload. That makes policies easier to understand and easier to update as new models arrive.

The larger point is that reliability is not only uptime. Reliability means the system behaves predictably when something goes wrong. Fallbacks can improve reliability, but only when they preserve compatibility, respect budgets, and leave a clear trail.

So the takeaway for today is simple. Do not bolt fallbacks on at the end. Treat them as a product feature. Make the policy explicit, test the route, expose the decision, and give developers control. In a model market that changes every week, that discipline turns provider volatility into a manageable part of the platform.

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
