from pathlib import Path
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


root = Path('/root/.openclaw/workspace/podcast')
ep = 118
title = 'EP118: AI API Context Window Management — More Tokens Are Not Always Better'
description = 'A practical guide to context window management for AI applications: budget tokens, rank information, summarize history, retrieve selectively, reserve output space, and handle overflow safely.'
pub_date = 'Thu, 06 Aug 2026 08:30:00 +0000'
script = 'EP118: AI API Context Window Management — More Tokens Are Not Always Better\n\nWelcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about context window management for AI applications. Modern models can accept very large prompts, but sending everything on every request is rarely the best design. Large contexts increase cost, latency, and failure risk, while important instructions can become harder for the model to identify.\n\nStart by treating context as a budget. The window must hold system instructions, conversation history, retrieved documents, tool schemas, user input, and enough space for the answer. Reserve output capacity before constructing the prompt. If the application fills the entire window with input, the model may truncate the response or reject the request.\n\nMeasure context by tokens, not characters. Token density varies by language, code, formatting, and data structure. Count tokens with the tokenizer or estimation method appropriate for the selected model. Add a safety margin because gateways, providers, and tool wrappers may introduce additional tokens.\n\nPrioritize information by purpose. System policy and current user intent normally matter more than old conversation turns. Retrieved evidence should be relevant to the current task. Tool definitions should include only tools the model can actually use. Give each context component a priority so trimming behavior is deterministic rather than accidental.\n\nDo not keep unlimited conversation history. Summarize older turns, preserve durable facts separately, and retain recent exchanges verbatim where nuance matters. A summary should record decisions, unresolved questions, constraints, and identifiers—not every sentence. When accuracy is critical, link the summary back to source records that can be retrieved again.\n\nRetrieval should reduce context, not flood it. Search a larger candidate set, rerank it, remove duplicates, and include only the passages needed for the answer. Preserve source metadata so citations remain possible. More documents can lower quality when irrelevant text competes with the evidence that actually matters.\n\nTool schemas are another hidden cost. Agent platforms may attach dozens of verbose tool definitions to every request. Select tools by task, shorten descriptions without losing constraints, and avoid sending unavailable tools. Tool selection can save thousands of tokens before the user writes a single word.\n\nUse prompt caching where supported. Stable system instructions, reference material, and tool schemas can often be placed in a reusable prefix. Track cached and uncached token usage separately. Caching reduces repeated processing cost, but it does not remove the need to keep context relevant and within model limits.\n\nHandle model switching explicitly. Different models have different context limits, tokenizers, tool formats, and output caps. A prompt that fits one route may overflow its fallback. The gateway or application should calculate against the selected route and keep enough headroom for fallback models that may have smaller windows.\n\nChoose a clear overflow policy. Options include trimming low-priority history, summarizing, retrieving fewer passages, splitting the task, asking the user to narrow the request, or routing to a larger-context model. Silent truncation is usually the worst option because it makes failures difficult to explain.\n\nLong-context models still need structure. Use clear sections, stable delimiters, document identifiers, and explicit instructions about which sources control the answer. Put critical constraints where the model can find them reliably, and test whether performance changes when evidence appears near the beginning, middle, or end.\n\nMonitor the right signals. Track input tokens, output reservation, context utilization, truncation events, summarization frequency, retrieval count, cache hits, latency, and cost per successful outcome. Compare these metrics by feature and model so one oversized workflow does not hide inside a platform average.\n\nTest with realistic worst cases. Include long conversations, multilingual text, code, large tool schemas, duplicated documents, and fallback routes. Confirm that the application preserves current intent and safety constraints after trimming. A context manager is successful only if the final answer remains useful.\n\nThe practical lesson is simple. A larger context window is capacity, not permission to send everything. Budget tokens, rank information, summarize history, retrieve selectively, reserve output space, and define overflow behavior before the request reaches the model.\n\nThat is it for today. Manage and route multi-model workloads through one unified API with Crazyrouter at crazyrouter.com, and see you in the next episode.'

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
key = re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)', tools).group(1)
parts = script.split('\n\n')

for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_chunk{i}.mp3'
    if out.exists() and out.stat().st_size > 1000:
        continue
    for attempt in range(1, 4):
        response = requests.post(
            'https://crazyrouter.com/v1/audio/speech',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
            timeout=300,
        )
        print('part', i, response.status_code, 'attempt', attempt, flush=True)
        if response.ok:
            out.write_bytes(response.content)
            break
        if attempt == 3:
            response.raise_for_status()
        time.sleep(5 * attempt)

concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file 'ep{ep:03d}_chunk{i}.mp3'\n" for i in range(1, len(parts) + 1)))
audio = root / f'audio/ep{ep:03d}.mp3'
subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(audio)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True)
seconds = float(json.loads(probe.stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
size = audio.stat().st_size

feed = root / 'feed.xml'
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
if not any((item.findtext('title') or '').startswith(f'EP{ep:03d}:') for item in channel.findall('item')):
    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = pub_date
    enclosure = ET.SubElement(item, 'enclosure')
    enclosure.set('url', f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3')
    enclosure.set('length', str(size))
    enclosure.set('type', 'audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    ET.SubElement(item, f'{{{ns}}}duration').text = duration
    ET.SubElement(item, f'{{{ns}}}episode').text = str(ep)
    ET.SubElement(item, f'{{{ns}}}episodeType').text = 'full'
    ET.SubElement(item, f'{{{ns}}}explicit').text = 'false'
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'
    existing = channel.findall('item')
    channel.insert(list(channel).index(existing[0]) if existing else len(list(channel)), item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)

print('DONE', audio, size, duration)
