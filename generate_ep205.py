from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 205
title = 'EP205: AI API Gateway Circuit Breakers - Stop Provider Failures From Becoming Your Outage'
description = 'A practical guide to circuit breakers for AI API gateways: isolate failing providers, choose useful failure signals, protect streaming requests, coordinate fallbacks, and recover gradually without creating a second incident.'
pub_date = 'Thu, 27 Aug 2026 22:45:00 +0000'
script = '''EP205: AI API Gateway Circuit Breakers - Stop Provider Failures From Becoming Your Outage

Welcome back to AI Dev Tools - The Crazyrouter Podcast. When an upstream AI provider becomes slow or starts returning errors, the obvious response is to try again. But if every request retries against the same unhealthy provider, the gateway can turn a provider problem into an application-wide outage. Today we are talking about circuit breakers for AI API gateways: how to stop spending capacity on a route that is failing, protect healthy traffic, and recover without creating a second incident.

A circuit breaker is a small state machine around a dependency. In the closed state, requests flow normally. In the open state, the gateway rejects or redirects requests without calling the unhealthy upstream. After a quiet period, the breaker enters a half-open state and permits a small number of probes. A successful probe can close the breaker. Failed probes keep it open. The pattern is simple, but AI APIs make the policy more nuanced because requests differ in model, workload, token cost, streaming behavior, and business value.

Start with the boundary. A single global breaker for an entire provider is usually too coarse. One provider may serve several models across multiple regions, and one broken model or region should not take all of them out of service. At the other extreme, a breaker per individual request is meaningless because it has no shared evidence. A useful scope is a route key such as provider, model, region, protocol, and workload class. Add tenant or product dimensions only when the traffic is genuinely isolated and the sample size supports a decision.

Next, define what counts as a failure. Transport failures are the easy examples: connection refusal, DNS errors, TLS failures, and upstream timeouts. HTTP five hundred responses and explicit rate limits may also count, but they do not all imply the same recovery behavior. A rate limit can mean a local capacity problem, while a provider-wide outage may require a longer pause. Preserve the original error class even when the breaker uses a common failure signal. Operators need to know whether the breaker opened because of overload, authentication, a bad request, or an actual dependency failure.

Do not count every unsuccessful request equally. A four hundred response caused by an invalid client payload should not make the provider look unhealthy. A content policy refusal may be valid provider behavior. A schema validation failure may indicate a model capability mismatch rather than a transport outage. Classify errors by retryability, ownership, and dependency health. Only failures that tell you something about the route's ability to serve valid work should affect its circuit.

Use a rolling window, not a single threshold over all history. The breaker needs enough recent observations to avoid opening because of one unlucky request, while still reacting before queues fill. Track both a minimum sample count and a failure threshold. For example, require a meaningful number of eligible calls, then open when the failure ratio or consecutive-failure limit is exceeded. A ratio alone is dangerous at low volume, and consecutive failures alone can overreact to a brief network flap. Keep the window time-based or bounded by count so old incidents cannot control today's routing.

Latency belongs in the decision too, but be precise about which latency. A provider that returns errors quickly is different from one that accepts work and stalls for thirty seconds. Track connect time, time to first token, inter-token gaps, and total completion time. For a streaming workload, a request that begins streaming and then goes silent can consume a connection and a concurrency slot even though it has not returned an HTTP error. A breaker policy should include timeouts and stall detection, otherwise the most expensive failure mode remains invisible.

Do not let the breaker fight the retry policy. Retries should be bounded by the original request deadline, and the breaker should see the outcome of an attempt with enough context to distinguish an immediate rejection from an upstream call. If each retry increments the failure counter, a single user request can dominate the window and open the circuit too quickly. If retries are completely hidden, the breaker may react too slowly to an incident. Record both attempt-level evidence and request-level outcome, then choose one consistent counting rule for the state machine.

Circuit opening is a traffic decision, not a health verdict for every request. When the circuit is open, fail fast with a stable gateway error or select an explicitly compatible fallback. Return a retryable signal and a correlation ID, but do not tell clients to retry immediately without a backoff. The response should make clear that the gateway did not spend another upstream attempt. This protects caller budgets and helps developers distinguish a deliberate admission decision from an unexplained provider error.

Fallbacks need their own protection. If provider A opens and all traffic moves to provider B, provider B can become the next failure. Give every fallback route an independent breaker and capacity limit. Define a fallback chain with a maximum number of hops, and carry the original deadline across the chain. A fallback that gets a fresh timeout is not resilience; it is a way to keep the user waiting after the contract has already expired. Also verify capability compatibility before switching. A route that cannot stream, call tools, or produce the required schema is not a valid substitute just because it is available.

Streaming requests require a special transition policy. If the circuit opens before the first token, the gateway can often return a normal fast failure or route elsewhere. If a stream has already delivered partial output, switching providers mid-response can corrupt the contract and duplicate content. Usually the correct action is to terminate honestly with a machine-readable partial result and record the incomplete attempt. Only workflows designed for resumable generation should attempt continuation, and they need an explicit continuation token or prefix contract. The breaker protects future calls; it cannot repair a stream that has already been sent.

Half-open recovery must be conservative. After the cool-down, allow a small number of probes rather than releasing the entire backlog. Prefer cheap, representative requests that exercise the same protocol and capability as real traffic. A health endpoint can be green while long structured generations are still failing. Give probes a separate concurrency budget and prevent multiple gateway instances from turning half-open into a thundering herd. In a distributed gateway, share breaker state or use an approach that tolerates some local disagreement without flooding the provider.

Recovery should require more than one lucky success. Close the circuit after a bounded sequence of representative probes succeeds, or gradually restore a small traffic percentage and watch the result. If the first recovered requests are slow or malformed, return to open immediately. Add hysteresis so the breaker does not flap between states around a threshold. The open duration can grow after repeated failures, with a maximum cap and an operator override that is audited. Manual force-close is useful during diagnosis, but it should not silently bypass capacity or authentication problems.

Make the breaker visible to developers and operators. Emit state transitions with route key, reason, window statistics, and configuration version. Track calls allowed, calls rejected by the breaker, fallback selections, probe results, time spent open, and user tasks affected. Break down metrics by provider, model, region, protocol, and workload class. A dashboard that only shows provider availability can miss the important question: did the gateway prevent a slow dependency from exhausting application concurrency?

Protect the control path. Breaker configuration is production policy, so version thresholds, cool-downs, probe limits, and route scopes. Validate changes before publishing them, and keep rollback fast. A threshold that is too sensitive causes unnecessary failovers and cost; one that is too permissive allows queues and retries to grow. Treat configuration changes as observable events and include the active version in traces. During an incident, operators should be able to answer which policy opened the circuit and why.

Test the state machine, not just the happy path. Inject connection failures, DNS errors, rate limits, slow first tokens, silent streaming gaps, malformed outputs, and failures after partial output. Verify that client errors do not open the circuit, that retries do not bypass the deadline, that fallback capacity is bounded, and that half-open probes do not stampede. Test several gateway instances at once, because distributed state and clock differences often change behavior. Also test recovery under real queue pressure: a breaker that works only when no work is waiting has not been proven.

There is an important limit. A circuit breaker cannot make an incompatible provider compatible, and it cannot replace capacity planning, deadlines, or good error classification. It is a fast isolation mechanism. Its value is that it stops a known-bad dependency from consuming more shared resources while giving the rest of the system a controlled path to continue. Combine it with admission control, bounded retries, capability-aware routing, and honest client errors.

The practical lesson is simple: open early enough to protect the system, scope the breaker narrowly enough to preserve healthy routes, count only meaningful dependency failures, and recover through measured probes. Carry deadlines through retries and fallbacks, treat streams as irreversible once output begins, and make every state transition explainable. For AI gateways, reliability is not just choosing a provider. It is deciding when to stop asking an unhealthy provider for one more chance.

That is it for today. Isolate failures, recover gradually, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one dependable API gateway.'''

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
