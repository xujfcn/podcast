from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 136
title = 'EP136: AI API Caching — Cut Cost Without Serving Stale Answers'
description = 'A practical guide to caching AI API work safely: choose cacheable requests, build stable keys, respect freshness, protect privacy, and measure savings without hurting answer quality.'
pub_date = 'Mon, 24 Aug 2026 08:30:00 +0000'
script = '''EP136: AI API Caching — Cut Cost Without Serving Stale Answers

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI API calls can be expensive and slow when the same work is repeated. Documentation assistants answer the same questions, evaluation suites replay identical prompts, and product flows often request stable transformations again and again. Caching can reduce cost and latency, but a careless cache can return the wrong answer to the wrong user. Today we will design caching that is useful without becoming a correctness or privacy problem.

Start by classifying requests. Exact deterministic tasks such as embeddings, fixed transformations, and repeated evaluation prompts are usually easier to cache than open-ended conversations. For generated answers, ask whether the same input, model, system instructions, tools, retrieved context, and relevant user permissions should produce an interchangeable result. If not, the request needs a more careful policy or no cache at all.

Build a complete cache key. Include the model or route, versioned system prompt, user prompt, relevant parameters, tool definitions, retrieval context version, locale, and output format. Omitting one of these can create collisions where an old or incompatible result looks valid. A version field lets you invalidate a whole class of entries when behavior changes.

Choose the right freshness rule. Some results can live for weeks, while pricing, inventory, account status, and current events may be stale within seconds. Use a time-to-live that reflects the data, not a convenient global default. When freshness is critical, consider stale-while-revalidate: serve a known result briefly while refreshing it in the background, but only when the product can tolerate that behavior.

Protect privacy and authorization. Never let a shared cache bypass user permissions. Include the right tenant or access scope in the key, or disable sharing for private requests. Avoid storing sensitive prompts and outputs unless retention is justified, encrypted, access-controlled, and documented. A cache is another data store, so it belongs in the threat model.

Cache at the right layer. An application cache can understand business semantics, a retrieval layer can cache documents or search results, and a gateway can provide consistent routing and accounting across services. A unified gateway such as Crazyrouter can help centralize model access, while teams still decide which product-level results are safe to reuse. Do not assume transport-level caching understands the meaning of an AI response.

Handle streaming and partial results explicitly. Decide whether to cache the final assembled response, the token stream, or neither. Store enough metadata to reproduce the response type and finish reason. If a stream is interrupted, do not treat a partial answer as a successful cache entry unless the application is designed for resumable output.

Make invalidation predictable. Tie cache versions to prompt templates, model upgrades, knowledge-base snapshots, and policy changes. When a customer edits source material, invalidate dependent results rather than waiting for a long TTL. If invalidation is difficult, use shorter freshness windows for the affected route.

Measure more than hit rate. Track cache hits, misses, prevented tokens, latency saved, storage cost, invalidation rate, stale-result complaints, and cost per accepted result. A high hit rate is not automatically good if cached answers cause support incidents. Compare quality and user outcomes between cache hits and fresh requests.

Plan failure behavior. If the cache is unavailable, the application should normally fall back to the model route rather than fail the entire product, subject to budget controls. Add timeouts and bounded retries around the cache itself. A cache that becomes a mandatory dependency can turn a cost optimization into an outage multiplier.

The practical lesson is simple: cache semantics, not just strings. Define identity, freshness, privacy, invalidation, and fallback behavior before chasing hit rates. Done carefully, caching makes AI products faster and cheaper while keeping answers trustworthy.

That is it for today. Save repeated work, but never skip the correctness check. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep136'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
