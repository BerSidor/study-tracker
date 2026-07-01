import sys, os, json, winreg, anthropic
from pathlib import Path
from datetime import datetime

if not os.environ.get("ANTHROPIC_API_KEY"):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            os.environ["ANTHROPIC_API_KEY"] = winreg.QueryValueEx(k, "ANTHROPIC_API_KEY")[0]
            print("Loaded ANTHROPIC_API_KEY from Windows registry")
    except OSError:
        sys.exit("ANTHROPIC_API_KEY not found in environment or registry")

TRANSCRIPT_DIR = Path.home() / ".claude" / "projects" / "C--Users-berna-Claude-Code-Learning"
NOTES_PATH = Path(__file__).parent / "notes.txt"

transcripts = sorted(TRANSCRIPT_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
print("Transcripts found:", len(transcripts))
if not transcripts:
    sys.exit("No transcripts")

print("Latest:", transcripts[-1].name)
lines = transcripts[-1].read_text(encoding="utf-8").splitlines()
print("Lines:", len(lines))

messages = []
for line in lines:
    try:
        entry = json.loads(line)
        if entry.get("type") not in ("user", "assistant"):
            continue
        msg = entry.get("message", {})
        role = msg.get("role", entry["type"])
        content = msg.get("content", "")
        text = (
            " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
            if isinstance(content, list) else str(content)
        )
        if text.strip():
            messages.append(f"{role}: {text[:300]}")
    except Exception as e:
        print("Parse error:", e)

print("Messages extracted:", len(messages))
if not messages:
    sys.exit("No messages")

transcript_text = "\n".join(messages[-5:])
print("Sample:\n", transcript_text[:400])
print("\nCalling Haiku...")

response = anthropic.Anthropic().messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=80,
    messages=[{"role": "user", "content": (
        "Based on this study session transcript, write exactly ONE short line "
        "summarising what was studied or built. Be specific about topics and tools. "
        'Format: "<topic> — <key concepts or tasks done>". No date, no preamble.\n\n'
        f"Transcript:\n{transcript_text}"
    )}],
)
summary = response.content[0].text.strip()
print("Summary:", summary)

now = datetime.now().strftime("%Y-%m-%d %H:%M")
with open(NOTES_PATH, "a", encoding="utf-8") as f:
    f.write(f"{now} | {summary}\n")
print("Written to", NOTES_PATH)
