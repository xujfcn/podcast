from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 108
title = 'EP108: AI Gateway Observability — Measure Latency, Cost, Quality, and Failover'
description = 'A practical observability blueprint for AI gateways: trace every request, separate time to first token from total latency, attribute cost, monitor fallbacks, protect prompt data, and alert on user-visible failures.'
pub_date = 'Mon, 27 Jul 2026 13:50:00 +0000'
script = """EP108: AI Gateway Observability — Measure Latency, Cost, Quality, and Failover

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are building an observability system for an AI API gateway. Traditional service monitoring is necessary, but it is not enough. An AI request can return HTTP 200 and still be slow, expensive, malformed, routed to the wrong model, or useless to the customer.

Start with one trace identifier that follows the request through authentication, routing, provider calls, retries, fallbacks, streaming, and billing. Return that identifier to the client and include it in support tooling. When a developer reports a bad response, your team should be able to find the exact route and sequence without asking them to send sensitive prompts over email.

Measure latency in stages. Record queue time, provider connection time, time to first token, streaming duration, and total duration. Time to first token shapes how responsive a chat application feels, while total duration matters for batch jobs. A single average latency number hides both experiences.

Use percentiles instead of relying on averages. Track the median, p ninety-five, and p ninety-nine by model, provider, region, and route. Averages can look healthy while a small but important group of users waits thirty seconds. Compare percentiles over time and against a known service objective.

Cost needs request-level attribution. Capture input tokens, output tokens, cached tokens, reasoning tokens where available, provider price, customer price, and any retry cost. Then aggregate by customer, API key, model, application, and feature. Cost per successful result is usually more useful than cost per raw request.

Make routing visible. Record the requested model, selected provider, actual upstream model, routing rule, and fallback reason. A fallback that saves availability can also change latency, capability, or price. Operators and customers need to know when that happened, especially for pinned or compliance-sensitive workloads.

Separate transport success from application success. Validate structured output, tool-call arguments, content policy outcomes, truncation, empty responses, and application-specific acceptance checks. An endpoint that returns valid JSON with the wrong schema is not healthy from the user's perspective.

Quality monitoring requires care. Use deterministic checks where possible, such as schema validity, citation presence, tool execution success, or exact task completion. For subjective tasks, sample outputs into a controlled evaluation pipeline. Do not treat an uncalibrated model judge as objective truth.

Protect customer data by default. Logs should store metadata and hashes rather than full prompts and responses unless a customer explicitly enables content logging. Redact secrets, personal information, authorization headers, and uploaded document contents. Set clear retention periods and access controls for every telemetry store.

Build dashboards around decisions. An operations view should show error rate, throttling, time to first token, fallback rate, provider health, and spend velocity. A product view should show completion success, feature usage, and cost per accepted result. A customer view should expose their usage and request identifiers without revealing internal credentials or other tenants.

Alerts should map to user impact. Page someone for sustained failure, extreme latency, exhausted provider capacity, broken billing, or runaway spend. Lower-priority changes belong in tickets or daily reports. Too many alerts train the team to ignore the one that matters.

Test the observability path itself. Simulate provider timeouts, malformed streaming events, rate limits, billing mismatches, and fallback exhaustion. Confirm that traces remain connected and alerts include the request identifiers, affected models, start time, and mitigation options.

Finally, use the data to improve routing. Compare providers by accepted-result rate, latency percentile, and effective cost for each workload. Observability is not only for incident response. It is the evidence that turns model routing from guesswork into an engineering system.

That is it for today. Trace the whole request, measure the experience the user actually sees, and protect the content behind the metrics. Build observable multi-model applications with the unified API at crazyrouter.com, and see you in the next episode."""

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
