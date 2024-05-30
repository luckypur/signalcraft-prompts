# Engineering notes

- **Offline-first:** deterministic mode means demos and unit tests work without billing/accounts.
- **Small vector index:** hashing+cosine keeps installation light. It doesn't understand paraphrases like a neural embedding service would.
- **LLM choice:** optional remote API only for copywriting; unsupported claims are still a risk. No automatic posting.
- **SQLite:** appropriate for a single operator, not a shared multi-tenant service.
- **Evaluation:** baseline syntax/certainty checks catch regressions; human review is still required.
