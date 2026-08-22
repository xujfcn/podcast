from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 196
title = 'EP196: AI API Security Posture — Turn Controls Into Continuous Evidence'
description = 'A practical guide to AI API security posture: inventory exposure, verify controls continuously, protect keys and data, constrain tools, and turn security assumptions into evidence that operators can act on.'
pub_date = 'Thu, 29 Oct 2026 08:30:00 +0000'
script = '''EP196: AI API Security Posture — Turn Controls Into Continuous Evidence

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Security posture is not a document that stays true because it was approved once. AI gateways change models, providers, prompts, tools, tenants, regions, and logging paths every week. A control can exist in configuration and still be absent from the request path. Today we are talking about AI API security posture: turning security assumptions into continuously checked evidence that engineers and operators can use.

Start with an inventory of exposure. List public endpoints, internal routes, API keys, service accounts, model providers, prompt stores, file storage, traces, queues, tools, webhooks, and administrative controls. Connect each asset to its owner, environment, data class, region, and business criticality. An inventory is useful when it reveals what can receive sensitive prompts, spend money, execute side effects, or change routing policy.

Define the controls that matter. Key scope and rotation, tenant isolation, authentication, authorization, data retention, residency, log redaction, tool approval, output validation, rate limits, quotas, admission control, dependency scanning, and incident response are different controls. Write what each control prevents, where it is enforced, and what evidence proves it is active. “We have security middleware” is not evidence that every fallback and streaming path passes through it.

Verify enforcement on real routes. Use safe synthetic requests to test authentication, tenant boundaries, restricted models, tool permissions, data-region rules, and logging redaction. Probe primary and fallback providers, streaming and non-streaming paths, retries, queued jobs, and asynchronous callbacks. A control that protects the common path but not the recovery path is a partial control, and incidents tend to find partial controls quickly.

Treat credentials as lifecycle objects. Record owner, scope, creation time, last use, expiry, rotation target, and emergency revocation path. Prefer short-lived or narrowly scoped credentials where practical. Detect unused, overprivileged, duplicated, and unexpectedly used keys. Rotation must preserve service continuity, but continuity should not become an excuse for credentials with no expiry or ownership.

Protect tenant and prompt data deliberately. Minimize what enters logs and traces, separate customer content from operational metadata, apply retention by data class, and enforce access to debugging tools. Check that caches, replay fixtures, evaluation datasets, provider telemetry, and support exports preserve tenant boundaries. A security posture review should include data that leaves the main API process, not only the request body at ingress.

Constrain tools as high-risk capabilities. Give each tool a precise schema, tenant scope, authorization rule, idempotency behavior, timeout, and audit event. Separate planning from committing side effects. Require human approval or an explicit policy for money movement, messages, account changes, and destructive actions. Test duplicate attempts, retries, model-generated arguments, and gateway restarts so a valid-looking tool call cannot bypass the commit boundary.

Make provider and model changes security-relevant. A new route can change retention, training use, region, moderation, tool support, or context handling. Capability and policy metadata must be versioned and checked before traffic moves. Do not treat a provider catalog update as harmless configuration. The approved route should include data policy, model capability, price, quota, and fallback constraints together.

Monitor posture drift continuously. Alert on policy versions that expire, workers with stale configuration, routes missing owners, keys past rotation windows, disabled filters, unexpected regions, unknown tools, and fallbacks outside the approved set. Compare intended, configured, and observed behavior. Sample traces and billing data to discover routes that documentation missed, while keeping the sample privacy-safe and access-controlled.

Prioritize findings by blast radius. A missing redaction rule on a low-risk internal test route is different from a tool authorization gap on a multi-tenant production route. Consider data sensitivity, side-effect capability, tenant count, spend exposure, exploitability, and time to detect. Fix controls that prevent irreversible harm first, then improve detection and recovery. Track accepted risk with an owner and expiry instead of allowing exceptions to become permanent.

Use evidence in release gates. A model or prompt change should show capability checks, route policy, data handling, tool behavior, logging, billing, and rollback evidence before exposure increases. A security control should be tested in the same gateway configuration that will serve production. Keep a stable control cohort and stop on cross-tenant leakage, unauthorized tools, unapproved data movement, missing audit records, or unexplained credential use.

Prepare incident actions. Operators need safe controls to revoke a key, pause a tool, block a provider, restrict a tenant, disable a route, increase review, and preserve evidence. Each action should have a narrow scope, owner, reason, expiry, and rollback path. Practice the sequence without exposing real customer data. The fastest incident response is the one that was designed before the alert arrived.

Measure security outcomes, not checkbox counts. Track time to revoke, stale credential count, policy coverage, invariant violations, unauthorized attempts, tool approval failures, cross-tenant test results, redaction coverage, and time to close high-risk findings. Also track false positives and operator burden. A control that creates so much noise that teams ignore it is not healthy posture, even if the dashboard is full of green checks.

The practical lesson is simple: security posture is continuous evidence about whether controls match exposure. Inventory the routes and data, define enforcement points, verify primary and fallback behavior, rotate credentials, constrain tools, monitor drift, gate releases, and rehearse emergency actions. AI gateways move quickly; the goal is to make safe operation visible at the same speed.

That is it for today. Verify the controls, reduce the blast radius, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep}'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration} {len(parts)} chunks')
