from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 181
title = 'EP181: AI API Error Taxonomy — Make Failures Actionable'
description = 'A practical guide to AI API error taxonomy: classify failures by retryability and ownership, preserve provider context, return stable client errors, prevent unsafe retries, and turn failure data into better operations.'
pub_date = 'Thu, 08 Oct 2026 08:30:00 +0000'
script = '''EP181: AI API Error Taxonomy — Make Failures Actionable

Welcome back to AI Dev Tools — The Crazyrouter Podcast. When an AI API fails, a generic 500 or 429 leaves everyone guessing. Should the client retry? Should it change the request? Is the provider still processing work? Or is the gateway protecting a budget or policy? Today we will design an error taxonomy that turns failures into safe decisions for clients, operators, and product teams.

Start by separating transport failure from application failure. A connection reset, DNS error, TLS problem, or gateway timeout says something about communication. An invalid request, unsupported model capability, policy denial, or exhausted quota says something about the operation. Keep those dimensions separate even when they share an HTTP status, because retrying a malformed request only creates noise while retrying a transient connection error may recover successfully.

Use a stable public error envelope. A useful response has an error type, a stable code, a human-readable message, a request ID, and a retryable hint when that hint is safe to provide. Include a provider code or upstream status only as structured metadata, not as the entire contract. Clients should branch on a documented code such as invalid_request, rate_limited, provider_unavailable, or policy_denied instead of parsing prose that may change with a deployment.

Classify errors by the next safe action. Fixable client errors need a corrected request. Authentication and authorization errors need a credential or permission change, not a retry loop. Rate limits need bounded waiting and respect for Retry-After. Capacity or provider availability errors may use a controlled fallback. Policy errors need a different allowed operation or a review path. Unknown outcomes require reconciliation before chargeable work is repeated.

Do not confuse retryable with retried. A failure can be technically transient but still unsafe to repeat if the provider may have accepted the request or a tool may have produced a side effect. The gateway should make retry decisions using operation state, idempotency information, and provider certainty. Return enough context for the client to continue safely without promising exactly-once behavior the system cannot prove.

Preserve the error chain internally. Record the gateway classification, adapter result, provider status, timeout stage, attempt number, and final action. Keep the public response small and safe, while traces retain the details needed for diagnosis. A provider's 503 might become provider_unavailable, but an internal trace should show whether it arrived before headers, during streaming, after partial output, or after a queued job was accepted.

Make the boundary between client and server ownership explicit. The client owns malformed JSON, missing required fields, invalid parameters, and expired credentials. The gateway owns routing policy, tenant limits, request validation, and protecting shared capacity. The provider owns its service availability and model-specific limits. Ownership makes support faster and prevents teams from retrying a problem that only a configuration or code change can solve.

Treat status codes as a transport hint, not the full taxonomy. A 400 can mean a fixable schema error or an unsupported capability. A 401 can mean an expired gateway credential, while a provider credential failure is an operator incident. A 429 can be a tenant quota, provider rate limit, or global overload. Put the precise category in the stable code and document which fields are safe for automation.

Streaming needs stage-aware errors. Before the first token, the gateway can return a normal structured error. After a stream begins, the HTTP status can no longer change, so send a typed terminal event with the request ID, whether output is partial, and whether the operation may still be running. Clients must distinguish a clean completion, a cancelled stream, a provider failure, and an interrupted connection. Never label partial output as a complete answer.

Async jobs need durable failure state. A webhook should identify the job, attempt, error code, and whether the job can be resumed or must be recreated. Store the last failure and a safe next action so polling clients do not infer state from the absence of an event. If a provider accepted the job but the callback is missing, use the provider operation ID and reconciliation workflow before declaring failure or starting a duplicate job.

Make fallbacks classification-aware. A fallback is reasonable for provider_unavailable or a bounded timeout when the request is compatible with another model. It is usually wrong for invalid_request, policy_denied, authentication_failed, or a schema mismatch caused by the gateway. Before switching routes, check capability, data residency, budget, and quality requirements. Log the original and fallback classifications so a rising fallback rate does not hide a provider regression.

Keep error messages useful without leaking secrets. Do not echo API keys, authorization headers, full prompts, private tenant names, or sensitive provider payloads. Redact model inputs in ordinary logs and cap the size of upstream messages. Give the caller a request ID and a support-safe explanation. Operators can use a protected trace view for details, while customers receive the minimum information needed to correct or recover.

Test the taxonomy as a contract. Create fixtures for malformed requests, unsupported parameters, expired credentials, tenant limits, provider 429s, provider 5xx responses, DNS failures, timeouts before and after acceptance, invalid model output, policy blocks, stream interruptions, and duplicate webhooks. Assert the public code, status, retry hint, headers, trace fields, and billing behavior. A taxonomy that exists only in a document will drift as adapters evolve.

Measure errors by user-visible outcome. Track error rate by stable code, endpoint, model route, provider, tenant tier, and client version. Separate prevented errors from unexpected failures, and show retries, fallback success, partial output, and eventual recovery. Alert on a sudden shift from invalid_request to provider_unavailable, a new unknown code, or a growing share of requests that end in an error after consuming provider work.

Version the taxonomy deliberately. Codes should remain stable long enough for SDKs and applications to depend on them. Add fields compatibly, document new categories, and provide a mapping for old provider-specific errors. Avoid exposing raw provider codes as your public API because providers change wording, status conventions, and retry semantics. The gateway's value is translating those differences into predictable behavior.

The practical lesson is simple: errors are part of the API product, not leftovers from the happy path. Separate transport from operation failure, return stable codes, classify the next safe action, preserve the internal chain, understand provider certainty, and test streaming and asynchronous boundaries. When every failure tells the client what to do next, the gateway becomes easier to integrate and much easier to operate.

That is it for today. Make failures legible, make retries safe, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
