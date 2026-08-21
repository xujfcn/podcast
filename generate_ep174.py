from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 174
title = 'EP174: MCP at the AI Gateway — Ship Useful Tools Without Shipping a Security Incident'
description = 'A practical guide to putting Model Context Protocol tools behind an AI API gateway: capability discovery, least privilege, approval boundaries, tenant isolation, observability, and safe rollout.'
pub_date = 'Thu, 01 Oct 2026 08:30:00 +0000'
script = '''EP174: MCP at the AI Gateway — Ship Useful Tools Without Shipping a Security Incident

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Tool-using models are moving from demos into real workflows, and the Model Context Protocol is making it easier to connect them to files, databases, SaaS APIs, and internal services. Today we will look at the part that gets less attention: how an AI API gateway can make MCP useful without turning every prompt into an unreviewed production action.

Start with a clear trust boundary. An MCP server is not just another model endpoint. It exposes capabilities, and some of those capabilities can read private data, change state, or trigger an external side effect. Put the gateway between the model and the tool server so authentication, policy, routing, logging, and rate limits have one consistent enforcement point.

Discover capabilities, but do not automatically trust them. At connection time, record the server identity, tool names, input schemas, resource patterns, and declared annotations. Compare that inventory with an allowlist owned by the application. A tool named “search” may be read-only, while a tool named “send” or “update” needs a much higher level of scrutiny. Names are clues, not authorization.

Apply least privilege at three layers. Give the model only the tools needed for the current task. Give the tool server credentials scoped to the specific tenant and resources. Give the gateway a policy that limits methods, records, fields, destinations, and request rates. If one layer fails open, the other layers should still prevent a broad data read or dangerous write.

Separate planning from execution. It is reasonable for a model to draft an email, propose a database update, or assemble a deployment plan. It is a different decision to execute it. Mark tools as read, propose, or commit operations, and require an explicit approval step for the last category. The approval should show the normalized arguments and the target, not merely repeat the model’s natural-language explanation.

Treat tool arguments as untrusted input. Validate them against the schema, then apply semantic checks. A valid path can still escape an allowed directory. A valid account identifier can belong to another tenant. A valid URL can point to an internal network. Normalize first, authorize second, and reject ambiguous values instead of guessing.

Design for tenant isolation from the beginning. Never let the model choose a tenant ID as the only boundary. Derive tenant context from the authenticated caller, bind it to the gateway session, and pass it to the tool server through a trusted channel. Log the decision without logging secrets or unnecessary customer content. Test cross-tenant reads and writes as first-class negative cases.

Put budgets around tools. Limit the number of tool calls per turn, the total execution time, response bytes, pagination depth, and retry count. A model can get stuck in a loop even when every individual call is valid. The gateway should stop runaway plans, return a clear reason, and preserve enough trace data for an engineer to understand what happened.

Be deliberate about prompt injection. Tool output is data, not instructions. A document, web page, ticket, or database row may contain text that tells the model to ignore policy or exfiltrate information. Label tool results as untrusted, keep system policy outside the tool-returned text, and require the gateway to enforce authorization independently of whatever the model says next.

Make observability useful and safe. Capture request ID, authenticated principal, model route, MCP server, tool name, policy decision, latency, status, and a redacted argument fingerprint. Trace the plan from model response to tool call to result, but use field-level redaction and short retention for sensitive payloads. Metrics should answer whether tools are reliable and whether policy is working, not become a second data lake.

Handle failures consistently. Translate tool-server timeouts, unavailable resources, invalid arguments, permission denials, and policy blocks into stable gateway errors. Retry only idempotent operations with an explicit budget. Never automatically retry a non-idempotent write unless the tool provides a safe idempotency key. A fallback model should not silently repeat a side effect that may already have succeeded.

Roll out new MCP servers like production dependencies. Start with a private test tenant and read-only tools. Replay a redacted fixture set, then run shadow plans that do not execute writes. Canary a small percentage of traffic, watch denial rates, tool latency, output size, and unexpected destinations, and define rollback thresholds before enabling more users. Version the server and tool schemas so a change is reviewable.

Test the dangerous paths, not just the happy path. Include malformed arguments, oversized results, pagination loops, revoked credentials, expired approvals, duplicate requests, tool output containing prompt injection, and a server that advertises a new capability unexpectedly. Verify that a cancelled model request cancels downstream work, and that an approval for one normalized action cannot be replayed against another target.

The gateway is most valuable when it turns these expectations into executable policy. Keep tool manifests, risk classes, schemas, approval rules, and audit requirements in version control. Let teams move quickly inside a safe default, while making exceptional access visible and deliberate. MCP can become a common interface for tools without becoming a common bypass around security.

The practical lesson is simple: connect models to tools through a boundary you can inspect and enforce. Discover capabilities, authorize narrowly, separate planning from execution, isolate tenants, budget calls, redact traces, and test failure modes before opening the connection to production.

That is it for today. Make the useful action easy to approve and the dangerous action hard to hide, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep174'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
