from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 163
title = 'EP163: AI API Cost Attribution — Know What Each Workflow Really Costs'
description = 'A practical guide to attributing AI API spend across teams, tenants, models, and workflows without losing the operational context behind each request.'
pub_date = 'Sun, 20 Sep 2026 08:30:00 +0000'
script = '''EP163: AI API Cost Attribution — Know What Each Workflow Really Costs

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI API bills are easy to total and surprisingly difficult to explain. A monthly number tells you what you spent, but not which customer, feature, model, or workflow created that spend. Today we will design practical cost attribution for AI applications.

Start with a stable identity for every request. Capture the tenant, workspace, project, environment, feature, workflow, and user or service account. Keep these fields separate from the prompt itself. Metadata should be queryable, privacy-aware, and consistent across providers. A gateway such as Crazyrouter can give applications one routing layer, but attribution still depends on the application sending useful ownership metadata.

Record the economics at the same time as the request. Store the model route, provider, input tokens, output tokens, cached tokens, image or video units, latency, retry count, and the price version used for the calculation. Do not reconstruct cost weeks later from a changing public price page. Pricing snapshots and immutable usage events make invoices explainable.

Separate direct cost from shared cost. A request can have a clear model charge, while storage, moderation, embeddings, retrieval, observability, and failed retries are shared overhead. Choose a policy: allocate shared costs by usage, by reserved capacity, or as a platform charge. The exact policy matters less than documenting it and applying it consistently.

Make retries visible. A timeout followed by a successful retry may look like one user action but create two billable requests. Keep the parent operation ID, attempt number, idempotency key, and final outcome. This lets engineers distinguish provider failures from expensive application behavior and prevents a “successful request” dashboard from hiding waste.

Use a small taxonomy that people can actually maintain. Feature names, cost centers, and workflow stages should come from controlled values rather than free-form labels. Version the taxonomy when a product changes. If a label is missing, route the event to an unattributed bucket and alert on it; silently dropping the cost is worse than showing a temporary unknown.

Give each audience the view it needs. Finance needs reconciled totals. Product teams need cost per feature and cost per active customer. Engineers need cost by route, retry, and latency tier. Customers may need a usage statement without seeing internal provider details. One event stream can support all four views when access controls and aggregation rules are designed early.

Add budgets and forecasts, not just reports. Set soft alerts for unusual growth and hard limits for workloads that can safely stop. Forecast from requests, tokens, and unit prices rather than from last month’s total alone. For long-running agents, track estimated remaining budget and make the agent degrade gracefully by shortening context, switching models, or asking for approval.

Protect the data. Cost metadata can reveal customer names, internal projects, and business priorities. Minimize sensitive labels, hash identifiers where appropriate, isolate tenants, and retain raw events only as long as operations and compliance require. Never put API keys, full prompts, or private documents into a cost dashboard merely because they are available in the request log.

Close the loop with routing decisions. Attribution is most useful when it changes behavior. Compare quality-adjusted cost across models, measure the effect of caching and batching, and route routine work to cheaper models while reserving premium routes for cases that justify them. A lower dollar cost is not a win if correction work or failure rates rise, so pair spend with quality and outcome metrics.

The practical lesson is simple: every AI request should answer who owns it, what it did, what it cost, and how that cost was calculated. Capture identity, price versions, retries, shared overhead, and outcomes at the source. With trustworthy attribution, cost control becomes an engineering feedback loop instead of a monthly surprise.

That is it for today. Know the cost behind every workflow, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep163'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
