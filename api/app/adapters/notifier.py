"""Notifiers: in-app (persisted alert) and console e-mail (dev). SMTP/Twilio later behind the same interface."""

import logging
from datetime import datetime

from app.models import Alert

log = logging.getLogger("notifier.email")


def in_quiet_hours(now: datetime, quiet: tuple[str, str] | list[str] | None) -> bool:
    if not quiet:
        return False
    start, end = quiet
    t = now.strftime("%H:%M")
    return (t >= start or t < end) if start > end else (start <= t < end)


class InAppNotifier:
    channel = "in_app"

    def __init__(self, store):
        self.store = store

    def send(self, alert: Alert, account: dict, now: datetime) -> str | None:
        return self.channel  # persisted by the engine; presence in the store is the delivery


class ConsoleEmailNotifier:
    channel = "email_console"

    def __init__(self, store=None):
        self.outbox: list[dict] = []
        self.store = store

    def send(self, alert: Alert, account: dict, now: datetime) -> str | None:
        prefs = account.get("preferences", {})
        if "email" not in prefs.get("channels", []):
            return None
        if alert.severity != "critical" and in_quiet_hours(now, prefs.get("quiet_hours")):
            return None
        msg = {"id": alert.id, "to": account["contact"]["email"], "subject": alert.title, "body": alert.body, "at": now.isoformat()}
        self.outbox.append(msg)
        if self.store is not None:
            self.store.put("outbox", f"{alert.id}", msg)
        log.info("EMAIL (console, not sent) to=%s subject=%s", msg["to"], msg["subject"])
        return self.channel


class NotifierChain:
    def __init__(self, *notifiers):
        self.notifiers = notifiers

    def send(self, alert: Alert, account: dict, now: datetime) -> list[str]:
        return [ch for n in self.notifiers if (ch := n.send(alert, account, now))]
