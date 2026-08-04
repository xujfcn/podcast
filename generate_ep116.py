from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 116
title = 'EP116: AI API SLOs and Error Budgets — Reliability You Can Actually Operate'
description = 'A practical guide to service-level objectives and error budgets for AI applications: define success by workload, measure latency and correctness, account for fallbacks, and use burn rates to operate reliability.'
pub_date = 'Tue, 04 Aug 2026 08:30:00 +0000'
script = 'EP116: AI API SLOs and Error Budgets — Reliability You Can Actually Operate\n\nWelcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about service-level objectives and error budgets for AI API products. Most teams say they want high reliability. Fewer teams define what reliability means for a streamed model response, a tool call, a background generation job, or a fallback that returns lower-quality output.\n\nStart with the user journey, not the provider dashboard. A provider can report healthy availability while your users see authentication failures, queue delays, malformed output, or a model that cannot complete the requested tool call. Your service-level indicators should measure the experience your product is responsible for.\n\nDefine success precisely. For a chat request, success might mean the first token arrives within three seconds and the response completes without an application error. For a structured extraction workflow, success may require valid schema output. For an agent task, the final tool action and user-visible result may matter more than the initial model response.\n\nUse separate objectives for different workload classes. Interactive chat, batch summarization, image generation, coding agents, and payment-linked operations have different latency and correctness needs. A single availability target across every endpoint produces a number that is easy to publish but difficult to operate.\n\nMeasure latency with percentiles. Average latency hides the users waiting the longest. Track time to first token and total completion time at the fiftieth, ninety-fifth, and ninety-ninth percentiles. For asynchronous jobs, track queue age and time to final artifact instead of pretending that request acceptance equals completion.\n\nInclude quality-related failure where it is measurable. Empty responses, invalid JSON, missing citations, failed tool calls, language mismatches, and unusable media can all be user-visible failures even when the HTTP status is two hundred. Not every quality issue belongs in a pager alert, but important product contracts should appear in the objective.\n\nAn error budget converts the objective into an operating allowance. If the target permits a small fraction of failed or excessively slow requests, that allowance can guide decisions. When the budget is healthy, teams can ship faster and test new routes. When it burns too quickly, reliability work should take priority over risky changes.\n\nUse burn-rate alerts instead of waiting for the monthly target to fail. A fast burn rate detects a severe outage quickly. A slower window catches gradual degradation such as rising tail latency or repeated fallback use. Combining short and long windows reduces noise while still identifying urgent incidents.\n\nAttribute budget consumption to the responsible layer. Separate application errors, gateway policy failures, provider failures, queue timeouts, schema failures, and customer cancellations. This helps the team choose the correct response rather than blaming the upstream provider for every unsuccessful request.\n\nTreat fallbacks honestly. A fallback can preserve availability, but it may change latency, context limits, tool support, safety behavior, or output quality. Decide whether a fallback result counts as full success, degraded success, or failure for each workload. Otherwise the dashboard can stay green while the product quietly becomes worse.\n\nConnect SLOs to cost. An aggressive retry policy may improve apparent availability while doubling spend and tail latency. A premium fallback may rescue important requests but be wasteful for low-value batch jobs. Monitor cost per successful outcome alongside reliability so the team can see the economic price of each objective.\n\nProtect tenant and regional policy during recovery. A response is not successful if it violates data residency, model allowlists, or customer routing rules. Include policy enforcement in synthetic tests and incident reviews. Reliability cannot mean bypassing the controls that make the service safe to use.\n\nBuild dashboards around decisions. Show current objective compliance, remaining error budget, burn rate, affected workloads, fallback volume, latency percentiles, and representative trace IDs. Operators should be able to move from a budget alert to the routes and failure modes consuming it.\n\nReview objectives as the product changes. A target designed for a simple chatbot may not fit an agent that performs financial actions. Revisit indicators after major model changes, new regions, new tools, and significant shifts in traffic. Keep historical definitions so trend reports remain understandable.\n\nThe practical lesson is simple. An AI reliability target should describe a successful user outcome, not merely an available endpoint. Define indicators by workload, measure latency and correctness, account for degraded fallbacks, and use error-budget burn to decide when to ship and when to stabilize.\n\nThat is it for today. Build reliable multi-model applications with unified routing and clear operational signals through Crazyrouter at crazyrouter.com, and see you in the next episode.'

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
