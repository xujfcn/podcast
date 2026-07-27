from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 107
title = 'EP107: AI API Versioning — Deprecate Models Without Breaking Customers'
description = 'A practical guide to versioning AI APIs and model routes: aliases, capability changes, deprecation windows, migration notices, compatibility tests, and rollback plans.'
pub_date = 'Mon, 27 Jul 2026 00:45:00 +0000'
script = """EP107: AI API Versioning — Deprecate Models Without Breaking Customers

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about a quiet part of AI infrastructure that becomes urgent the moment a model changes: versioning. Models improve quickly, but developers need stable contracts, predictable migrations, and enough notice to change production systems safely.

Start by separating the model name from the application contract. A provider model identifier can change, disappear, or gain different defaults. Your gateway should expose a clear route and document what that route promises: context limits, tool support, structured output, streaming, latency expectations, and pricing behavior.

Aliases are useful, but they need honest semantics. An alias such as fast, balanced, or reasoning can point to a recommended model while allowing the implementation to evolve. If an application depends on exact behavior, it should be able to pin a dated or immutable version. The more important the workflow, the less it should rely on an undocumented moving target.

Versioning is not only about syntax. A new model may accept the same JSON request while changing output style, tool selection, refusal behavior, token usage, or latency. Compatibility tests should therefore exercise real prompts and real workflows, not only check whether the endpoint returns HTTP 200.

Build a capability registry. Record whether each model supports vision, tools, JSON schema, streaming, reasoning controls, long context, image generation, audio, and provider-specific parameters. Include limits and known incompatibilities. Routing decisions should use this registry instead of assuming that similar model names provide identical capabilities.

Plan deprecation as a lifecycle. Announce the replacement, publish the differences, set a retirement date, and show migration examples. During the compatibility window, keep the old route available when practical and measure how much traffic still depends on it. A warning that nobody can see is not a migration plan.

Make notices actionable. Identify the affected route, the replacement route, the deadline, the behavior differences, and the test a developer should run. Put this information in the model catalog, API responses where appropriate, documentation, and direct customer communication for high-impact changes.

Use shadow traffic or replay tests before switching defaults. Send a safe sample of representative requests to the candidate route, compare accepted-result rate, structured output, tool calls, latency, token usage, and cost. Do not copy sensitive production data into an evaluation system without the right privacy controls.

Keep rollback possible. A migration should be a configuration change with a clear previous target, not an irreversible code rewrite. Record which alias pointed to which version, when it changed, and what metrics would trigger a rollback. This makes an incident diagnosable instead of turning it into a debate about which change happened first.

Be careful with automatic upgrades. They are convenient for low-risk classification or summarization, but dangerous for workflows with strict schemas, financial decisions, code changes, or customer-visible wording. Route by risk and allow teams to choose between a maintained alias and a pinned version.

Pricing changes belong in the same release process. A model that is technically compatible may still change the economics of a workflow. Track cost per accepted result, not just the advertised token price, and notify users when a recommended route changes its cost or fallback behavior.

Finally, treat documentation as part of the API. Keep model IDs, examples, limits, deprecation dates, and migration guides synchronized with the live catalog. A stale page can be as damaging as a broken endpoint because developers build integrations from what they can read.

That is it for today. Give every model route a contract, every deprecation a deadline, and every migration a test and rollback path. Build stable AI integrations with the unified API at crazyrouter.com, and see you in the next episode."""

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
