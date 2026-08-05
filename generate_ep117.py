from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 117
title = 'EP117: AI API Capacity Planning — Prepare for Traffic Before It Becomes an Incident'
description = 'A practical guide to AI API capacity planning: forecast tokens, concurrency, queues, quotas, burst traffic, and fallback headroom before growth turns into an incident.'
pub_date = 'Wed, 05 Aug 2026 08:30:00 +0000'
script = "EP117: AI API Capacity Planning — Prepare for Traffic Before It Becomes an Incident\n\nWelcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about capacity planning for AI API applications. Traditional systems plan around requests per second, CPU, memory, and database connections. AI workloads add token volume, context size, output length, model-specific limits, queue time, and provider quotas. A simple request count is no longer enough.\n\nStart by classifying workloads. Interactive chat, coding agents, document extraction, image generation, embeddings, and batch summarization behave differently. Record arrival rate, input size, expected output, latency target, concurrency, and retry behavior for each class. Planning from one global average will underestimate the peaks that actually cause incidents.\n\nTranslate traffic into model demand. For language models, estimate input and output tokens per minute, concurrent streams, and requests per minute. For image or video generation, measure jobs in flight and completion time. Providers may enforce several limits simultaneously, so spare request capacity does not help when the token quota is exhausted.\n\nPlan for bursts, not only daily totals. Product launches, cron jobs, customer imports, and regional traffic patterns can compress a day's work into a few minutes. Use historical peak windows and realistic growth scenarios. Separate predictable bursts from unexpected ones so scheduled jobs can be moved away from interactive traffic.\n\nConcurrency is often the hidden constraint. Streaming responses hold connections open, agents make multiple sequential calls, and retries overlap with new traffic. Measure the full lifetime of an operation rather than counting only the initial request. A workflow with five model calls can consume far more capacity than its user action count suggests.\n\nBuild queues with explicit policies. Batch and asynchronous work should have priority, expiration, maximum retry count, and idempotency keys. Monitor queue age, not just queue length. A short queue of long-running video jobs may represent more delay than thousands of fast embedding tasks.\n\nReserve capacity for failure. If normal operation consumes nearly every quota, there is no room for retries or provider failover. Keep headroom for traffic growth, regional outages, and slower fallback models. The required margin depends on workload importance and how quickly additional quota can be obtained.\n\nTreat fallback capacity as a real dependency. A secondary provider is not useful if its quota supports only a small fraction of production traffic. Test exact payloads and estimate how much load each fallback route can absorb. Decide which workloads keep full service, which degrade, and which wait in a queue during a failover.\n\nControl demand before dropping requests. Limit maximum context, cap output tokens, trim conversation history, cache repeated results, deduplicate jobs, and use smaller models for routine tasks. These controls reduce both cost and capacity pressure. Apply them by workload rather than imposing one crude global limit.\n\nUse admission control for overload. When capacity is exhausted, reject or defer low-priority work early with a clear response. Allowing every request to enter the system can create retry storms, longer queues, and timeouts that waste capacity without producing useful outcomes.\n\nWatch the right indicators. Track quota utilization, tokens per minute, concurrent streams, queue age, retry volume, fallback use, provider throttling, and latency percentiles. Add cost per successful outcome because an overloaded system may spend more while completing less work.\n\nRun load tests with representative prompts and workflows. Tiny synthetic requests will not reveal problems caused by large contexts, tool schemas, streaming, or agent loops. Test gradual growth, sudden bursts, provider throttling, and partial failover. Confirm that limits protect important traffic and that recovery does not release a queue all at once.\n\nReview forecasts regularly. Compare predicted demand with actual usage by model, feature, tenant, and region. Update assumptions after launches, pricing changes, model migrations, and new agent behavior. Capacity planning is a feedback loop, not a spreadsheet created once before production.\n\nThe practical lesson is simple. Plan AI capacity in tokens, concurrency, queue time, and successful workflows—not just requests per second. Classify demand, keep failure headroom, validate fallback quotas, control overload early, and test with realistic payloads.\n\nThat is it for today. Route and monitor multi-model workloads through one unified API with Crazyrouter at crazyrouter.com, and see you in the next episode."

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
key = re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)', tools).group(1)
parts = script.split('\n\n')

for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_chunk{i}.mp3'
    if out.exists() and out.stat().st_size > 1000:
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
subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(audio)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True)
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
