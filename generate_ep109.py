from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 109
title = 'EP109: AI API Rate Limits — Survive 429s Without Creating a Retry Storm'
description = 'A production guide to AI API rate limits: concurrency budgets, token-aware throttling, Retry-After, exponential backoff, fair queues, fallback controls, and overload testing.'
pub_date = 'Tue, 28 Jul 2026 08:30:00 +0000'
script = """EP109: AI API Rate Limits — Survive 429s Without Creating a Retry Storm

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about rate limits. A provider returning HTTP 429 is not unusual. The real incident begins when every client retries at once, fills the queue, triggers more limits, and turns a temporary capacity problem into a system-wide outage.

First, learn what is being limited. Providers may enforce requests per minute, tokens per minute, concurrent requests, daily quotas, or separate limits for each model and account. A gateway should model these dimensions independently. Counting only requests is misleading when one prompt uses five hundred tokens and another uses one hundred thousand.

Set an explicit concurrency budget for every upstream route. Do not allow application traffic to create an unlimited number of in-flight provider calls. Use a semaphore or admission controller, and leave headroom for retries, health checks, and high-priority workloads. A full budget should create backpressure before it creates upstream chaos.

Honor Retry-After whenever the provider sends it. Otherwise, use exponential backoff with random jitter. Jitter matters because identical retry schedules synchronize clients into another traffic spike. Put a hard limit on attempts and total elapsed time. A request should never retry forever just because each individual wait looks reasonable.

Retries need a budget, not just a policy. Track the ratio of retry traffic to original traffic and stop retrying when the system is overloaded. Reserve retry capacity separately so failed work cannot consume every available slot. For interactive requests, one fast fallback may be better than three slow attempts against the same provider.

Build a token-aware queue. Estimate input size before dispatch and reserve expected output capacity when practical. Update the estimate from actual usage after completion. It will not be perfect, but it is much better than treating every request as equal while a few large-context jobs consume the entire token allowance.

Use fair scheduling between customers and workloads. Without it, one batch job can starve every chat request. Apply per-tenant limits, weighted queues, or separate capacity pools for interactive, background, and administrative traffic. Fairness is part of reliability in a multi-tenant gateway.

Fallbacks must respect capabilities and economics. A substitute model should support the required context length, tools, structured output, and policy constraints. It should also stay within the customer's price and latency boundaries. A fallback that returns an incompatible answer is not recovery.

Expose useful limit information to clients. Return a stable error code, request identifier, whether the failure is retryable, and an appropriate Retry-After value. If you publish remaining quota headers, define their scope clearly. Ambiguous quota numbers encourage clients to build incorrect retry logic.

Protect long-running streams. Once output has started, blindly replaying the request can duplicate text, tool calls, or charges. Track whether a response is safe to retry and use idempotency keys for operations that can trigger external effects. Streaming failures need different recovery logic from failures before the first token.

Monitor saturation before 429 volume becomes high. Watch queue depth, queue wait time, active concurrency, token consumption velocity, retry amplification, and rejection rate by route. Alert on sustained user impact rather than every individual rate-limit response.

Test overload deliberately. Replay bursts, large prompts, slow streams, provider throttling, and partial regional failures in a controlled environment. Confirm that the queue remains bounded, high-priority traffic keeps moving, retries stay within budget, and recovery does not cause a second spike.

Finally, coordinate limits across providers. A gateway can smooth temporary capacity problems by routing eligible work elsewhere, but shared fallback capacity can also become the next bottleneck. Admission control should understand the whole route graph, not only the provider that failed first.

That is it for today. Bound concurrency, honor provider signals, add jitter, schedule fairly, and test overload before customers do it for you. Build resilient multi-model applications with the unified API at crazyrouter.com, and see you in the next episode."""

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
