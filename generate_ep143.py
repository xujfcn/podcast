from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 143
title = 'EP143: Context Engineering — Keep Long AI Requests Useful and Affordable'
description = 'A practical guide to context engineering for AI APIs: select relevant information, manage long inputs, preserve important state, control token costs, and improve answer quality.'
pub_date = 'Mon, 31 Aug 2026 08:30:00 +0000'
script = '''EP143: Context Engineering — Keep Long AI Requests Useful and Affordable

Welcome back to AI Dev Tools — The Crazyrouter Podcast. As AI applications become more capable, their prompts often become longer: conversation history, retrieved documents, tool results, policies, examples, and user preferences all compete for attention. More context is not automatically better. Today we will build a context engineering practice that keeps long requests relevant, reliable, and affordable.

Start with a context budget. Define how many tokens each part of the request may consume: instructions, recent conversation, retrieved evidence, tool output, examples, and the requested answer. Reserve space for the completion instead of filling the entire model window with input. A hard budget turns prompt growth into an observable engineering constraint.

Separate stable from changing information. System instructions, schemas, and product policies may be reused or cached, while user messages and retrieved documents change frequently. Keeping these categories distinct makes caching, debugging, and invalidation easier. Version stable context so a prompt change can be connected to a quality change.

Retrieve for relevance, not volume. Use metadata filters, access control, recency, and task-specific search before sending documents to the model. A large pile of loosely related passages can bury the evidence that matters. Include source identifiers and enough surrounding context to preserve meaning, but do not send every result by default.

Compress carefully. Summaries, extracted facts, and deduplicated passages can reduce tokens, but compression may remove exceptions, numbers, or qualifications. Preserve citations and provenance, and validate summaries on representative tasks. For high-stakes decisions, keep the original evidence available for inspection rather than treating a summary as the only record.

Manage conversation history deliberately. Keep recent turns when recency matters, summarize older discussion when continuity matters, and retain explicit user decisions separately from casual dialogue. Do not let a long transcript silently push out the current task or critical safety instructions. A durable state record is often better than replaying an ever-growing chat window.

Control tool output. Tool responses should return the fields needed for the next decision, not every column or debug message. Paginate large results, cap repeated calls, and summarize intermediate data in application code when possible. The model should receive a useful representation of tool state, while the full result remains available through an auditable record.

Protect access boundaries. Context assembly is an authorization step. Filter documents and conversation state by tenant, user, and purpose before retrieval and before prompt construction. Never rely on the model to ignore information that the application should not have provided in the first place.

Route by task and context size. Short classification may use a smaller route, while a long synthesis task may require a model with a larger window or stronger reasoning. A unified gateway such as Crazyrouter can keep the application integration stable while routing policies account for context length, latency, and cost. Measure the outcome, not just the maximum window advertised by a model.

Observe context quality. Track input tokens, truncation, retrieval hit rate, citation coverage, context assembly latency, cache reuse, accepted-result rate, and cost per successful task. Sample cases where the answer is wrong despite a successful request. The failure may be missing evidence, irrelevant evidence, instruction conflict, or an over-compressed summary.

Test context changes as production changes. Evaluate retrieval settings, summarization prompts, history policies, and context budgets with the same representative tasks. Include long inputs, conflicting sources, missing evidence, permission boundaries, and prompt injection inside retrieved text. A smaller prompt that loses a critical exception is not an optimization.

The practical lesson is simple: context is an engineered input, not a transcript dump. Budget it, retrieve selectively, preserve provenance, protect access boundaries, and measure whether the information helped. Good context engineering improves quality while keeping latency and token spend under control.

That is it for today. Give the model the right evidence, not all the evidence. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep143'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
