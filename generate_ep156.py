from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 156
title = 'EP156: AI API Drift — Detect Quality Changes Before Users Do'
description = 'A practical guide to detecting AI API drift: monitor quality, latency, routing, prompts, and provider behavior over time, then investigate and respond before users notice.'
pub_date = 'Sun, 13 Sep 2026 08:30:00 +0000'
script = '''EP156: AI API Drift — Detect Quality Changes Before Users Do

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI systems can change even when your application code does not. A provider may update a model, a prompt template may evolve, retrieval data may shift, traffic may move to a fallback route, or user behavior may change. These changes can slowly alter quality, latency, and cost without producing an obvious outage. Today we will build a practical approach to detecting AI API drift.

Start by defining what should remain stable. Identify the accepted-result rate, structured-output validity, task-specific quality, latency percentiles, fallback share, token usage, and cost ranges that matter for each workflow. Stability does not mean every answer must be identical. It means important outcomes and constraints remain within an understood range.

Keep a reference dataset. Use a versioned set of representative requests with expected properties, not just exact text answers. Include common cases, difficult edge cases, long inputs, multilingual examples, and historical failures. Run it on a schedule and after changes to models, prompts, routing, retrieval, or provider configuration.

Monitor production slices. Break signals down by model, route, tenant, feature, language, input size, and time window. An overall average can hide a serious regression in one customer segment or one fallback route. Compare recent behavior with a baseline using enough volume to avoid reacting to normal randomness.

Track the full configuration. Record model identifiers, prompt versions, schema versions, tool definitions, retrieval snapshots, routing policies, provider regions, and effective prices. When a metric moves, operators need to know which inputs changed. A gateway such as Crazyrouter can centralize routes, but the application must preserve the metadata that explains the final request.

Use layered drift signals. Deterministic checks catch schema failures, missing citations, invalid tool arguments, and unexpected error classes. Statistical checks catch shifts in token counts, latency, output length, or route share. Sampled human review and calibrated evaluators help detect quality changes that simple syntax checks cannot see.

Distinguish drift from incidents. A sudden jump in timeout rate may indicate provider trouble, while a gradual decline in accepted answers may indicate prompt or retrieval changes. Compare control routes, deployment annotations, provider status, and traffic mix. Do not automatically roll back every signal before confirming that the signal represents real user impact.

Set useful thresholds. Alert on sustained changes in accepted-result quality, p95 latency, validation failure, fallback share, or cost per successful task. Use different thresholds for different workflows. A support summarizer and a financial extraction pipeline should not have identical tolerance for uncertainty or malformed output.

Investigate with preserved evidence. Keep sanitized request metadata, response validation results, route decisions, and relevant configuration versions long enough to compare periods. Protect private prompts and user data. A drift investigation should be reproducible without creating a second privacy problem in the monitoring system.

Respond with graduated actions. Start with increased sampling or review, then compare a candidate prompt or route, canary a change, and roll back when the evidence supports it. If the cause is a provider update, route to an approved alternative or communicate a limitation. Document the finding and add the failure case to the evaluation dataset.

Review baselines periodically. Products evolve, and a historical baseline can become less relevant as users, tasks, and models change. Version baselines rather than overwriting them. This preserves the ability to explain improvement or regression across major changes while keeping current alerts useful.

The practical lesson is simple: AI reliability includes stability over time. Define important outcomes, version the inputs, monitor slices, preserve evidence, distinguish drift from incidents, and respond gradually. With continuous drift detection, teams can catch silent changes before they become customer reports.

That is it for today. Watch the trend, not just the outage. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep156'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
