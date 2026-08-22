from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 182
title = 'EP182: AI API Observability — Trace Every Request From Gateway to Model'
description = 'A practical guide to AI API observability: define request context, trace multi-provider calls, measure useful latency and quality signals, protect sensitive data, correlate retries and spend, and make production failures diagnosable.'
pub_date = 'Fri, 09 Oct 2026 08:30:00 +0000'
script = '''EP182: AI API Observability — Trace Every Request From Gateway to Model

Welcome back to AI Dev Tools — The Crazyrouter Podcast. When an AI request is slow, expensive, or wrong, a single request count does not explain what happened. The gateway may have routed across providers, retried after a timeout, streamed partial output, or invoked tools through several services. Today we will design observability that follows one logical operation across that whole path without turning sensitive prompts into ordinary logs.

Start with a stable request context. Generate a request ID at the public boundary, accept a trusted upstream trace context when one exists, and create a logical operation ID for work that can span retries or asynchronous jobs. Keep attempt IDs separate from the logical ID. One customer operation may have three provider attempts, but support and billing should still be able to find the complete story with one safe identifier.

Propagate context deliberately. The gateway should pass trace headers to internal services and attach a provider-safe correlation value when the upstream API supports one. Do not forward arbitrary customer headers or expose internal topology. Context propagation is a contract: document which IDs are stable, which are internal, how long they are retained, and which identifier a customer should include in a support request.

Instrument the stages that change the outcome. Record admission, authentication, policy checks, queue wait, route selection, provider connection, time to first token, streaming duration, tool calls, usage accounting, and final settlement. A total duration without stage boundaries hides the difference between a slow queue, a slow provider, and a client that stopped reading. Name spans by operation and stage rather than by raw prompt text or unbounded URL values.

Measure distributions, not just averages. For interactive text, track time to first token, inter-token gaps, total generation time, and completion rate. For images, video, and asynchronous jobs, track queue delay, provider processing time, webhook delay, and reconciliation time. Report p50, p95, and p99 by route and workload class. A healthy average can coexist with a terrible tail that only affects large prompts or a particular provider region.

Make routing visible. Every trace should show the selected model family, provider, region, adapter version, and reason for the route, using normalized labels. Record whether the choice came from default policy, capability matching, a fallback, a canary, or a tenant override. Keep provider names and model identifiers in controlled dimensions so a new model cannot create an unlimited-cardinality metrics problem.

Correlate attempts without hiding them. A retry is not a second unrelated request, and a fallback is not a successful first attempt. Store the attempt number, trigger, delay, provider outcome, and whether any work was accepted upstream. This lets operators distinguish a route that succeeds quickly from one that succeeds only after expensive retries. It also gives billing and incident review a reliable explanation for provider work that happened before the final answer.

Treat streaming as a first-class trace. Record when headers were sent, when the first token arrived, how many output chunks were emitted, whether the client disconnected, and whether the provider closed cleanly. Never infer completion solely from a socket closing. Emit a terminal operation state internally, and connect it to usage settlement so an interrupted stream is not silently counted as either a free failure or a complete response.

Asynchronous work needs durable status transitions. Give a job one operation ID and record accepted, queued, running, succeeded, failed, cancelled, and reconciliation states with timestamps. A webhook span should link to the provider operation ID but should not be the only source of truth. If the callback is late or duplicated, the trace should show the polling or reconciliation action and make it clear whether a duplicate job was prevented.

Add quality signals carefully. HTTP success does not mean a useful answer. Depending on the product, record structured-output validation, moderation result, tool-call success, citation checks, user feedback, or downstream task completion. Keep these as privacy-conscious aggregates or redacted classifications. Do not put full prompts, generated answers, documents, or tool arguments into traces by default just because they are convenient for debugging.

Separate metrics, logs, and traces. Metrics answer whether a class of requests is changing. Logs explain a specific decision or state transition. Traces connect the stages of one operation. Put stable codes and bounded labels in metrics, structured event data in logs, and timing plus relationships in traces. A giant JSON log containing every token is expensive, difficult to query, and a serious data exposure risk.

Build a privacy boundary into the telemetry pipeline. Redact authorization headers, API keys, email addresses, tenant secrets, and provider payloads before export. Hash or tokenize identifiers only when the mapping is controlled and genuinely needed. Apply retention by data class: aggregate metrics can live longer than detailed request events. Make access to high-sensitivity traces auditable, and test redaction with realistic prompts that contain secrets rather than relying on a few hand-written examples.

Control cardinality and cost. Never use prompt text, user IDs, request IDs, or arbitrary error messages as metric labels. Sample successful detailed traces more aggressively than rare failures, but keep enough metadata to explain cost and quality. Tail-based sampling is useful when a request becomes slow, falls back, produces partial output, or fails validation. Budget telemetry itself, because an observability system that costs as much as inference will not survive growth.

Connect observability to spend and quotas. Include the pricing version, estimated usage, actual usage, reservation, and settlement references as protected links to accounting records. Do not duplicate financial details into every public log. With correlation in place, an operator can answer whether a cost spike came from longer outputs, retries, a model change, a fallback storm, or a stuck asynchronous job. That is much more useful than a daily total with no path back to the responsible workload.

Turn traces into actionable alerts. Alert on user-visible symptoms such as rising time to first token, increased partial streams, falling structured-output validity, growing reconciliation age, or a sudden change in cost per successful task. Group alerts by route and operation class so a provider-specific regression does not page every service. Include a representative trace ID and the normalized decision path, while keeping sensitive payloads behind the protected investigation workflow.

Test the telemetry contract. Exercise a normal request, a provider timeout before acceptance, a retry after uncertain acceptance, a fallback, a stream interrupted after output begins, a duplicate webhook, a client disconnect, and a redaction case. Assert that IDs relate correctly, required spans close, terminal state is recorded, usage links to the logical operation, and no secret appears in exported logs. Observability that is not tested will disappear exactly when an incident needs it.

Keep dashboards organized around decisions. A route health view should show availability, tail latency, first-token latency, fallback rate, and quality checks. A tenant view should show bounded usage and budget outcomes. An operation view should reconstruct the timeline from admission to settlement. An incident view should compare affected routes, model versions, regions, and deploys. Avoid a wall of charts; each panel should answer what changed, who is affected, and what action is safe next.

The practical lesson is simple: observability is the connective tissue between reliability, cost, and product quality. Give every logical operation a safe identity, trace stages and attempts, measure distributions, preserve asynchronous state, protect sensitive content, and connect telemetry to accounting and user-visible outcomes. When a request is slow or wrong, the team should be able to explain what happened without guessing or reading customer prompts.

That is it for today. Make every request diagnosable, keep telemetry safe, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script)
parts = script.split('\n\n')
for i, part in enumerate(parts, 1):
    subprocess.run(['edge-tts', '--voice', 'en-US-GuyNeural', '--text', part, '--write-media', str(root / f'episodes/ep{ep:03d}_chunk{i}.mp3')], check=True)
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
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep}'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration} {len(parts)} chunks')
