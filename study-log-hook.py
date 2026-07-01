import sys
import json
import os

import session_note

NOTES_PATH = os.path.join(os.path.dirname(__file__), "notes.txt")


def main():
    hook_input = json.loads(sys.stdin.read())
    transcript_path = hook_input.get("transcript_path", "")

    transcript_text = ""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_text = session_note.transcript_to_text(f)
    except FileNotFoundError:
        pass

    if transcript_text:
        summary = session_note.summarize(transcript_text)
    else:
        summary = "Study session — no transcript available"

    session_note.append_note(NOTES_PATH, summary)


if __name__ == "__main__":
    main()
