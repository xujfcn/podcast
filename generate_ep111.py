from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 111
title = 'EP111: AI API Data Retention — Keep Prompts, Outputs, and Traces Under Control'
description = 'A practical data-retention guide for AI systems: classify prompts and outputs, minimize storage, set deletion windows, protect traces, isolate tenants, and verify that deletion really works.'
pub_date = 'Thu, 30 Jul 2026 08:30:00 +0000'
script = """EP111: AI API Data Retention — Keep Prompts, Outputs, and Traces Under Control

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about data retention in AI applications. Prompts and model outputs can contain customer records, source code, contracts, support conversations, and personal information. Keeping everything forever may feel useful for debugging, but it creates security, privacy, and operational risk.

Start by mapping the full data path. A request may pass through an application server, an AI gateway, an upstream provider, a tracing platform, a cache, an evaluation pipeline, and a support dashboard. A retention policy is incomplete if it covers only the primary database.

Classify data before choosing how long to keep it. Separate authentication metadata, request metadata, prompt content, model output, tool arguments, uploaded files, and billing records. These categories have different operational value and different exposure if compromised.

Default to collecting less. Most reliability questions can be answered with model name, latency, token usage, status, route, retry count, and an anonymous request identifier. Full prompt and response bodies should be an explicit feature with a defined purpose, not an accidental side effect of verbose logging.

Use short retention windows for sensitive content. Raw prompts and outputs may need only hours or days for debugging, while aggregated usage metrics can remain useful for months. Make the window configurable by environment, tenant, and data category instead of applying one global number.

Keep billing evidence separate from conversational content. You usually need durable records of time, model, token counts, price, and transaction identifiers. You usually do not need the customer's entire prompt to prove how much a request cost.

Treat traces as sensitive production data. Distributed traces often capture request bodies, authorization headers, tool calls, database queries, and provider responses. Configure field allowlists, redact secrets before export, and review sampling rules so a debugging tool does not become a shadow archive.

Design caches with deletion in mind. Prompt caches, semantic caches, CDN objects, local worker disks, and temporary files can outlive the database record that created them. Use bounded time-to-live values, tenant-aware cache keys, and a way to invalidate related objects when a deletion request arrives.

Preserve tenant isolation in every storage layer. A tenant identifier should be attached to logs, traces, objects, evaluations, and backups. Access controls must use the authenticated tenant context, not a user-supplied filter that could expose another customer's retained data.

Make deletion a workflow, not a single database statement. A reliable deletion job finds primary records, replicas, search indexes, caches, object storage, derived datasets, and queued exports. It records what was removed without copying the sensitive content into the deletion audit itself.

Backups need an explicit policy too. Immediate removal from immutable backups may be impractical, but deleted data should not silently return during a restore. Maintain tombstones or replay deletion events after recovery, limit backup lifetime, and document the maximum time until expired backups disappear.

Give customers clear controls. Explain what content is stored, why it is stored, how long it remains, and whether logging can be disabled. Enterprise teams may need zero-retention routes, regional storage, or tenant-specific windows. These should be enforceable product settings rather than support promises.

Verify provider behavior. Upstream AI providers differ in abuse monitoring, training policies, enterprise retention, and zero-data-retention eligibility. Record the policy attached to each route and do not claim end-to-end zero retention unless every component in that route supports it.

Test the policy continuously. Send a marked synthetic prompt through the production-like pipeline, wait for its retention window, and search every storage and observability system. Also test deletion during retries, failed exports, provider outages, and backup restoration.

Finally, monitor retention itself. Alert when deletion jobs fail, storage grows unexpectedly, logging settings change, or a new integration starts receiving content. Data minimization is not a document written once. It is a production control that can drift.

That is it for today. Map every copy, collect only what you need, separate billing metadata from content, and prove that expiration and deletion work. Build privacy-aware multi-model applications with the unified API at crazyrouter.com, and see you in the next episode."""

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
