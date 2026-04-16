from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from email_router import EmailRouter


def make_router():
    with patch("email_router.AgentMail") as mock_agentmail:
        client = MagicMock()
        mock_agentmail.return_value = client
        yield EmailRouter(api_key="test-key"), client


def test_route_for_contexts():
    with patch("email_router.AgentMail"):
        router = EmailRouter(api_key="test-key")

    assert router.route_for("Manito project").name == "manito"
    assert router.route_for("Sea of Ink campaign").name == "sea_of_ink"
    assert router.route_for("random other").name == "steven"


def test_send_uses_correct_inbox(monkeypatch):
    with patch("email_router.AgentMail") as mock_agentmail:
        client = MagicMock()
        client.inboxes.messages.send.return_value = SimpleNamespace(ok=True)
        mock_agentmail.return_value = client
        router = EmailRouter(api_key="test-key")

    router.send("Manito launch", "person@example.com", "Subject", "Body")

    client.inboxes.messages.send.assert_called_once()
    inbox_id = client.inboxes.messages.send.call_args.args[0]
    assert inbox_id == "manito_ai@agentmail.to"


def test_list_messages_uses_correct_inbox():
    with patch("email_router.AgentMail") as mock_agentmail:
        client = MagicMock()
        client.inboxes.messages.list.return_value = SimpleNamespace(messages=[])
        mock_agentmail.return_value = client
        router = EmailRouter(api_key="test-key")

    router.list_messages("Sea of Ink", limit=5)

    client.inboxes.messages.list.assert_called_once()
    inbox_id = client.inboxes.messages.list.call_args.args[0]
    assert inbox_id == "steven_sea_of_ink@agentmail.to"
