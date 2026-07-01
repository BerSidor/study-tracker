import json

from session_note import (
    MAX_CHARS_PER_MESSAGE,
    MAX_MESSAGES,
    append_note,
    transcript_to_text,
)


def _line(type_, role, content):
    return json.dumps({"type": type_, "message": {"role": role, "content": content}})


# ── transcript_to_text (the real Claude Code schema) ─────────────────────────────

def test_parses_nested_message_schema():
    lines = [
        _line("user", "user", "teach me hooks"),
        _line("assistant", "assistant", "a hook fires on events"),
    ]
    assert transcript_to_text(lines) == "user: teach me hooks\nassistant: a hook fires on events"


def test_extracts_text_blocks_from_list_content():
    content = [
        {"type": "text", "text": "first"},
        {"type": "tool_use", "name": "x"},      # non-text block ignored
        {"type": "text", "text": "second"},
    ]
    assert transcript_to_text([_line("assistant", "assistant", content)]) == "assistant: first second"


def test_skips_non_message_entries_and_bad_json():
    lines = [
        '{"type": "summary"}',                    # not user/assistant
        "not json at all",                        # malformed
        "",                                       # blank
        _line("user", "user", "real message"),
    ]
    assert transcript_to_text(lines) == "user: real message"


def test_keeps_only_last_N_messages():
    lines = [_line("user", "user", f"msg {i}") for i in range(MAX_MESSAGES + 5)]
    out = transcript_to_text(lines).splitlines()
    assert len(out) == MAX_MESSAGES
    assert out[-1] == f"user: msg {MAX_MESSAGES + 4}"


def test_truncates_long_messages():
    long_text = "x" * (MAX_CHARS_PER_MESSAGE + 100)
    out = transcript_to_text([_line("user", "user", long_text)])
    assert out == "user: " + "x" * MAX_CHARS_PER_MESSAGE


def test_old_message_schema_is_ignored():
    # The hook's old schema ({type:"message"}) is NOT the real format — confirm it
    # yields nothing, which is exactly the silent bug consolidation fixes.
    old = json.dumps({"type": "message", "role": "user", "content": "hi"})
    assert transcript_to_text([old]) == ""


# ── append_note ──────────────────────────────────────────────────────────────────

def test_append_note_writes_timestamped_line(tmp_path):
    notes = tmp_path / "notes.txt"
    append_note(notes, "MCP servers — built a notes server")
    line = notes.read_text(encoding="utf-8").strip()
    assert line.endswith(" | MCP servers — built a notes server")
    # leading "YYYY-MM-DD HH:MM | "
    assert line[4] == "-" and line[7] == "-" and " | " in line


def test_append_note_appends_not_overwrites(tmp_path):
    notes = tmp_path / "notes.txt"
    append_note(notes, "first")
    append_note(notes, "second")
    assert len(notes.read_text(encoding="utf-8").strip().splitlines()) == 2
