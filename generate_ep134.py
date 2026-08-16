from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 134
title = 'EP134: AI Agent Workflows — Control Tool Calls, State, and Spend'
description = 'A practical guide to operating AI agent workflows: bound tool calls, persist state safely, validate actions, control retries and spend, and make long-running automation observable.'
pub_date = 'Sat, 22 Aug 2026 08:30:00 +0000'
script = '''EP134: AI Agent Workflows — Control Tool Calls, State, and Spend

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI agents are moving from single responses to multi-step workflows. They read context, call tools, inspect results, revise plans, and continue until a task is complete. That flexibility is useful, but every extra step adds latency, cost, and a chance of an unintended action. Today we will look at the controls that make agent workflows dependable.

Start with an explicit task boundary. Define what the agent is allowed to accomplish, what it must not do, and the conditions that end the run. A vague instruction such as keep improving can create an open-ended loop. Use a completion contract: required output, validation checks, maximum steps, deadline, and escalation path.

Treat tool calls as production operations. Give each tool a narrow schema, validate arguments before execution, and separate read actions from write actions. For destructive or externally visible actions, require approval or a stronger policy check. The model should propose an action, but application code should decide whether that action is permitted.

Persist state deliberately. Store the task identifier, current step, tool results, and important decisions in a durable record. Do not rely on the conversation window as the only source of truth. Durable state makes retries safer, supports resuming after a timeout, and lets operators inspect what happened without replaying every prompt.

Design for idempotency. Agents retry because networks fail, providers time out, and tool responses arrive late. A payment, ticket creation, deployment, or database write must not happen twice just because the model repeated a call. Use idempotency keys, request status, and deduplication at the tool boundary.

Control the loop budget. Set limits for total steps, tool calls, tokens, wall-clock time, and spend. Track the budget across the whole workflow rather than resetting it after each model request. If the agent reaches a limit, return a clear partial state and ask for human intervention instead of silently continuing.

Validate every important transition. Check that tool output matches the expected schema, that required fields are present, and that the next action is consistent with the current state. For generated code or structured documents, run deterministic checks before accepting the result. Validation is often cheaper than repairing a bad action later.

Route models by step. Planning, classification, extraction, and summarization may use a lighter model, while ambiguous reasoning or complex code may need a stronger one. A unified gateway such as Crazyrouter lets teams keep one API integration while applying different model policies to different workflow stages. Measure cost per successful task, not just the price of one call.

Make failures observable. Record trace identifiers, model routes, tool names, latency, retries, validation failures, fallback use, and spend. Redact secrets and sensitive prompt content. Operators need enough information to diagnose a stalled agent without turning logs into a copy of every private user conversation.

Build human handoffs into the design. Escalate when confidence is low, a policy check fails, the task exceeds its budget, or a write action needs approval. A good handoff includes the current state, evidence collected, proposed next action, and the exact reason the agent stopped. Humans should not have to reconstruct the entire run.

The practical lesson is simple: agent quality is not just model intelligence. It is the quality of the boundaries, tools, state, validation, budgets, and recovery paths around the model. Control the workflow and you can make automation more capable without making it more fragile.

That is it for today. Give every agent a boundary and every action a check. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep134'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
