from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 114
title = 'EP114: AI API Monitoring and Observability — Find the Failure Before Users Do'
description = 'A practical observability guide for AI applications: measure latency, quality, routing, cost, retries, and provider health together so teams can detect silent failures before users report them.'
pub_date = 'Sun, 02 Aug 2026 08:30:00 +0000'
script = """EP114: AI API Monitoring and Observability — Find the Failure Before Users Do

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about monitoring and observability for AI API applications. A green uptime check does not mean an AI product is healthy. The endpoint may return HTTP 200 while latency doubles, output quality drops, tool calls fail, or the wrong model is selected for a tenant.

Start with the request journey. Capture a correlation ID from the application through the gateway, provider route, response, billing record, and user-visible result. Without one trace identifier, an operator has to guess whether a slow response came from the client, the gateway, the provider, a queue, or a retry.

Measure more than latency. Track time to first token, total response time, tokens per second, input and output tokens, payload size, queue delay, retry count, timeout rate, and cancellation rate. Streaming applications need both time to first token and time to completion. A fast first token can still hide a response that takes too long to finish.

Break metrics down by route. Aggregate numbers can look normal while one model, region, customer tier, or feature is failing. Dimensions should include model, provider, endpoint type, region, status class, application, and tenant policy where allowed. Keep cardinality under control by using stable labels and putting request-specific details in traces.

Watch for silent quality failures. A response can be valid JSON and still be unusable. Monitor schema validation, tool-call completion, citation presence, refusal rates, empty outputs, language mismatches, and task-specific evaluation scores. For important workflows, sample completed requests for offline review instead of pretending that availability is a proxy for quality.

Separate provider failure from application failure. Record the selected route, fallback decision, upstream status, normalized error code, and whether the request was retried. This lets a team answer a practical question quickly: did the provider fail, or did our own timeout, payload transformation, authentication, or rate-limit policy cause the failure?

Cost deserves first-class monitoring. Track spend by model, feature, tenant, route, and successful outcome. A cheaper model that requires three retries may cost more than a reliable model. Alert on sudden changes in token usage, unusually large prompts, duplicate requests, and cost per successful task rather than only total daily spend.

Build alerts around user impact. Alert on error-budget burn, time-to-first-token, failed tool calls, queue age, schema failures, and cost anomalies. Avoid paging on every transient provider error. A good alert includes the affected route, likely cause, current fallback, sample request IDs, and a link to the relevant trace or dashboard.

Use synthetic checks carefully. A scheduled request can confirm that authentication, routing, and a basic model response work. It cannot prove that production prompts, tools, large contexts, regional policies, or billing reconciliation work. Maintain a small set of synthetic scenarios that represent the real product, and mark their spend clearly.

Protect sensitive data in telemetry. Do not put full prompts, completions, API keys, or customer documents into ordinary logs. Redact secrets, hash or tokenize identifiers, sample payloads selectively, and apply tenant-scoped access. Observability is part of the security boundary, not an exception to it.

Keep traces useful for streaming and asynchronous jobs. Record when a request enters a queue, when a provider accepts it, when the first token arrives, when the final result is persisted, and when the user receives it. For background jobs, link retries and callbacks to the original trace rather than creating unrelated records.

Create a dashboard that supports decisions. The first view should show current availability, latency, quality signals, spend, provider health, and fallback volume. The next view should allow comparison by model and region. Operators should be able to move from an aggregate anomaly to a handful of representative request IDs without searching through raw logs.

Test observability during incidents. Deliberately expire a test credential, force a provider timeout, send an invalid tool schema, and route a workload to a fallback. Confirm that the right metric changes, the alert fires, the trace is complete, and the support view contains enough evidence without exposing customer content.

The practical lesson is simple. AI monitoring must connect infrastructure health to model behavior and business outcomes. Trace every request, measure streaming and quality signals, monitor cost per successful task, isolate sensitive telemetry, and make alerts actionable. When those pieces are in place, the team can investigate before users have to explain what went wrong.

That is it for today. Build observable multi-model applications with a unified API and clear routing data through Crazyrouter at crazyrouter.com, and see you in the next episode."""

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
