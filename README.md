# SignalCraft — incident communication prompt lab

**Scope:** small / ~3 of 10 complexity. **Technical theme:** prompt engineering and evaluations (2024-era portfolio track).

When an incident hits, the difficult part isn't generating a paragraph — it's keeping the message factual and consistent for different audiences. SignalCraft builds controlled incident updates using versioned prompt styles, lightweight vector retrieval from runbooks, and format/certainty evaluations.

This is a self-contained portfolio project. The historical *theme* is not a claim about the code's creation date.

## Start

```bash
docker compose up --build -d
```

- UI: http://localhost:8011
- Interactive API: http://localhost:8011/docs
- Health: `curl http://localhost:8011/health`
- Seed data: six incident runbooks created automatically in a persisted SQLite database
- Stop: `docker compose down`; erase seed/history: `docker compose down -v`

No paid account is necessary. With `OPENAI_API_KEY` unset, a deterministic drafting engine shows the complete flow and stores examples. For real model-generated text, `cp .env.example .env`, set the key, and restart (`docker compose up -d`). The key is injected into the container, never shown in the browser. The API may incur model charges.

## Try it

```bash
curl -s localhost:8011/api/draft -H 'content-type: application/json' -d '{"summary":"Login service is failing for customers","severity":"SEV2","variant":"empathetic"}'
curl -s localhost:8011/api/evaluate
```

Use the **Compare variants** UI button to see how changes to prompt wording alter outputs. The response includes retrieved runbook IDs, the exact message payload, and simple automated checks. `/api/history` retains the latest 25 requests.

## How it works

`browser → FastAPI → hashed-token vector retrieval → prompt builder → model/offline generator → quality rules → SQLite`

Key choices:
- `app/search.py`: 256-dimensional signed feature hashing + cosine search, not a trained semantic embedding model; intentionally small and deterministic.
- `app/prompts.py`: separated system instructions, JSON-encoded untrusted incident text, three prompt variants.
- `app/quality.py`: checks labels and a short list of overconfident phrases, **not** factuality.
- `app/storage.py`: SQL schema and idempotent seed, no setup script.

## Tests / local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
DB_PATH=/tmp/signalcraft.sqlite3 pytest -q
DB_PATH=/tmp/signalcraft.sqlite3 uvicorn app.main:app --reload --port 8011
```

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/draft` | Draft plus prompt, evidence, checks |
| POST | `/api/compare` | Compare all three prompt styles |
| GET | `/api/search?q=payment` | Runbook vector retrieval |
| GET | `/api/runbooks` | Seeded domain references |
| GET | `/api/history` | Local generation log |
| GET | `/api/evaluate` | Three deterministic eval cases |

## Intentional limitations

This is a local single-user tool, without authentication, PII redaction, or production incident integrations. Feature hashing is lexical rather than fully semantic. The offline draft is template-driven, not an LLM, and does not prove prompt quality. Real incidents should be approved by an operator before publication. Nothing sends messages externally.

## Ideas I would tackle next

A/B testing on anonymized actual incidents; human relevance labels; external alert ingestion; provider token/cost tracking. See `docs/decisions.md` for tradeoffs.

MIT license. Development history in this project is an illustrative Git timeline for learning purposes, not independent evidence of work performed on the dates shown.
