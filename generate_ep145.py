from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 145
title = 'EP145: Streaming AI APIs — Build Fast, Honest Real-Time Experiences'
description = 'A practical guide to streaming AI APIs: design event flows, handle disconnects, surface partial output honestly, control buffering, and measure time to useful response.'
pub_date = 'Wed, 2 Sep 2026 08:30:00 +0000'
script = '''EP145: Streaming AI APIs — Build Fast, Honest Real-Time Experiences

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Users often judge an AI product by its first visible response, not by the total number of tokens produced. Streaming can reduce perceived latency and make long answers feel interactive, but it also introduces partial state, disconnects, buffering, and cancellation problems. Today we will design streaming AI APIs that feel fast without pretending incomplete output is final.

Start with an explicit event contract. Define events for request acceptance, model start, text deltas, tool activity, usage, completion, cancellation, and error. Include a request or stream identifier in every event. Clients should not have to infer whether a connection ended normally or simply disappeared.

Measure time to useful response. Time to first byte is helpful, but the first token may be whitespace, a disclaimer, or an incomplete sentence. Track time to first meaningful text, time to the first structured result, and total completion time. Compare these metrics by route, model, prompt size, and client type.

Choose the transport deliberately. Server-sent events are simple for one-way token streams, while WebSockets can support richer bidirectional interactions. Whichever transport you use, document reconnection behavior, heartbeat intervals, proxy timeouts, event ordering, and maximum stream duration. A streaming connection still needs ordinary authentication and authorization.

Control buffering. Reverse proxies, middleware, and client libraries can hold several events before flushing them, eliminating the perceived latency benefit. Configure buffering intentionally, send heartbeats where needed, and test through the same CDN or gateway path used in production. A local curl test is not enough evidence for a real user experience.

Treat partial output as partial state. Do not save a streamed answer as complete until a finish event and validation checks succeed. If the connection breaks, preserve the partial text separately and mark it incomplete. For structured output, stream an internal representation only when the client can handle incremental parsing safely; otherwise assemble and validate before exposing the final object.

Handle disconnects and cancellation. Clients close tabs, lose networks, and change their minds. Propagate cancellation to the upstream model when possible so abandoned streams do not keep consuming tokens. Make cancellation idempotent, clean up server-side state, and record whether the provider stopped promptly or continued producing billable output.

Design reconnects without duplication. A reconnecting client should use the stream ID and last received event position when the service supports replay. Otherwise, return a clear resume or restart choice. Do not append a restarted answer blindly to an old partial response. Include sequence numbers so clients can detect missing or duplicated events.

Keep errors visible and useful. An error before any content can be shown as a normal request failure. An error after partial text needs a different presentation, such as incomplete output with a retry action. Record the stage, provider route, bytes sent, tokens used, and cancellation reason. A gateway such as Crazyrouter can centralize model routing while the application owns the stream contract presented to users.

Protect cost and capacity. Limit concurrent streams, maximum duration, output tokens, and idle time. Apply priority policies so abandoned or low-value streams do not starve interactive work. Monitor active streams, disconnect rates, time to first useful response, completion rate, and cost per accepted answer.

Test the uncomfortable paths. Simulate slow tokens, proxy buffering, mobile disconnects, duplicate events, malformed final output, provider timeouts, cancellation races, and client reconnects. Verify that users see honest state, workers are cleaned up, and the accounting matches what the provider actually processed.

The practical lesson is simple: streaming is a protocol and state machine, not a cosmetic switch. Define events, flush intentionally, preserve sequence, handle cancellation, validate completion, and measure useful latency. Done well, streaming makes AI products feel responsive without hiding reliability problems behind animation.

That is it for today. Show progress honestly and finish reliably. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep145'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
