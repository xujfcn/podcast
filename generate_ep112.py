from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 112
title = 'EP112: AI API Data Residency — Control Where Prompts and Outputs Are Processed'
description = 'A practical guide to AI data residency: map every processing region, classify workloads, enforce compliant routing, control telemetry and tool calls, and test regional failover.'
pub_date = 'Fri, 31 Jul 2026 08:30:00 +0000'
script = 'EP112: AI API Data Residency — Control Where Prompts and Outputs Are Processed\n\nWelcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about data residency in multi-model AI systems. Teams often ask where prompts, outputs, uploaded files, and traces are stored. The harder question is where that data is processed at every step of the request path.\n\nStart by separating data residency from data sovereignty and data localization. Residency describes where data is stored or processed. Sovereignty describes which laws and authorities apply. Localization is a legal or contractual requirement to keep certain data inside a defined region. These terms overlap, but they are not interchangeable.\n\nMap the complete route. A request may begin in a browser, pass through an edge network, enter your application region, cross an AI gateway, reach a provider endpoint, call tools, write traces, and return through a cache. Choosing a regional database does not create regional AI processing if the model call leaves that geography.\n\nClassify workloads before building regional policy. Public marketing copy, internal source code, customer support records, healthcare documents, and identity data do not carry the same risk. Attach a data class to each workload so routing decisions can be enforced automatically instead of relying on developers to remember a compliance checklist.\n\nBuild a provider and model capability registry. For each route, record supported regions, processing locations, storage behavior, retention terms, subprocessors, and zero-data-retention eligibility. Treat these facts as versioned operational metadata because providers can change infrastructure and policy over time.\n\nUse policy-based routing. A request marked European Union only should be eligible only for routes that satisfy the full policy. If the preferred model is unavailable, the gateway must choose another compliant route or fail clearly. A silent fallback to a non-compliant region is not graceful degradation. It is a policy violation.\n\nKeep control-plane data separate from content. Global dashboards may need model names, token counts, latency, status codes, and billing totals. They usually do not need raw prompts or outputs. Regional content processing can coexist with centralized aggregate operations when telemetry is minimized and identifiers are carefully designed.\n\nWatch the observability layer. Logs, traces, error trackers, session replay, and analytics frequently export data to a different region than the application. Redact content before export, use field allowlists, disable request-body capture by default, and verify where the observability vendor stores replicas and backups.\n\nTool calls extend the residency boundary. An agent may use a compliant model endpoint and then send extracted content to search, email, CRM, vector database, or document-processing tools in another jurisdiction. Evaluate the complete agent workflow, not just the language model provider.\n\nDesign regional caches and queues deliberately. Message queues, dead-letter topics, prompt caches, object stores, and temporary worker disks can preserve content outside the intended region. Use region-scoped resources, bounded retention, tenant-aware encryption, and explicit cleanup for failed jobs.\n\nEncryption is necessary, but it does not decide jurisdiction. Encrypt data in transit and at rest, isolate tenant keys, and rotate credentials. Still, do not claim that encryption alone satisfies a residency requirement. Processing location, operator access, backups, and legal control remain relevant.\n\nMake regional guarantees visible in product configuration. Customers should be able to select an allowed region or policy profile, understand which models are available under that profile, and see why a requested route was rejected. Compliance should be an enforceable setting with auditable evidence, not a sentence hidden in documentation.\n\nTest failover and disaster recovery. Regional incidents create pressure to bypass policy. Run exercises where the primary region or provider is unavailable and verify that the system selects only approved fallbacks. Restore backups into the correct geography and confirm that routing policy survives configuration recovery.\n\nAudit with synthetic markers. Send non-sensitive test prompts carrying unique identifiers through every regional route. Search logs, traces, caches, storage, and downstream tools for those markers. This gives concrete evidence of where data traveled and reveals hidden copies that architecture diagrams missed.\n\nMonitor policy drift. Alert when a route changes region metadata, a new provider becomes eligible, a fallback crosses a boundary, or telemetry begins exporting new fields. Revalidate vendor claims periodically and preserve the policy version attached to each request for later investigation.\n\nThe practical lesson is simple. Data residency is an end-to-end routing property, not a database setting. Map the path, classify workloads, maintain regional capabilities, enforce policy at the gateway, and test every fallback and tool call.\n\nThat is it for today. Build region-aware multi-model applications with clear routing controls through the unified API at crazyrouter.com, and see you in the next episode.'

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
