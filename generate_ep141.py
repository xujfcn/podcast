from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 141
title = 'EP141: Structured AI Outputs — Make JSON Reliable in Production'
description = 'A practical guide to reliable structured AI outputs: design schemas, constrain generation, validate and repair responses, version contracts, and monitor JSON workflows in production.'
pub_date = 'Sat, 29 Aug 2026 08:30:00 +0000'
script = '''EP141: Structured AI Outputs — Make JSON Reliable in Production

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Many AI applications do not need a paragraph; they need a record that another program can trust. That might be an extracted invoice, a routing decision, a tool call, or a list of classified items. Asking for JSON is easy. Making structured output reliable under real traffic requires a contract, validation, and a recovery path. Today we will build that system.

Start with a schema, not an example. Define required fields, types, allowed values, nesting, null behavior, maximum lengths, and the meaning of an empty result. Examples are useful for the model, but only a schema tells application code what it can safely consume. Keep the contract as close as possible to the code that validates and uses it.

Make the schema task-specific. A giant universal response object creates ambiguity and encourages the model to fill fields that do not apply. Use small schemas for extraction, classification, planning, or tool arguments. Smaller contracts are easier to test, cheaper to generate, and safer to evolve.

Constrain generation when the route supports it. Use structured-output or JSON-schema modes where available, and configure tool parameters with precise types and descriptions. A unified gateway such as Crazyrouter can keep model access consistent, but capability differences still matter. Verify which models enforce the schema and which merely receive it as an instruction.

Validate at the boundary. Parse the response with a real JSON parser, validate it against the schema, reject trailing text when the contract forbids it, and check business rules that a schema cannot express. For example, a date may have the right string type but still be impossible, and a valid account identifier may not belong to the requesting tenant.

Treat invalid output as a classified failure. Distinguish truncated responses, malformed JSON, missing fields, wrong enum values, schema violations, and business-rule failures. These categories guide different fixes: increase output limits, simplify the prompt, adjust the schema, retry with a bounded policy, or send the case to review.

Use repair carefully. A small deterministic cleanup may remove an unwanted code fence, but broad string manipulation can silently change meaning. If a repair requires another model call, preserve the original output, cap attempts, and validate the repaired result with the same strict contract. Never let an unvalidated repair reach a write operation.

Version contracts explicitly. When a field changes meaning or a new required value appears, create a new schema version or maintain backward compatibility through an adapter. Record the schema version in traces and stored results. This makes failures explainable when old workers and new producers coexist during a deployment.

Design for uncertainty. Let the schema represent unknown, not found, and not applicable as distinct states when the product needs that distinction. Require evidence or source references for extracted values where possible. A model that says unknown is often safer than one that invents a plausible value to satisfy a required string.

Test adversarially. Include missing information, conflicting documents, long values, unusual Unicode, extra keys, prompt injection inside source text, and outputs near the token limit. Replay historical failures and test every model or routing change against the same contract. Measure valid-output rate, accepted-result rate, repair rate, retries, latency, and cost.

The practical lesson is simple: structured output is an API contract with a probabilistic producer. Define the schema, constrain generation, validate twice, version changes, and make uncertainty explicit. With those controls, AI responses can become dependable inputs to real software instead of hopeful strings.

That is it for today. Parse first, trust second. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep141'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
