from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 165
title = 'EP165: AI API Incident Response — Recover Fast Without Losing Trust'
description = 'A practical guide to AI API incident response: detect user-visible failures, coordinate diagnosis, control fallback traffic, communicate clearly, and turn incidents into durable improvements.'
pub_date = 'Tue, 22 Sep 2026 08:30:00 +0000'
script = '''EP165: AI API Incident Response — Recover Fast Without Losing Trust

Welcome back to AI Dev Tools — The Crazyrouter Podcast. An AI API incident is rarely just an error rate on a dashboard. Users may receive incomplete answers, invalid JSON, slow streams, unexpected refusals, or expensive fallback results while the main endpoint still returns HTTP 200. Today we will build an incident-response practice that restores useful service quickly and preserves trust.

Start with user-visible symptoms. Define what counts as an incident for each workload: time to first token, accepted-result rate, tool-call success, output completeness, queue age, or cost per successful task. A single global uptime number hides the failures that matter most. Alerts should link directly to the affected route, model, tenant, and workflow.

Create a clear incident record. Capture the start time, affected services, suspected change, current impact, owner, severity, and next update time. Use one shared timeline for evidence and decisions. Keep request IDs, provider IDs, route versions, and configuration changes connected so responders do not spend the first hour searching across unrelated logs.

Stabilize before optimizing. Stop risky rollouts, reduce optional work, cap retries, and protect remaining capacity. If a provider is timing out, unlimited retries can turn a partial outage into a full one. A gateway such as Crazyrouter can help switch routes centrally, but the fallback policy should account for capability, price, region, and data-handling requirements.

Choose fallbacks by contract, not by brand name. The backup model must support the features the workflow actually uses: streaming, vision, tools, structured output, context length, or safety policy. Validate fallback responses at the application boundary. If the result is not safe to use, return a clear degraded state or ask the user to retry instead of silently inserting unreliable data downstream.

Preserve idempotency during recovery. Queues may replay work, clients may retry, and operators may run a repair command twice. Use operation IDs, attempt numbers, and explicit state transitions. Separate model generation from external side effects so an incident response can replay analysis without sending a duplicate message, payment, or deployment.

Communicate with precision. Tell users what is affected, what still works, and what they should do. Avoid vague claims such as “everything is fixed” while monitoring is still catching up. Internally, give support and engineering teams the same incident summary, known limitations, and next update time. Clear communication reduces duplicate reports and prevents responders from making contradictory promises.

Investigate with a timeline. Compare the first bad request with the last known good request. Check model releases, prompt changes, provider status, quota use, network latency, validation failures, fallback share, and traffic shape. Distinguish correlation from cause. A provider outage may expose an application retry bug, and a prompt change may reveal a contract that was never validated.

Close the loop after recovery. Write a blameless review focused on what happened, how it was detected, why safeguards did or did not work, and which changes have an owner and due date. Improve runbooks, evaluations, alerts, routing rules, capacity limits, and customer communication templates. An incident is not fully closed when the graph is green; it is closed when the system is harder to break in the same way.

Measure recovery quality. Track time to detect, time to acknowledge, time to stabilize, time to restore accepted results, fallback success, duplicate work, user impact, and follow-up completion. Compare these metrics by workload. A fast recovery that serves invalid structured data is not a successful recovery, and a longer recovery with honest degradation may protect users better.

The practical lesson is simple: AI incident response combines reliability engineering with product judgment. Define user-visible failure, stabilize traffic, use contract-aware fallbacks, protect side effects, communicate honestly, and turn every incident into a concrete guard. Recovery speed matters, but trustworthy recovery matters more.

That is it for today. Recover clearly, learn permanently, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep165'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
