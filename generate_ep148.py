from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 148
title = 'EP148: AI API Routing — Choose the Right Model for Every Request'
description = 'A practical guide to AI API routing: classify requests, match models to tasks, combine latency, quality, and cost policies, and make routing decisions observable and easy to change.'
pub_date = 'Sat, 5 Sep 2026 08:30:00 +0000'
script = '''EP148: AI API Routing — Choose the Right Model for Every Request

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Many AI applications begin with one model and one endpoint. As the product grows, that simple choice becomes a constraint. Different tasks need different tradeoffs: fast classification, careful reasoning, long context, low cost, structured output, or regional availability. Today we will design model routing as an explicit policy instead of a pile of scattered conditionals.

Start with workload classification. Identify the task type, required capabilities, input size, latency target, quality threshold, data policy, and budget. A short label request should not automatically use the same route as a long research task. Keep classification deterministic where possible, and record the reason for each route decision.

Build a capability matrix. Track context limits, vision support, tool calling, structured output, streaming, languages, latency, availability, and pricing for every approved model. Validate these properties with real requests because compatible API shapes do not guarantee identical behavior. Version the matrix when provider capabilities or prices change.

Separate hard constraints from preferences. Data residency, required tools, and maximum context may eliminate a route completely. Among the remaining candidates, optimize for quality, latency, cost, or availability according to the workload. This prevents a cheap but incompatible model from being selected merely because it scored well on one dimension.

Use a stable policy layer. Keep model selection in a gateway or routing service rather than duplicating it across every application. A unified gateway such as Crazyrouter can provide one API surface while policy selects the underlying route. Version policies, review changes, and make the previous policy easy to restore.

Use progressive routing when useful. A small model can handle clear, low-risk requests, while an uncertainty signal, validation failure, or task complexity can escalate to a stronger route. Define escalation rules in application code and cap the number of hops. Do not let the model route itself indefinitely based on an unverified confidence statement.

Account for the full request cost. Include input and output tokens, retries, fallback attempts, latency impact, caching, and human review. A route with the lowest per-token price may be more expensive per accepted result if it produces invalid output or requires repeated repair. Compare routes on the product outcome they deliver.

Keep routing decisions observable. Record policy version, candidate routes, selected model, exclusion reason, fallback path, latency, validation result, token usage, and effective cost. Do not log sensitive prompts just to explain a route. Structured metadata is usually enough for operators to understand why traffic moved.

Test routing as a system. Build a dataset of representative workloads and replay it against candidate policies. Measure quality, p95 latency, errors, fallback share, cost, and important slices such as language, tenant, and context size. Test boundary cases where small changes in input length or task label could select a different model.

Plan for change. Providers add models, retire endpoints, change prices, and experience regional capacity differences. Keep a review cadence for the capability matrix and policy thresholds. Use canary traffic for routing changes, compare old and new decisions, and retain rollback capacity until the new policy is trusted.

The practical lesson is simple: routing is product logic with operational consequences. Classify requests, enforce hard constraints, optimize explicit tradeoffs, observe every decision, and test policies against real workloads. With a deliberate routing layer, teams can adopt new models without rewriting every application or guessing which model should handle each task.

That is it for today. Route by need, not by habit. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep148'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
