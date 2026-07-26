from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 106
title = 'EP106: Prompt Caching in Production — Lower Cost Without Stale Behavior'
description = 'A practical guide to prompt caching for AI APIs: cacheable prefixes, routing consistency, measurement, invalidation, privacy, and the production checks that keep savings reliable.'
pub_date = 'Sun, 26 Jul 2026 15:45:00 +0000'
script = """EP106: Prompt Caching in Production — Lower Cost Without Stale Behavior

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are looking at prompt caching: a useful way to reduce repeated input processing when AI applications send the same large instructions, documents, or tool definitions across many requests.

The basic opportunity is simple. Production prompts often contain a stable prefix and a small changing suffix. The stable part may include a system prompt, policy manual, repository context, product catalog, or tool schema. If the provider can reuse work for that prefix, later requests may become cheaper or faster.

Start by identifying genuinely stable content. Separate global instructions from user-specific state, current events, temporary permissions, and request data. A cache works best when the beginning of the prompt remains byte-for-byte consistent. Small changes near the front can prevent reuse even when most of the content is identical.

Prompt construction therefore becomes an engineering interface. Keep stable sections in a deterministic order. Normalize generated schemas. Avoid timestamps, random identifiers, and request-specific metadata inside the reusable prefix. Put volatile context as late as the model and provider format allow.

Measure cache behavior explicitly. Record cache creation tokens, cache read tokens, ordinary input tokens, output tokens, model, provider, route, latency, and final task result. A lower input bill is useful only if the response remains correct and the overall workflow still succeeds.

Routing consistency matters. A cache created on one provider, model version, or region may not exist on another. Aggressive load balancing can reduce cache hits, while strict route affinity can reduce resilience. Choose the tradeoff deliberately and keep fallback behavior correct when a cached route is unavailable.

Do not assume every request deserves caching. A short prompt with low repetition may gain nothing. Large shared instructions used many times are stronger candidates. Estimate the break-even point using real traffic frequency, cache lifetime, write cost, read discount, and the probability that the prefix changes.

Treat invalidation as a product requirement. When a policy, tool schema, price, permission, or knowledge document changes, the application must stop relying on the old prefix. Version cacheable content and include the version in observability so operators can connect an unexpected answer to the exact prompt state.

Privacy boundaries must remain intact. Never let cache design mix tenant-specific data across users unless the provider contract and your own access model make that explicitly safe. Shared prefixes should contain only content intended to be shared, and sensitive material should follow the same retention and logging rules as uncached prompts.

Test output stability before rollout. Compare cached and uncached requests on a representative evaluation set. Check structured output, tool selection, citations, instruction following, latency, and accepted-result rate. Caching should be an optimization below the application contract, not a source of different behavior.

Roll out with a small traffic slice. Watch cache hit rate, cost per accepted result, tail latency, fallback frequency, and error rate. A high hit rate can still be misleading if requests become harder to debug or route failures create expensive retries.

Prompt caching works best when prompts are already well structured. Stable instructions, versioned context, deterministic serialization, and clear tenant boundaries improve the system even before savings appear. The cache then rewards good prompt architecture instead of hiding weak design.

That is it for today. Find the repeated prefixes, measure the full workflow, and make invalidation and privacy part of the implementation from day one. Build with the unified API at crazyrouter.com, and see you in the next episode."""

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
key = re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)', tools).group(1)
parts = script.split('\n\n')

for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_chunk{i}.mp3'
    if out.exists() and out.stat().st_size > 1000:
        print('part', i, 'cached', flush=True)
        continue
    for attempt in range(1, 4):
        response = requests.post(
            'https://crazyrouter.com/v1/audio/speech',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
            timeout=300,
        )
        print('part', i, response.status_code, 'attempt', attempt, flush=True)
        if response.ok:
            out.write_bytes(response.content)
            break
        if attempt == 3:
            response.raise_for_status()
        time.sleep(5 * attempt)

concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file 'ep{ep:03d}_chunk{i}.mp3'\n" for i in range(1, len(parts) + 1)))
audio = root / f'audio/ep{ep:03d}.mp3'
subprocess.run(
    ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(audio)],
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
probe = subprocess.run(
    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)],
    capture_output=True,
    text=True,
    check=True,
)
seconds = float(json.loads(probe.stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
size = audio.stat().st_size

feed = root / 'feed.xml'
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
if not any((item.findtext('title') or '').startswith(f'EP{ep:03d}:') for item in channel.findall('item')):
    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = pub_date
    enclosure = ET.SubElement(item, 'enclosure')
    enclosure.set('url', f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3')
    enclosure.set('length', str(size))
    enclosure.set('type', 'audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    ET.SubElement(item, f'{{{ns}}}duration').text = duration
    ET.SubElement(item, f'{{{ns}}}episode').text = str(ep)
    ET.SubElement(item, f'{{{ns}}}episodeType').text = 'full'
    ET.SubElement(item, f'{{{ns}}}explicit').text = 'false'
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'
    existing = channel.findall('item')
    channel.insert(list(channel).index(existing[0]) if existing else len(list(channel)), item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)

print('DONE', audio, size, duration)
