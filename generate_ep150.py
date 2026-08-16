from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 150
title = 'EP150: AI API Prompt Optimization — Reduce Tokens Without Losing Quality'
description = 'A practical guide to optimizing AI API prompts: remove waste, preserve critical instructions, control context growth, measure quality, and reduce token spend safely.'
pub_date = 'Mon, 7 Sep 2026 08:30:00 +0000'
script = '''EP150: AI API Prompt Optimization — Reduce Tokens Without Losing Quality

Welcome back to AI Dev Tools — The Crazyrouter Podcast. One of the fastest ways to reduce AI API cost and latency is to send less unnecessary context. But prompt optimization is not a contest to make every request shorter. Removing a sentence can remove a safety rule, an important exception, or the evidence needed for a correct answer. Today we will optimize prompts with measurable quality controls.

Start with a prompt inventory. Capture system instructions, examples, conversation history, retrieved passages, tool descriptions, and formatting requirements separately. Measure their token contribution and identify which parts are stable, duplicated, or only relevant to certain tasks. A total prompt size tells you there is a problem; a component inventory tells you what to change.

Remove duplication first. Repeated policy text, duplicated document passages, verbose tool descriptions, and old conversation turns often add tokens without adding information. Deduplicate retrieved evidence and keep one authoritative version of each instruction. This is usually safer than rewriting the core behavior immediately.

Separate task instructions from data. Clear boundaries make prompts easier to inspect and reduce confusion when user content or retrieved documents contain instruction-like text. Keep stable instructions versioned, and label examples and evidence so the model can distinguish them from the rules it must follow.

Make examples earn their place. Few-shot examples can improve consistency, but irrelevant or contradictory examples increase cost and may confuse the model. Measure performance with and without each example group. Keep examples short, representative, and aligned with the current output contract.

Control history deliberately. Do not replay an entire conversation when only a decision, preference, or unresolved issue matters. Summarize older turns, preserve important state in structured fields, and remove obsolete instructions. Test summaries against the original task so compression does not erase a qualification the user relies on.

Tune retrieval before expanding the model window. More documents do not guarantee better answers. Use filters, reranking, deduplication, and source-aware limits to send the smallest evidence set that supports the task. Preserve citations and provenance, and make missing evidence explicit instead of filling the context with loosely related passages.

Optimize tool descriptions and results. Describe parameters, constraints, and failure modes precisely, but do not include a full manual in every request. Return only the fields needed for the next decision, paginate large results, and keep detailed records outside the prompt. This reduces both input tokens and the chance that important tool output gets buried.

Use prompt caching where applicable. Keep stable prefixes stable, separate changing user content, and version the prefix when instructions change. A gateway such as Crazyrouter can provide a consistent model access layer while the application controls prompt composition and cache semantics. Track cached and uncached usage separately when pricing supports it.

Measure quality per outcome. Compare valid-output rate, accepted-result rate, factual or task-specific quality, latency, retries, and cost per successful task before and after each change. Evaluate important slices such as long inputs, languages, tenants, and edge cases. A smaller prompt that saves tokens but increases human review is not a successful optimization.

Roll out incrementally. Version the prompt, run a representative evaluation suite, canary real traffic, and keep the previous prompt available for rollback. Record the prompt version and route in traces so a quality change can be connected to a specific edit. Treat prompt changes like code changes when they affect production behavior.

The practical lesson is simple: optimize information density, not just character count. Inventory the prompt, remove duplication, control history and retrieval, preserve boundaries, measure accepted outcomes, and roll out reversibly. That is how teams reduce AI API spend while keeping the instructions and evidence that quality depends on.

That is it for today. Send the model less noise, not less truth. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep150'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
