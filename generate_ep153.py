from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 153
title = 'EP153: Production RAG APIs — Build Retrieval That Users Can Trust'
description = 'A practical guide to production RAG APIs: prepare documents, retrieve relevant evidence, enforce permissions, cite sources, measure groundedness, and recover from stale indexes.'
pub_date = 'Thu, 10 Sep 2026 08:30:00 +0000'
script = '''EP153: Production RAG APIs — Build Retrieval That Users Can Trust

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Retrieval-augmented generation is often described as a simple pipeline: search for documents, add them to a prompt, and ask a model for an answer. In production, the hard part is making sure the retrieved evidence is relevant, authorized, fresh, and actually reflected in the response. Today we will build a RAG API that users can trust.

Start with document preparation. Extract text while preserving headings, tables, page references, and source metadata. Remove boilerplate and duplicate content, but keep the information needed to interpret exceptions. Record the source ID, version, owner, effective date, and access scope alongside every chunk.

Choose chunking by meaning. Fixed token windows are easy to implement, but they can split a definition from its qualification or separate a table heading from its values. Use headings, sections, semantic boundaries, and modest overlap where appropriate. Evaluate chunking on real questions rather than assuming a single chunk size works for every document type.

Make indexing versioned and observable. Record the embedding model, chunking configuration, parser version, and source snapshot. Monitor failed documents, missing metadata, duplicate chunks, index lag, and deletion propagation. A unified gateway such as Crazyrouter can handle the generation route, but retrieval infrastructure still needs its own lifecycle and health signals.

Enforce permissions before retrieval. Filter by tenant, user, document scope, and purpose before returning candidates to the prompt. Do not retrieve broadly and hope the model will ignore unauthorized passages. Test cross-tenant isolation, revoked access, inherited permissions, and documents whose metadata is incomplete.

Retrieve for the question. Combine keyword, semantic, metadata, recency, and access filters when the workload benefits from them. Rerank candidates if the first retrieval stage returns a noisy set, and cap the evidence that reaches the model. More passages can increase distraction, cost, and the chance of conflicting instructions.

Preserve provenance. Give every passage a source identifier, title, version, and location that can be cited in the final response. Instruct the model to distinguish supported evidence from uncertainty and to say when the available sources do not answer the question. A citation that points to a document but not the relevant section is less useful than a precise reference.

Validate grounded answers. Check that citations refer to retrieved sources, required evidence is present, and the answer does not claim facts absent from the context. Use deterministic checks, sampled human review, and task-specific graders. Track groundedness, retrieval hit rate, answer acceptance, abstention quality, and user corrections rather than relying on one generic score.

Handle freshness deliberately. Set update expectations by document type, refresh indexes after approved changes, and show effective dates when they matter. If indexing is delayed, make that status visible to operators and decide whether the system should answer from the previous snapshot, abstain, or route to a different workflow.

Protect the prompt boundary. Retrieved documents are data, not instructions. Separate evidence from system policy and user commands, and defend against prompt injection embedded in documents. Keep tool permissions and write actions outside the model’s authority unless an explicit policy permits them.

Design recovery paths. If retrieval is empty, the index is unavailable, or confidence is low, return a clear limited answer or escalate rather than inventing one. Cache and retry boundedly, preserve request traces, and keep the source snapshot used for an answer so incidents can be reproduced.

The practical lesson is simple: production RAG is a data, authorization, retrieval, and evaluation system around a model. Prepare documents carefully, enforce access before search, retrieve selectively, cite precisely, measure groundedness, and handle stale or missing evidence honestly. That is how a RAG API becomes dependable instead of merely impressive in a demo.

That is it for today. Give the model evidence it can prove, not context it can only repeat. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep153'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
