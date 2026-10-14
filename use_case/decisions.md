# Decision log

One row per architectural decision, with the option you rejected and why.

> **Week 5 asks you to defend your agent architecture against the alternatives.**
> **Week 10's handoff doc is largely this file.** Both are much easier if you
> wrote the reasoning down while you still remembered it.

A decision without a rejected alternative is not a decision, it is a default.
If you cannot name what you did not do, you did not choose.

| Week | Decision | What you rejected | Why | What would change your mind |
| --- | --- | --- | --- | --- |
| 1 | Start as a pipeline of functions, not an agent. Week 1 is one function: one document in, one article card out. The end goal is the full solution for the customer (sweep the sources, card every document, rank, store, weekly report, and conversational retrieval over the papers), built by putting steps around this same function. | A multi-agent architecture from day one, with one agent each for search, screening, comparison, translation and packaging, as the original brief proposes. | On the four questions the full solution scores 1 to 2: it must call out to search and a database, but the order of steps is fixed and can be drawn in advance, and a card is either accepted or flagged for a human. A fixed pipeline gives a known cost per document and outputs I can score against the goldens. | Evidence that fixed steps fail on real requests: for example the sweep missing relevant papers unless the search is reformulated per topic, or chat questions that need several retrieval steps a fixed flow cannot plan. |
| 3 | <!-- retrieval approach --> | <!-- --> | <!-- --> | <!-- --> |
| 5 | <!-- agent architecture --> | <!-- --> | <!-- --> | <!-- --> |
| 6 | <!-- guardrail level --> | <!-- --> | <!-- --> | <!-- --> |
| 7 | <!-- memory type --> | <!-- --> | <!-- --> | <!-- --> |
| 8 | <!-- model --> | <!-- --> | <!-- --> | <!-- --> |

**Week 1, the strongest case for the opposite verdict.** The customer asked for agents, and the
real work is open-ended: a researcher's request can be about any topic, the right sources differ
per topic, and a good literature search reformulates itself when the first results are poor. A
fixed pipeline may only automate the easy part. I would switch if, with retrieval in place, the
pipeline's results on real requests were clearly worse than what a researcher finds by hand.

---

The last column is the one people skip and the one people ask about. "We chose
dense retrieval; we would switch to hybrid if exact-match queries went above ~20%
of traffic" is an engineering position. "We chose dense retrieval" is a
preference.
