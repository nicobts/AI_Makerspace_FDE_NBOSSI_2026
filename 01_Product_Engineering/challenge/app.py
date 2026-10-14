"""The server.

`gradio.Server` is a FastAPI app with Gradio's API engine bolted in. You get
queueing, streaming, and MCP for free, but you bring your own frontend. That
split is the point: the API is the product, the UI is disposable.
"""

import json
import os
import tomllib
from pathlib import Path

from fastapi.responses import HTMLResponse
from gradio import Server

from llm import stream_reply
from schema import Request, Response

app = Server()

FRONTEND = Path(__file__).parent / "frontend" / "index.html"
_PYPROJECT = Path(__file__).parent / "pyproject.toml"
VERSION = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]


# --- The API -----------------------------------------------------------------
# The `-> str` return annotation is REQUIRED. Without it Gradio infers zero
# output components and silently returns nothing. Ask us how we know.


CARD_INSTRUCTIONS = """You turn one scientific publication about coffee into an article card for an R&D researcher.

Reply with one JSON object and nothing else. It must match this JSON schema:
{schema}

Rules:
- Set needs_human to true, give needs_human_reason, and leave every other field null when the text is not a study or review, is too short to judge, or is not about coffee.
- Use only what the text states. Leave sample_size null when no number is given; never estimate one.
- category, study_type, main_finding, trust_level and trust_warnings are always in English.
- Write summary_* and notes_* only for these languages: {languages}. Leave the others null.
- relevance: 1 = background, 2 = worth reading, 3 = act on it. Judge it against the reader's focus when one is given.
- A weak study still gets a card: lower trust_level and list the trust_warnings that explain it.

Title: {title}
Source: {source}
Reader's focus: {focus}

Publication text:
{document_text}
"""


def _card_prompt(request: Request) -> str:
    return CARD_INSTRUCTIONS.format(
        schema=json.dumps(Response.model_json_schema()),
        languages=", ".join(request.output_languages),
        title=request.title or "not given",
        source=request.source or "not given",
        focus=request.focus or "not given",
        document_text=request.document_text,
    )


def _to_card(raw: str, request: Request) -> Response:
    # Models often wrap JSON in a code fence or a sentence; keep only the object.
    start, end = raw.find("{"), raw.rfind("}")
    try:
        card = Response.model_validate_json(raw[start : end + 1])
    except ValueError:
        # An answer that breaks the contract is a decline, not a half-filled card.
        return Response(
            needs_human=True,
            needs_human_reason="The model's answer did not match the contract; "
            "a researcher should read this document.",
        )
    if "en" not in request.output_languages:
        card.summary_en = card.notes_en = None
    if "it" not in request.output_languages:
        card.summary_it = card.notes_it = None
    return card


@app.api(name="summarize_research_paper")
def summarize_research_paper(
    document_text: str,
    title: str | None = None,
    source: str | None = None,
    focus: str | None = None,
    output_languages: list[str] | None = None,
) -> str:
    """Turn the text of one coffee research paper or abstract into an article card.

    Returns JSON with a category, a relevance score from 1 to 3, the key facts,
    a summary and reader notes in English and/or Italian, and a trust level with
    the warning signs found. Returns needs_human=true with a reason, and no
    card, when the text is not a study, is too short to judge, or is not about
    coffee. Use it for one document at a time; it does not search for papers.
    """
    request = Request(
        document_text=document_text,
        title=title,
        source=source,
        focus=focus,
        output_languages=output_languages or ["en", "it"],
    )
    raw = ""
    for raw in stream_reply(_card_prompt(request)):
        yield raw
    # The last value replaces the raw stream with the validated card.
    yield _to_card(raw, request).model_dump_json(indent=2)


# --- The frontend ------------------------------------------------------------
# Defining a route at "/" replaces Gradio's default UI with ours.


@app.get("/", response_class=HTMLResponse)
def homepage() -> str:
    return FRONTEND.read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    """Your future ops team will thank you. Load balancers need this."""
    return {"status": "ok", "model": os.getenv("LLM_MODEL", "gpt-4.1-mini")}


@app.get("/version")
def version() -> dict:
    return {"version": VERSION}


if __name__ == "__main__":
    # 0.0.0.0 so the container is reachable from the host. On your laptop this
    # is fine. On a firm network, "reachable from where, exactly?" is the
    # question this challenge wants you to go ask.
    #
    # Read the port rather than hardcoding it, so a machine that already has
    # something on 7860 can move this one without editing code.
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    # Gradio announces the address it BOUND to, which is 0.0.0.0 -- not an
    # address a browser can open. Windows rejects it outright; macOS and Linux
    # quietly redirect it to localhost, which is why it looks fine on some
    # machines and broken on others. Print the one that always works.
    print(f"\n  Open http://localhost:{port} in your browser\n", flush=True)
    app.launch(server_name="0.0.0.0", server_port=port)
