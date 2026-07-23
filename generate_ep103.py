from pathlib import Path
import json, re, subprocess, time, xml.etree.ElementTree as ET
import requests

root = Path('/root/.openclaw/workspace/podcast')
ep = 103
title = 'EP103: Model Capability Contracts — Stop Silent Failures Across Providers'
description = 'How to define and enforce model capability contracts for tools, JSON output, context limits, vision, streaming, retries, and safe multi-provider routing.'
pub_date = 'Thu, 23 Jul 2026 08:30:00 +0000'
script = """EP103: Model Capability Contracts — Stop Silent Failures Across Providers

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about model capability contracts: a practical way to stop multi-provider applications from routing requests to models that cannot reliably execute them.

An OpenAI-compatible endpoint makes transport easier, but it does not make every model behavior identical. Models differ in tool calling, structured output, context length, image support, streaming events, parameter handling, and safety behavior. If routing only checks the model name and price, failures will appear later as malformed output, ignored settings, or incomplete tool calls.

A capability contract is a machine-readable description of what a route supports and what your application requires. Begin with explicit fields for text, vision, audio, tools, parallel tool calls, strict JSON schema, streaming, prompt caching, maximum input, maximum output, and supported sampling parameters. Use tested capabilities, not marketing labels.

Separate claimed support from verified support. A provider may document JSON mode, but your acceptance test might show that nested schemas fail or extra fields appear under pressure. Record both the advertised feature and the level your production tests actually approve. Routing should rely on the verified level.

Define requirements per task. A chat answer may need only text and streaming. An invoice extractor may require image input, strict structured output, and a validated schema. An autonomous workflow may require tools, idempotent retries, and stable tool-call identifiers. The request should carry these requirements before the router chooses a model.

Then make routing enforce the contract. If no approved route meets the requirements, return a clear capability error instead of automatically choosing a weaker option. An unnoticed downgrade can produce a response that looks successful while omitting a required field, skipping a tool, or shortening the available context.

Context limits need special treatment. Do not compare only the advertised token window. Reserve space for system instructions, tool definitions, retrieved documents, and the expected completion. Tokenization also differs across model families. Estimate with a safety margin and define a truncation policy before routing.

For structured output, validate twice. First confirm that the route supports the requested schema mode. Then validate the actual response in your application. A provider returning HTTP 200 does not mean the contract was satisfied. Store the validation error category so routing quality can be measured over time.

Tool calling needs its own compatibility tests. Check argument encoding, required fields, multiple calls in one turn, call identifiers, streaming deltas, and behavior when a tool result is large. Normalize provider responses at the gateway, but preserve enough raw metadata to debug discrepancies.

Version the contracts. Provider behavior changes, models are upgraded, and aliases may point to new snapshots. Tie each verified contract to a model version, provider route, test-suite version, and verification date. Re-run the suite after SDK updates or routing changes.

Add contract metrics to operations. Track capability mismatch rate, schema acceptance rate, tool-call success, truncation events, fallback frequency, and cost per accepted result. A cheaper route that frequently violates the contract is not actually cheaper.

A good rollout starts with a small conformance suite. Create representative prompts for every required capability, run them against candidate routes, and store pass or fail evidence. Promote only routes that meet your threshold. Use canary traffic before broad production access.

The key idea is simple: compatibility should be proven before routing, not guessed after an incident. Capability contracts turn vague model labels into enforceable production policy.

That is it for today. Define what the task needs, verify what each route can do, and fail clearly when they do not match. Try the unified API at crazyrouter.com, and see you in the next episode."""

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
key = re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)', tools).group(1)
paras = script.split('\n\n')
parts = [
    '\n\n'.join(paras[:3]),
    '\n\n'.join(paras[3:6]),
    'Define requirements per task. A chat answer may need only text and streaming.',
    'An invoice extractor may require image input, strict structured output, and a validated schema.',
    'An autonomous workflow may require tools, idempotent retries, and stable tool-call identifiers.',
    'The request should carry these requirements before the router chooses a model.',
    *paras[7:],
]
for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_chunk{i}.mp3'
    if out.exists() and out.stat().st_size > 1000:
        print('part', i, 'cached', flush=True)
        continue
    for attempt in range(1, 4):
        response = requests.post(
            'https://crazyrouter.com/v1/audio/speech',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
            timeout=300,
        )
        print('part', i, response.status_code, 'attempt', attempt, flush=True)
        if response.ok:
            out.write_bytes(response.content)
            break
        if attempt == 3:
            response.raise_for_status()
        time.sleep(5 * attempt)

concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file 'ep{ep:03d}_chunk{i}.mp3'\n" for i in range(1, len(parts) + 1)))
audio = root / f'audio/ep{ep:03d}.mp3'
subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(audio)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True)
seconds = float(json.loads(probe.stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
size = audio.stat().st_size

feed = root / 'feed.xml'
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
if not any((item.findtext('title') or '').startswith(f'EP{ep:03d}:') for item in channel.findall('item')):
    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = pub_date
    enclosure = ET.SubElement(item, 'enclosure')
    enclosure.set('url', f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3')
    enclosure.set('length', str(size))
    enclosure.set('type', 'audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    ET.SubElement(item, f'{{{ns}}}duration').text = duration
    ET.SubElement(item, f'{{{ns}}}episode').text = str(ep)
    ET.SubElement(item, f'{{{ns}}}episodeType').text = 'full'
    ET.SubElement(item, f'{{{ns}}}explicit').text = 'false'
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'
    existing = channel.findall('item')
    channel.insert(list(channel).index(existing[0]) if existing else len(list(channel)), item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)

print('DONE', audio, size, duration)
