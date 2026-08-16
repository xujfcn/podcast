from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 138
title = 'EP138: AI API Security — Protect Keys, Prompts, and Tool Access'
description = 'A practical guide to securing AI API applications: protect credentials, isolate tenants, redact telemetry, constrain tools, validate outputs, and respond to incidents.'
pub_date = 'Wed, 26 Aug 2026 08:30:00 +0000'
script = '''EP138: AI API Security — Protect Keys, Prompts, and Tool Access

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI applications combine API credentials, private context, model outputs, and sometimes powerful tools. That combination creates a security surface wider than a traditional request-response service. Today we will build a practical security baseline for AI API workloads.

Start with credential isolation. Keep provider and gateway keys out of source code, prompts, client-side bundles, screenshots, and ordinary logs. Use a secret manager or protected environment configuration, assign separate keys by service or environment, and rotate them when a developer, deployment, or integration changes. A gateway such as Crazyrouter can centralize upstream access, but the application still needs careful key handling.

Use least privilege. A key used for inference should not automatically be able to manage billing, users, or routing policies. Separate administrative operations from runtime traffic. Limit who can create keys, who can view usage, and which services can access each secret. Review permissions periodically instead of treating the initial setup as permanent.

Protect tenant boundaries. Include tenant identity in authorization decisions, usage accounting, cache keys, traces, and tool permissions. Never assume that a model prompt or a user-provided identifier is a trustworthy access-control signal. Check permissions in application code before retrieving private context or executing an action.

Treat prompts as untrusted input. User content, retrieved documents, web pages, and tool results may contain instructions designed to redirect the model. Separate data from control instructions, constrain what the model is allowed to do, and avoid giving the model direct authority to redefine its own policies. Prompt-injection defenses are not a single filter; they are layered boundaries around data, tools, and approvals.

Constrain tools aggressively. Give each tool a narrow schema and the minimum permissions required. Prefer read-only operations by default. For writes, require deterministic validation, idempotency, and approval for high-impact actions. The model can suggest a command, but a policy layer should decide whether the command is allowed.

Validate outputs before using them. Treat generated URLs, SQL, code, JSON, and file paths as untrusted until checked. Use schemas, allowlists, sandboxed execution, parameterized queries, and output-size limits. A valid-looking response can still contain an unsafe destination or an operation outside the intended business rule.

Redact telemetry. Traces and error reports should help diagnose failures without becoming a copy of every private conversation. Remove API keys, authorization headers, personal identifiers, and sensitive retrieved content. Use sampling, short retention, access controls, and separate secure storage for the small amount of data needed for investigations.

Plan for abuse and budget attacks. Set per-user and per-tenant quotas, maximum prompt and output sizes, tool-call limits, and spend alerts. Watch for repeated long prompts, automated key sharing, unexpected geographies, and sudden changes in model mix. Security and cost controls reinforce each other when they are based on the same request identity.

Prepare incident response. Know how to revoke a key, disable a route, block a tenant, preserve relevant traces, notify owners, and restore service with a clean credential. Test the procedure. During an incident, speed matters, but so does evidence: record what changed, which requests were affected, and which secrets must be rotated.

The practical lesson is simple: secure the whole AI path, not just the endpoint. Protect credentials, isolate data, constrain tools, validate outputs, redact logs, and rehearse response. AI features become much easier to trust when every powerful boundary has an explicit control.

That is it for today. Give every model call the minimum access it needs. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep138'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
