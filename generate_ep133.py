from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 133
title = 'EP133: AI API Deprecation Plans — Retire Models Without Surprising Users'
description = 'A practical guide to retiring AI models safely: identify dependencies, publish timelines, provide replacement routes, test compatibility, monitor migrations, and preserve rollback options.'
pub_date = 'Fri, 21 Aug 2026 08:30:00 +0000'
script = '''EP133: AI API Deprecation Plans — Retire Models Without Surprising Users

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI models do not stay available forever. Providers release replacements, change capacity, revise pricing, and eventually retire older endpoints. For developers, the dangerous part is rarely the announcement itself. The danger is discovering a hidden dependency after production traffic starts failing. Today we will build a practical model deprecation plan.

Begin with dependency discovery. Search application code, environment files, routing policies, scheduled jobs, evaluation scripts, dashboards, support tools, and customer documentation for the model name and aliases. Query gateway logs to find real traffic, including low-volume workloads that static code searches may miss. Assign an owner to every active dependency.

Publish a clear timeline. A useful notice includes the affected model, the final availability date, the recommended replacement, expected behavior differences, and milestones for testing and migration. Use exact dates rather than phrases such as soon or next month. Send reminders as the deadline approaches, but avoid changing the date casually because teams build their own release plans around it.

Choose replacement routes by capability, not branding. Check context limits, structured output, tool calling, vision, streaming, latency, regional availability, and parameter support. If no single replacement matches every workload, provide different recommendations by task. A coding agent and a short classification pipeline may need different successors.

Make compatibility testing easy. Publish sample payloads, known parameter changes, and a concise migration checklist. Offer a temporary alias or gateway route when possible, but explain whether it preserves behavior or only preserves the model name. Developers need to know what remains compatible and what must be retested.

Create an evaluation window. Let application owners replay representative requests against the replacement while the old model is still available. Compare accepted-result rate, validation failures, latency, token usage, retries, and cost per successful task. Include edge cases and historical incidents, not just happy-path prompts.

Use staged migration. Shift internal workloads first, then canary a small percentage of eligible production traffic. Monitor errors, fallback share, user complaints, and spend. Increase traffic in controlled steps. A unified gateway such as Crazyrouter can centralize this routing change so teams do not have to edit every application at once.

Define what happens at the deadline. Decide whether requests receive a clear error, route to an approved replacement, or continue temporarily for explicitly exempted workloads. Silent fallback may keep traffic moving, but it can also change quality, cost, or data handling without the application owner knowing. If you use automatic fallback, make it visible in logs and notifications.

Preserve rollback during the transition. Keep the previous route, credentials, and capacity available until the replacement has passed its observation period, unless the upstream provider removes it first. Document emergency contacts and the exact rollback procedure. If rollback is impossible, prepare a safe failure mode rather than improvising under pressure.

After retirement, verify that traffic has actually stopped. Watch for stale clients, delayed jobs, and old deployment environments. Remove obsolete secrets, aliases, dashboards, and documentation only after confirming there are no legitimate callers. Record the final migration outcome and the problems discovered so the next deprecation becomes easier.

The practical lesson is simple: model retirement is a product and operations event, not just a catalog edit. Find dependencies, communicate exact dates, provide tested replacements, migrate gradually, and make deadline behavior explicit. Done well, deprecation becomes routine maintenance instead of a production incident.

That is it for today. Retire routes carefully, and keep users informed. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep133'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
