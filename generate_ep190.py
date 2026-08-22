from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 190
title = 'EP190: AI API Post-Incident Learning — Turn Failures Into Durable Reliability Improvements'
description = 'A practical guide to learning from AI API incidents: build a precise timeline, separate causes from conditions, prioritize corrective actions, improve tests and runbooks, and verify that reliability actually improves.'
pub_date = 'Fri, 23 Oct 2026 08:30:00 +0000'
script = '''EP190: AI API Post-Incident Learning — Turn Failures Into Durable Reliability Improvements

Welcome back to AI Dev Tools — The Crazyrouter Podcast. An incident is not finished when traffic returns. The valuable work begins when the team can explain what users experienced, why safeguards did not stop it, and which changes will make the next failure smaller or easier to recover from. Today we are talking about post-incident learning for AI APIs: turning a painful outage into durable improvements in design, operations, testing, and product behavior.

Start with a factual timeline. Collect deploys, configuration changes, provider events, queue depth, latency, errors, retries, fallbacks, admission decisions, billing records, and user reports. Mark when the first user-visible symptom appeared, when detection happened, when mitigation began, when service became useful, and when verification completed. Use request and operation IDs to connect gateway attempts, provider calls, tool actions, and stored results without relying on memory.

Separate impact from implementation detail. Describe which workloads failed, which tenants were affected, how many requests missed deadlines, whether any side effects duplicated, and whether charges were uncertain. A provider timeout may be the trigger, but the customer impact may have been amplified by an unbounded retry policy or a missing fallback capability check. Quantify accepted-result loss, queue delay, extra tokens, support contacts, and recovery time where evidence allows.

Use a blameless but precise analysis. Blameless does not mean causeless. Identify the technical conditions, decisions, assumptions, and missing controls that allowed the incident to grow. Ask what the system made reasonable for an operator to believe at each step. Avoid turning one person into the explanation; a reliable system must make the safe action visible and repeatable even under pressure.

Distinguish trigger, contributing factors, and escape points. The trigger may be a provider regression, a bad model alias, a credential expiry, or a traffic burst. Contributing factors may include stale capability metadata, insufficient capacity, weak alerting, or a client retry storm. Escape points are the controls that should have limited impact but did not: circuit breakers, deadlines, quotas, validation, admission control, or recovery checks. This classification makes corrective work more targeted.

Check the full request lifecycle. Review admission, routing, provider execution, streaming, validation, tool authorization, cancellation, billing, storage, and client retry behavior. AI failures often cross boundaries: a valid transport response can contain invalid JSON, a cancelled stream can still consume tokens, or a fallback can be available but incompatible with the request contract. The post-incident review should follow the user journey rather than stopping at the first 500 response.

Turn findings into specific actions. “Improve reliability” is not an action. A useful item names the change, owner, deadline, affected workload, verification method, and expected risk reduction. Actions may include bounding retries, adding a route capability check, reserving interactive capacity, persisting idempotency state, improving a metric, updating a runbook, or changing a client contract. Prefer controls that reduce blast radius automatically over reminders that depend on perfect attention.

Prioritize by risk and leverage. Fix data loss, duplicate side effects, unsafe routing, and uncontrolled spend before polishing dashboards. Then address detection and recovery speed. A small guard that prevents one tenant from consuming a shared pool may be more valuable than a broad refactor. Track residual risk explicitly when an action cannot be completed immediately, and assign an expiry or review date rather than letting it disappear in a backlog.

Convert the incident into tests. Reproduce the trigger with a small fixture, then add boundary cases: provider slowdown, malformed output, late cancellation, duplicate client retry, gateway restart after reservation, fallback capability mismatch, queue expiration, and uncertain billing. Assert user-visible outcomes, not only internal function calls. Contract tests should prove that one logical operation produces one committed side effect and one understandable client state.

Improve observability based on unanswered questions. If the team could not tell whether a request was queued, retried, hedged, cancelled, billed, or accepted, add the smallest useful field and dashboard. Record route, model, provider, operation ID, attempt ID, policy version, workload class, deadline, winner reason, validation result, and cost where appropriate. Protect prompt and customer data with redaction and access controls. More logs are not automatically better; every signal should help answer a recovery question.

Update runbooks around decisions. A good runbook says what symptom confirms the condition, which checks are safe, what traffic to pause, how to choose a fallback, when to drain queues, and what evidence permits recovery. Include commands or links that are safe to run, expected outputs, escalation ownership, and rollback steps. Test the runbook with someone who did not write it. If it only works for the original author, it is undocumented expertise rather than an operational control.

Review client behavior too. The gateway may recover while clients continue sending aggressive retries, polling too frequently, or treating partial results as complete. Document retry-after, idempotency, job states, degraded responses, and error ownership. Provide SDK guidance and examples for deadlines, cancellation, and safe retries. Reliability is a shared contract; improving only the server can leave the same incident pattern ready to return through client behavior.

Measure whether the fix worked. Define a before-and-after baseline for detection time, mitigation time, accepted-result rate, tail latency, duplicate actions, fallback share, cost per accepted result, and queue recovery. Run a canary or controlled failure drill when safe. A merged pull request is not evidence of risk reduction. Close an action only when the intended behavior is observable and a test, drill, or production measurement confirms it.

Look for systemic patterns across incidents. One provider timeout, one expired credential, and one bad model release may share the same weakness: no bounded deadline budget or no last-known-good route. Maintain a small incident taxonomy and review recurring categories across teams and services. Fix common mechanisms at the gateway or platform layer when appropriate, while keeping workload-specific policies explicit.

Share the useful parts without oversharing sensitive data. Internal teams need enough detail to avoid repeating the failure. Customers need an accurate impact summary, affected time window, remediation, and any action they should take. Do not publish prompts, credentials, private tenant data, or provider details that create security risk. Honest communication builds trust when it distinguishes confirmed facts, uncertainty, and completed remediation.

The practical lesson is simple: an incident becomes valuable only when it changes future behavior. Build the timeline from evidence, quantify user impact, separate trigger from escape points, assign concrete fixes, add failure tests, improve decision-quality observability, update runbooks, and verify the measured result. Reliable AI APIs are not systems that never fail. They are systems that learn faster than their failure modes evolve.

That is it for today. Learn precisely, fix the leverage points, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
print(f'DONE {audio} {size} bytes {duration} {len(parts)} chunks')
