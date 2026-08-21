from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 178
title = 'EP178: AI API Load Testing — Find Capacity Before Production Does'
description = 'A practical guide to load testing AI APIs: model realistic workloads, separate concurrency from rate limits, protect budgets, measure accepted results, rehearse provider failures, and turn test data into capacity decisions.'
pub_date = 'Mon, 05 Oct 2026 08:30:00 +0000'
script = '''EP178: AI API Load Testing — Find Capacity Before Production Does

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Teams often load test a web API with a fixed response and a predictable database. AI APIs are different. Response time varies with prompts, output length, model choice, provider capacity, tool calls, and retries. Today we will build a practical load-testing plan that tells you how much useful work your gateway can handle before a launch turns into a queue, a budget surprise, or a provider incident.

Start with the workload, not the number of virtual users. Record the request shapes your product actually sends: short classification, long document analysis, chat with conversation history, structured extraction, tool calling, and streaming. Capture prompt size, expected output range, model route, tenant tier, and whether the request is interactive or background. A test that sends one tiny prompt cannot represent a mixed production workload.

Build a small, privacy-safe fixture set. Use synthetic or redacted prompts with the same token distributions and schema variety as production. Include normal cases, long contexts, malformed inputs, tool requests, and requests that should be rejected. Keep the fixture versioned with the test so a result can be reproduced after a prompt, model, or gateway change.

Separate the dimensions of load. Requests per second measures arrival rate, while concurrency measures work in flight. Tokens per second measures generation pressure, and payload bytes measure network and parsing work. A system can tolerate a high request rate for short calls but collapse under a small number of long generations. Report each dimension instead of hiding everything behind one users number.

Warm up before measuring. Providers, connection pools, caches, containers, and autoscaling policies may all behave differently during the first minutes. Use a ramp from a low baseline to the expected peak, hold each step long enough to observe queues and recovery, then add a stress phase. Mark warm-up, steady state, burst, and cooldown separately so cold-start effects do not become your headline result.

Define success as an accepted result, not just an HTTP 200. The response must arrive within the workload deadline, satisfy the expected schema or quality gate, and avoid an unsafe or duplicate tool action. Record provider errors, gateway errors, rejected requests, validation failures, retries, fallbacks, and abandoned clients. A test can show excellent availability while quietly returning unusable output.

Protect the budget while you test. Put a hard ceiling on requests, tokens, wall-clock duration, and estimated spend. Use a dedicated test tenant and label every request so test traffic cannot be confused with customer usage. Add a kill switch that stops arrivals and cancels work in flight. The fastest way to learn whether a load test is controlled is to ask whether an operator can stop it immediately.

Measure the whole path. Capture time to first token when streaming, total completion time, queue wait, provider time, gateway processing time, payload size, and tokens generated. Track p50, p95, and p99, but also show timeout and cancellation rates. Correlate traces by request ID across the gateway, provider adapter, validation layer, billing, and client harness. Without a breakdown, a slow result only tells you that something is slow.

Test fairness and isolation. Mix tenants with different quotas and priority classes. Verify that one noisy customer cannot consume every connection, queue slot, token budget, or provider route. Test interactive traffic alongside batch work, and confirm that admission control rejects or delays the right class with a useful retry signal. Capacity is not sufficient if the system serves the largest sender while everyone else waits.

Rehearse the failures that load exposes. Inject provider 429s, elevated latency, malformed responses, connection resets, validation failures, and a full downstream queue. Watch whether retries multiply traffic, whether fallbacks have enough headroom, and whether a circuit breaker actually opens. Run the same scenario with idempotency keys and verify that a retried request does not create duplicate tool effects or duplicate charges.

Test autoscaling and recovery, not only the peak. Hold traffic above the normal level until scaling should occur, then reduce it and observe whether workers, connections, queues, and memory return to baseline. Look for slow leaks in buffers, orphaned provider requests, and autoscalers that react to request count but ignore token volume. A platform that survives a burst but cannot recover is still carrying hidden capacity debt.

Compare routes using the same workload. When you evaluate a model or provider, keep fixtures, arrival pattern, deadlines, and acceptance checks constant. Compare cost per accepted result, accepted-result rate, queue time, tail completion time, fallback share, and generated tokens. The cheapest provider at idle is not necessarily the cheapest route at the concurrency your users create.

Turn results into explicit capacity policy. Choose a normal operating point below the first sign of queue instability, reserve headroom for bursts and provider degradation, and set limits for concurrent requests, tokens, output length, and tenant share. Document the assumptions behind the number: fixture mix, region, model routes, proxy path, and failure budget. Capacity is a decision with evidence, not a permanent property of a model.

Keep the test in the release workflow. Run a small smoke load on every gateway or prompt change, a representative rehearsal before launches, and a scheduled full test as providers and traffic patterns evolve. Store time-series results and alert on regressions in accepted-result rate, queue wait, cost, or recovery time. A load test that runs once and disappears from the repository becomes historical trivia.

The practical lesson is simple: load test the work your product really does, measure accepted results across every layer, cap spend, exercise failures, and convert observations into admission and capacity rules. AI API gateways make this easier by centralizing routing, quotas, retries, traces, and billing labels, but the test still has to model the customer workload honestly.

That is it for today. Rehearse the peak before the peak arrives, keep your budgets bounded, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep}'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
