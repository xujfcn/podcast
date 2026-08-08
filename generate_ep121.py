from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 121
title = 'EP121: AI API Evaluation in Production — Measure What Users Actually Need'
description = 'A practical guide to evaluating AI API systems in production: define task outcomes, build representative datasets, combine human and automated checks, run canaries, and connect quality to cost and reliability.'
pub_date = 'Sun, 09 Aug 2026 08:30:00 +0000'
script = 'EP121: AI API Evaluation in Production — Measure What Users Actually Need\n\nWelcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about evaluating AI API systems in production. A model can score well on a benchmark and still fail your users. Production evaluation connects model behavior to the tasks, constraints, latency, cost, and safety requirements that matter in your application.\n\nStart with a task taxonomy. Separate summarization, extraction, classification, coding, search answers, tool use, and creative generation. Each task needs different evidence of success. A single overall quality score hides useful differences and can encourage teams to optimize the wrong workload.\n\nDefine the outcome before choosing the metric. For extraction, measure schema validity and field accuracy. For retrieval answers, measure groundedness and citation coverage. For agents, measure successful task completion and tool-call correctness. For customer support, combine resolution, escalation, policy compliance, and user feedback.\n\nBuild a representative evaluation set. Include common cases, difficult cases, multilingual inputs, long contexts, ambiguous requests, adversarial inputs, and recent production failures. Remove unnecessary personal data and record why each example exists. A small, carefully maintained set is more useful than a huge collection nobody reviews.\n\nUse multiple evaluators. Deterministic checks work well for JSON validity, required fields, exact labels, latency, and token budgets. Human review helps with usefulness, tone, and subtle factual errors. Model-based judges can scale comparisons, but calibrate them against human decisions and watch for systematic preferences.\n\nEvaluate the whole route. The model is only one part of the system. Include prompt templates, retrieval, tool definitions, transformations, retries, fallbacks, and post-processing. A route that looks good in isolation may fail after a gateway changes the context or a fallback receives a different payload shape.\n\nTrack production slices. Compare quality by model, provider, region, language, tenant tier, prompt version, and application feature. Aggregate scores can remain stable while one important customer segment degrades. Keep dimensions stable enough to compare releases without creating unmanageable reporting noise.\n\nAdd online signals carefully. User corrections, re-prompts, abandonments, escalations, thumbs-down events, and successful tool actions can reveal quality problems. They are not perfect labels, so interpret them with context. A user may re-prompt because they changed their mind, not because the first answer failed.\n\nUse canary releases and shadow tests. Send a small percentage of traffic to a new model or prompt, or evaluate the candidate on copied inputs without showing its output to users. Compare quality, tail latency, cost, refusal behavior, and tool reliability before expanding the rollout.\n\nWatch for evaluation drift. Models, provider behavior, prompts, user traffic, and business requirements change. A benchmark that was useful six months ago may no longer represent current risk. Review the evaluation set after incidents, product changes, and major model updates.\n\nKeep quality tied to economics. Report cost per successful outcome, not only tokens or requests. A slightly more expensive model may be cheaper overall if it prevents retries, escalations, or manual correction. Conversely, a premium model may be wasteful for routine tasks that a smaller route handles reliably.\n\nMake failures actionable. Every failed example should identify a likely class: missing context, wrong route, instruction conflict, tool error, hallucination, formatting failure, policy refusal, or latency timeout. Link these classes to engineering owners and regression tests so evaluation changes production behavior.\n\nProtect evaluation data. Store datasets, traces, labels, and judge outputs with appropriate access controls. Redact sensitive content, separate tenant data, and record retention. Evaluation systems can become a shadow data warehouse if teams copy production prompts without governance.\n\nThe practical lesson is simple. Production evaluation is not a leaderboard. Define success by task, test the entire route, combine deterministic and human evidence, slice results by real workloads, and connect quality to cost and reliability. Then model routing becomes an evidence-based engineering decision.\n\nThat is it for today. Evaluate and route multi-model applications through one unified API with Crazyrouter at crazyrouter.com, and see you in the next episode.'

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
key = re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)', tools).group(1)
parts = script.split('\n\n')

for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_chunk{i}.mp3'
    if out.exists() and out.stat().st_size > 1000:
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
