from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 129
title = 'EP129: AI API Reliability — Design for Retries, Timeouts, and Provider Failures'
description = 'A practical reliability playbook for AI API applications: deadlines, retries, fallbacks, idempotency, streaming recovery, and the metrics that reveal real user impact.'
pub_date = 'Mon, 17 Aug 2026 08:30:00 +0000'
script = '''EP129: AI API Reliability — Design for Retries, Timeouts, and Provider Failures

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about a part of AI engineering that becomes important the moment real users arrive: reliability. A model can be impressive in a demo and still produce a poor product if requests time out, streams stop halfway through, or one provider failure takes down the whole workflow.

Start with a deadline, not an unlimited timeout. Decide how long the user experience can wait, then divide that budget across queueing, retrieval, model generation, tools, and any fallback. A retry that starts after the deadline is not resilience; it is delayed failure.

Retry only errors that are likely to recover. Rate limits, temporary upstream failures, and connection resets may deserve a retry. Invalid requests, authentication errors, content-policy decisions, and malformed tool arguments usually need a different response. Use exponential backoff with jitter, cap the number of attempts, and respect the provider's retry-after signal.

Protect every side effect with idempotency. If an AI agent sends an email, charges an account, creates a ticket, or changes a database row, a retry must not duplicate that action. Give each logical operation an idempotency key, record its state, and make the tool handler safe when the same request arrives twice.

Design fallbacks around the contract. A fallback model does not need to be identical, but it must return something the application can safely consume. Keep structured output schemas stable, validate every response, and reject or repair invalid output before it reaches downstream code. A cheaper model that returns valid JSON is often more useful than a stronger model that breaks the parser.

Streaming deserves its own failure plan. Track whether the response has started, how many tokens have arrived, and whether the connection ended cleanly. After partial output, silently restarting can confuse users or duplicate actions. Show a clear recovery state, resume only when the workflow supports it, and never treat an incomplete tool call as a completed one.

Centralize routing and observability. Record the request ID, route, provider, model, latency, retries, time-to-first-token, output validation result, and final outcome. Do not log API keys, private prompts, or customer documents. With a unified gateway such as Crazyrouter, these fields can be compared across providers without rewriting every application integration.

Measure user impact, not just uptime. A service can report ninety-nine point nine percent availability while users experience slow answers, empty responses, repeated retries, or incorrect fallbacks. Track successful task completion, timeout rate, invalid-output rate, fallback rate, p95 latency, and cost per successful outcome.

Test the unpleasant paths before production. Simulate 429 responses, long delays, truncated streams, provider outages, malformed JSON, and tool timeouts. Verify that deadlines are enforced, retries stop, side effects remain single, and the user receives a useful explanation. Turn every confirmed production failure into a regression test.

Reliability is not one clever retry loop. It is a set of explicit contracts: a deadline, a retry policy, a safe fallback, idempotent tools, observable routes, and a tested recovery experience. Build those pieces early, and adding new models becomes a controlled change instead of a new source of surprises.

That is it for today. Make failure boring before it becomes expensive. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep129'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
