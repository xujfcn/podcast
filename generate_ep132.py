from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 132
title = 'EP132: AI Model Migration Runbooks — Switch Models Without Breaking Production'
description = 'A practical runbook for migrating production AI workloads between models: inventory dependencies, test compatibility, canary traffic, control fallbacks, communicate changes, and keep rollback fast.'
pub_date = 'Thu, 20 Aug 2026 08:30:00 +0000'
script = '''EP132: AI Model Migration Runbooks — Switch Models Without Breaking Production

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI teams change models constantly. A newer model arrives, pricing changes, a provider retires an endpoint, or a workload needs better latency. Yet many teams still handle migration as a one-line configuration edit. In production, that is risky. Today we will build a model migration runbook that makes change controlled and reversible.

Start with an inventory. List every workload using the current model, including background jobs, evaluation scripts, support tools, and forgotten staging environments. Record the exact model name, endpoint, request parameters, context limits, tool schemas, output format, timeout, retry policy, and fallback route. You cannot migrate dependencies you do not know exist.

Next, define the compatibility contract. The replacement model must support the capabilities the workload actually uses. Check streaming, vision, structured output, tool calling, system messages, token limits, and parameter behavior. Do not assume two OpenAI-compatible endpoints behave identically. Replay real production-shaped payloads and validate the responses with the same parser and business rules used by the application.

Build a representative test set. Include common requests, difficult edge cases, long inputs, multilingual content, malformed data, and known historical failures. Compare accepted-result rate, not subjective style alone. If users depend on JSON, citations, code patches, or tool actions, those requirements must be scored explicitly.

Measure operational differences. Record time to first token, total latency, tail latency, token usage, retries, and cost per accepted result. A migration that improves benchmark quality but doubles timeout failures is not an upgrade. Likewise, a cheaper model may cost more after retries and repair.

Prepare the routing change before the launch. Use a stable application-facing alias or gateway policy rather than hard-coding a new model throughout the codebase. A unified gateway such as Crazyrouter lets teams change the underlying route while keeping one integration surface. Version the routing policy, review it like code, and make the previous configuration easy to restore.

Roll out gradually. Begin with shadow traffic when privacy and cost allow, then send a small canary percentage of real eligible requests. Compare the new and old routes over the same time window. Watch quality failures, latency, error classes, fallback share, and spend. Increase traffic in stages only when thresholds remain healthy.

Design rollback before migration. Define who can trigger it, which metrics justify it, and how quickly the old route can be restored. Preserve compatible credentials and capacity during the observation period. A rollback should be a tested policy change, not an improvised deployment during an incident.

Communicate the migration. Tell application owners what changes, which model name or alias is affected, the expected timeline, known behavior differences, and where to report problems. If customers choose models directly, provide a deprecation window and concrete replacement examples. Silent changes save one announcement but create weeks of confusing support cases.

After the cutover, keep monitoring. Some failures appear only with rare prompts, traffic peaks, or long-running agents. Review fallback use, validation errors, user complaints, and cost for several days. Update documentation and remove the old route only after the new path has earned confidence.

The practical lesson is simple: model migration is an operational change, not a string replacement. Inventory dependencies, define compatibility, replay real workloads, canary traffic, prepare rollback, and communicate clearly. With a runbook, teams can adopt better models quickly without making users absorb the risk.

That is it for today. Make every model change reversible. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep132'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
