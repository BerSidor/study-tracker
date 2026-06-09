import json
import urllib.request


class SyncError(Exception):
    pass


def sync_session(web_app_url: str, payload: dict) -> None:
    body = json.dumps({"action": "log_session", "session": payload}).encode()
    req = urllib.request.Request(
        web_app_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        raise SyncError(str(e)) from e

    if not result.get("success"):
        raise SyncError(result.get("error", "Unknown error from Apps Script"))
