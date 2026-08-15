from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 130
title = 'EP130: AI API Cost Control — Optimize the Whole Workflow, Not Just Token Prices'
description = 'A practical cost-control guide for AI API products: measure cost per successful task, reduce waste, route by difficulty, control context, and protect margins without degrading user outcomes.'
pub_date = 'Tue, 18 Aug 2026 08:30:00 +0000'
script = '''EP130: AI API Cost Control — Optimize the Whole Workflow, Not Just Token Prices

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about AI API cost control. The first instinct is usually to compare the price per million tokens. That number matters, but it is only one part of the bill. A cheap request that fails, retries, or needs human repair can cost more than a slightly more expensive request that completes correctly the first time.

Start with the right unit: cost per successful task. Include input and output tokens, retries, fallbacks, tool calls, retrieval, storage, and any human correction. Then connect the number to a real product outcome such as a resolved support case, a accepted document, or a completed coding change. This tells you which optimizations actually improve the business.

Control context before changing models. Long conversation history, duplicated instructions, oversized retrieved documents, and unused tool schemas all consume tokens. Set a context budget, reserve space for the answer, rank information by relevance, summarize old turns, and remove content that the model cannot use. Better context often improves both quality and cost.

Route by difficulty. Simple classification, extraction, rewriting, and short summaries do not need the same model as ambiguous reasoning or complex code generation. Define workload classes, test representative examples, and route each class to the least expensive model that meets its quality and reliability target. A unified gateway such as Crazyrouter makes this policy easier to change without rewriting application integrations.

Treat retries as spend. A retry budget should be tied to a deadline and an error class. Do not retry invalid requests or deterministic validation failures. Use exponential backoff for temporary failures, cap attempts, and stop when the result can no longer arrive in time. Track retry tokens separately, because a rising retry share can erase the savings from a cheaper model.

Use caching where behavior allows it. Stable system instructions, reference material, and repeated prefixes can often be cached. Measure cache hit rate, actual token savings, and whether invalidation is correct. Never cache private data across tenants, and do not trade correctness for a misleading dashboard number.

Control output length deliberately. Ask for the format and level of detail the task needs. Structured outputs, concise explanations, and bounded reasoning can reduce waste and make validation easier. But avoid arbitrary tiny limits that cause truncation and force a second request. The goal is the shortest complete answer, not the shortest answer.

Set operational guardrails. Give each tenant, feature, and environment a budget. Alert on unusual spend, token spikes, retry storms, and fallback changes. Add circuit breakers for runaway loops and require explicit approval for expensive models in development. Cost controls should fail clearly and safely rather than silently producing incomplete business results.

Evaluate quality and cost together. Run the same workload across candidate models and record accepted-result rate, latency, retries, fallback share, and cost per accepted result. A model with a lower list price is not a win if it produces more invalid JSON, misses required facts, or causes more timeouts. Use canaries and keep rollback easy.

The practical lesson is simple: optimize the workflow, not just the token price. Reduce unnecessary context, route by task, cache stable inputs, bound outputs, control retries, and measure the cost of a successful result. That approach lowers spend while preserving the experience users actually came for.

That is it for today. Make every successful task count. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep130'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
