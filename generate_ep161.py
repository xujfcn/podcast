from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 161
title = 'EP161: AI API Key Management — Rotate Credentials Without Downtime'
description = 'A practical guide to AI API key management: scope credentials, rotate them safely, detect leaks, preserve service continuity, and make secret ownership auditable.'
pub_date = 'Fri, 18 Sep 2026 08:30:00 +0000'
script = '''EP161: AI API Key Management — Rotate Credentials Without Downtime

Welcome back to AI Dev Tools — The Crazyrouter Podcast. API keys are easy to create and surprisingly difficult to operate well. They end up in local environments, CI logs, dashboards, notebooks, and third-party integrations. When a key is exposed, teams often face a bad choice between leaving it active and breaking production by revoking it immediately. Today we will build a key-management practice that makes rotation routine and incidents recoverable.

Start with ownership and scope. Every credential should have an owner, purpose, environment, service, tenant, allowed route, creation date, and expiration or review date. Separate inference keys from administrative credentials, and limit each key to the smallest set of operations it needs. A gateway such as Crazyrouter can centralize provider access, while applications still need scoped credentials and clear ownership.

Keep secrets out of code and clients. Load keys through a secret manager or protected runtime configuration, never through source files, browser bundles, prompts, screenshots, or ordinary logs. Client-side applications should use a controlled backend or short-lived scoped token rather than exposing a powerful provider key to every user.

Design dual-key rotation. Create the replacement credential before disabling the old one. Deploy support for both active versions, switch traffic gradually, verify usage, and revoke the old key only after all expected callers have moved. Keep the overlap window bounded and record exactly which services have acknowledged the new credential.

Make rotation observable. Track key version or fingerprint, service, route, success and failure counts, last use time, and rotation state without storing the secret itself. Alert on continued use of a key scheduled for revocation, unexpected regions, new callers, or a sudden usage spike. Operators need to know whether a key is unused, forgotten, or still serving critical traffic.

Test failure before rotation day. Revoke a staging key, expire a credential, deny one route, and simulate a secret-manager outage. Verify that applications fail clearly, retry without storms, and recover when the replacement becomes available. A key rotation that works only when every deployment is perfectly synchronized is not a reliable rotation.

Respond quickly to exposure. Define who can revoke, rotate, investigate, and communicate. When a key appears in a public repository or log, preserve minimal evidence, disable or restrict it, issue a replacement, review access records, and search for copies. Do not wait for a complete forensic report before stopping active abuse. Keep the response procedure available even if the normal secret owner is unavailable.

Protect the replacement. A newly rotated key is not safer if it is distributed through the same insecure channel. Use encrypted secret delivery, short-lived access where possible, least-privilege runtime identities, and deployment checks that prevent plaintext secrets from entering artifacts. Verify that old values are removed from logs, caches, and build output according to retention policy.

Separate human and machine access. Developers may need a local credential with low limits, while production workloads need a service identity with narrowly defined permissions. Administrative actions should use separate audited credentials and stronger approval. Never make one universal key convenient for every environment and workflow.

Plan for provider and route changes. If an upstream provider key is rotated behind a stable gateway policy, applications may not need a simultaneous code deployment. Still record the effective route and credential owner, test the new path, and preserve a rollback option. Abstraction reduces coordination cost, but it does not eliminate operational verification.

Review the inventory regularly. Remove forgotten keys, confirm owners, check expiration, inspect unused credentials, and compare expected callers with observed use. Automate reminders and secret scanning, but keep a human review for high-impact credentials. The inventory is valuable only when it reflects actual deployed systems.

The practical lesson is simple: key security is an operational lifecycle. Scope credentials, keep them out of client code, rotate with overlap, monitor fingerprints, rehearse revocation, and respond quickly to exposure. When ownership and automation are clear, teams can replace secrets without turning routine maintenance into downtime.

That is it for today. Make credential replacement boring, observable, and reversible. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep161'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
