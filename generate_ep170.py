from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 170
title = 'EP170: AI API Usage Statements — Make Every Charge Explainable'
description = 'A practical guide to AI API usage statements: reconcile requests, tokens, routes, retries, and invoices so customers and teams can understand every charge.'
pub_date = 'Sun, 27 Sep 2026 08:30:00 +0000'
script = '''EP170: AI API Usage Statements — Make Every Charge Explainable

Welcome back to AI Dev Tools — The Crazyrouter Podcast. A customer may accept a bill they do not like, but they rarely accept a bill they cannot understand. AI usage combines tokens, model routes, retries, caching, asynchronous jobs, and provider timing. Today we will design usage statements that make every charge explainable.

Start with an immutable usage event. Record the operation ID, tenant, project, timestamp, model route, provider, input and output units, cache status, retry attempt, final outcome, and price version. Do not calculate an invoice from mutable dashboards alone. A stable event record lets finance, support, and engineering reconcile the same underlying activity.

Separate operations from attempts. One user action may create several provider requests because of a timeout, validation failure, or fallback. Show the customer the billable operation and, where useful, summarize the attempts that contributed to it. Internally, keep every attempt so teams can identify retry waste without making the statement impossible to read.

Explain the pricing unit. State whether a line is priced by input tokens, output tokens, cached tokens, images, audio seconds, video units, or a fixed operation fee. Include the quantity, unit price, discount or markup policy, and line total. A gateway such as Crazyrouter can standardize access to many routes, but the statement should make the selected route and pricing basis visible.

Use a clear time boundary. Specify the billing period, timezone, cutoff behavior, and when late provider usage is reconciled. Asynchronous jobs and delayed usage reports can otherwise appear in a surprising month. If an amount is estimated, label it as estimated and provide the reconciliation rule for the final charge.

Connect charges to outcomes. Include feature, workflow, or project labels where customers have supplied them. A raw model name is less useful than “document extraction” or “support assistant.” Keep labels privacy-aware and restrict visibility by tenant. Helpful context should explain usage without exposing prompts, documents, or other customers.

Handle credits and adjustments transparently. Show opening balance, purchases, promotions, refunds, corrections, and closing balance separately from consumption. If a failed request was credited back, show the adjustment rather than silently changing the total. Reconciliation becomes much easier when the statement tells the story of the balance.

Build a reconciliation process. Compare usage events with provider reports, internal ledger entries, and payment records. Track unmatched, delayed, duplicated, and corrected events. Make reconciliation idempotent so a late provider report does not double-charge a customer. Disputes should lead to a traceable event, not a manual number typed into a spreadsheet.

Give support the evidence they need. A support agent should be able to find a statement line by date, operation ID, feature, or model route, then see the relevant usage and adjustment history without accessing sensitive prompt content. Clear evidence shortens disputes and gives engineering a precise reproduction target.

Protect the statement itself. Apply tenant isolation, role-based access, export controls, retention limits, and safe filenames. PDFs and CSVs can be forwarded easily, so avoid including secrets or unnecessary personal data. Sign or version exported statements when they are used for accounting or compliance.

The practical lesson is simple: an explainable AI bill is built from durable events, explicit units, visible adjustments, and reliable reconciliation. Show what was used, how it was priced, what was credited, and which outcome it supported. When every charge has a traceable explanation, billing becomes part of product trust rather than a source of friction.

That is it for today. Make every charge explainable, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep170'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
