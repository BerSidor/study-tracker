import subprocess
import sys
from pathlib import Path
from typing import Protocol

_SCRIPT = Path(__file__).parent / "toast-notify.ps1"


class Notifier(Protocol):
    def notify(self, message: str) -> None: ...


class WindowsToastNotifier:
    def notify(self, message: str) -> None:
        subprocess.run(
            ["powershell", "-NonInteractive", "-File", str(_SCRIPT), "-Message", message],
            timeout=10,
            capture_output=True,
        )


class NullNotifier:
    def notify(self, message: str) -> None:
        pass


def make_notifier() -> Notifier:
    if sys.platform == "win32":
        return WindowsToastNotifier()
    return NullNotifier()
