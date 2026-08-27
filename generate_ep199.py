from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 199
title = 'EP199: AI API Failure Capsules — Make Intermittent Bugs Reproducible'
description = 'A practical guide to failure capsules for AI APIs: capture safe request fingerprints, routing decisions, timing, adapter versions, and replayable evidence so developers can diagnose intermittent failures without exposing sensitive prompts.'
pub_date = 'Thu, 27 Aug 2026 16:15:00 +0000'
script = '''EP199: AI API Failure Capsules — Make Intermittent Bugs Reproducible

Welcome back to AI Dev Tools — The Crazyrouter Podcast. The hardest AI API bug is often the one that disappears when an engineer tries to reproduce it. A request times out only for one tenant. A stream ends without a final event. A structured response fails validation after a route changes. Support receives a screenshot, a timestamp, and the sentence, “It happened again.” Today we are talking about failure capsules: compact, privacy-aware evidence packages that turn intermittent gateway failures into something developers can inspect and replay.

A failure capsule is not a giant log export. It is a deliberately assembled record of one request lifecycle. It connects what the client attempted, what the gateway decided, what each upstream hop observed, and how the request finally ended. The capsule should be addressable by a trace identifier that developers can safely share with support. The goal is to preserve enough evidence to explain behavior without copying every prompt, response, header, or secret.

Begin with a stable request fingerprint. Record the endpoint, contract version, requested model or capability, streaming mode, tool and schema identifiers, input size, and a hash of the canonical request shape. Do not put raw authorization headers in the capsule. Do not assume prompts are safe merely because they came from a test environment. Capture content only under an explicit retention policy, and prefer hashes, lengths, classifications, and redacted samples when the full text is unnecessary.

Next, record the routing decision as a sequence, not just the final provider. A useful capsule explains which routes were eligible, which were excluded, the policy version used, the chosen region, and whether a retry or fallback occurred. It should show machine-readable reason codes such as capability mismatch, quota protection, health score, residency rule, or deadline remaining. Without those reasons, an engineer sees where traffic went but cannot tell why it went there.

Time must be represented as a lifecycle. Capture when the gateway accepted the request, completed admission checks, selected a route, opened the upstream connection, received headers, delivered the first token, observed the last token, validated the result, and closed the client stream. Use one consistent clock for durations and include wall-clock time only for correlation. This distinguishes provider latency from queueing, gateway work, validation, and slow client delivery.

Streaming requests need an event summary. Storing every token is usually unnecessary and may expose user data. Instead, record event counts, byte counts, sequence gaps, first and last event types, finish markers, cancellation signals, and the point where an error appeared. If a client reports a truncated answer, the capsule should reveal whether the provider stopped, the gateway lost an event, the client disconnected, or the output hit a configured limit.

Capture the exact software and configuration identity involved. Include the gateway release, adapter version, routing-policy revision, capability-registry revision, model identifier returned by the provider, and relevant feature flags. Avoid dumping the entire environment. The important question is whether engineers can recreate the decision boundary that existed at that moment. A bug that cannot be tied to deployed state will keep turning into guesswork.

Errors should retain their causal chain. A client may receive a stable gateway code, but the capsule can safely connect that code to an upstream status, transport failure, parser exception, validation result, or deadline owner. Mark which layer generated the terminal error and whether any partial output had already been sent. This prevents a generic timeout label from hiding the difference between a provider timeout, an exhausted gateway deadline, and a client cancellation.

Cost and usage evidence belongs in the capsule too. Record input and output units reported by each attempt, whether values are measured or estimated, which attempts were billable, and whether reconciliation is pending. When fallback occurs, developers need to understand both reliability and spend. A request that eventually succeeds may still reveal duplicated work, an expensive repair pass, or usage that never reached the customer ledger.

Design replay in levels. Level one replays only the gateway decision using metadata and synthetic content. Level two sends a redacted fixture through adapters in a non-billable test harness. Level three, available only under strict authorization, replays retained content against an isolated provider route. Default to the least sensitive level that can test the hypothesis. Every replay must use new idempotency keys and disable external tool side effects unless a dedicated simulator is present.

Make capsule creation cheap and selective. Generate a minimal capsule for every failed request, then enrich it for sampled successes, important tenants, new releases, or suspicious patterns. Success capsules are essential because diagnosis requires a baseline. Comparing one failure against similar successful requests often exposes the relevant difference faster than reading the failed trace alone.

Give developers access without giving them a data leak. A dashboard should show a concise timeline, route reasons, version identities, safe error details, and a downloadable redacted artifact. Apply tenant isolation, short retention, audit access, and field-level redaction before storage. If raw content is separately retained, keep it behind stronger authorization and never embed it in a support URL.

Test the capsule system before incidents. Inject upstream timeouts, malformed streaming events, quota rejection, route changes, validation failures, client cancellation, and partial tool calls. Verify that each capsule identifies the responsible layer and contains enough information for a replay. Also test redaction with secrets hidden in prompts, tool arguments, metadata, and unusual headers. Diagnostic tooling that leaks credentials is a second incident waiting to happen.

Measure whether capsules improve operations. Track the percentage of failures with complete evidence, time from report to owning component, reproduction rate, support escalations, and incidents closed without requesting raw customer data. Review fields that engineers never use and remove them. Add fields only when a real investigation proves they would shorten diagnosis. A failure capsule should remain focused evidence, not become an accidental data warehouse.

The practical lesson is simple: intermittent AI API bugs become manageable when every request can leave behind a safe, connected explanation. Fingerprint the request, preserve routing reasons, build a precise lifecycle, summarize streams, pin software versions, retain causal errors, reconcile usage, and support controlled replay. That gives developers something far more useful than “please try again”: a path from one failed request to a reproducible cause.

That is it for today. Make failures explainable, keep customer data protected, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one dependable API gateway.'''

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script)
parts = script.split('\n\n')
for i, part in enumerate(parts, 1):
    subprocess.run(['edge-tts', '--voice', 'en-US-GuyNeural', '--text', part, '--write-media', str(root / f'episodes/ep{ep:03d}_chunk{i}.mp3')], check=True)
concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file 'ep{ep:03d}_chunk{i}.mp3'\n" for i in range(1, len(parts) + 1)))
audio = root / f'audio/ep{ep:03d}.mp3'
subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c:a', 'libmp3lame', '-q:a', '4', str(audio)], check=True)
seconds = float(json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True).stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
feed = root / 'feed.xml'
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in channel.findall('item')):
    item = ET.Element('item')
    for tag, value in [('title', title), ('description', description), ('pubDate', pub_date)]:
        ET.SubElement(item, tag).text = value
    enc = ET.SubElement(item, 'enclosure')
    enc.attrib.update(url=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3', length=str(audio.stat().st_size), type='audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    for tag, value in [('duration', duration), ('episode', str(ep)), ('episodeType', 'full'), ('explicit', 'false')]:
        ET.SubElement(item, f'{{{ns}}}{tag}').text = value
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep}'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {audio.stat().st_size} bytes {duration} {len(parts)} chunks')
