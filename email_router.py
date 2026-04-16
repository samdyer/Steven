"""AgentMail inbox routing helpers.

Routes mail by brand/project to the correct AgentMail inbox.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict

from agentmail import AgentMail


DEFAULT_INBOXES: Dict[str, str] = {
    "manito": "manito_ai@agentmail.to",
    "sea_of_ink": "steven_sea_of_ink@agentmail.to",
    "steven": "steven_claw@agentmail.to",
}


@dataclass
class EmailRoute:
    name: str
    inbox_id: str


class EmailRouter:
    """Simple inbox router for brand-aware email workflows."""

    def __init__(self, api_key: str | None = None, inboxes: Dict[str, str] | None = None):
        self.client = AgentMail(api_key=api_key or os.environ.get("AGENTMAIL_API_KEY"))
        self.inboxes = dict(inboxes or DEFAULT_INBOXES)

    def route_for(self, context: str) -> EmailRoute:
        key = context.strip().lower()
        if "manito" in key:
            return EmailRoute(name="manito", inbox_id=self.inboxes["manito"])
        if "sea of ink" in key:
            return EmailRoute(name="sea_of_ink", inbox_id=self.inboxes["sea_of_ink"])
        return EmailRoute(name="steven", inbox_id=self.inboxes["steven"])

    def send(self, context: str, to: str, subject: str, text: str, html: str | None = None):
        route = self.route_for(context)
        payload = {"to": to, "subject": subject, "text": text}
        if html is not None:
            payload["html"] = html
        return self.client.inboxes.messages.send(route.inbox_id, **payload)

    def list_messages(self, context: str, limit: int = 10):
        route = self.route_for(context)
        return self.client.inboxes.messages.list(route.inbox_id, limit=limit)
