from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 197
title = 'EP197: AI API SLOs — Turn Reliability Targets Into Routing Decisions'
description = 'A practical guide to AI API SLOs: define user-centered objectives, account for streaming and accepted results, budget latency and errors, and connect reliability targets to routing, fallback, and release decisions.'
pub_date = 'Thu, 27 Aug 2026 08:30:00 +0000'
script = '''EP197: AI API SLOs — Turn Reliability Targets Into Routing Decisions

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Reliability targets are useful only when they change decisions. An AI API can be technically available while users wait too long, receive invalid structured output, lose a stream, or pay for work that never completes. Today we are talking about service level objectives for AI APIs: turning user expectations into measurable budgets that guide routing, fallbacks, capacity, and releases.

Start with the user journey. Define what “successful” means for each important workload: a completed chat turn, a valid JSON result, a finished tool action, or a generated asset that can actually be downloaded. Availability as HTTP 200 is too weak. Measure accepted results, because a fast but unusable response is still a failure from the user’s perspective.

Separate the service indicators. Track request success, accepted-result rate, time to first token, inter-token delay, completion time, stream completion, timeout rate, retry rate, fallback share, and cost per accepted result. Slice them by route, model, provider, region, tenant, workload class, prompt size, output size, and streaming mode. A single average hides the exact users who experience the incident.

Use percentiles and windows that match the experience. Average latency cannot represent a slow tail, and a monthly aggregate can hide a bad afternoon. Define targets such as a first-token percentile for interactive traffic and a completion percentile for bounded tasks. Pair short alert windows with a longer error budget so operators can react quickly without turning every fluctuation into an emergency.

Make the SLO mathematically honest. If a request can fail because of transport, provider rejection, policy denial, validation failure, or client cancellation, decide which outcomes count against which objective. Document exclusions narrowly. Do not remove difficult traffic from the denominator simply because it is expensive or inconvenient; otherwise the dashboard becomes a story about easy requests.

Budget latency across the gateway. Reserve time for authentication, policy checks, queueing, provider attempts, validation, and response delivery. Retries and fallbacks must fit inside the user deadline. An attempt that begins after the deadline is not resilience; it is wasted work that may increase cost and concurrency pressure. Carry one deadline through every hop and cancel work that can no longer succeed.

Connect SLOs to routing. When a provider consumes its latency or error budget, reduce exposure, shift eligible traffic, or require a safer fallback. Route selection must respect capability, region, data policy, cost, and context limits, not just raw availability. A cheaper provider that violates the structured-output objective is not cheaper for the complete workflow.

Treat streaming as its own contract. Time to first token can look healthy while the stream stalls halfway through. Track disconnects, heartbeat gaps, token delivery delays, completion markers, and client cancellation. Backpressure and queue limits should protect both the producer and the client. If a stream cannot finish within its budget, the system needs a clear partial-result or retry policy.

Use error budgets to govern change. A healthy budget can permit a controlled model rollout, while a nearly exhausted budget should pause risky changes and prioritize recovery. Define the stop conditions before a canary starts: accepted-result regression, tail latency increase, validation failures, cost spike, or fallback amplification. Error budgets are a decision system, not a punishment score.

Include dependencies and asynchronous work. Provider APIs, DNS, queues, object storage, moderation services, tool endpoints, and billing paths can all affect the user objective. For jobs that finish later, define enqueue success separately from completion success and freshness. Otherwise a queue that accepts everything can appear healthy while users wait indefinitely.

Make multi-tenant fairness visible. One noisy tenant or long-context workload can consume concurrency and damage everyone’s tail latency. Add per-tenant quotas, admission control, and workload-aware pools where needed. Report both global SLOs and protected-tenant slices. Reliability is not achieved by allowing the largest customer to spend the entire shared budget.

Design recovery around the objective. Operators should have narrow controls to pause a provider, reduce concurrency, disable a tool, select a known-good model, or restrict a workload. Each control needs an owner, reason, expiry, and rollback path. After recovery, verify accepted results and tail behavior rather than declaring success when health checks turn green.

Review the SLOs as the product changes. New models, longer contexts, tools, image outputs, and international regions alter the cost and latency shape. Revisit targets when the user journey changes, but preserve historical measurements so a relaxed target cannot make a regression disappear. Keep definitions versioned alongside route and policy changes.

The practical lesson is simple: an AI API SLO should describe a result users can rely on, expose the tail that hurts, and spend its budget on explicit decisions. Measure accepted outcomes, budget every hop, separate streaming from completion, route by capability and policy, use error budgets for releases, protect tenants, and rehearse recovery controls.

That is it for today. Make the target measurable, make the budget actionable, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
seconds = float(json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True).stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
feed = root / 'feed.xml'
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in channel.findall('item')):
    item = ET.Element('item')
    for tag, value in [('title', title), ('description', description), ('pubDate', pub_date)]: ET.SubElement(item, tag).text = value
    enc = ET.SubElement(item, 'enclosure'); enc.attrib.update(url=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3', length=str(audio.stat().st_size), type='audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    for tag, value in [('duration', duration), ('episode', str(ep)), ('episodeType', 'full'), ('explicit', 'false')]: ET.SubElement(item, f'{{{ns}}}{tag}').text = value
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep}'
    channel.insert(0, item); tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {audio.stat().st_size} bytes {duration} {len(parts)} chunks')
