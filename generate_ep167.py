from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 167
title = 'EP167: AI API Capacity Planning — Scale Before the Queue Becomes the Product'
description = 'A practical guide to AI API capacity planning: forecast demand, budget concurrency, protect latency, size queues, and preserve reliable service during bursts.'
pub_date = 'Thu, 24 Sep 2026 08:30:00 +0000'
script = '''EP167: AI API Capacity Planning — Scale Before the Queue Becomes the Product

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI applications often fail during growth in a predictable way: requests wait longer, retries multiply, providers throttle traffic, and users experience a queue instead of a product. Today we will build a practical capacity plan for AI APIs.

Start with workload shape. Measure requests per minute, input and output tokens, concurrency, payload size, streaming duration, and burst behavior. A thousand short classification requests and a thousand long agent runs consume very different capacity. Forecast by workload class rather than using one average request number.

Define the user-facing target. Set budgets for time to first token, completion latency, queue age, accepted-result rate, and maximum retry delay. Capacity planning is not only about serving more traffic; it is about preserving the experience that makes the feature useful. A system that is technically available but consistently too slow is already under-capacity.

Separate limits. Track application concurrency, gateway concurrency, provider quotas, token-per-minute limits, connection pools, queue workers, and downstream database capacity. The narrowest limit controls the system. A gateway such as Crazyrouter can centralize routing and usage visibility, but each layer still needs an explicit budget and overload behavior.

Plan for bursts and recovery. Size for normal traffic, expected peaks, and a safe emergency margin. Model what happens after a provider outage ends and queued work returns at once. Without admission control, recovery traffic can create a second incident. Use bounded queues, backpressure, priority classes, and controlled ramp-up.

Protect interactive traffic. Separate user-facing requests from batch jobs, evaluations, indexing, and background agents. Give each class its own concurrency and budget. A large offline run should not consume every connection while a customer waits for a simple answer. Fairness is a product decision, so make it visible in policy and metrics.

Use graceful degradation. When capacity is tight, shorten optional context, reduce output limits, switch to a compatible lower-cost route, defer non-urgent work, or ask the user to retry later. Degradation should preserve correctness and communicate what changed. Never hide overload by silently dropping requests or returning incomplete data as if it were complete.

Control retries. Retry only failures that are likely to recover, use bounded exponential backoff, honor Retry-After, and cap total attempts per operation. Record the original request ID and attempt number. A retry budget should be included in capacity forecasts because a ten percent failure rate can create much more than ten percent extra traffic.

Load-test realistic behavior. Include long contexts, streaming connections, tool calls, validation failures, provider throttling, and fallback routes. Test both steady state and sudden bursts. Watch queue age, token throughput, memory, connection usage, accepted-result rate, and cost. Synthetic tests that use only tiny prompts will produce dangerously optimistic plans.

Review capacity continuously. Compare forecasts with actual traffic, revise model mix and provider limits, and document assumptions. Add alerts before saturation, not after users report timeouts. A good capacity plan is a living control system that connects demand, reliability, cost, and release decisions.

The practical lesson is simple: capacity is a user experience budget. Measure workload shape, separate traffic classes, reserve headroom, control retries, degrade honestly, and test recovery as seriously as peak load. When queues are designed deliberately, growth becomes manageable instead of surprising.

That is it for today. Scale before the queue becomes the product, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep167'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
