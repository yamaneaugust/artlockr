# ArtLockr: Technical Explainer Script (2 minutes)

---

**[INTRO - 15 seconds]**

ArtLockr is an AI-powered copyright detection system that helps artists protect their work from unauthorized use in AI training datasets. Let me explain how it works under the hood.

**[FEATURE EXTRACTION - 30 seconds]**

When you upload artwork to ArtLockr, we immediately run it through a ResNet deep learning model. ResNet is a convolutional neural network that's been trained to understand visual features. It converts your image into a high-dimensional feature vector - essentially a mathematical fingerprint that captures the unique characteristics of your artwork: composition, style, color patterns, and texture.

Here's the crucial part: we immediately delete your original image. We only store this feature vector. This is privacy-first by design - no one can reconstruct your artwork from the feature vector alone.

**[FAISS VECTOR SEARCH - 30 seconds]**

When you run a detection scan, we use FAISS - that's Facebook AI Similarity Search. Traditional similarity search would compare your artwork against every single image in a database one by one. That's O(n) complexity - slow and expensive.

FAISS uses approximate nearest neighbor search with vector quantization. It organizes vectors into clusters and uses inverted indices, achieving O(log n) complexity. This means we can search millions of images in under 5 milliseconds - that's 100,000 times faster than brute force comparison.

**[MULTI-METRIC FUSION - 25 seconds]**

But we don't stop at cosine similarity. We use multi-metric fusion - combining five different similarity metrics: cosine similarity, Euclidean distance, Manhattan distance, Pearson correlation, and Jaccard similarity. Each metric captures different aspects of similarity. We weight and combine these scores, boosting our accuracy from about 85% with cosine alone to roughly 95% with fusion.

**[SECURITY & BLOCKING - 20 seconds]**

For organization blocking, we implement multi-layer API protection. When a request comes in, we analyze IP reputation, check behavioral patterns, and detect adversarial attacks - like modified images designed to fool the system. Blocked organizations are denied at the middleware level before they can access any feature vectors.

**[CLOSING - 10 seconds]**

The result? A privacy-preserving, lightning-fast copyright detection system that gives artists real protection in the age of AI. All powered by modern deep learning, vector search, and security infrastructure.

---

**Word count:** ~330 words
**Estimated speaking time:** 2 minutes at normal pace
