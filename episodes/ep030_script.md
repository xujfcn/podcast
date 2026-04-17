# EP030: The AI Pricing War — Why Model Costs Dropped 90% in One Year

Welcome back to AI Dev Tools, the Crazyrouter Podcast. Today we're talking about money — specifically, why AI API pricing has collapsed over the past twelve months and what that means for developers building products right now.

If you were using GPT-4 in early 2025, you were paying thirty dollars per million input tokens. Today, GPT-4o costs two dollars and fifty cents. That's a ninety-two percent drop in just over a year.

And it's not just OpenAI. Let's look at the numbers across the board.

## The price collapse

Claude Opus went from seventy-five dollars per million output tokens to under fifteen. Gemini 1.5 Pro launched at seven dollars and now Gemini 2.5 Pro is under five. DeepSeek V3 came in at twenty-seven cents per million input tokens — that's roughly one hundred times cheaper than GPT-4 was a year ago.

What's driving this? Three things.

First, competition. When it was just OpenAI, they could charge whatever they wanted. Now you've got Anthropic, Google, DeepSeek, Meta with Llama, Mistral, and a dozen others all fighting for developer adoption. Price is the easiest lever to pull.

Second, inference efficiency. Every provider has gotten dramatically better at serving models. Quantization, speculative decoding, custom silicon — all of these reduce the actual cost of running a model. When your costs drop, you can drop prices and still maintain margins.

Third, open source pressure. DeepSeek and Llama proved that near-frontier performance is possible at a fraction of the cost. That puts a ceiling on what anyone can charge for proprietary models. If Claude costs ten times more than DeepSeek for similar quality on routine tasks, developers will just use DeepSeek.

## What this means for developers

The obvious takeaway is that AI is getting cheaper. But the more interesting takeaway is that the pricing landscape is now incredibly fragmented.

Right now, the cheapest model for coding tasks is different from the cheapest model for summarization, which is different from the cheapest model for image understanding. And these rankings change every few weeks as providers update pricing.

This is actually a problem. If you hardcode one model into your application, you're probably overpaying for some tasks and underperforming on others.

The smart approach is model routing — sending each request to the best model for that specific task and budget. A coding question goes to Claude. A simple classification goes to DeepSeek. A multimodal task goes to Gemini. All through one API endpoint.

## The hidden costs

Price per token isn't the whole story. There are three hidden costs most developers miss.

One — rate limits. The cheapest model doesn't help if you can't get enough throughput. Some providers throttle heavily on their lowest tiers.

Two — latency. A model that costs half as much but takes three times longer might actually cost you more in user experience and infrastructure.

Three — reliability. If a provider has frequent outages, you need a fallback. Running two providers costs more than one, but less than downtime.

When you factor in rate limits, latency, and reliability, the true cost of using AI APIs is often two to three times the raw token price.

## The pricing models are diverging

Here's something most people haven't noticed — providers are experimenting with completely different pricing structures.

OpenAI still charges per token. Anthropic charges per token but with aggressive prompt caching discounts. Google offers a free tier up to a certain rate limit and then charges per token. DeepSeek has different pricing for cache hits versus misses.

Some providers are moving toward subscription models for API access. Others are experimenting with commitment-based discounts — commit to a certain spend level and get a lower rate.

This divergence makes it even harder to do apples-to-apples comparisons. Which is exactly why having a unified gateway that normalizes pricing across providers is becoming essential infrastructure.

## What to expect next

Prices will keep falling, but not uniformly. Frontier models — the absolute best performers — will maintain premium pricing. But the tier just below frontier will become nearly free.

We're heading toward a world where basic AI capabilities — summarization, classification, simple Q&A — cost essentially nothing. The premium will be on reasoning, long-context, and specialized capabilities.

For developers, the strategy is clear: don't lock into one provider, don't optimize for today's prices, and build your architecture to route between models as the landscape shifts.

## Bottom line

The AI pricing war is great for developers. But navigating it requires staying on top of a constantly shifting landscape. The winners will be teams that can dynamically route to the best model for each task at the best price — without rewriting their code every time a provider changes their pricing.

That's it for today. If you want one API key that automatically gives you access to six hundred plus models at competitive pricing, check out crazyrouter.com. See you next episode.
