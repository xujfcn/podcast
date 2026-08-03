from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 115
title = 'EP115: AI API Cost Attribution — Know What Every Feature Actually Costs'
description = 'A practical guide to AI API cost attribution: connect model usage, retries, routing, and price history to user-visible outcomes so product and finance teams can optimize real unit economics.'
pub_date = 'Mon, 03 Aug 2026 08:30:00 +0000'
script = "EP115: AI API Cost Attribution — Know What Every Feature Actually Costs\n\nWelcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about cost attribution for AI API products. A monthly provider bill tells you how much money left the account. It does not tell you which feature created the cost, which customer received value, or which route wasted tokens on retries.\n\nStart with a stable request identity. Every model call should carry a request ID that connects the application event, gateway route, provider response, usage record, and billing entry. For workflows with several model calls, add a parent operation ID so the team can calculate the full cost of one user action.\n\nDefine the dimensions that matter before collecting data. Useful labels include product, feature, environment, tenant, model, provider, region, endpoint type, and workload class. Avoid putting email addresses, raw prompts, or arbitrary user input into metric labels. Use internal identifiers and keep sensitive mappings in controlled systems.\n\nAttribute both input and output usage. Input tokens may include system instructions, retrieved documents, tool schemas, conversation history, and user content. Output tokens may include reasoning, visible text, tool arguments, or structured data. If the provider reports cached tokens or separate reasoning usage, preserve those fields instead of reducing everything to one total.\n\nTrack the complete workflow cost. A support answer might require embedding, retrieval, reranking, a chat completion, and a follow-up tool call. Looking only at the final chat request understates the real cost. Aggregate every child operation under the user-visible outcome and record whether that outcome succeeded.\n\nRetries and fallbacks need special treatment. A timeout can produce provider usage even when the application receives no answer. A retry can then create a second charge. Record each attempt separately, but attribute all attempts to the same parent operation. This exposes the cost of unreliability rather than hiding it inside average token spend.\n\nUse actual route pricing. Model aliases can point to different providers or pricing tiers over time. Store the selected route, price version, currency, and timestamp with the usage record. Recalculating historical cost using today's price table can make reports disagree with invoices and hide the impact of routing changes.\n\nMeasure cost per successful outcome. Cost per request is useful, but it can reward cheap failures. Better metrics include cost per resolved support ticket, accepted code change, completed document, qualified lead, or successful agent task. Pair spend with latency and quality so optimization does not quietly damage the product.\n\nCreate budgets at several levels. Set organization, team, feature, tenant, and experiment budgets where appropriate. Use soft alerts before hard limits. A sudden cost spike may come from growth, a bug, a prompt expansion, or an attack. The response should depend on the cause, not only the number.\n\nDetect common leakage patterns. Watch for duplicated requests, unbounded conversation history, repeated retrieval context, oversized tool schemas, accidental use of premium models, retry storms, abandoned streaming responses, and test traffic hitting production. These problems often save more money than negotiating a small price reduction.\n\nHandle shared infrastructure fairly. Gateway fees, storage, vector databases, observability, and background evaluation may not map perfectly to one request. Separate direct model cost from allocated platform cost. Document the allocation rule so finance and engineering can understand why a feature's reported margin changed.\n\nGive product teams useful views. A good dashboard shows daily spend, cost per successful outcome, model mix, retry cost, cache savings, and the largest changes by feature. It should let a team move from an anomaly to representative operation IDs without exposing customer content.\n\nReconcile estimates with provider records and invoices. Usage events can be delayed, duplicated, or missing after an incident. Compare internal totals with provider exports, gateway records, credits, and invoice adjustments. Keep the difference visible rather than silently forcing the numbers to match.\n\nTurn attribution into routing decisions. Once cost and quality are linked to each workload, teams can use smaller models for routine tasks, premium models for difficult cases, and fallbacks only where the expected value justifies them. This is more reliable than choosing one model for the entire product.\n\nThe practical lesson is simple. AI cost control begins with attribution, not with a cheaper price list. Connect every attempt to a user-visible outcome, preserve route and price history, expose retry waste, and optimize cost per successful result. Then engineering, product, and finance can make decisions from the same evidence.\n\nThat is it for today. Track and route multi-model workloads through one unified API with Crazyrouter at crazyrouter.com, and see you in the next episode."

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
