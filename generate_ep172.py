from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 172
title = 'EP172: AI API Runbooks — Turn Operational Knowledge Into Fast Recovery'
description = 'A practical guide to AI API runbooks: document symptoms, first actions, rollback paths, escalation rules, and verification steps so operators can recover systems consistently.'
pub_date = 'Tue, 29 Sep 2026 08:30:00 +0000'
script = '''EP172: AI API Runbooks — Turn Operational Knowledge Into Fast Recovery

Welcome back to AI Dev Tools — The Crazyrouter Podcast. During an AI API incident, the difference between a five-minute recovery and a one-hour outage is often not intelligence. It is whether the team can find the right action, understand its risk, and verify the result without guessing. Today we will build runbooks that turn operational knowledge into fast, repeatable recovery.

Start with symptoms, not implementation details. A useful runbook begins with what an operator can observe: elevated timeouts, malformed structured output, provider throttling, rising queue age, unusual spend, or a failed tool action. Link each symptom to the dashboards, logs, traces, and request identifiers that confirm the condition.

Define the first safe actions. Every runbook should say what to check, what to pause, and what not to do. Stop a risky rollout, cap retries, protect interactive traffic, or disable an optional tool before attempting a large configuration change. Early actions should reduce blast radius and preserve evidence.

Document decision points. If the primary provider is failing, determine whether the issue is regional, route-specific, quota-related, or application-side. If a fallback is available, verify its capability contract before switching traffic. A gateway such as Crazyrouter can centralize route changes, but the runbook must state which workloads are compatible with each fallback and what tradeoffs apply.

Include exact rollback paths. Name the configuration, version, command or control, owner, and expected propagation time. Explain how to undo the change if metrics worsen. Avoid instructions that depend on an individual remembering an undocumented dashboard click. Reversible actions should be easy to identify; risky actions should require explicit confirmation.

Make verification concrete. “Check that it works” is not a verification step. Specify the metrics and sample requests that should recover: accepted-result rate, time to first token, validation failures, queue age, fallback share, cost per task, or tool-call success. Include both a positive test and a check that the original failure is no longer spreading.

Separate emergency and follow-up work. The incident runbook should restore service and protect users. The post-incident checklist should collect evidence, reconcile usage, notify stakeholders, and create durable fixes. Mixing long-term cleanup into the first response makes urgent recovery slower and increases operator load.

Design for handoffs. Record current impact, actions already taken, open hypotheses, next update time, and the person responsible. Use a shared timeline so a new responder can contribute without repeating experiments. Clear handoffs are especially important when incidents cross provider, application, support, and finance teams.

Test runbooks regularly. Run a short tabletop exercise, inject a controlled failure, or ask someone unfamiliar with the system to follow the document. Time how long it takes to find the right page and complete verification. Broken links, stale screenshots, missing permissions, and ambiguous ownership are operational defects, not editorial imperfections.

Version and review the documents. Link a runbook to the services, routes, and policies it covers. Review it after incidents, architecture changes, provider migrations, and ownership changes. Track last verified date and reviewer. A short accurate runbook is more valuable than a comprehensive document that nobody trusts.

The practical lesson is simple: a runbook is executable knowledge. Start from symptoms, reduce blast radius, make decisions explicit, document rollback, verify with measurable signals, and practice the handoff. When recovery steps are clear and current, teams can move quickly without turning every incident into improvisation.

That is it for today. Make recovery repeatable, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script)
parts = script.split('\n\n')
for i, part in enumerate(parts, 1):
    subprocess.run(['edge-tts', '--voice', 'en-US-GuyNeural', '--text', part, '--write-media', str(root / f'episodes/ep{ep:03d}_chunk{i}.mp3')], check=True)
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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep172'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
