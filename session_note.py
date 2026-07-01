"""Turn a Claude Code transcript into a one-line study note.

Shared by the Stop hook (`study-log-hook.py`) and the web server's background
note-writer. Each caller owns only its genuine differences — where the transcript
comes from, whether to bootstrap the API key, and what to do on error/empty. The
parsing, the LLM summary, and the note format live here so the two never drift.

(They used to drift: the hook parsed a `{type:"message"}` schema while the server
parsed the real Claude Code `{type:"user"|"assistant", message:{...}}` schema, so the
hook silently produced "no transcript available" every run. This module uses the real
schema.)
"""

import json
from datetime import datetime

import anthropic

MODEL = "claude-haiku-4-5-20251001"
MAX_MESSAGES = 30          # enough context without blowing the token budget
MAX_CHARS_PER_MESSAGE = 500

_SUMMARY_PROMPT = (
    "Based on this study session transcript, write exactly ONE short line "
    "summarising what was studied or built. Be specific about topics and tools. "
    'Format: "<topic> — <key concepts or tasks done>". No date, no preamble.\n\n'
    "Transcript:\n{transcript}"
)


def transcript_to_text(lines) -> str:
    """Extract the last ``MAX_MESSAGES`` ``"role: text"`` lines from transcript JSONL.

    Accepts any iterable of raw JSONL lines. Handles the Claude Code schema —
    ``{type: "user"|"assistant", message: {role, content}}`` — where ``content`` is a
    string or a list of ``{type:"text", text}`` blocks. Malformed lines are skipped.
    """
    messages = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") not in ("user", "assistant"):
            continue
        msg = entry.get("message", {}) or {}
        role = msg.get("role", entry["type"])
        content = msg.get("content", "")
        if isinstance(content, list):
            text = " ".join(
                b.get("text", "") for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            )
        else:
            text = str(content)
        if text.strip():
            messages.append(f"{role}: {text[:MAX_CHARS_PER_MESSAGE]}")
    return "\n".join(messages[-MAX_MESSAGES:])


def summarize(transcript_text: str) -> str:
    """One-line summary of a transcript, via the Haiku model."""
    response = anthropic.Anthropic().messages.create(
        model=MODEL,
        max_tokens=80,
        messages=[
            {"role": "user", "content": _SUMMARY_PROMPT.format(transcript=transcript_text)}
        ],
    )
    return response.content[0].text.strip()


def append_note(notes_path, summary: str) -> None:
    """Append a timestamped note line to ``notes_path``."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(notes_path, "a", encoding="utf-8") as f:
        f.write(f"{now} | {summary}\n")
