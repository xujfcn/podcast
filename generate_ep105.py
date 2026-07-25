from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 105
title = 'EP105: Claude Opus 5 Is Live — A Practical Evaluation Plan for Developers'
description = 'Claude Opus 5 is now available on Crazyrouter. Here is a disciplined plan for evaluating a new flagship model on quality, reliability, latency, and cost before moving production traffic.'
pub_date = 'Sat, 25 Jul 2026 08:30:00 +0000'
script = """EP105: Claude Opus 5 Is Live — A Practical Evaluation Plan for Developers

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Claude Opus 5 is now available on Crazyrouter. A major model launch is exciting, but the useful question for a development team is not whether the model is new. It is whether the model improves your real workload enough to justify changing production traffic.

Start with a representative evaluation set. Collect actual prompts from coding, analysis, support, extraction, planning, and agent workflows. Remove private data, preserve the difficult edge cases, and include examples where the current model succeeds as well as where it fails. A benchmark made only from failures can exaggerate the value of switching.

Define success before running the test. For code, that may mean passing tests, following repository conventions, and producing a minimal patch. For analysis, it may mean factual accuracy, complete evidence, and a useful recommendation. For agents, measure tool selection, argument correctness, recovery from errors, and the number of steps required to finish.

Use blind comparisons where possible. Show reviewers two outputs without model names and ask which one better satisfies the rubric. Model reputation can influence judgment, especially around a flagship launch. Blind scoring makes the result about the work instead of the label.

Test reliability, not just the best answer. Run important cases more than once. A model that produces one brilliant response and four inconsistent ones may be less useful than a model with slightly lower peak quality but dependable behavior. Track variance, malformed outputs, refusals, tool errors, and incomplete responses.

Measure latency by workflow stage. Time to first token affects chat experiences, while total completion time matters for background jobs. Agent workflows also need step-level timing because a small delay repeated across many tool calls can dominate the user experience.

Evaluate cost with the prompts you actually send. Record input tokens, output tokens, retries, cache behavior, and any increase in agent steps. A stronger model can sometimes reduce total cost by solving a task in fewer attempts, while a longer or more elaborate response can move cost in the other direction.

Check operational compatibility. Validate structured output, streaming, tool calls, cancellation, timeout handling, and retry behavior. Confirm that logs and usage records identify the model correctly. These details often decide whether a model is ready for production even when response quality is excellent.

Roll out gradually. Start with internal traffic, then a small percentage of low-risk production requests. Compare success rate, latency, cost, and user feedback against the current route. Keep a fallback available and define the threshold that will pause or reverse the rollout.

Use routing instead of treating migration as all or nothing. Claude Opus 5 may become the preferred choice for the hardest reasoning or coding tasks while faster or lower-cost models continue handling routine work. The right result is a portfolio that matches model capability to task value.

Finally, save the evaluation set and rerun it when prompts, tools, or models change. A one-time launch test becomes much more valuable when it turns into a repeatable decision process.

Claude Opus 5 is live on Crazyrouter. Try it on your own difficult cases, measure the full workflow, and move production traffic based on evidence. Visit crazyrouter.com, and see you in the next episode."""

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
key = re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)', tools).group(1)
parts = script.split('\n\n')

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
subprocess.run(
    ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(audio)],
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
probe = subprocess.run(
    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)],
    capture_output=True,
    text=True,
    check=True,
)
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
