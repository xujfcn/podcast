from pathlib import Path
import re, requests, subprocess, json, xml.etree.ElementTree as ET
from email.utils import formatdate
from datetime import datetime, timezone

root = Path('/root/.openclaw/workspace/podcast')
(root/'episodes').mkdir(exist_ok=True)
(root/'audio').mkdir(exist_ok=True)

script = """EP086: DeepSeek Rate Limits Are Not One Number

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about something that looks boring until it breaks production: DeepSeek rate limits.

Most teams want a single answer. What is the TPM? What is the RPM? How many requests can I send? But DeepSeek is a good example of why production AI infrastructure cannot treat rate limits as one clean number.

The official DeepSeek API currently describes its public limit mostly as account-level concurrency. For the current V4 family, deepseek-v4-pro is documented around five hundred concurrent requests per account, and deepseek-v4-flash around twenty five hundred concurrent requests per account. That is not the same thing as tokens per minute. It means a request occupies one slot from the moment it is sent until the model finishes responding.

That detail matters. A short non-streaming request and a long reasoning request do not consume the same amount of time. If your app sends many slow prompts, concurrency becomes the real bottleneck. If your app sends many tiny prompts, request-per-minute and token-per-minute limits may matter more. But on the official DeepSeek API, the public planning number is concurrency, not a neat TPM table.

Now compare that with cloud platforms. Azure Foundry publishes a much more classic quota shape for DeepSeek R1 and DeepSeek V3: tokens per minute, requests per minute, and concurrent requests. The documented default is five million TPM, five thousand RPM, and three hundred concurrent requests for those DeepSeek models. That is easy to put into a router, easy to monitor, and easy to explain to customers.

Alibaba Cloud Model Studio uses another style. It publishes RPM and TPM by model, region, and sometimes by upstream supplier. Some DeepSeek routes are very generous, around ten thousand to fifteen thousand RPM with one point two million TPM. But other names that look similar can be much lower. For example, a dated R1 route can be only sixty RPM and one hundred thousand TPM. If your router only matches by the brand name DeepSeek, you will send traffic into the wrong pipe.

Tencent Cloud has a similar lesson. Its DeepSeek API can show a high account-level QPM, but individual models may have lower TPM. One model version can be fifteen thousand QPM but only three hundred thousand TPM. That is still useful, but it changes the workload it should receive.

AWS Bedrock adds another dimension. Bedrock quotas are managed per account, per region, and per model, with token usage controlled by service quotas. Some DeepSeek V3 class quotas are extremely high in public quota tables, but the usable value still depends on region availability, account approval, and whether the model is enabled for your account.

Google Cloud and other model-as-a-service platforms often require checking the actual project quota in the console. The public documentation may explain the quota system, but not always give a stable one-line number for every DeepSeek model. That means your production registry should support an unknown or console-confirmed state, not pretend every provider has equal data quality.

So what should a gateway do?

First, store limits as structured capacity, not prose. A useful provider registry should track request limit, input TPM, output TPM, total TPM, concurrency, region, account scope, and confidence level. DeepSeek official should be represented as a concurrency-limited provider. Azure should be represented as TPM plus RPM plus concurrency. Alibaba should be represented per model and per region. Tencent should separate QPM from TPM. AWS should carry service quota metadata.

Second, do not route purely by price. A cheaper model path with a tiny TPM can be worse than a more expensive path with stable capacity. The metric that matters is cost per successful task under load, including retries, queueing, throttling, and fallback.

Third, smooth traffic. Many platforms enforce not only minute-level RPM and TPM, but also second-level burst protection. If you send a sudden spike, you can get throttled even when your one-minute total looks safe. A gateway needs leaky-bucket scheduling, per-provider queues, and graceful fallback instead of just retrying everything at once.

Fourth, treat rate-limit errors as routing signals. A 429 should not simply fail the user. It should update provider health, reduce the temporary send rate, and move eligible traffic to another provider with compatible context length, output style, and price.

The big takeaway is simple: DeepSeek capacity is not a single number. It is a shape. Official DeepSeek exposes concurrency. Cloud providers expose TPM, RPM, QPM, and region-specific quotas. Production AI systems need to model that shape directly.

For developers building on top of multiple AI providers, this is exactly why API gateways matter. The user does not care whether the failure came from TPM, RPM, concurrency, or burst protection. They care whether the task completed. Good infrastructure turns provider-specific limits into reliable product behavior.

That is it for today. If you are building AI workflows, do not ask only, how cheap is this model? Ask: how much real work can this route finish per minute, and what happens when it gets crowded?

Thanks for listening to AI Dev Tools — The Crazyrouter Podcast. See you in the next episode."""

script_path = root/'episodes/ep086_script.txt'
script_path.write_text(script, encoding='utf-8')

text = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8', errors='ignore')
m = re.search(r'Authorization: Bearer ([^"\s]+)', text) or re.search(r'Bearer\s+(sk-[A-Za-z0-9_\-]+)', text)
if not m:
    raise SystemExit('Crazyrouter API key not found')
key = m.group(1)

paras = script.split('\n\n')
n = len(paras)
parts = ['\n\n'.join(paras[:n//3]), '\n\n'.join(paras[n//3:2*n//3]), '\n\n'.join(paras[2*n//3:])]
for i, part in enumerate(parts, 1):
    out = root/f'episodes/ep086_part{i}.mp3'
    if not out.exists() or out.stat().st_size < 1000:
        r = requests.post(
            'https://crazyrouter.com/v1/audio/speech',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
            timeout=300,
        )
        print('part', i, 'status', r.status_code, r.headers.get('content-type'), flush=True)
        if not r.ok:
            print(r.text[:1000])
            r.raise_for_status()
        out.write_bytes(r.content)
    print('saved', out, out.stat().st_size, flush=True)

concat = root/'episodes/ep086_concat.txt'
concat.write_text("file 'ep086_part1.mp3'\nfile 'ep086_part2.mp3'\nfile 'ep086_part3.mp3'\n", encoding='utf-8')
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(root/'audio/ep086.mp3')], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
audio = root/'audio/ep086.mp3'
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
    if (existing.findtext('title') or '').startswith('EP086:'):
        print('EP086 already in feed')
        break
else:
    item = ET.Element('item')
    ET.SubElement(item,'title').text = 'EP086: DeepSeek Rate Limits Are Not One Number'
    ET.SubElement(item,'description').text = 'A practical episode about DeepSeek official concurrency limits, cloud-provider TPM and RPM quotas, and why AI gateways need structured capacity routing instead of a single rate-limit number.'
    ET.SubElement(item,'pubDate').text = 'Tue, 16 Jun 2026 08:55:00 +0000'
    enc = ET.SubElement(item,'enclosure')
    enc.set('url','https://xujfcn.github.io/podcast/audio/ep086.mp3')
    enc.set('length',str(size))
    enc.set('type','audio/mpeg')
    ET.SubElement(item,'guid').text = 'https://xujfcn.github.io/podcast/audio/ep086.mp3'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = dur
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episode').text = '86'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType').text = 'full'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'
    ET.SubElement(item,'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep086'
    items = list(channel.findall('item'))
    if items:
        channel.insert(list(channel).index(items[0]), item)
    else:
        channel.append(item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
    print('inserted EP086', size, dur)

ET.parse(feed)
print('done', audio, size, dur)
