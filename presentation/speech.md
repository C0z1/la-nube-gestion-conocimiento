# Speech — La Nube Knowledge Assistant (≈10 minutes)

Slides: https://claude.ai/artifact/6t6j8niso1rLXymJKEiCZg · One block per slide. *Italics* = what to do, not what to say.
Pace: about 130 words per minute. The live demo (slide 6) is optional; if time is short, skip it and read the slide.

---

## 1 · Cover (0:00 – 0:40)

Good afternoon. My name is Felix Yael, and today I'm presenting La Nube Knowledge Assistant.

La Nube is a neighbourhood supermarket: two registers, a butcher counter and a small server that keeps selling even when the internet goes down. It already runs on its own point-of-sale system. What I built sits on top of it: a system that takes everything the store knows — manuals, reports, tickets, inventory records and policies — and makes it searchable from the register, which is exactly where questions happen.

## 2 · Objective (0:40 – 1:40)

Let me start with the problem.

In a small business, knowledge lives in two or three heads: the owner's and the manager's. When a new cashier forgets how to do the cash cut, or how to charge a card when the internet is down, they have to stop the line and ask. And when someone leaves the store, what they knew leaves with them.

So the objective of this project is simple: turn what only the owner knows into answers anyone can find in seconds. Technically, that means one integrated prototype that classifies documents, recommends related ones, answers questions in plain language and shows how the knowledge connects — deployed on the web and measured with real metrics.

## 3 · Where it is used (1:40 – 2:30)

This is not a theoretical exercise. The point of sale is real, and the register is operated only with the keyboard: F1 for cash, F2 for card, F4 for credit, F8 for the menu and the cash cut.

There are three users. The cashier, who needs answers without stopping the line. The manager, who authorizes refunds and discounts and reviews exceptions every day. And the owner, who needs reports and policies to make decisions.

That's why twenty-one of the documents come straight from the real POS manuals. I left out anything private: employee names, network details, costs and suppliers.

## 4 · The system (2:30 – 3:20)

The result is one web app with five functions.

**Search** understands meaning, not just exact words. **Ask the assistant** answers questions from the documents and always cites its source — and if it doesn't know, it says so instead of inventing. **Recommendations** suggest related documents, and the sidebar learns from what you searched during your session. **Classify** files a new document into the right category automatically. And the **knowledge graph** lets you explore how documents, topics and concepts connect. A sixth tab shows the evaluation, live.

## 5 · Architecture (3:20 – 4:20)

Under the hood there are three layers.

First, the knowledge sources: 102 documents in five categories, tagged with 23 topics, plus the ontology from Phase One, now expanded to 558 triples.

Second, the engine. It combines two ways of reading text. TF-IDF is precise with exact terms like "F6" or "CFDI". Embeddings — from a model called WordLlama — capture meaning, so "the web connection is lost" lands near "what happens if the internet goes down". WordLlama is only sixteen megabytes and runs without a graphics card, so it could run on the store's own server. On top of that sit the classifier, the recommender, the chatbot and the graph.

Third, the Streamlit app, published in the cloud.

And at the bottom, a quality loop: a script scores everything against answers I labelled by hand, and the results appear inside the app.

## 6 · Real example: the cashier asks (4:20 – 5:30)

Let's see it working. These are real outputs.

A cashier finishes their shift and asks: "How do I do the cash cut?" The answer: F8, option 5 — with the source, document D04.

The internet goes down and a customer wants to pay by card. The assistant says: use "charge manually" on the terminal and type the authorization number.

A cashier gets their PIN wrong several times: after five attempts the user is locked for fifteen minutes, or until the owner unlocks it.

And if you ask for a chocolate cake recipe, it says it couldn't find that in the store documents. It doesn't invent.

*Optional live demo: open the "Ask the assistant" tab and type `How do I charge a card if there is no internet?`*

## 7 · Real example: the manager searches (5:30 – 6:20)

Now the manager, who wants to know who keeps cancelling tickets. They type exactly that. No document contains the words "keeps cancelling" — but the system understands the meaning and returns the cancellations and audit log report first.

When they open the daily exceptions policy, the sidebar uses that context and recommends the cancellations report, the discount policy and the refunds summary: exactly what they need to spot a pattern and talk to the person. That's knowledge being reused instead of searched for from scratch.

## 8 · Real example: the owner organizes (6:20 – 7:00)

For the owner, new documents file themselves: a note about a 120-peso shortage in register 2 is classified as a Report; a delivery of thirty boxes of soda goes to Inventory.

On the right is the real knowledge graph from the app, filtered to cash closing and customer credit. Dots are documents, diamonds are topics, and the grey nodes are the classes from our Phase One ontology. This is how the conceptual model became something you can actually explore.

## 9 · Results (7:00 – 8:00)

How well does it work? Everything was measured against answers I labelled by hand by reading the documents, not against the ontology, so the evaluation isn't circular.

Classification reaches a macro F1 of 0.85, with precision 0.86 and recall 0.85.

For search, the key number is 0.76: when people ask the way they talk, the first right document ranks much higher than with the Phase One keyword search, which scored 0.52.

Recommendations: half of the five suggestions are relevant, against six percent at random, and the search history lifts ambiguous searches from 0.40 to 0.51.

And the chatbot: the answer contains the right fact in 17 of 18 questions, the right source is always in the top three, and it refused all off-topic questions.

## 10 · Usability and limits (8:00 – 8:50)

We tested it with [N] real users: three tasks and the System Usability Scale. The average score was [SUS], where 68 is average. [One sentence with the most common comment from the testers.]

I also want to be honest about the limits. Some everyday phrases still miss: "who still owes us money" ranks a refund document first. The corpus is in English and partly fictional — the procedures are real, the sales figures are illustrative. And a larger model, MiniLM, scored 0.86 offline, but it needs more memory than the free hosting tier allows.

## 11 · Impact (8:50 – 9:35)

So what changes for the store?

Training: new cashiers learn by asking at the register, and the manager stops repeating the same answers. Retrieval: instead of calling the owner, you get an answer in seconds with its source. Reuse: lessons from an outage or high shrinkage stop being forgotten, because related documents surface together. And decisions: the owner finds credit, shrinkage and supplier information fast, and sees how it connects.

The real shift is this: tacit knowledge in two people's heads becomes explicit knowledge that stays, even when someone leaves.

## 12 · Conclusions and recommendations (9:35 – 10:15)

To conclude: all four components work together in one deployed app, and they were measured, not assumed. Meaning-based search is the biggest gain, and grounding every answer in a cited document keeps the chatbot honest.

My recommendations: run a one-month pilot on register 1 and record the questions people ask; translate the corpus to Spanish and keep it updated as the POS changes; move to the stronger MiniLM model once the app runs on the store's own server; and expand searches with the ontology, so "corte de caja" also finds "cash cut".

Thank you. The app is live at [app URL] — I'm happy to take questions.

---

## Likely questions

- **Why not just use ChatGPT?** It would answer from the internet, not from the store's procedures, and could invent. This system answers only from the store's documents and cites them; an LLM can be plugged in with an API key, but it only rewrites what retrieval found.
- **How did you measure precision and recall?** For classification, 5-fold cross-validation over the 102 labelled documents. For search, 26 queries where I marked which documents are relevant, then precision at 3, recall at 5 and MRR.
- **Is the data real?** The procedures come from the store's actual POS manuals, anonymised. Sales figures and some reports are illustrative.
- **What does it cost?** The base version runs free: a 16 MB model on CPU and the free Streamlit tier. LLM answers are optional and paid per use.
- **Why is the hybrid search slightly worse than embeddings on some metrics?** On everyday wording they tie (MRR 0.76); the hybrid keeps a perfect score on exact keyword queries, which is why it's the default.
