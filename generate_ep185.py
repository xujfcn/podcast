from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 185
title = 'EP185: AI API Quotas — Separate Fairness From Mere Rate Limits'
description = 'A practical guide to AI API quotas: separate requests from tokens and concurrency, allocate fair tenant budgets, handle bursts, prevent noisy neighbors, and make quota decisions visible and reversible.'
pub_date = 'Sun, 18 Oct 2026 08:30:00 +0000'
script = '''EP185: AI API Quotas — Separate Fairness From Mere Rate Limits

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Rate limits tell you how fast traffic may arrive. Quotas answer a different question: how much of a scarce resource may a customer, team, workflow, or model consume over a period of time? AI systems need both. Without quotas, one tenant can exhaust a shared budget, consume all provider capacity, or turn a short burst into a long outage for everyone else. Today we are building a quota system that is fair, measurable, and practical to operate.

Start by naming the resource. A request quota is easy to explain, but requests are not equal. One short classification call and one long generation can have very different token cost, latency, and provider impact. Track requests, input tokens, output tokens, estimated spend, concurrent executions, and queue occupancy separately. A tenant may be below its request limit while consuming most of the token budget. Another may use many small requests without creating much load. A useful policy makes the scarce unit explicit instead of hiding it behind one counter.

Keep quota, rate limit, and concurrency as separate controls. A rate limit protects a short time window, such as requests per second. A quota protects a longer allocation, such as tokens per day or dollars per month. A concurrency limit protects work in progress, especially long streaming generations. Combining these into one generic limit produces confusing behavior: a customer can be rejected even though it has budget, or accepted into a queue that it cannot drain. Return the control that actually blocked the request and include reset or retry information when it is safe to do so.

Choose the accounting boundary carefully. A quota can belong to an API key, user, project, organization, model, route, or billing account. Most real systems need a hierarchy. A project may have a daily token budget, each key may have a concurrency cap, and a premium workflow may reserve capacity from a separate pool. Enforce the narrowest applicable rule first, then check parent budgets. Record which rule denied the operation. This makes support conversations answerable and prevents a local key from bypassing an organization-wide limit.

Make reservations atomic. The gateway should estimate the maximum resource commitment before sending work upstream, reserve it, and settle the reservation when actual usage is known. For a streamed response, reserve an output ceiling and release unused capacity as tokens arrive or when the stream ends. For an image or video job, reserve the estimated job cost before submission. If reservation and dispatch are separate operations, two requests can both observe the same remaining budget and overspend it. Use an atomic store operation or a durable ledger with idempotent reservation IDs.

Do not pretend estimates are exact. Token counts can differ across providers, and final output length is unknown at admission time. Track estimated, reserved, actual, and billable usage as distinct values. Settle the difference after completion, then reconcile late provider usage reports. If the provider only exposes usage after a failure, keep the reservation until that event is accounted for. A quota system that rejects correctly but reports inaccurate consumption will eventually lose trust.

Design for bursts without allowing permanent hoarding. A simple fixed daily counter makes traffic at midnight and traffic at the end of the day behave strangely. A token bucket gives a customer a refill rate and a bounded burst capacity. A rolling window is easier to audit but can create boundary spikes. Pick the model that matches the product promise. Document whether unused burst capacity expires, whether quota carries over, and whether reserved capacity is returned after cancellation. These details affect customer behavior as much as the headline number.

Fairness is not the same as equal allocation. A production batch job may need more total tokens but can tolerate delay. An interactive chat may need low latency but only a small budget. Assign separate pools or priorities by workload class, then enforce per-tenant ceilings inside each pool. Use weighted fair queuing when several tenants share a constrained provider route. Avoid letting priority become a permanent bypass: premium traffic still needs a cap, and emergency traffic should have an explicit budget and an audit trail.

Protect against noisy neighbors at every layer. Tenant limits alone are not enough if all tenants share one provider connection pool, worker queue, or model semaphore. Partition queues and concurrency where practical. At minimum, account for tenant identity when selecting work from a shared queue, and apply a maximum service share. Measure queue wait, service time, rejection rate, and provider throttling by tenant and workload. A quota policy is failing if the counters look fair while one customer experiences all the latency.

Be precise about what happens when a quota is nearly exhausted. The gateway can reject immediately, allow a small overdraft, downgrade to a cheaper model, queue for the next refill, or require explicit approval. The correct choice depends on the workflow. A user-facing chat may get a clear budget message and a smaller context limit. A background summarization job may wait. A billing-critical operation should not silently switch models. Never hide a downgrade behind a successful HTTP status; expose the selected route and policy decision in trace metadata and, where appropriate, a response header.

Retries and fallbacks must share the same logical budget. If an upstream timeout causes two retries and a provider fallback, charging only the successful attempt encourages accidental overspend. Group all attempts under one operation ID, reserve according to the policy, and set a maximum attempt and spend budget. A failed request may consume provider tokens even when the client receives an error. Reconcile that usage and distinguish customer-visible work from speculative or failed work in reporting.

Give customers useful visibility. Show current usage, remaining budget, reservation state, reset time, and the rule that would block the next request. For administrators, provide breakdowns by model, route, key, workflow, and time period. Alert on abnormal burn rate, repeated denials, reservation leaks, and large gaps between estimated and actual usage. A dashboard that only displays a daily percentage is not enough to explain why a request was rejected or why the budget disappeared.

Test the hard cases before enabling enforcement. Send simultaneous requests at the exact budget boundary. Crash the gateway after reservation but before dispatch. Disconnect a stream while tokens are arriving. Make the provider return usage late. Retry the same request with the same idempotency key. Change a tenant's plan while work is in flight. Verify that no reservation is counted twice, no released capacity becomes negative, and a restart can recover open reservations from durable state. Load-test with uneven tenants so fairness is measured under contention rather than assumed.

Version quota policy like an API contract. A change from requests to tokens can surprise clients even when the documented limit number increases. Publish effective dates, expose policy versions in administrative data, and give customers a migration window. Keep a dry-run mode that records what would have been denied before enforcement begins. Roll out by tenant or route, compare accepted-result rate and latency, and keep an emergency override with a strict audit log. A quota system should be reversible when its assumptions are wrong.

The practical lesson is simple: quotas are resource allocation, not just rejection counters. Separate requests, tokens, spend, and concurrency. Reserve atomically, settle against actual usage, make bursts bounded, isolate noisy neighbors, share budgets across retries, and tell operators exactly which rule made the decision. Fair AI API access comes from explicit accounting and visible policy, not from a single rate-limit number.

That is it for today. Allocate carefully, measure the real resource, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
