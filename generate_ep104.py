from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 104
title = 'EP104: AI API Cost Guardrails — Keep Production Spend Predictable'
description = 'A practical framework for AI API budgets, token limits, routing rules, alerts, quotas, and circuit breakers that prevent surprise production costs.'
pub_date = 'Fri, 24 Jul 2026 08:30:00 +0000'
script = """EP104: AI API Cost Guardrails — Keep Production Spend Predictable

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about cost guardrails: the controls that let an AI product stay useful without allowing a traffic spike, prompt bug, or model change to turn into an unexpected bill.

Cost control starts with visibility. Every request should record the model, provider, input tokens, output tokens, cache status, retries, latency, route, tenant, feature, and final outcome. Without this data, a monthly invoice can tell you that spending rose, but not which workflow or customer caused it.

Set budgets at more than one level. A company-wide budget catches a catastrophic increase. A workspace budget protects against one customer consuming the shared pool. Feature budgets reveal expensive experiments. Per-request limits prevent a single long prompt or agent loop from doing disproportionate damage.

Use both token and currency limits. Token ceilings protect context and output size, while currency estimates account for differences between models. Reserve a maximum completion allowance before sending a request, then reconcile the actual usage after it finishes. A budget that is checked only after the charge is too late.

Choose model defaults deliberately. Route ordinary chat, classification, extraction, and summaries to models that meet the quality target at the lowest reliable cost. Escalate only when the task requires deeper reasoning, vision, a larger context window, or a specific capability. Expensive models should be an intentional exception, not a hidden default.

Treat retries as a cost multiplier. A timeout can mean the provider already did the work even when the caller did not receive the response. Use idempotency keys, cap retry counts, and track retry cost separately. If a route fails repeatedly, open a circuit breaker instead of allowing every worker to keep buying failed attempts.

Streaming needs a hard stop as well. Users may abandon a page while generation continues, or an agent may keep receiving tokens after it has enough information. Cancel disconnected requests, set maximum output tokens, and stop tool loops when their step or spending budget is reached.

Build quotas around real product behavior. A daily request quota is simple, but a weighted credit system is often fairer because a small model classification and a long-context reasoning task should not consume the same allowance. Make quota responses clear so users can understand whether to wait, upgrade, or reduce usage.

Alerts should be early and actionable. Notify operators when spend rate exceeds the expected baseline, when a model's unit cost changes, when fallback traffic becomes expensive, or when one tenant grows abnormally. Include the responsible route and the next control to use, such as lowering a cap or disabling a feature.

Test these controls with failure drills. Simulate an accidental large context, a recursive agent, a provider outage that triggers costly fallback, and a traffic burst. Verify that limits block the right requests, preserve essential traffic, and leave enough logs to explain the decision.

Cost guardrails are not about making AI products restrictive. They create room to ship useful capabilities with confidence, because each layer limits the blast radius of a mistake while keeping normal work moving.

That is it for today. Measure every request, set limits before the charge, and make expensive behavior deliberate. Try the unified API at crazyrouter.com, and see you in the next episode."""

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
