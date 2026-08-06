from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 119
title = 'EP119: AI API Data Privacy by Design — Build Useful Systems Without Oversharing'
description = 'A practical guide to privacy by design for AI API applications: minimize data, classify routes, isolate tenants, limit retention, protect telemetry, validate tools, and test fallbacks safely.'
pub_date = 'Fri, 07 Aug 2026 08:30:00 +0000'
script = "EP119: AI API Data Privacy by Design — Build Useful Systems Without Oversharing\n\nWelcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about privacy by design for AI API applications. Sending a prompt to a model is not only a product decision. It is also a decision about data classification, retention, access, location, logging, and what happens when a request is retried or routed to a fallback.\n\nStart with data inventory. Identify what enters the system: user messages, uploaded files, retrieved documents, tool arguments, account identifiers, and generated outputs. Classify each category by sensitivity and purpose. If the team does not know what data is present, it cannot choose an appropriate route or retention policy.\n\nMinimize before sending. Remove fields the model does not need, replace direct identifiers with short-lived references, and redact secrets from logs and prompts. A support assistant may need an order status but not a full payment card number. A document workflow may need selected clauses rather than an entire customer archive.\n\nSeparate tenant data by policy. Retrieval indexes, caches, prompt templates, traces, and evaluation datasets should carry tenant identity and access controls. Never assume that a shared cache is safe simply because the model provider is trusted. A cached answer containing one customer's context can become another customer's data leak.\n\nMake routing privacy-aware. Model selection should consider region, provider terms, data residency, retention behavior, and whether a workload is allowed to use a particular route. A cheaper or faster model is not an acceptable fallback if it violates the tenant's policy.\n\nControl retention in every layer. Review application logs, gateway traces, provider records, object storage, queues, backups, and analytics exports. Set different retention periods for operational metadata and prompt content. Deleting the primary record is not deletion if a copy remains in an evaluation bucket or debug archive.\n\nTreat observability as sensitive. Store request IDs, route decisions, status codes, latency, token counts, and normalized errors by default. Keep full prompts and completions out of ordinary logs. When content is necessary for debugging, use sampling, redaction, approval, encryption, and a short expiration time.\n\nProtect tools and connectors. An agent can expose more data through a tool call than through its original prompt. Validate arguments, enforce tenant-scoped permissions, limit returned fields, and record the authorization decision. Tool access should be independent of what the model asks for.\n\nHandle retries and fallbacks carefully. A timeout may cause the same sensitive payload to be sent twice, possibly to different providers. Use idempotency keys where possible, record the route for every attempt, and make fallback eligibility explicit. Privacy policy must survive an outage, not disappear when the primary route is unavailable.\n\nGive users meaningful controls. Explain what data is processed, why it is needed, how long it is retained, and whether it is used for improvement where relevant. Provide deletion and export paths that cover stored prompts, generated files, embeddings, and derived evaluation records.\n\nTest privacy like functionality. Create cases for cross-tenant retrieval, secret leakage, region-ineligible routing, unauthorized tools, cache collisions, verbose error messages, and deletion gaps. Confirm that the system fails closed and that the resulting evidence is visible to operators without exposing the protected content.\n\nKeep a data-flow diagram current. Show the application, gateway, providers, queues, storage, observability, and support systems. Mark trust boundaries and data transformations. A diagram that reflects the production route is more useful than a policy document that describes an older architecture.\n\nThe practical lesson is simple. Privacy is not a final filter around an AI API. Minimize data, classify routes, isolate tenants, limit retention, protect telemetry, validate tools, and test fallbacks under the same policy. The safest useful system is one that sends less data and can prove where the rest went.\n\nThat is it for today. Build privacy-aware multi-model applications through the unified API at crazyrouter.com, and see you in the next episode."

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
