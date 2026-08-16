from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 152
title = 'EP152: Async AI APIs — Make Webhooks Reliable for Long-Running Jobs'
description = 'A practical guide to reliable asynchronous AI APIs: design webhook contracts, sign events, handle duplicates, retry safely, track job state, and make long-running results trustworthy.'
pub_date = 'Wed, 9 Sep 2026 08:30:00 +0000'
script = '''EP152: Async AI APIs — Make Webhooks Reliable for Long-Running Jobs

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Some AI tasks take longer than an HTTP request should remain open. Video generation, document processing, large batch jobs, and multi-step workflows need a durable asynchronous interface. Webhooks can notify a client when work finishes, but only when delivery, authentication, duplication, and state transitions are designed deliberately. Today we will build a reliable webhook workflow for long-running AI jobs.

Start with a durable job state. When a request is accepted, create a job identifier and store its tenant, input reference, route, configuration version, status, progress, deadline, and callback policy. Do not treat the webhook as the system of record. The callback is a notification that the client can use to fetch or reconcile the authoritative job state.

Define a small event contract. Include event ID, event type, job ID, attempt number, creation time, schema version, and a link or reference to the result. Separate events such as job accepted, progress changed, completed, failed, and cancelled. Avoid putting large outputs directly into a callback when a short-lived authenticated result URL is safer and easier to retry.

Authenticate every delivery. Sign the exact request body with a rotating secret, include a timestamp, and reject stale or replayed signatures. Give each customer or endpoint an independently revocable secret. A gateway such as Crazyrouter can standardize model access, but the webhook receiver still owns its endpoint security, validation, and authorization.

Assume delivery is at least once. Networks fail after the receiver commits but before it responds, so the sender may deliver the same event again. Store processed event IDs or use an idempotent state transition keyed by event and job. A duplicate completion must not create two charges, two emails, or two downstream records.

Make transitions monotonic. A job should not move from completed back to running because an old progress event arrived late. Validate that each event belongs to the expected job, version, and tenant, then apply it according to an explicit transition table. Preserve the raw event and the resulting state for investigation.

Retry with discipline. Retry timeouts and temporary 5xx responses with exponential backoff and jitter. Respect a delivery deadline, cap attempts, and move exhausted events to a durable dead-letter state. Do not retry invalid signatures or permanent 4xx responses forever. Make the next retry time visible to operators.

Let receivers acknowledge quickly. Webhook handlers should authenticate, validate, persist, and enqueue work before returning a success response. They should not wait for a large download, a second model call, or a complex business process inside the delivery request. Fast acknowledgement reduces duplicate delivery and protects the receiver during bursts.

Handle ordering and reconciliation. Progress events may arrive late or out of order. Include sequence numbers or state versions where ordering matters, and provide a polling or reconciliation endpoint so clients can recover from missed callbacks. A client that never receives the completion event should still be able to discover the final result.

Protect result access. Use tenant-scoped authorization, short-lived URLs, expiration, and explicit deletion rules. Do not assume that knowing a job ID grants access to its output. Keep callback payloads free of secrets and unnecessary private content, and record which principal downloaded the result when auditability matters.

Monitor the whole workflow. Track job age, queue delay, completion rate, callback success rate, duplicate rate, retry count, dead-letter events, result download failures, and time from completion to client acknowledgement. Alert on stuck jobs and rising delivery failures, not just provider HTTP errors.

The practical lesson is simple: asynchronous AI APIs need durable state and reliable notifications. Define a precise event contract, sign deliveries, expect duplicates, enforce valid transitions, retry safely, acknowledge quickly, and provide reconciliation. With these controls, long-running AI jobs can feel dependable even when networks and workers are not.

That is it for today. Make completion discoverable even when a callback is missed. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep152'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
