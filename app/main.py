import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .prompts import Incident, VARIANTS, build_prompt, deterministic_draft
from .quality import score_draft
from .search import search
from .storage import connect, runbooks

LOCK = threading.Lock()


class DraftRequest(BaseModel):
    summary: str = Field(min_length=8, max_length=1200)
    audience: str = Field(default="customers", pattern="^(customers|internal|partners)$")
    severity: str = Field(default="SEV2", pattern="^(SEV1|SEV2|SEV3)$")
    confirmed: str = Field(default="", max_length=1000)
    variant: str = Field(default="brief", pattern="^(brief|empathetic|technical)$")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = connect()
    yield
    app.state.db.close()


app = FastAPI(title="SignalCraft | incident comms prompt lab", version="1.0", lifespan=lifespan)


@app.get("/")
def home():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "openai" if os.getenv("OPENAI_API_KEY") else "offline"}


@app.get("/api/runbooks")
def list_runbooks():
    with LOCK:
        return runbooks(app.state.db)


@app.get("/api/search")
def search_runbooks(q: str):
    if not q.strip():
        raise HTTPException(400, "q is required")
    return search(q, list_runbooks())



async def make_draft(req: DraftRequest, persist: bool = True):
    incident = Incident(req.summary, req.audience, req.severity, req.confirmed)
    evidence = search(req.summary, list_runbooks(), 2)
    prompt = build_prompt(incident, req.variant, evidence)

    provider = "offline"
    fallback_used = False

    if os.getenv("OPENAI_API_KEY"):
        from openai import APIError, AsyncOpenAI

        try:
            response = await AsyncOpenAI().chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=prompt,
                temperature=0.2,
                timeout=20,
            )

            draft = (response.choices[0].message.content or "").strip()

            if not draft:
                raise ValueError("Model returned an empty draft")

            provider = "openai"

        except (APIError, ValueError) as exc:
            logger.warning(
                "LLM generation failed: %s",
                type(exc).__name__,
            )

            if os.getenv("ALLOW_OFFLINE_FALLBACK", "false").lower() == "true":
                draft = deterministic_draft(
                    incident, req.variant, evidence
                )
                provider = "offline_fallback"
                fallback_used = True
            else:
                raise HTTPException(
                    status_code=503,
                    detail="AI generation unavailable; no draft saved",
                ) from exc
    else:
        draft = deterministic_draft(
            incident, req.variant, evidence
        )

    evaluation = score_draft(draft)

    if persist:
        with LOCK:
            app.state.db.execute(
                "INSERT INTO generations(incident,audience,variant,prompt,output,provider) VALUES(?,?,?,?,?,?)",
                (
                    req.summary,
                    req.audience,
                    req.variant,
                    str(prompt),
                    draft,
                    provider,
                ),
            )
            app.state.db.commit()

    return {
        "draft": draft,
        "variant": req.variant,
        "quality": evaluation,
        "provider": provider,
        "fallback_used": fallback_used,
        "sources": [
            {
                "id": e["id"],
                "title": e["title"],
                "score": e["score"],
            }
            for e in evidence
        ],
        "prompt": prompt,
    }



@app.post("/api/draft")
async def draft(req: DraftRequest):
    return await make_draft(req)


@app.post("/api/compare")
async def compare(req: DraftRequest):
    results = []
    for variant in VARIANTS:
        results.append(await make_draft(req.model_copy(update={"variant": variant}), persist=False))
    return {"variants": results, "recommended": max(results, key=lambda r: r["quality"]["score"])["variant"]}


@app.get("/api/history")
def history():
    with LOCK:
        rows = app.state.db.execute(
            "SELECT id,created_at,incident,variant,output,provider FROM generations ORDER BY id DESC LIMIT 25"
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/evaluate")
def evaluate():
    from .prompts import deterministic_draft
    cases = [
        Incident("Database reads are failing", "customers", "SEV1"),
        Incident("Payment confirmation is delayed", "partners", "SEV2"),
        Incident("Sign-in is intermittently unavailable", "internal", "SEV3"),
    ]
    scores = [score_draft(deterministic_draft(x, "brief", search(x.summary, list_runbooks(), 1))) for x in cases]
    return {"total": len(cases), "passed": sum(x["passed"] for x in scores), "cases": scores,
            "note": "Format and certainty checks only; not a factual accuracy benchmark."}
