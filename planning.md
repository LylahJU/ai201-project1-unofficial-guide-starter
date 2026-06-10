# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
Affordable dining at UCSC (campus + nearby Santa Cruz)

Dining at UC Santa Cruz is generally viewed by students as convenient and accommodating to a variety of dietary needs, though opinions on food quality vary, with common concerns including repetitive menus and inconsistent meal quality. To save money, many students seek affordable off-campus dining options in Santa Cruz, such as local taquerias and pizza spots, while also utilizing campus resources like Basic Needs programs and food assistance services to help manage food expenses.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit | On campus food ranking | https://www.reddit.com/r/UCSC/comments/1j6z2u9/on_campus_food_ranking/?utm_source=chatgpt.com |
| 2 | Reddit | best food on campus? | https://www.reddit.com/r/UCSC/comments/1io8bo2/best_food_on_campus/ |
| 3 | Reddit | Dining hall meals/food yall genuinely enjoyed?? | https://www.reddit.com/r/UCSC/comments/1dgu2dh/dining_hall_mealsfood_yall_genuinely_enjoyed/ |
| 4 | Santa Cruz Local | 10 meals under $10: The best cheap eats in Santa Cruz County | https://santacruzlocal.org/2025/12/05/10-meals-under-10-the-best-cheap-eats-in-santa-cruz-county/ |
| 5 | Reddit | dining hall food | https://www.reddit.com/r/UCSC/comments/16u7gfq/dining_hall_food/ |
| 6 | Reddit  | How consistent are the dining halls | https://www.reddit.com/r/UCSC/comments/1r488hw/how_consistent_are_the_dining_halls/ |
| 7 | UCSC | Required Residence Hall Meal Plans | https://dining.ucsc.edu/plans-pricing/residence-hall/ |
| 8 | UCSC | Dietary Needs and Allergies | https://dining.ucsc.edu/wellness/dietary/ |
| 9 | Reddit | Cheapest food in Santa Cruz | https://www.reddit.com/r/UCSC/comments/1nc9rf1/cheapest_food_in_santa_cruz/ |
| 10 | UCSC | On-Campus Food Resources | https://basicneeds.ucsc.edu/food-security/on-campus/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

Semantic Chunking.

The dataset includes short Reddit comments and Yelp reviews, along with longer UCSC webpages and guides. Reddit comments and reviews will be treated as individual chunks when possible. Longer documents will be split by headings or FAQ sections into 250-token chunks with 50-token overlap.

**Chunk size:**
250 tokens
**Overlap:**
50 tokens
**Reasoning:**
The overlap preserves important information that spans chunk boundaries. Chunks that are too small may miss context, while chunks that are too large may retrieve unrelated information and reduce search accuracy.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
all-MiniLM-L6-v2 via Sentence Transformers
**Top-k:**
5 chunks per query
**Production tradeoff reflection:**
all-MiniLM-L6-v2 provides efficient semantic retrieval with low computational cost. In a production system with unlimited resources, larger models such as OpenAI's text-embedding-3-large could improve retrieval accuracy and support longer contexts, but would increase latency and cost.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Which affordable restaurants do UCSC students commonly recommend? | Taqueria Santa Cruz, Taqueria Vallarta, and Pleasure Pizza. |
| 2 | What complaints do students have about UCSC dining halls? | Repetitive menus and inconsistent food quality. |
| 3 | What advice do students give about UCSC meal plans? | Avoid large meal plans unless eating on campus frequently. |
| 4 | What food assistance resources are available at UCSC? | Basic Needs Program, Slug Support, CalFresh, and food pantries. |
| 5 | What dining hall foods do students report enjoying? | Salad bars, breakfast foods, samosas, and pasta dishes. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Student reviews and Reddit posts may be subjective, inconsistent, or outdated, resulting in conflicting information.

2. Semantic retrieval may return off-topic chunks or split related information across chunk boundaries, reducing answer quality.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

Documents (Reddit, Yelp, UCSC webpages) 
↓ 
Semantic Chunking (250 tokens, 50 overlap) 
↓ 
all-MiniLM-L6-v2 Embeddings 
↓ 
ChromaDB Vector Database 
↓ 
Top-5 Semantic Retrieval 
↓ 
LLM Response Generation (Groq model)

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
Generate Python code for loading source documents and implementing semantic chunking with 250-token chunks and 50-token overlap. Verify that chunk sizes and overlaps match the specifications by inspecting sample outputs.
**Milestone 4 — Embedding and retrieval:**
Implement embeddings using all-MiniLM-L6-v2 and store vectors in ChromaDB. Verify retrieval quality by testing the evaluation questions and ensuring relevant chunks appear in the top 5 results.
**Milestone 5 — Generation and interface:**
Create the RAG pipeline that combines retrieved chunks with an LLM prompt and builds a simple user interface. Verify that responses answer the evaluation questions accurately and include information from the retrieved sources.