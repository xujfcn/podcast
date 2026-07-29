from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 110
title = 'EP110: AI API Key Security — Protect Multi-Tenant Gateways from Credential Leaks'
description = 'A practical security guide for AI gateways: scoped credentials, secret storage, log redaction, rotation, misuse detection, tenant isolation, and emergency revocation.'
pub_date = 'Wed, 29 Jul 2026 08:30:00 +0000'
script = """EP110: AI API Key Security — Protect Multi-Tenant Gateways from Credential Leaks

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about API key security for multi-model applications. A leaked AI credential can create unexpected charges, expose customer data, and give an attacker access to powerful tools. The safest design assumes that some credentials will eventually be copied, logged, or committed by mistake.

Start by separating credentials by environment and purpose. Production, staging, local development, background jobs, and customer-facing applications should not share one master key. A compromise should affect the smallest possible area, and every key should have a clear owner and workload.

Apply least privilege even when a provider offers broad credentials. At the gateway layer, restrict which models, endpoints, features, spending limits, and source applications each key can access. A key used for text classification should not automatically be able to generate video, call expensive reasoning models, or administer an account.

Never ship a reusable secret inside browser or mobile application code. Client applications should call a trusted backend or obtain a short-lived, narrowly scoped token. Anything delivered to an end-user device must be treated as recoverable by that user.

Store secrets in a dedicated secret manager or protected runtime environment. Do not place them in source files, container images, shell history, support tickets, or shared documents. Encrypt secrets at rest, restrict who can retrieve them, and record access to the secret store.

Design logs so credentials cannot appear in the first place. Redact authorization headers, signed URLs, cookies, query parameters, and provider responses that may echo sensitive values. Test the redaction rules with malformed headers and unusual casing. A dashboard is not a safe secret vault.

Use key fingerprints for operations. Store and display a short irreversible identifier so support teams can identify a key without seeing the credential itself. Audit records should include the fingerprint, tenant, action, source, and time, but never the full secret.

Make rotation routine rather than exceptional. Support two active credentials during a transition, allow applications to verify the replacement, and then revoke the old key. Rotation that requires downtime will be postponed until after a leak, which is the worst time to discover the process is fragile.

Detect misuse from behavior, not only from known leaked strings. Watch for sudden spend, new regions, unusual models, abnormal request volume, repeated authorization failures, and access outside expected hours. Combine these signals carefully because legitimate deployments can also change traffic patterns.

Enforce strong tenant isolation throughout the gateway. Authentication should establish a tenant once, and every database query, cache key, usage record, trace, file, and billing event must preserve that boundary. Never trust a tenant identifier supplied in the request body when it can be derived from the authenticated credential.

Prepare emergency revocation. Operators need a fast way to disable one key, one tenant, one upstream provider credential, or an entire compromised route. Revocation should propagate quickly across caches and workers. Document who can trigger it and how affected customers will be notified.

Protect provider master credentials behind the gateway. Customers should never receive the upstream key, and internal services should access only the provider credentials they need. If one routing worker is compromised, it should not reveal every credential in the platform.

Test the controls. Commit a fake secret to a test repository, send a credential through logging paths, rotate a production-like key, and simulate a compromised tenant. Confirm that detection, revocation, audit records, and customer impact all behave as designed.

Finally, make secure behavior easy for developers. Provide clear environment variable examples, secret scanning guidance, scoped keys, usage alerts, and one-click revocation. Security improves when the safe path is also the fastest path.

That is it for today. Scope every key, keep secrets out of clients and logs, isolate every tenant, and practice rotation before an incident. Build secure multi-model applications with the unified API at crazyrouter.com, and see you in the next episode."""

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
