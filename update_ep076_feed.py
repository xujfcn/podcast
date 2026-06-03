#!/usr/bin/env python3
from pathlib import Path
root=Path('/root/.openclaw/workspace/podcast')
feed=root/'feed.xml'
s=feed.read_text()
item='''    <item><title>EP076: Dynamic Workflows for AI Coding Agents</title><description>Dynamic workflows are changing AI coding from one long agent chat into structured orchestration. This episode explains planner, implementer, adversarial reviewer, and verifier packets; why ultracode-style workflows can get expensive; and how model routing through an API gateway helps teams control cost, latency, and evidence.</description><pubDate>Wed, 03 Jun 2026 09:45:00 +0000</pubDate><enclosure url="https://xujfcn.github.io/podcast/audio/ep076.mp3" length="9091725" type="audio/mpeg" /><guid>https://xujfcn.github.io/podcast/audio/ep076.mp3</guid><itunes:duration>7:34</itunes:duration><itunes:episode>76</itunes:episode><itunes:episodeType>full</itunes:episodeType><itunes:explicit>false</itunes:explicit><link>https://crazyrouter.com?utm_source=rss&amp;utm_medium=podcast</link></item>
'''
if 'EP076: Dynamic Workflows for AI Coding Agents' not in s:
    marker='    <item><title>EP075:'
    idx=s.index(marker)
    s=s[:idx]+item+s[idx:]
    feed.write_text(s)
print('feed_has_ep076', 'EP076: Dynamic Workflows for AI Coding Agents' in feed.read_text())
