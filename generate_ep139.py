from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 139
title = 'EP139: AI API Evaluation — Turn Prompt Tests Into Release Gates'
description = 'A practical guide to evaluating AI API changes: build representative datasets, score quality and reliability, catch regressions, and make evaluations useful release gates.'
pub_date = 'Thu, 27 Aug 2026 08:30:00 +0000'
script = '''EP139: AI API Evaluation — Turn Prompt Tests Into Release Gates

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI systems can pass a demo and still regress in production. A model update may improve one benchmark while breaking structured output, tool selection, latency, or a small but important customer workflow. Today we will turn prompt tests into a repeatable evaluation process that can support release decisions.

Start with a representative dataset. Collect common requests, difficult edge cases, multilingual inputs, long contexts, malformed inputs, and examples from previous incidents. Include the tasks that matter to users, not only prompts that are easy to label. Keep a held-out set that is not used to tune prompts or routing policies.

Define the contract for each task. Some outputs need exact matching, some need valid JSON, some need citations, and some need a human judgment about usefulness. Write down the required fields, prohibited behavior, acceptable variation, and failure conditions. An evaluation without a clear contract becomes a collection of opinions.

Use layered scoring. Deterministic checks should run first: schema validity, required fields, code compilation, citation format, tool arguments, and policy constraints. Then use task-specific graders or human review for quality. Model-based judges can help scale comparisons, but calibrate them against human-labeled examples and inspect disagreements instead of treating the score as truth.

Compare changes fairly. Replay the same dataset against the current and candidate routes with controlled parameters. Record model, prompt version, tool definitions, retrieval snapshot, latency, token usage, retries, and cost. A score difference is difficult to interpret when several variables changed at once. A gateway such as Crazyrouter can keep route selection consistent while teams compare models through one API surface.

Track slices, not just averages. Overall quality may remain flat while a critical language, customer tier, or long-context slice gets worse. Break results down by task type, difficulty, language, input length, and failure category. Set minimum thresholds for important slices so a strong average cannot hide a serious regression.

Evaluate reliability and economics. Measure accepted-result rate, timeout rate, validation failures, fallback share, p95 latency, tokens per accepted result, and cost per successful task. A candidate that scores slightly higher but times out twice as often may be a poor production choice. Connect quality to the business outcome the workflow is meant to produce.

Make evaluations reproducible. Version datasets, graders, prompt templates, routing policies, and configuration. Store outputs and summaries with a run identifier. Fix random seeds where supported, but remember that provider behavior can still change. Reproducibility means being able to explain what was tested and why the result changed.

Turn results into release gates. Define which failures block deployment, which trigger manual review, and which are accepted with an explicit note. Run a small smoke suite on every change and a broader suite before model, prompt, or retrieval upgrades. Keep the gate fast enough that engineers use it instead of bypassing it.

Close the loop with production data. Sample real failures, remove sensitive information, and add useful cases to the dataset. Review false positives and false negatives in the graders. An evaluation suite should evolve with the product, while its historical versions remain available so teams can compare progress honestly.

The practical lesson is simple: evaluation is an engineering system, not a leaderboard screenshot. Use representative data, explicit contracts, layered graders, slice analysis, reproducible runs, and clear release gates. That is how teams improve AI applications without trading invisible regressions for impressive demos.

That is it for today. Test the change that users will actually experience. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep139'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
