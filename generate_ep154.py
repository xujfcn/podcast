from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 154
title = 'EP154: AI Tool Calling — Make Function Calls Safe and Reliable'
description = 'A practical guide to reliable AI tool calling: design precise schemas, validate arguments, enforce permissions, handle failures, prevent duplicate actions, and audit every call.'
pub_date = 'Fri, 11 Sep 2026 08:30:00 +0000'
script = '''EP154: AI Tool Calling — Make Function Calls Safe and Reliable

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Tool calling lets an AI application move beyond text and interact with calendars, databases, search systems, tickets, and business workflows. It also means a model can propose an action that has real consequences. Today we will design tool calling so it is useful, constrained, and auditable in production.

Start with a narrow tool contract. Define the tool name, purpose, required arguments, types, allowed values, limits, and failure responses. Avoid one universal tool with a command string that accepts anything. Small, explicit tools make model behavior easier to validate and application permissions easier to enforce.

Separate proposal from execution. The model may select a tool and generate arguments, but application code should validate the call before execution. Check tenant, user, resource, authorization, rate limits, and business rules outside the model. Never treat a plausible tool call as proof that the action is allowed.

Use strict argument validation. Parse the arguments as structured data, reject unknown fields where appropriate, enforce maximum lengths and ranges, and normalize identifiers before lookup. Validate relationships that a schema cannot express, such as whether a requested account belongs to the current tenant or whether a date range is permitted.

Prefer read-only tools first. Search, retrieve, calculate, and inspect operations are easier to retry and review than writes. For a write action, require idempotency keys, explicit confirmation when impact is high, and a deterministic record of what will change. A gateway such as Crazyrouter can provide a consistent model interface, while the application owns the final authorization decision.

Design for ambiguity. Let the model ask for missing information instead of guessing required arguments. Represent unknown, not applicable, and not found as distinct outcomes when the workflow needs that distinction. If a tool result is incomplete or contradictory, return a clear status that leads to clarification or review rather than encouraging another blind call.

Make execution idempotent. Models retry, workers restart, and network responses can be lost after a tool has succeeded. Use idempotency keys and durable attempt records for actions such as creating tickets, sending messages, charging accounts, or changing deployments. A repeated call should return the existing result or a safe status, not perform the action twice.

Control the tool loop. Set limits for total tool calls, repeated calls to the same tool, tokens, elapsed time, and spend. Detect cycles where the model alternates between the same tools without progress. When the budget ends, preserve the current state and return a useful handoff instead of silently continuing.

Treat tool output as untrusted data. Validate the response schema, cap its size, redact secrets, and separate returned content from instructions. A web page, database field, or user-generated ticket may contain text that tries to redirect the model. Tool results should inform the next step, not redefine the system policy.

Handle failures explicitly. Distinguish invalid arguments, permission denial, not found, rate limits, timeouts, provider errors, and business-rule rejection. Give the model enough structured information to recover when recovery is safe, but do not expose sensitive diagnostics or encourage repeated attempts at a permanent failure.

Audit the whole action. Record request ID, tenant, actor, model, policy version, selected tool, validated arguments, approval state, execution result, latency, and idempotency key. Redact secrets and unnecessary private content. These records let operators answer what happened without relying on an unverifiable model transcript.

The practical lesson is simple: tool calling is an authorization and workflow problem wrapped in a model interface. Define narrow schemas, validate outside the model, enforce permissions, make writes idempotent, bound the loop, treat results as untrusted, and audit every action. With those controls, AI can operate real systems without becoming an uncontrolled command channel.

That is it for today. Let the model suggest actions, and let the application decide. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep154'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
