from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 160
title = 'EP160: Multi-Tenant AI APIs — Isolate Usage, Limits, and Reliability'
description = "A practical guide to multi-tenant AI APIs: isolate data, quotas, concurrency, cost, and observability so one customer cannot degrade another customer's experience."
pub_date = 'Thu, 17 Sep 2026 08:30:00 +0000'
script = '''EP160: Multi-Tenant AI APIs — Isolate Usage, Limits, and Reliability

Welcome back to AI Dev Tools — The Crazyrouter Podcast. An AI API can work perfectly for one team and still fail as a shared service. One customer sends unusually long prompts, another launches a batch job, and a third suddenly sees timeouts because all three are competing for the same provider capacity. Today we will design multi-tenant AI APIs that keep usage, limits, data, and reliability properly separated.

Start with a tenant identity that the application controls. Every request should carry a trusted tenant and principal context from authenticated middleware, not from a user-provided field inside the prompt or request body. Propagate that identity into authorization, routing, quotas, usage records, caches, traces, and support workflows.

Separate data by default. Enforce tenant scope before retrieval, cache lookup, file access, tool execution, and result delivery. Include tenant identity in keys and indexes where sharing is not explicitly allowed. Test cross-tenant reads, stale permissions, deleted users, and administrative access paths. A shared model endpoint does not justify shared application state.

Design quotas at multiple levels. Requests per minute, tokens per minute, concurrent generations, storage, batch jobs, and daily spend are different resources. Set limits by tenant, user, API key, product, and priority where the product requires it. Return clear status and retry guidance when a limit is reached instead of turning every rejection into a mysterious provider error.

Protect concurrency. A tenant with many long-running streams or tool loops can consume capacity even when request counts look normal. Use weighted concurrency, queue limits, deadlines, and separate pools for interactive and background work. A gateway such as Crazyrouter can centralize provider access while application policy ensures one tenant cannot starve the others.

Make fairness explicit. Define whether limits are strict, burstable, weighted by plan, or shared across a team. Reserve capacity for interactive requests and high-priority workflows. Document what happens during provider degradation: queue, reduce output, switch to an approved route, or reject low-priority work. Fairness is easier to operate when the policy is visible before an incident.

Attribute cost accurately. Record tenant, feature, model, route, input and output tokens, retries, fallbacks, cached usage, and accepted-result status. Separate platform overhead from customer usage. Report cost per accepted outcome when raw token totals would mislead, and make adjustments for shared infrastructure explainable.

Keep keys and permissions isolated. Use separate credentials or scoped API keys where possible, rotate them independently, and make revocation tenant-specific. Do not let a customer-selected model name bypass the approved route, region, data policy, or budget. Administrative support tools should have audited access and should not inherit ordinary customer permissions.

Make observability tenant-aware without leaking tenants. Operators need to see which tenant is throttled, failing, or generating unusual spend, but one customer must not see another customer's prompts, traces, or usage details. Redact sensitive content, aggregate dashboards where appropriate, and enforce access on both raw traces and derived reports.

Handle noisy neighbors and abuse. Detect sudden prompt growth, repeated retries, key sharing, long-lived streams, and tool-call loops. Apply progressive controls such as warnings, temporary throttling, route restrictions, or manual review. Keep the response proportional and preserve a path for legitimate customers to recover from accidental overuse.

Test isolation under load. Run concurrent tenants with different prompt sizes, priorities, failure rates, and batch behavior. Verify that one tenant's quota, cache, queue, fallback, or outage does not silently change another tenant's results. Measure per-tenant latency, accepted-result rate, error rate, throttling, and cost during the test.

The practical lesson is simple: multi-tenancy is a reliability boundary, not just a billing field. Authenticate tenant identity, isolate data, budget every scarce resource, enforce fair concurrency, attribute cost, protect observability, and test noisy-neighbor behavior. With those controls, a shared AI API can scale without making every customer absorb someone else's workload.

That is it for today. Share the infrastructure, not the blast radius. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep160'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
