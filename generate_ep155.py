from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 155
title = 'EP155: AI API Local Development — Test Integrations Before Production'
description = 'A practical guide to local AI API development: use mock providers, replay fixtures, test failure paths, protect secrets, and promote integrations to production with confidence.'
pub_date = 'Sat, 12 Sep 2026 08:30:00 +0000'
script = '''EP155: AI API Local Development — Test Integrations Before Production

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI integrations are often tested against live providers from a developer laptop, which makes failures slow, expensive, and difficult to reproduce. A temporary rate limit looks like a code bug, a provider change looks like a flaky test, and a leaked key can become a security incident. Today we will build a safer local development workflow for AI APIs.

Start with a clear boundary between environments. Use separate credentials, projects, routes, and data for local, staging, and production. Never copy a production API key into a local environment just to make a test pass. A gateway such as Crazyrouter can provide one compatible API surface, while each environment receives its own restricted configuration.

Use mock providers for deterministic tests. Return fixed responses for common success cases, malformed JSON, empty content, tool errors, timeouts, rate limits, and provider failures. Mocks should reproduce the response shape and timing signals that application code depends on, not merely return a generic string. This lets developers test recovery paths without spending tokens.

Keep replay fixtures from real behavior. Capture sanitized requests and responses from representative workflows, including long inputs, edge cases, and historical incidents. Remove secrets, personal data, and proprietary content before committing fixtures. Version the fixtures with the prompt, schema, model, and route metadata so a failing replay has enough context to be useful.

Test the contract locally. Validate request construction, authentication headers, streaming events, structured outputs, error mapping, retries, cancellation, and usage accounting. Contract tests should fail when a client library or gateway changes an assumption. Do not wait for an end-to-end production-like test to discover that a field was renamed.

Simulate the unhappy path deliberately. Add latency, disconnects, partial streams, invalid credentials, 429 responses, context overflow, malformed output, and provider downtime. Verify bounded retries, clear user messages, circuit breakers, cleanup, and fallback behavior. A local test that only checks the happy path gives false confidence.

Make local state safe and repeatable. Use disposable databases, isolated queues, temporary files, and seeded test data. Give each test a unique tenant or namespace, and clean up after it. If the application stores prompts, outputs, or traces, ensure local retention is short and access is restricted.

Protect secrets and logs. Load credentials from a secret store or environment mechanism that is not committed to source control. Add pre-commit checks for key patterns, redact authorization headers and private content, and make debug logging opt-in. Local development is still part of the security boundary because laptops and shared logs can be compromised.

Use a small live smoke suite. Mocks cannot reveal provider availability, real tokenization, pricing, or capability differences. Run a limited authenticated test against an approved non-production route, with a strict budget and sanitized inputs. Keep it separate from ordinary unit tests and alert on unexpected cost or output changes.

Promote with evidence. Require contract tests, replay tests, failure-path tests, and a live smoke check before staging. Compare latency, accepted-result rate, retries, and cost against the previous integration. Record configuration versions and make the promotion reversible. Developers should know exactly what was tested before production traffic is enabled.

The practical lesson is simple: local AI development should be deterministic, private, and realistic enough to expose failure. Use mocks for speed, sanitized fixtures for coverage, small live tests for reality, and separate credentials for safety. That combination helps teams move quickly without turning every code change into an expensive production experiment.

That is it for today. Test the failure before the user finds it. Visit crazyrouter.com, and see you in the next episode.'''

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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep155'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
