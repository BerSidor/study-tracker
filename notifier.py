from typing import Protocol


class Notifier(Protocol):
    def notify(self, message: str) -> None: ...


class NullNotifier:
    def notify(self, message: str) -> None:
        pass


def make_notifier() -> Notifier:
    return NullNotifier()
