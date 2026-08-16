from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 135
title = 'EP135: AI API Observability — Measure Quality, Latency, and Cost Together'
description = 'A practical guide to AI API observability: connect traces, quality signals, latency, errors, token usage, and cost so teams can debug and improve production workloads.'
pub_date = 'Sun, 23 Aug 2026 08:30:00 +0000'
script = '''EP135: AI API Observability — Measure Quality, Latency, and Cost Together

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI applications can fail in ways that ordinary web dashboards do not explain. A request may return HTTP 200 while producing invalid JSON, an answer may be correct but too slow, or a cheaper model may create more retries and higher total cost. Today we will build an observability approach that connects quality, performance, and spend.

Start with a request trace. Give every user operation a correlation ID and carry it across the application, gateway, model request, tool call, retry, and fallback. Record the route, model, provider, streaming mode, status, latency, and token counts. Without a shared trace ID, one slow user request becomes a collection of unrelated log lines.

Separate the latency components. Measure time to first token, time between streamed tokens, total completion time, queue time, and upstream response time. These metrics answer different questions. A fast first token does not help if the final answer arrives after the user has timed out. Track percentiles, especially p95 and p99, rather than relying on averages.

Capture quality signals that can be checked. For structured output, record schema-validation success. For tool use, record whether the selected tool was appropriate and whether the result completed the task. For retrieval, measure citation presence or groundedness where a reliable evaluator exists. Combine automated checks with sampled human review, because no single score represents every use case.

Make errors meaningful. Distinguish authentication failures, rate limits, timeouts, context overflow, content-policy responses, malformed outputs, and application-level rejection. A generic failure count cannot tell an engineer whether to change credentials, add backoff, shorten prompts, or fix a parser.

Track retries and fallbacks as first-class events. A request that succeeds only after two retries is not equivalent to a first-attempt success. Record which route was attempted, why the fallback activated, and whether the fallback preserved quality. This also prevents teams from underestimating the real cost of reliability problems.

Connect usage to cost. Store input tokens, output tokens, cached tokens when available, and the effective price for the selected route. Report cost per request, cost per accepted result, and cost by product feature or customer cohort. A unified gateway such as Crazyrouter can provide one routing and accounting layer across models, making comparisons easier while applications keep a consistent API surface.

Protect sensitive data in telemetry. Do not place API keys, full private prompts, or unredacted personal data into ordinary logs. Prefer hashed identifiers, sampled payloads, structured metadata, and short-lived restricted traces. Observability is useful only if it does not create a second security problem.

Create useful dashboards. The first dashboard should show request volume, success rate, p95 latency, validation failures, fallback share, and cost. Break each metric down by model, route, endpoint, and feature. Add links from an alert to representative traces, so an on-call engineer can move from a symptom to evidence quickly.

Set alerts around user impact. Alert on sustained increases in failed accepted results, timeout rate, schema errors, or cost per successful task. Avoid paging on every transient provider error. Use thresholds and windows that reflect the workload, and annotate deployments, routing changes, and provider incidents so teams can distinguish regressions from known events.

The practical lesson is simple: AI observability cannot stop at uptime. Measure whether the answer was usable, how long it took, what route produced it, and what it cost. When those signals share one trace, teams can improve quality and reliability without guessing.

That is it for today. Instrument the outcome, not just the request. Visit crazyrouter.com, and see you in the next episode.'''

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script)
parts = script.split('\n\n')
for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_chunk{i}.mp3'
    subprocess.run(['edge-tts', '--voice', 'en-US-GuyNeural', '--text', part, '--write-media', str(out)], check=True)
concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file 'ep{ep:03d}_chunk{i}.mp3'\n" for i in range(1, len(parts) + 1)))
audio = root / f'audio/ep{ep:03d}.mp3'
subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c:a', 'libmp3lame', '-q:a', '4', str(audio)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True)
seconds = float(json.loads(probe.stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
size = audio.stat().st_size
feed = root / 'feed.xml'
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in channel.findall('item')):
    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = pub_date
    enc = ET.SubElement(item, 'enclosure')
    enc.attrib.update(url=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3', length=str(size), type='audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    ET.SubElement(item, f'{{{ns}}}duration').text = duration
    ET.SubElement(item, f'{{{ns}}}episode').text = str(ep)
    ET.SubElement(item, f'{{{ns}}}episodeType').text = 'full'
    ET.SubElement(item, f'{{{ns}}}explicit').text = 'false'
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep135'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
