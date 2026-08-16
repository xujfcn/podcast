from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 157
title = 'EP157: AI API Safety Filters — Protect Users Without Blocking Useful Work'
description = 'A practical guide to AI API safety filtering: define risk policies, classify inputs and outputs, handle uncertainty, review edge cases, and keep safeguards observable and adaptable.'
pub_date = 'Mon, 14 Sep 2026 08:30:00 +0000'
script = '''EP157: AI API Safety Filters — Protect Users Without Blocking Useful Work

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI applications need to handle requests that vary from harmless to clearly dangerous, with a large gray area in between. A single keyword filter cannot understand context, while an over-aggressive blocker frustrates legitimate users. Today we will design safety filtering for AI APIs as a layered, observable policy system.

Start with the risk model. Define the harms relevant to the product, such as privacy exposure, fraud assistance, self-harm content, malware, harassment, or unsafe real-world instructions. The right policy depends on the use case, user age, geography, and whether the system only answers questions or can take actions. Write down the intended behavior before choosing a vendor score.

Separate input and output controls. An input filter can identify risky requests before expensive inference or tool access. An output filter can catch unsafe or policy-violating responses after generation. Neither is sufficient alone. Tool arguments, retrieved documents, file uploads, and streamed content also need appropriate checks.

Use layered signals. Combine deterministic rules, provider safety classifiers, task-specific validators, and human review for ambiguous cases. Rules are predictable but narrow; model-based classifiers understand context but can be uncertain or drift. Preserve the signal and policy version that led to a decision so operators can explain why content was allowed, blocked, or escalated.

Define actions by confidence and severity. A high-confidence, high-severity case may be blocked immediately. An uncertain or lower-risk case may receive a safer completion, a clarification request, reduced tool permissions, or human review. Avoid treating every borderline score as an outage. The user-facing response should be clear without revealing a path around the safeguard.

Protect the policy boundary. User text, retrieved documents, and tool results may contain instructions that try to disable filtering or redefine the rules. Keep safety policy outside untrusted content, apply checks to tool calls and outputs, and never let the model grant itself an exception. A gateway such as Crazyrouter can provide a consistent model route while the application retains control of policy enforcement.

Handle streaming carefully. Decide whether moderation happens before tokens are released, on buffered segments, or on the assembled result. If partial output can be harmful, do not expose it before a suitable check. If a stream is interrupted by a safety decision, mark the result as stopped and avoid presenting the partial content as complete.

Minimize sensitive logging. Safety investigations need evidence, but raw prompts and outputs can contain personal or dangerous content. Store classifications, policy decisions, hashes, redacted samples, and restricted references where possible. Define retention, access, and deletion rules, and ensure safety telemetry does not become a new source of exposure.

Test the gray areas. Build a versioned test set with direct harmful requests, benign requests using risky words, multilingual phrasing, indirect instructions, role-play, prompt injection, misspellings, and adversarial attempts to evade filters. Measure false positives, false negatives, latency, cost, and user recovery, not just block rate.

Create an appeal and review path. Legitimate users need a way to report incorrect blocks, while operators need a queue for ambiguous cases and policy exceptions. Review samples regularly, separate product feedback from emergency incidents, and update policies with documented rationale. A safeguard that cannot be improved will eventually become either ineffective or unusable.

Monitor policy performance. Track block, allow, escalate, and safe-completion rates by workflow, region, language, model, and policy version. Watch for sudden shifts after provider or prompt changes. Alert on harmful incidents and classifier failures, but also investigate a sudden rise in false positives that may quietly damage the product.

The practical lesson is simple: safety filtering is a decision system, not a keyword blacklist. Define risks, layer signals, apply controls across the full request path, handle uncertainty explicitly, protect telemetry, and learn from reviewed cases. Strong safeguards should reduce harm while keeping legitimate work moving.

That is it for today. Make safety visible, measured, and capable of improvement. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep157'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
