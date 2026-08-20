from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 166
title = 'EP166: AI API Quality Gates — Stop Bad Outputs Before They Reach Users'
description = 'A practical guide to AI API quality gates: validate structure, ground answers, check tool actions, measure accepted results, and fail safely when outputs are not ready.'
pub_date = 'Wed, 23 Sep 2026 08:30:00 +0000'
script = '''EP166: AI API Quality Gates — Stop Bad Outputs Before They Reach Users

Welcome back to AI Dev Tools — The Crazyrouter Podcast. A model response is not automatically a usable result. It may be incomplete, unsupported by evidence, malformed for a downstream parser, or unsafe to turn into an external action. Today we will design quality gates that catch bad AI outputs before they reach users or production systems.

Start with the contract. Define what a successful result means for each workflow: required fields, acceptable evidence, language, format, confidence, latency, and permitted actions. “The model answered” is not a quality criterion. A contract gives the application something concrete to validate after generation.

Validate structure first. Parse JSON, check schemas, enforce enums, verify required fields, and reject unexpected values. For tool calls, validate names and arguments before execution. Keep repair attempts bounded and observable. If a response cannot be repaired safely, return a clear retry or review state instead of passing malformed data downstream.

Check meaning, not only syntax. A response can be valid JSON and still be wrong. Use citations, retrieval checks, deterministic business rules, entailment checks, or a second model only where the risk justifies the cost. A gateway such as Crazyrouter can provide a consistent model access layer, but workload-specific quality policy belongs at the application boundary.

Measure accepted results. Track how often users accept, edit, retry, reject, or escalate an output. Include fallback use, validation failures, repair attempts, and human corrections in the cost and quality picture. A high HTTP success rate can coexist with poor product quality; accepted-result rate is closer to the outcome users actually need.

Design safe failure states. Not every failed check should produce a generic error. A missing citation may request more evidence. Invalid arguments may ask the model to retry. A policy risk may require human review. A timeout may use a compatible fallback. Make the next action explicit so users and operators understand what happened.

Keep gates proportional to risk. A draft summary may need formatting and basic grounding checks. A financial transfer, medical recommendation, or production deployment needs stronger validation, permissions, and possibly human approval. Excessive gates add latency and cost, while weak gates allow silent damage. Match the control to the consequence.

Test the gates themselves. Build fixtures for malformed JSON, incomplete lists, unsupported claims, prompt injection, tool argument confusion, empty retrieval, provider truncation, and fallback capability gaps. Test both detection and recovery. A quality gate that detects a failure but leaves the queue stuck is not a complete production control.

Version everything that affects acceptance. Store the prompt version, schema version, policy version, evaluator version, model route, and evidence snapshot with the result. When quality changes, responders need to know whether the cause was the model, the prompt, the data, or the gate. Versioned evidence also makes audits and rollbacks possible.

Give users honest feedback. If an answer is uncertain, show that uncertainty in useful language. If a result is being checked, say so. If the system cannot complete the task, explain the safe next step. Trust grows when the product distinguishes a verified answer from a plausible draft instead of presenting every output with the same confidence.

The practical lesson is simple: generation is only one stage of an AI workflow. Define the contract, validate structure and meaning, measure accepted results, fail safely, and version the evidence behind every decision. Quality gates turn model output into a dependable product capability.

That is it for today. Validate before you trust, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep166'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
