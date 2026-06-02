#!/usr/bin/env python3
from pathlib import Path
import html
root=Path('/root/.openclaw/workspace/podcast')
feed=root/'feed.xml'
s=feed.read_text()
item='''    <item><title>EP075: API Billing Is Product Infrastructure</title><description>API billing is no longer just an accounting detail. This episode explains why Anthropic and Claude API cost depends on payload design, long context, output length, retries, agent loops, and fallback strategy — and why production teams should measure cost per successful task instead of raw token price.</description><pubDate>Tue, 02 Jun 2026 10:30:00 +0000</pubDate><enclosure url="https://xujfcn.github.io/podcast/audio/ep075.mp3" length="8049165" type="audio/mpeg" /><guid>https://xujfcn.github.io/podcast/audio/ep075.mp3</guid><itunes:duration>6:42</itunes:duration><itunes:episode>75</itunes:episode><itunes:episodeType>full</itunes:episodeType><itunes:explicit>false</itunes:explicit><link>https://crazyrouter.com?utm_source=rss&amp;utm_medium=podcast</link></item>
'''
if 'EP075: API Billing Is Product Infrastructure' not in s:
    marker='    <item><title>EP074:'
    idx=s.index(marker)
    s=s[:idx]+item+s[idx:]
    feed.write_text(s)
print('feed_has_ep075', 'EP075: API Billing Is Product Infrastructure' in feed.read_text())
