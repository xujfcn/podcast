from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 137
title = 'EP137: AI API Rate Limits — Build Fair, Resilient Traffic Control'
description = 'A practical guide to AI API rate limits: distinguish quotas from concurrency, use bounded backoff, prioritize traffic fairly, protect budgets, and avoid retry storms.'
pub_date = 'Tue, 25 Aug 2026 08:30:00 +0000'
script = '''EP137: AI API Rate Limits — Build Fair, Resilient Traffic Control

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI applications often fail under pressure not because the model is unavailable, but because traffic exceeds a quota or too many requests arrive at once. A rate-limit response is useful feedback, yet poor retry logic can turn a temporary limit into a full outage. Today we will design fair and resilient traffic control for AI APIs.

First, distinguish the limits. Requests per minute, tokens per minute, concurrent requests, daily spend, and maximum request size are different constraints. A workload can be below its request quota while exceeding its token quota, or have enough total capacity but too many in-flight generations. Name and monitor each limit separately.

Apply limits at the right scope. A single global bucket is simple, but it lets one customer or background job consume capacity needed by interactive users. Use separate budgets for tenants, products, priorities, and environments where appropriate. A unified gateway such as Crazyrouter can provide a central routing layer, while application policies decide which traffic deserves priority.

Use queues for work that can wait. Interactive requests need a short deadline and a clear overload response. Batch jobs can enter a durable queue and drain when capacity returns. Do not hide a five-minute queue behind a loading spinner designed for a two-second interaction. Match the admission policy to the user experience.

Retry only when retrying makes sense. Respect Retry-After when provided, classify rate limits separately from invalid requests, and use exponential backoff with jitter. Cap the number of attempts and the total retry time. Retrying a malformed request or an over-sized prompt will never fix the cause.

Prevent retry storms. If every worker retries on the same schedule, the next wave arrives together and repeats the failure. Add randomized delay, shared admission control, circuit breakers, and a limit on queued work. When the system is overloaded, shed low-priority traffic deliberately rather than letting all requests fail unpredictably.

Control token demand. Limit maximum output tokens, trim unnecessary context, and reserve capacity for important routes. Token budgets often matter more than request counts because one long generation can consume the capacity of many short calls. Track requested and actual usage so the policy reflects reality.

Make fairness visible. Define how priority works and expose useful status to callers: accepted, queued, delayed, rejected, or retried. For multi-tenant systems, track utilization and throttling by tenant. A customer should not have to guess whether a slow response is an upstream incident, a local queue, or an account-level limit.

Design graceful degradation. When the preferred route is constrained, consider a smaller model, shorter output, asynchronous delivery, or a cached result if quality remains acceptable. Make the fallback explicit in metadata and logs. Automatic degradation should not quietly change a high-stakes workflow without an approval or notification policy.

Test overload before production. Generate bursts, long prompts, concurrent streams, provider 429 responses, slow responses, and recovery. Verify that queues are bounded, retries stop, priority is respected, and recovery does not create another spike. Measure success rate, time to recovery, wasted tokens, and user-visible latency.

The practical lesson is simple: rate limits are part of the product contract. Model the limits, admit traffic deliberately, retry with discipline, prioritize fairly, and degrade transparently. Good traffic control protects both the provider relationship and the users who depend on your application.

That is it for today. Bound the traffic before the traffic bounds you. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep137'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
