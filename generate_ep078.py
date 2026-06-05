import re, json, subprocess, time
from pathlib import Path
import requests
import xml.etree.ElementTree as ET

root = Path('/tmp/podcast')
(root/'episodes').mkdir(exist_ok=True)
(root/'audio').mkdir(exist_ok=True)

title = 'EP078: One-Click Configuration Is Developer Onboarding Infrastructure'
desc = 'One-click setup scripts are more than convenience. This episode explains how WorkBuddy-style custom model configuration, local models.json files, Base URL normalization, backups, API key handling, and troubleshooting checklists turn fragile AI tool setup into repeatable developer onboarding infrastructure.'
pub = 'Fri, 05 Jun 2026 12:25:00 +0000'
script = '''Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today’s episode is about one-click configuration scripts, and why they matter more than they look.

A setup script is not glamorous. It does not sound like model routing, agent orchestration, prompt engineering, or benchmark design. It sounds like a small utility: download this file, run this command, write a JSON config, restart the app.

But for developer tools, that small utility can be the difference between adoption and churn.

Think about a desktop AI tool that supports custom models. The user wants to connect an OpenAI-compatible provider. In theory, the process is simple. They need an API key, a Base URL, a model name, and a few capability flags. In practice, there are many small places to fail.

The config file might be in a hidden user directory. The JSON structure might be an array. The URL might need slash v one. The model name must match exactly. The API key must be local and valid. The app might need a full restart. Existing custom models should not be destroyed. The old config should be backed up. Duplicate model IDs should be updated instead of appended again and again.

None of these problems are intellectually difficult. But each one creates friction.

And friction during onboarding is expensive.

When a developer is trying a new AI tool, they are usually evaluating trust. Does this thing work? Is it understandable? If it breaks, can I recover? Does it respect my local files? Does it leak my key? Can I inspect what changed?

A good one-click configuration script answers those questions through behavior.

It creates the directory if it does not exist. It reads the existing config before writing. It makes a timestamped backup. It normalizes the Base URL. It accepts an API key from an environment variable, but can also prompt securely. It deduplicates model IDs. It preserves unrelated custom models. It prints exactly what it changed. It tells the user to restart the app.

That is not just scripting. That is developer experience design.

Let’s use a concrete example: configuring WorkBuddy custom models.

WorkBuddy can read local model configuration from a models dot json file under the user profile. That file can define custom models with fields like id, name, vendor, url, api key, supports tool call, supports images, supports reasoning, and whether to use a custom protocol.

A manual configuration guide can explain those fields, and it should. But many users do not want to become experts in the config file before they can try the tool. They want a safe path to a working setup.

That is where a PowerShell setup script fits.

The script can take a base URL like https://cn.crazyrouter.com and normalize it to https://cn.crazyrouter.com slash v one. It can write several model entries at once. It can support a default model list, while still allowing users to override the list with parameters. It can create a backup before touching the existing file. It can offer a replace mode for users who want to clean up older entries.

The important point is not that every team should use the same script. The important point is that every developer tool should think this way.

A configuration workflow has a life cycle.

First, there is discovery. The user needs to know where the config lives and what the settings mean.

Second, there is execution. The user needs a command or interface that creates a valid config.

Third, there is verification. The user needs to know what changed and what to do next.

Fourth, there is recovery. The user needs a backup path if something goes wrong.

Fifth, there is troubleshooting. The user needs a checklist for the common failures: wrong key, wrong URL, missing slash v one, invalid model ID, app not restarted, malformed JSON, duplicate entries, or unsupported model capabilities.

Most onboarding content only covers the second step. It gives a command. But a real onboarding system covers all five.

This is especially important for OpenAI-compatible APIs.

The phrase OpenAI-compatible sounds simple, but it hides several assumptions. Does the client expect the Base URL to include slash v one? Does the endpoint path get appended by the SDK? Does the tool use the exact URL or rewrite it? Does the model support tools? Does it support images? Does it support reasoning flags? Does the provider accept the same payload shape?

A one-click script cannot solve every compatibility difference, but it can eliminate the basic configuration mistakes.

That creates two kinds of value.

The first is immediate user value. The user spends less time editing JSON and more time using the tool.

The second is support value. The support team receives fewer repetitive setup questions. And when a user does run into an issue, the support team can ask: did the script run successfully, where is the backup, what model ID was written, what Base URL was normalized, and did WorkBuddy restart?

This turns a vague support conversation into a structured debugging path.

There is also a content strategy lesson here.

A setup script should not be promoted only with a GitHub README. It needs a small content system around it.

You want a beginner guide: how custom model configuration works.

You want a troubleshooting guide: what to check when the model does not appear.

You want a script walkthrough: how the PowerShell code handles backups, deduplication, Base URL normalization, and local API key storage.

You want a security explanation: what the script reads, what it writes, and what it does not upload.

You want a platform-specific version for stricter developer communities, where the article focuses on local configuration and PowerShell automation rather than sounding like an advertisement.

And you want a more direct version for channels where it is acceptable to include the actual endpoint and the exact integration guide.

That is how you promote a small developer utility without making it feel like a sales pitch.

The principle is simple: lead with the user’s configuration problem, then show the script as the solution.

Do not start with “use our service.” Start with “here is why WorkBuddy custom model config breaks, here is the file, here are the fields, here are the failure modes, and here is a script that automates the safe path.”

This approach works because it respects the developer.

Developers do not mind tools being useful. They mind being marketed to before their problem is understood.

A good setup script also needs transparency. If it is a PowerShell script, users should be able to open the raw file and read it. The README should show what file will be modified. It should state that the API key is written locally. It should explain how to run the script after downloading it, not only through a pipe to execution. It should document backup and restore.

That transparency builds trust.

For AI tools, trust is not optional. Users are pasting keys, connecting models, and letting agents interact with local files. Even when the script is harmless, the user needs to understand it.

So the best one-click setup is not just one click. It is inspectable one click.

One command for convenience. Source code for review. Parameters for customization. Backups for safety. Troubleshooting docs for recovery.

That is the standard we should expect from AI developer tooling.

If you are building an AI product, look for places where users keep asking the same setup question. That question might be hiding a script opportunity.

If users keep asking where the config file is, create the file for them.

If users keep forgetting slash v one, normalize the URL.

If users keep duplicating model entries, deduplicate by model ID.

If users fear breaking their setup, create a backup before writing.

If users wonder whether the key is uploaded, explain that it is local and make the script easy to inspect.

These are not minor details. They are the practical edge of developer experience.

In AI infrastructure, model quality matters. Pricing matters. Latency matters. But before any of that matters, the first request has to work.

One-click configuration helps that first request happen.

And when the first request works, the user has momentum.

That’s it for today. Thanks for listening to AI Dev Tools — The Crazyrouter Podcast. If you are building AI tools, do not underestimate setup scripts. They are not just automation. They are onboarding infrastructure.'''

(root/'episodes/ep078_script.txt').write_text(script, encoding='utf-8')
(root/'episodes/ep078.md').write_text(f'# {title}\n\n{desc}\n', encoding='utf-8')

# Get Crazyrouter key from workspace TOOLS.md
text = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
m = re.search(r'Authorization: Bearer ([^"\s]+)', text) or re.search(r'Bearer\s+(sk-[A-Za-z0-9_\-]+)', text)
if not m:
    raise SystemExit('Crazyrouter API key not found')
key = m.group(1)

paras = script.split('\n\n')
n = len(paras)
parts = ['\n\n'.join(paras[:n//3]), '\n\n'.join(paras[n//3:2*n//3]), '\n\n'.join(paras[2*n//3:])]
for i, part in enumerate(parts, 1):
    r = requests.post(
        'https://crazyrouter.com/v1/audio/speech',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
        timeout=300,
    )
    print('part', i, r.status_code, r.headers.get('content-type'), len(r.content), flush=True)
    if not r.ok:
        print(r.text[:1000]); r.raise_for_status()
    (root/f'episodes/ep078_part{i}.mp3').write_bytes(r.content)

concat = root/'episodes/ep078_concat.txt'
concat.write_text("file 'ep078_part1.mp3'\nfile 'ep078_part2.mp3'\nfile 'ep078_part3.mp3'\n", encoding='utf-8')
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(root/'audio/ep078.mp3')], check=True)

# probe duration
try:
    pr = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(root/'audio/ep078.mp3')], capture_output=True, text=True, check=True)
    sec = float(json.loads(pr.stdout)['format']['duration'])
    dur = f'{int(sec//60)}:{int(sec%60):02d}'
except Exception:
    dur = '8:00'
size = (root/'audio/ep078.mp3').stat().st_size

# update feed
ET.register_namespace('atom','http://www.w3.org/2005/Atom')
ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')
feed = root/'feed.xml'
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
# remove existing if any to avoid dup
for existing in list(channel.findall('item')):
    if (existing.findtext('title') or '').startswith('EP078:'):
        channel.remove(existing)
item = ET.Element('item')
ET.SubElement(item,'title').text = title
ET.SubElement(item,'description').text = desc
ET.SubElement(item,'pubDate').text = pub
enc = ET.SubElement(item,'enclosure')
enc.set('url','https://xujfcn.github.io/podcast/audio/ep078.mp3')
enc.set('length',str(size))
enc.set('type','audio/mpeg')
ET.SubElement(item,'guid').text = 'https://xujfcn.github.io/podcast/audio/ep078.mp3'
ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = dur
ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episode').text = '78'
ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType').text = 'full'
ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'
ET.SubElement(item,'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast'
items = list(channel.findall('item'))
if items:
    channel.insert(list(channel).index(items[0]), item)
else:
    channel.append(item)
tree.write(feed, encoding='utf-8', xml_declaration=True)
print('EP078 ready', size, dur, flush=True)
