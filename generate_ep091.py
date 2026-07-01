from pathlib import Path
import re, requests, subprocess, json, xml.etree.ElementTree as ET
from email.utils import formatdate

root = Path('/root/.openclaw/workspace/podcast')
(root/'episodes').mkdir(exist_ok=True)
(root/'audio').mkdir(exist_ok=True)

ep = 91
title = 'EP091: Shipping New Claude Models Without Breaking Developer Workflows'
short_title = 'Shipping New Claude Models Without Breaking Developer Workflows'
description = 'A practical episode on launching new Claude-family models in an API gateway: model aliases, unified endpoints, token allowlists, docs language, test emails, request examples, and how to help developers try a new model without changing their whole stack.'
pub_date = 'Wed, 01 Jul 2026 09:50:00 +0000'

script = """EP091: Shipping New Claude Models Without Breaking Developer Workflows

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about a deceptively simple product update: adding a new Claude-family model to an API gateway, and announcing it in a way that helps developers actually use it.

When a new model becomes available, the obvious message is, “the model is live.” But for developers, that is only the headline. The real question is: can I use it with my current key, my current billing account, my current logging setup, and my current deployment process?

That is where API gateways matter. A good gateway reduces the number of moving parts between a developer and a new model. Instead of creating a separate provider account, adding a new payment method, rotating environment variables, and rewriting monitoring logic, the developer should be able to select a model name, send a request to the gateway endpoint, and inspect the result in the same console they already use.

But the wording around this matters. Some teams describe everything as “OpenAI-compatible.” That phrase can be useful when you are explaining request shapes, but it can also be confusing when the model itself is not from OpenAI. A better product message is often simpler: use your existing gateway key, call the unified gateway endpoint, and set the model field to the new model name.

That framing keeps the focus where it belongs. The developer does not need to think about the native provider account. They do not need to think about a separate key. They just need to know the exact endpoint, the exact model string, and any access-control details that could block the request.

For example, when announcing a model like claude-sonnet-5, the most useful information is concise: model name, endpoint, authentication method, and a short request example. If the platform supports token-level model allowlists, that should be mentioned clearly. Many real production errors are not caused by a broken model route. They are caused by a token that is not allowed to call the model yet.

This is a small detail, but it saves support time. A user sees the announcement, copies the model name, sends a request, and receives an authorization error. If the email already says, “if your API token uses a model allowlist, enable this model first,” the user has a path to fix it without opening a ticket.

There is another lesson here: product emails should be tested like product features. Send a test email first. Check the subject. Check the CTA. Check whether code blocks wrap badly on mobile. Check whether links include tracking parameters where humans click them, but never add tracking parameters to API endpoints inside code examples. A base URL in a code block should remain clean.

For AI infrastructure products, this distinction is important. Marketing links should have UTM parameters so growth teams can measure the campaign. API endpoints should not. Developers copy code examples directly. If a tracking parameter accidentally appears in a base URL or request path, you have turned measurement into a bug.

The same principle applies to claims. Avoid over-explaining provider internals in a launch email unless it helps the user. A new model announcement does not need a long essay about routing strategy. It needs to answer: what is new, how do I call it, what key do I use, where do I check logs, and what should I do if access fails?

There is also a docs implication. The pricing page, model list, and launch email should agree on the model string. The console should show the same name. If aliases exist, they should be intentional, documented, and stable. Model naming drift is one of the fastest ways to create confusion in developer tools.

In a mature gateway, every model launch should have a small checklist. First, verify the route with a real request. Second, confirm the model appears in the model list or pricing page. Third, test token permissions. Fourth, publish a short request example. Fifth, send a test email. Sixth, monitor logs after the announcement for common failures.

This is not bureaucracy. It is operational hygiene. Model launches happen quickly, especially in the current AI market. Without a repeatable checklist, teams can announce something that is technically available but hard for users to activate.

The best launch experience is boring in the right way. The user reads the email, copies the model name, sends a request, sees a response, and moves on. No new account. No surprise billing flow. No mysterious permission issue. No documentation mismatch.

That is the real value of a gateway in the model-launch cycle. It turns a fast-moving model ecosystem into something developers can consume predictably. And when the product copy is precise, the support burden goes down because users understand exactly what changed and exactly how to try it.

So the takeaway for today is simple. When shipping a new Claude model through a gateway, do not just say it is live. Give developers the stable path: existing key, unified endpoint, exact model name, clean code example, clear allowlist note, and a console link. That is how a model announcement becomes a usable developer workflow.

That is it for today. Thanks for listening to AI Dev Tools — The Crazyrouter Podcast. See you in the next episode."""

script_path = root/f'episodes/ep{ep:03d}_script.txt'
script_path.write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8', errors='ignore')
m = re.search(r'Bearer\s+(sk-[A-Za-z0-9_\-]+)', tools)
if not m:
    raise SystemExit('Crazyrouter API key not found')
key = m.group(1)

paras = script.split('\n\n')
n = len(paras)
parts = ['\n\n'.join(paras[:n//3]), '\n\n'.join(paras[n//3:2*n//3]), '\n\n'.join(paras[2*n//3:])]
for i, part in enumerate(parts, 1):
    out = root/f'episodes/ep{ep:03d}_part{i}.mp3'
    if not out.exists() or out.stat().st_size < 1000:
        r = requests.post(
            'https://crazyrouter.com/v1/audio/speech',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
            timeout=300,
        )
        print('part', i, 'status', r.status_code, r.headers.get('content-type'), flush=True)
        if not r.ok:
            print(r.text[:500])
            r.raise_for_status()
        out.write_bytes(r.content)
    print('saved', out.name, out.stat().st_size, flush=True)

concat = root/f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join([f"file 'ep{ep:03d}_part{i}.mp3'\n" for i in range(1,4)]), encoding='utf-8')
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(root/f'audio/ep{ep:03d}.mp3')], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
audio = root/f'audio/ep{ep:03d}.mp3'
size = audio.stat().st_size

try:
    r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)], capture_output=True, text=True, check=True)
    sec = float(json.loads(r.stdout)['format']['duration'])
    dur = f"{int(sec//60)}:{int(sec%60):02d}"
except Exception:
    dur = '6:00'

feed = root/'feed.xml'
ET.register_namespace('atom','http://www.w3.org/2005/Atom')
ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
for existing in channel.findall('item'):
    if (existing.findtext('title') or '').startswith(f'EP{ep:03d}:'):
        print(f'EP{ep:03d} already in feed')
        break
else:
    item = ET.Element('item')
    ET.SubElement(item,'title').text = title
    ET.SubElement(item,'description').text = description
    ET.SubElement(item,'pubDate').text = pub_date
    enc = ET.SubElement(item,'enclosure')
    enc.set('url',f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3')
    enc.set('length',str(size))
    enc.set('type','audio/mpeg')
    ET.SubElement(item,'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = dur
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episode').text = str(ep)
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType').text = 'full'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'
    ET.SubElement(item,'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'
    items = list(channel.findall('item'))
    if items:
        channel.insert(list(channel).index(items[0]), item)
    else:
        channel.append(item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
    print('inserted', f'EP{ep:03d}', size, dur)

ET.parse(feed)
print('done', audio, size, dur)
