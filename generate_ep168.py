from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 168
title = 'EP168: AI API Budget Alerts — Turn Spend Surprises Into Early Signals'
description = 'A practical guide to AI API budget alerts: set useful thresholds, detect anomalies, separate expected growth from waste, and connect alerts to safe actions.'
pub_date = 'Fri, 25 Sep 2026 08:30:00 +0000'
script = '''EP168: AI API Budget Alerts — Turn Spend Surprises Into Early Signals

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Most teams discover AI API cost problems after the invoice arrives. By then, the expensive traffic has already happened and the people responsible are trying to reconstruct what changed. Today we will design budget alerts that turn spend surprises into early, actionable signals.

Start with ownership. Every alert should identify the tenant, product, feature, workflow, environment, and route responsible for the spend. A single company-wide threshold is useful for finance, but it is not enough for engineering. Ownership turns an alert from a number to a decision: investigate, adjust routing, pause a job, or approve more budget.

Use several kinds of thresholds. A daily or monthly budget protects the total. A rate threshold catches sudden spend per hour. A unit-cost threshold catches a workflow that became more expensive per accepted result. A forecast threshold warns when current usage is likely to exceed the period budget. Combining these views catches both sudden incidents and slow, compounding waste.

Alert on drivers, not only dollars. Track requests, input tokens, output tokens, cached tokens, retries, fallback share, image or video units, and cost per successful task. A bill can rise because demand grew as planned, because a prompt doubled in size, because retries multiplied, or because traffic moved to a premium model. The response depends on the driver.

Make baselines workload-aware. Compare a feature with its own recent behavior, its normal hourly pattern, and its expected release plan. Global averages can hide a small but expensive tenant or mistake a predictable Monday spike for an incident. A gateway such as Crazyrouter can help centralize route and usage data, while application metadata supplies the context needed for useful baselines.

Reduce alert fatigue. Set warning, action, and emergency levels with clear owners and response times. Group related alerts into one incident when they share a cause. Suppress duplicates during a known outage, but keep the underlying usage visible. If every alert requires a meeting, teams will eventually ignore all of them.

Connect alerts to safe actions. A warning may open an investigation. A high threshold may reduce optional context, switch routine traffic to a compatible cheaper route, slow batch work, or require approval for a new job. A hard circuit breaker should be reserved for workloads that can safely stop. Never let an automated budget action silently damage critical user workflows.

Account for delayed costs. Some providers report usage after the request completes, and asynchronous jobs may run for hours. Record estimated cost, final cost, and reconciliation status. Make sure alerts do not fire repeatedly as late usage arrives. Stable operation requires both real-time estimates and an authoritative accounting pass.

Protect sensitive information. Cost labels can reveal customer names, projects, or business priorities. Restrict dashboards by tenant and role, minimize prompt content in telemetry, and use safe identifiers. Budget visibility should not become a shortcut for exposing private request data.

Review alerts after every incident. Did the alert fire early enough? Did it identify the right owner? Was the threshold too noisy or too slow? Did the suggested action actually reduce waste without hurting quality? Tune the rule, the metadata, and the runbook together. A budget alert is part of an operating control, not merely a line on a dashboard.

The practical lesson is simple: good cost alerts explain what changed, who owns it, how urgent it is, and what safe action is available. Combine budgets, rates, forecasts, drivers, and accepted-result cost. When alerts are connected to decisions, teams can control spend before a surprise becomes an invoice.

That is it for today. Catch the signal before the bill, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep168'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
