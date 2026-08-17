from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 158
title = 'EP158: Voice AI APIs — Build Reliable Speech-to-Text and Text-to-Speech Flows'
description = 'A practical guide to voice AI APIs: handle audio formats, streaming, transcription quality, synthesis latency, privacy, retries, and reliable audio delivery in production.'
pub_date = 'Tue, 15 Sep 2026 08:30:00 +0000'
script = '''EP158: Voice AI APIs — Build Reliable Speech-to-Text and Text-to-Speech Flows

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Voice features make AI products feel immediate and natural, but audio adds a different set of engineering problems. Files have formats, sample rates, durations, and noisy environments. Streaming introduces partial results and interruption. Privacy rules apply to recordings and transcripts alike. Today we will build reliable speech-to-text and text-to-speech workflows.

Start by defining the audio contract. Specify accepted codecs, containers, sample rates, channels, maximum duration, maximum bytes, and whether the input is a file or live stream. Normalize audio before inference when possible, and reject unsupported formats early with an actionable error. Consistent input reduces provider-specific surprises.

Separate transcription stages. Upload, decode, normalize, transcribe, post-process, and store each have different failure modes. Record the language, diarization or speaker settings, timestamps, confidence signals, and model route. If the product displays a transcript, preserve a link to the source segment so users can inspect uncertain words.

Handle real-world audio. Background noise, accents, overlapping speakers, silence, clipping, and code-switching can all reduce accuracy. Use voice activity detection, reasonable silence limits, language hints, and speaker labels when the task needs them. Do not turn low confidence into a polished-looking fact without a review or uncertainty path.

Design streaming transcription carefully. Decide whether interim text is advisory and final text is authoritative. Include sequence numbers, segment IDs, timestamps, and explicit completion events. If a connection drops, let the client resume or mark the transcript incomplete rather than appending duplicated partial text.

Treat transcripts as sensitive data. Recordings can contain personal, financial, or proprietary information, and transcripts may be easier to search than the original audio. Apply access controls, retention limits, deletion workflows, encryption, and redaction. Keep raw audio out of general logs, and document whether providers retain or train on submitted content.

For text-to-speech, define delivery expectations. Choose voice, language, speaking rate, pronunciation rules, format, and maximum output duration. Generate audio in chunks when the user needs low time to first sound, but make sure chunk boundaries do not create clicks, repeated words, or unnatural pauses. Store the final artifact separately from temporary segments.

Make synthesis interruptible. Voice assistants should stop speaking when the user starts talking or cancels the request. Propagate cancellation upstream where possible, close streams, clean up temporary files, and account for audio already generated. A voice response that cannot be interrupted feels slow even when its first byte was fast.

Validate audio output. Check container, codec, sample rate, duration, byte size, and decodability before publishing or returning a URL. Use short-lived authenticated URLs for private audio, and distinguish a complete file from a partial stream. A unified gateway such as Crazyrouter can centralize model access while the application remains responsible for media validation and delivery.

Control cost and latency. Track audio minutes, input and output bytes, time to first transcript, time to first audio, total latency, retries, and cost per accepted interaction. Use smaller or faster routes for simple tasks, cache reusable synthesis where rights allow, and enforce duration limits to prevent accidental runaway jobs.

Test the uncomfortable cases. Use noisy audio, long recordings, language changes, disconnects, malformed files, provider timeouts, cancellation races, and overlapping speech. Compare transcript quality and user recovery, not only HTTP status. Voice systems are successful when users can understand, correct, and continue after imperfect input.

The practical lesson is simple: voice AI is a media pipeline with a conversational interface. Normalize audio, preserve uncertainty, protect recordings, stream with explicit state, validate media, handle interruption, and measure useful latency. With those controls, speech features can feel natural without becoming opaque or fragile.

That is it for today. Make every spoken interaction recoverable and respectful of privacy. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep158'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
