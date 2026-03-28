# EP007: AI API Rate Limits — What Every Developer Needs to Know

## Script (~4 min, ~950 words)

**[INTRO]**

Hey, welcome back to AI Dev Tools — the Crazyrouter Podcast. I'm your host, and today we're tackling something that every developer hits at some point: rate limits. You're building your app, everything works perfectly in development, you deploy to production, real users show up — and suddenly you're getting 429 errors everywhere. Your app breaks. Your users are furious. And you're scrambling to figure out what went wrong.

Let's make sure that never happens to you.

**[WHAT ARE RATE LIMITS?]**

Rate limits are restrictions that API providers place on how many requests you can make in a given time window. Think of it like a highway with a speed limit — except instead of miles per hour, it's requests per minute, or tokens per minute, or requests per day.

Every major AI provider has them. OpenAI limits you based on your usage tier — a free tier developer might get 3 requests per minute on GPT-4o, while a Tier 5 customer gets 10,000. Anthropic uses a similar tier system. Google's Gemini API has both requests-per-minute and tokens-per-minute caps.

And here's the tricky part — rate limits aren't just about requests. Most providers track multiple dimensions simultaneously. You might be under your requests-per-minute limit but over your tokens-per-minute limit. Or you hit a daily token cap you didn't even know existed.

**[THE REAL-WORLD PAIN]**

Let me paint a picture. You're building a customer support chatbot. Works great with 10 test users. You launch, get featured on Hacker News, suddenly 500 people are chatting simultaneously. Each conversation is making 2-3 API calls — that's 1,500 requests hitting your backend at once.

If you're on OpenAI's Tier 1, you might only have 500 requests per minute for GPT-4o. Half your users get errors. Your app looks broken. The Hacker News thread turns from "cool product" to "this doesn't even work."

This happens more than you'd think. I've seen startups burn through their entire daily token budget in the first hour after a Product Hunt launch.

**[STRATEGIES THAT WORK]**

So how do you handle this? Five strategies.

First — implement exponential backoff with jitter. When you get a 429, don't immediately retry. Wait one second, then two, then four — with a random offset so all your retries don't hit at the same time. Most HTTP libraries have this built in. Use it.

Second — add a request queue. Instead of firing API calls the moment a user sends a message, put them in a queue with a rate limiter. Libraries like bottleneck for Node.js or ratelimit for Python make this trivial. You control exactly how many requests per second go out.

Third — cache aggressively. If 50 users ask "what's your return policy?", you don't need 50 separate API calls. Cache common responses. Even a 5-minute cache can cut your API calls by 60-70% for support chatbots.

Fourth — use streaming responses. A single streaming request uses one rate limit slot but delivers tokens progressively. Your users see text appearing immediately instead of waiting for a complete response. Better UX and better rate limit efficiency.

Fifth — and this is the big one — use multiple providers through a gateway.

**[THE MULTI-PROVIDER ADVANTAGE]**

Here's where it gets interesting. If you're locked to one provider, you're locked to one set of rate limits. But if you route through an API gateway like Crazyrouter, you can distribute load across multiple providers.

Think about it — GPT-4o has a rate limit. Claude has a separate rate limit. Gemini has another. If your app can use any of these models interchangeably — and for most tasks, you can — you've effectively tripled your capacity.

With Crazyrouter, you set up fallback routing. Primary request goes to Claude. If Claude returns a 429, the gateway automatically routes to GPT-4o. If that's limited too, it falls back to Gemini. Your user never sees an error. They just get a response.

One API key. One endpoint. But behind the scenes, you have access to the rate limits of every provider combined. For high-traffic applications, this is a game-changer.

**[MONITORING AND PLANNING]**

Last thing — monitor your usage before you hit limits. Every provider exposes rate limit headers in their API responses. Track them. Set up alerts at 70% capacity. Know your limits before your users discover them for you.

And plan ahead. If you know a launch is coming, request a rate limit increase from your provider. OpenAI and Anthropic both allow this — but it takes time, sometimes days. Don't wait until launch day.

**[OUTRO]**

Rate limits are one of those boring infrastructure topics that becomes extremely exciting when your app goes down in production. Don't learn this lesson the hard way. Implement backoff, add queuing, cache smart, and seriously — consider a multi-provider setup. Your future self will thank you.

That's it for today. If you want to try multi-provider routing with zero setup, check out Crazyrouter at crazyrouter.com — one API key, 627-plus models, automatic failover. I'll see you in the next episode.
