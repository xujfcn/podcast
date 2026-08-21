from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 169
title = 'EP169: AI API Rate Limits — Build Fair, Resilient Traffic Control'
description = 'A practical guide to AI API rate limits: distinguish quotas from concurrency, use bounded backoff, prioritize traffic fairly, protect budgets, and avoid retry storms.'
pub_date = 'Sat, 26 Sep 2026 08:30:00 +0000'
script = '''EP169: AI API Rate Limits — Build Fair, Resilient Traffic Control

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Rate limits are not just a provider inconvenience. They are a traffic-control problem that determines which users get service, how quickly work recovers, and whether a temporary limit turns into a wider outage. Today we will design fair and resilient rate limiting for AI APIs.

Start by separating the limits. Requests per minute, tokens per minute, concurrent requests, queue depth, connection pools, and monthly spend are different controls. A request can fit one limit and violate another. Track each dimension independently so an application can explain whether it is waiting for tokens, concurrency, provider capacity, or budget.

Apply limits at the right ownership level. Protect the whole service, but also isolate tenants, projects, users, API keys, and workload classes. A single noisy customer should not consume the capacity reserved for everyone else. A gateway such as Crazyrouter can centralize route access and usage accounting, while application policy decides how customer and feature budgets should be prioritized.

Use token-aware admission control. Counting requests alone treats a tiny classification call like a long-context agent run. Estimate input and output tokens before dispatch, reserve capacity, and release unused reservations when the result arrives. Conservative estimates are safer than allowing every request through and discovering overload after the provider rejects it.

Handle 429 responses deliberately. Read Retry-After when available, use exponential backoff with jitter, cap the number of attempts, and preserve the operation deadline. Do not retry every error identically. A permanent validation error needs correction, while a temporary capacity response may deserve a delayed retry or a compatible fallback.

Give traffic a fair queue. Interactive requests usually need a tighter latency target than batch jobs, but priority should not permanently starve ordinary work. Use weighted queues, aging, maximum wait times, and reserved capacity for critical workflows. Make the policy visible in metrics so a change in traffic behavior does not look like a mysterious provider problem.

Protect retries and fallbacks. When a primary route slows down, sending the same full load to every backup can exhaust the entire provider pool. Set a retry budget per operation and a fallback budget per workload. Reduce optional context or defer non-urgent work when capacity is scarce. A graceful degraded result is often safer than an uncontrolled retry storm.

Return useful responses to clients. Include a clear error category, retry guidance, request ID, and whether the operation was accepted, queued, or rejected. For asynchronous work, return a durable job ID instead of making clients poll an overloaded synchronous endpoint. Good client signals reduce accidental hammering and make recovery easier.

Observe the queue, not only the provider. Track admitted requests, rejected requests, wait time, token reservations, retry attempts, fallback share, queue age, and accepted-result rate. Compare these by tenant and workload. A low provider error rate can hide a growing internal queue, while a high 429 rate may simply reflect a well-functioning local guard that is protecting users.

Test overload as a normal scenario. Generate bursts, long requests, partial provider outages, delayed Retry-After values, and simultaneous fallback traffic. Verify fairness, cancellation, budget enforcement, and recovery speed. Test that a cancelled client releases capacity and that a worker restart does not lose or duplicate queued jobs.

The practical lesson is simple: rate limiting is a reliability and fairness contract. Separate the dimensions, reserve capacity by cost, back off with discipline, prioritize transparently, cap retries, and measure the queue. When traffic control is designed deliberately, limits protect the product instead of surprising it.

That is it for today. Control the traffic before traffic controls you, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script)
parts = script.split('\n\n')
for i, part in enumerate(parts, 1):
    subprocess.run(['edge-tts', '--voice', 'en-US-GuyNeural', '--text', part, '--write-media', str(root / f'episodes/ep{ep:03d}_chunk{i}.mp3')], check=True)
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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep169'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
