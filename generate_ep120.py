from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 120
title = 'EP120: AI API Governance — Turn Model Access Into an Operable System'
description = 'A practical guide to AI API governance: inventory routes, define workload access, version model policy, separate secrets, audit changes, govern data movement, and automate compliance checks.'
pub_date = 'Sat, 08 Aug 2026 08:30:00 +0000'
script = 'EP120: AI API Governance — Turn Model Access Into an Operable System\n\nWelcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about governance for AI API applications. Governance is not a committee document that sits beside the product. It is the set of rules, approvals, identities, logs, and automated checks that determine which workloads can use which models and what happens when something changes.\n\nStart with an inventory. Record every application, model route, provider, owner, environment, data class, region, and business purpose. Unknown routes are difficult to secure and even harder to retire. Give each route a clear owner and an expiration or review date.\n\nDefine access by workload. A development experiment should not automatically receive production credentials or access to sensitive customer data. Use separate projects, keys, scopes, quotas, and environments. Give agents only the tools and models required for their task, and make high-impact actions require explicit authorization.\n\nPut model selection under policy. Rules can cover approved providers, regions, data residency, maximum spend, context limits, safety requirements, and fallback eligibility. Keep these rules versioned so an operator can explain why a request took a particular route at a particular time.\n\nUse approvals for meaningful changes. Adding a provider, enabling a premium model, changing retention, increasing a tenant quota, or modifying a fallback can affect security, cost, and user experience. Automate low-risk changes, but require review for changes that cross a trust or spending boundary.\n\nSeparate policy from secrets. Configuration should identify the route and required credential scope without embedding raw keys in repositories, prompts, logs, or tickets. Rotate secrets, audit access, and make emergency revocation fast. A governance system that cannot revoke a compromised key is mostly paperwork.\n\nMake audit records useful. Capture who changed the policy, what changed, when it became active, which version handled a request, and whether an approval was required. Store request IDs and route decisions, but avoid putting full customer prompts into general audit logs.\n\nGovern data movement. Track where prompts, files, embeddings, traces, backups, and generated outputs are processed and retained. A fallback provider, evaluation dataset, or debugging export can cross a data boundary even when the primary application does not.\n\nControl third-party tools. Model output should not be enough to authorize a payment, delete a record, publish content, or access another tenant. Use server-side authorization, allowlists, input validation, confirmation steps, and idempotency keys around consequential actions.\n\nSet spending guardrails. Budgets, rate limits, model allowlists, and anomaly alerts should exist at organization, team, application, and tenant levels where needed. Pair a hard limit with a graceful degraded path so an exhausted budget does not create an uncontrolled retry storm.\n\nTest policy continuously. Use automated checks for unapproved models, missing owners, expired credentials, wrong-region routes, excessive permissions, logging of secrets, and fallback paths that violate policy. Run these checks in CI and periodically against live configuration.\n\nPlan for incidents and exceptions. Operators may need an emergency route during an outage, but emergency access should be time-limited, scoped, logged, and reviewed afterward. An exception that never expires becomes the new undocumented architecture.\n\nGive developers a paved road. Provide approved SDK configuration, standard headers, trace propagation, safe defaults, usage reporting, and examples for common workloads. Governance works better when the compliant path is also the easiest path.\n\nThe practical lesson is simple. AI governance becomes real when it is encoded in identity, routing policy, approvals, quotas, audit trails, and automated tests. Inventory what exists, constrain what can happen, record why it happened, and make exceptions expire.\n\nThat is it for today. Build governed multi-model applications through the unified API at crazyrouter.com, and see you in the next episode.'

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
