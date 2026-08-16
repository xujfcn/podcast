from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 144
title = 'EP144: AI API Failover — Keep Production Traffic Moving During Outages'
description = 'A practical guide to AI API failover: classify failures, design provider routes, preserve request context, avoid retry storms, and verify that fallback traffic remains reliable and affordable.'
pub_date = 'Tue, 1 Sep 2026 08:30:00 +0000'
script = '''EP144: AI API Failover — Keep Production Traffic Moving During Outages

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI applications depend on providers that can experience timeouts, rate limits, regional incidents, capacity changes, and model-specific failures. A single endpoint may work perfectly until it does not. Today we will design AI API failover that keeps useful traffic moving without hiding failures or creating a second outage.

Start with failure classification. Distinguish connection errors, DNS and transport failures, timeouts, rate limits, authentication errors, context overflow, policy rejections, malformed outputs, and provider-wide incidents. Some failures are safe to retry on another route. Others are caused by the request itself and will fail everywhere. Treating every error as interchangeable wastes capacity and makes diagnosis harder.

Define route capabilities. A fallback model must support the features the workflow needs: streaming, vision, tool calling, structured output, context size, and language coverage. Maintain a capability matrix with tested behavior, not just a list of model names. A route that accepts the request but produces unusable output is not a successful fallback.

Choose routing policy by workload. Interactive requests may need the lowest latency, while batch jobs can favor cost or queue availability. High-stakes workflows may require an approved replacement rather than an arbitrary cheaper model. A unified gateway such as Crazyrouter can centralize provider routes and policy changes while applications keep a stable API surface.

Keep retries bounded. Retry transient failures with exponential backoff and jitter, but cap attempts and total elapsed time. A request that has already consumed most of its deadline should not start an unlimited fallback chain. Respect provider retry guidance where available, and make sure each downstream attempt has a smaller remaining timeout.

Prevent retry storms. Use circuit breakers, health windows, shared admission control, and per-route concurrency limits. When a provider is unhealthy, stop sending every request there just to rediscover the same failure. Half-open probes can test recovery with a small amount of traffic before the route is fully restored.

Preserve request semantics. Carry the same user intent, system policy, output contract, and relevant context to the fallback, but account for capability differences and token limits. Do not silently drop a safety instruction or a required tool definition just because the second route has a different interface. Record what changed between attempts.

Validate fallback responses independently. Apply the same schema, business rules, tool checks, and quality signals used for the primary route. Log whether the request succeeded on the first attempt, after fallback, or only after application repair. A lower error rate is not enough if fallback outputs increase downstream corrections or user complaints.

Control cost and duplication. A failed provider attempt may still consume tokens or incur charges. Track spend by attempt and by accepted result, and avoid duplicating expensive long prompts when a clear non-retryable failure has occurred. Set a maximum fallback budget for each request and a separate emergency policy for critical workloads.

Make operations visible. Expose route, attempt count, fallback reason, latency, and final status in traces and dashboards. Notify operators when fallback share rises, when a circuit opens, or when a route’s quality drops. Users may see a brief status message or a reduced capability, but they should not receive misleading certainty about what happened.

Test real outage behavior. Simulate timeouts, 429s, invalid credentials, partial provider failures, slow recovery, and incompatible fallback capabilities. Verify that traffic moves, queues remain bounded, alerts fire, and recovery does not cause a thundering herd. Rehearse rollback of routing policies before the next incident.

The practical lesson is simple: failover is a tested routing system, not a second model name in a catch block. Classify errors, choose compatible routes, bound retries, preserve semantics, validate results, and measure cost and quality. With those controls, provider incidents become manageable operating events instead of surprise application outages.

That is it for today. Make the backup route as deliberate as the primary route. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep144'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
