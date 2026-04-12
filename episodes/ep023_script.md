# EP023: Embedding Models Compared — Which One Should You Actually Use?

Welcome back to AI Dev Tools, the Crazyrouter Podcast. I'm your host, and today we're diving into embedding models — the unsung heroes behind every search bar, recommendation engine, and RAG pipeline in production right now.

If you've built anything with AI retrieval, you've had to pick an embedding model. And in April 2026, there are more options than ever. So let's cut through the noise and compare what actually matters.

## The Contenders

We're looking at five embedding models that developers are actually using in production today.

First, OpenAI's text-embedding-3-small and text-embedding-3-large. These are still the default choice for most teams. Small gives you 1536 dimensions, large goes up to 3072. They're fast, well-documented, and the pricing is hard to beat — small runs about 0.02 dollars per million tokens, large is 0.13.

Second, Cohere's embed-v4. This one's been gaining serious traction. It supports over 100 languages natively, handles both search and classification tasks, and the quality on multilingual benchmarks is genuinely impressive. If you're building for a global audience, Cohere deserves a hard look.

Third, Google's Gemini embedding. Integrated into the Gemini API, it produces 768-dimension vectors by default. The big advantage here is if you're already in the Google ecosystem — Vertex AI, BigQuery vector search — it slots right in.

Fourth, Voyage AI's voyage-3. This is the specialist pick. Voyage models consistently top the MTEB leaderboard for code search and technical documentation retrieval. If your use case is developer tools or code-heavy, Voyage is worth the premium.

And fifth, open-source options like BGE-M3 and Nomic Embed. These run locally, cost nothing per query, and for many use cases perform within five to ten percent of the commercial options. The trade-off is you're managing infrastructure.

## What Actually Matters When Choosing

Let me save you some benchmarking time. Here are the four things that actually determine which embedding model works best for your app.

Number one: retrieval quality on YOUR data. Generic benchmarks like MTEB are useful directionally, but I've seen teams where the "worse" model on benchmarks performed better on their specific domain. Always test with your actual queries and documents. Build a small eval set — fifty to a hundred query-document pairs — and measure recall at ten. That's worth more than any leaderboard.

Number two: dimension size and storage cost. This is where people get surprised. If you're embedding a million documents at 3072 dimensions with float32, that's about 12 gigabytes just for vectors. Switch to text-embedding-3-small at 1536 dimensions and you've halved your storage. Use Matryoshka dimensionality reduction — which OpenAI and several others now support — and you can go even lower with minimal quality loss. At scale, your vector database bill can dwarf your embedding API cost.

Number three: latency. For real-time search, you need embeddings generated fast. OpenAI small typically returns in 20 to 50 milliseconds. Voyage is slightly slower. Self-hosted models vary wildly depending on your GPU. If you're doing batch indexing, latency matters less. If you're embedding user queries at search time, every millisecond counts.

Number four: multilingual support. If your content is English-only, most models work fine. The moment you add Chinese, Japanese, Korean, Arabic, or mixed-language content, your options narrow fast. Cohere embed-v4 and BGE-M3 lead here. OpenAI's models handle multilingual reasonably well but aren't optimized for it.

## The Practical Recommendation

Here's my honest take for most developers in 2026.

Start with text-embedding-3-small from OpenAI. It's cheap, fast, good enough for eighty percent of use cases, and you can switch later without rebuilding your entire pipeline — especially if you're using an API gateway like Crazyrouter that lets you swap providers with one parameter change.

If you need multilingual, go Cohere embed-v4. If you need code search, go Voyage. If you need to keep data on-premise or want zero per-query cost, go BGE-M3 with a local deployment.

And here's the key insight most people miss: your chunking strategy matters more than your embedding model choice. I've seen teams spend weeks A/B testing embedding models when switching from fixed-size chunks to semantic chunking with overlap gave them a bigger retrieval quality boost than any model swap.

## Using Embeddings Through Crazyrouter

One more thing — if you're experimenting with different embedding models, Crazyrouter supports all the major embedding providers through a single API endpoint. Same OpenAI-compatible format, just change the model name. That means you can benchmark OpenAI, Cohere, Voyage, and Gemini embeddings without touching your application code. Just swap the model parameter and compare results.

That's it for today. Embedding models are a solved-enough problem that you shouldn't agonize over the choice — pick one, build your eval set, and optimize your chunking. The model is the easy part to swap later.

Try Crazyrouter at crazyrouter.com — one API key for 627 plus AI models, including all the embedding providers we talked about today. See you next episode.
