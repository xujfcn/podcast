from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 147
title = 'EP147: AI API Data Governance — Control Retention, Residency, and Use'
description = 'A practical guide to AI API data governance: classify inputs, control retention, document processing locations, manage training use, and build deletion and audit workflows.'
pub_date = 'Fri, 4 Sep 2026 08:30:00 +0000'
script = '''EP147: AI API Data Governance — Control Retention, Residency, and Use

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI applications send more than prompts. They send customer records, source code, documents, images, conversation history, and tool results. Before those workloads scale, teams need to know what data is being processed, where it goes, how long it is retained, and who can access it. Today we will build a practical data governance baseline for AI APIs.

Start with classification. Separate public, internal, confidential, personal, regulated, and secret data according to the rules that apply to your organization. Classification should happen before prompt construction and should be enforced by application policy, not left entirely to the model. A workflow that handles support tickets may need a different route from one that handles payment or health information.

Map the data path. Document the application, gateway, model provider, logging system, cache, vector store, file store, and downstream tools that receive or derive data. Record what is sent at each stage, the purpose, the processing region, the retention period, and the responsible owner. A unified gateway such as Crazyrouter can simplify model routing, but it does not remove the need to understand the complete path.

Make provider terms operational. Confirm whether submitted content is used for training, how abuse monitoring works, where processing occurs, what deletion options exist, and which subprocessors are involved. Store the approved route and its data-handling properties in a capability or policy registry. Do not rely on an old contract or a sales summary when a production workflow changes.

Minimize before sending. Remove fields the task does not need, mask identifiers, redact secrets, and use summaries or extracted facts when the original document is unnecessary. Data minimization lowers exposure, storage, and cost at the same time. Keep the original record in the system of record when it must be retained, rather than copying it into every prompt and trace.

Control retention across every layer. Define separate limits for application logs, provider records, caches, object storage, vector indexes, conversation state, and evaluation datasets. Build deletion jobs and verify them. Expiring a database row does not necessarily remove a cached embedding, a saved file, or a copied trace.

Respect residency and transfer requirements. Route data according to customer, region, and regulatory policy. If a workload cannot leave a location, make that constraint explicit in routing and reject incompatible fallbacks. Record the actual route used so an audit can distinguish policy from assumption.

Separate tenant data. Enforce authorization during retrieval, cache lookup, trace access, and tool execution. Include the correct tenant scope in keys and indexes, but do not use a user-controlled string as proof of authorization. Test cross-tenant isolation with adversarial cases and inspect both successful and failed access paths.

Manage training and evaluation data carefully. Production prompts copied into a benchmark can contain personal or proprietary information. Redact, sample, access-control, and document evaluation datasets. Keep dataset versions and approval records so teams know why a sample exists and when it should be removed.

Give users and operators a clear workflow. Support access, correction, deletion, retention exceptions, and incident investigation where required. Record consent or policy basis when relevant, and make an escalation path visible to the owners of the data. Governance is easier to maintain when it is implemented as a workflow with owners and deadlines rather than a document no one consults.

Audit useful evidence. Log route, policy decision, data class, purpose, tenant, retention rule, and deletion status without storing unnecessary sensitive content. Review exceptions, blocked requests, residency mismatches, and unexpected data fields. Run periodic tests to verify that the controls still match the deployed architecture.

The practical lesson is simple: AI data governance is a systems problem. Classify inputs, map every copy, minimize before sending, constrain routes, control retention, isolate tenants, and verify deletion. When these controls are built into the API workflow, teams can scale AI features without losing track of the data that makes them possible.

That is it for today. Know the data path before you optimize the model path. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep147'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
