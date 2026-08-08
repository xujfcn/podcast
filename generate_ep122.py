from pathlib import Path
import base64
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
import requests

root = Path('/root/.openclaw/workspace/podcast')
ep = 122
title = 'EP122: AI API Reliability — Retries, Fallbacks, and Timeouts That Actually Work'
description = 'A practical guide to making AI API applications dependable in production: set realistic timeouts, retry only safe failures, design provider fallbacks, prevent retry storms, and measure successful outcomes instead of raw uptime.'
pub_date = 'Mon, 10 Aug 2026 08:30:00 +0000'
script = '''EP122: AI API Reliability — Retries, Fallbacks, and Timeouts That Actually Work

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about reliability for AI API applications. A model can be accurate and your gateway can be healthy, yet users still experience failures when a request times out, a provider throttles traffic, or a retry turns one incident into a much larger outage. Reliable AI systems need deliberate behavior at every layer.

Start by defining what success means. A request that returns HTTP 200 is not necessarily a successful task. The response may be malformed, incomplete, too slow to be useful, or unable to complete a required tool call. Track successful outcomes, not just request success. Useful metrics include completion rate, valid-output rate, p50 and p95 latency, cost per successful task, and the percentage of requests recovered by a fallback.

Timeouts should match the task. A short classification request and a long coding or document-generation request should not share one global timeout. Set a connection timeout, a time-to-first-token timeout, and an overall deadline. For streaming responses, also use an idle timeout so a connection that stays open without progress does not consume resources forever. Pass the remaining deadline through internal services instead of allowing each layer to start its own full timer.

Retries are not a universal fix. Retry transient network errors, rate limits, and selected provider failures, but do not retry invalid requests, authentication errors, policy refusals, or deterministic schema failures. Use exponential backoff with jitter. Cap the number of attempts and the total retry time. If a request triggers an external side effect, make the operation idempotent or require a request identifier before retrying. Otherwise, a timeout can cause duplicate actions.

Prevent retry storms. If the client retries, the gateway retries, and a provider SDK retries, one user request can become many upstream requests. Choose one primary retry owner and make the other layers conservative. Add a retry budget per tenant and globally. When the budget is exhausted, fail quickly with a useful error rather than making a congested provider even more congested.

Fallbacks should be based on capability, not only price. A fallback model must support the required context length, input modality, tool format, structured-output behavior, and safety constraints. Keep a route policy that says which models are acceptable for each task. A cheap text model is not a valid fallback for an image request, and a model with different tool-call syntax may need an adapter before it can safely receive the same payload.

Use circuit breakers and health signals. When a provider is failing repeatedly, open the circuit and temporarily stop sending it normal traffic. Probe it with controlled health checks or a small canary volume before restoring traffic. Distinguish provider health from model health: one model may be degraded while another model at the same provider remains usable. Also track regional and account-level limits, because a provider can be reachable while your specific quota is exhausted.

Graceful degradation is part of product design. If the premium route is unavailable, perhaps return a shorter answer, defer a long job, disable an optional enrichment step, or ask the user to retry later. Tell the user what happened without exposing internal credentials or unstable provider details. A clear partial result is often better than an opaque five-minute wait.

Observability must connect the whole request. Record a correlation ID, route decision, provider, model, attempt count, fallback reason, latency phases, token usage, and final outcome. Redact sensitive prompts and responses according to your data policy. When an incident happens, engineers should be able to answer: did the request fail at the client, gateway, provider, tool, or validation layer?

Test failure paths intentionally. Inject timeouts, 429 responses, malformed JSON, truncated streams, slow tool calls, and provider disconnects. Verify that retries stop at the deadline, fallbacks preserve the request contract, and users do not receive duplicate side effects. Run these tests in staging and with a small production canary. Reliability that exists only in a diagram is not reliability.

The practical lesson is simple. Use task-specific deadlines, retry only transient and safe failures, prevent layered retry storms, choose capability-compatible fallbacks, and measure recovered successful outcomes. With a unified API gateway such as Crazyrouter, you can centralize routing, fallback, cost, and observability policies while keeping your application code focused on the product.

That is it for today. Build AI applications that remain useful when the network, provider, or model has a bad day. Visit crazyrouter.com, and see you in the next episode.'''

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
key = re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)', tools).group(1)
parts = script.split('\n\n')
for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_chunk{i}.mp3'
    for attempt in range(1, 4):
        response = requests.post('https://crazyrouter.com/v1/audio/speech', headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}, json={'model': 'tts-1', 'voice': 'alloy', 'input': part}, timeout=300)
        print('part', i, response.status_code, 'attempt', attempt, flush=True)
        if response.ok:
            out.write_bytes(response.content)
            break
        if attempt == 3:
            response.raise_for_status()
        time.sleep(5 * attempt)

concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file 'ep{ep:03d}_chunk{i}.mp3'\n" for i in range(1, len(parts) + 1)), encoding='utf-8')
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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep122'
    existing = channel.findall('item')
    channel.insert(list(channel).index(existing[0]) if existing else len(list(channel)), item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print('DONE', audio, size, duration, flush=True)
