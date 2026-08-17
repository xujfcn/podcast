from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 162
title = 'EP162: Human-in-the-Loop AI APIs — Escalate the Right Decisions'
description = 'A practical guide to human-in-the-loop AI APIs: define review thresholds, package evidence, manage queues, prevent duplicate actions, and learn from human decisions.'
pub_date = 'Sat, 19 Sep 2026 08:30:00 +0000'
script = '''EP162: Human-in-the-Loop AI APIs — Escalate the Right Decisions

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Automation does not have to mean removing people from every decision. For ambiguous, high-impact, or low-confidence tasks, the safest design is often a clear handoff to a human. The challenge is making that handoff fast, informed, and consistent instead of turning it into an unstructured inbox. Today we will design human-in-the-loop AI APIs.

Start with decision boundaries. Define which outcomes the model can complete automatically, which require review, and which must be blocked. Use task-specific signals such as confidence, validation failure, policy risk, monetary impact, or missing evidence. Do not ask humans to review everything; reserve attention for cases where human judgment materially reduces risk.

Package evidence with the review request. Include the task, proposed answer or action, relevant source references, validation results, uncertainty signals, and a concise reason for escalation. A reviewer should not reconstruct the entire model conversation or search through raw logs to understand what needs a decision.

Keep authority explicit. A reviewer may approve, reject, edit, request more information, or route the case to another queue. Record which actions are permitted and require stronger approval for external side effects. A gateway such as Crazyrouter can provide a stable model route, but application policy must decide what a human approval actually authorizes.

Build a durable review state. Store the task ID, owner, priority, deadline, current status, proposed result, evidence version, policy version, and decision history. Do not let a browser tab or an email thread become the system of record. Durable state supports reassignment, recovery, audits, and accurate reporting.

Prevent duplicate actions. A reviewer may click twice, a browser may retry, or a worker may process the same approval event again. Use idempotency keys and explicit state transitions so an approved payment, message, ticket, or deployment cannot happen twice. Separate the decision from the execution record when the action has external consequences.

Manage queue fairness. Prioritize by risk, deadline, customer impact, and service level rather than arrival time alone. Set maximum waiting times, notify owners, and move abandoned work to a recovery queue. A low-risk batch task should not block an urgent safety review, while high-priority work should not become an excuse for permanently starving ordinary requests.

Give reviewers useful controls. Provide side-by-side evidence, structured edits, reason codes, and keyboard-efficient actions where appropriate. Make uncertainty and missing information visible. Avoid forcing reviewers to accept a model output when the right answer is not yet known; allow them to request clarification or mark the case unresolved.

Protect reviewer privacy and consistency. Restrict access by tenant and purpose, redact unnecessary sensitive data, and log decisions without exposing more content than required. Use guidelines, examples, calibration sessions, and periodic agreement checks so similar cases receive similar treatment across reviewers and shifts.

Feed decisions back into the system carefully. Human corrections can improve prompts, evaluations, routing, and policy, but do not silently train on every decision. Classify feedback, preserve provenance, remove sensitive data where required, and review changes before they affect production behavior. A unified gateway such as Crazyrouter can help compare routes, while the application owns the feedback lifecycle.

Measure the workflow. Track escalation rate, review latency, queue age, agreement rate, correction rate, rework, accepted-result quality, and cost per completed task. A lower escalation rate is not automatically better if it means unsafe automation. Optimize for the product outcome and risk level, not for making the human queue disappear.

The practical lesson is simple: human review is an engineered control plane. Define boundaries, package evidence, persist state, enforce idempotency, manage queues fairly, protect reviewers, and learn from decisions deliberately. When escalation is designed well, people handle the cases where judgment matters most while automation keeps the routine work moving.

That is it for today. Escalate with evidence, not confusion. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep162'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
