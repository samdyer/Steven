import argparse
import sys

from email_router import EmailRouter
from llm_wrapper import LLMWrapper

llm = LLMWrapper()
email_router = EmailRouter()


def process_user_request(user_input: str) -> str:
    """Send a user prompt through the LLM wrapper and return the result."""
    return llm.generate_content(user_input)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run prompts through the LLM wrapper or route email through AgentMail.")
    subparsers = parser.add_subparsers(dest="command")

    llm_parser = subparsers.add_parser("llm", help="Send a prompt through the LLM wrapper")
    llm_parser.add_argument("prompt", nargs="?", help="Prompt to send to the model")

    send_parser = subparsers.add_parser("email-send", help="Send an email via AgentMail")
    send_parser.add_argument("context", help="Routing context, e.g. Manito, Sea of Ink, or Steven")
    send_parser.add_argument("to", help="Recipient email address")
    send_parser.add_argument("subject", help="Email subject")
    send_parser.add_argument("text", help="Plain-text email body")
    send_parser.add_argument("--html", help="Optional HTML email body")

    list_parser = subparsers.add_parser("email-list", help="List inbox messages via AgentMail")
    list_parser.add_argument("context", help="Routing context, e.g. Manito, Sea of Ink, or Steven")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of messages to list")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "llm"):
        prompt = getattr(args, "prompt", None)
        if not prompt:
            prompt = sys.stdin.read().strip()
        if not prompt:
            parser.error("a prompt is required either as an argument or via stdin")
        print(process_user_request(prompt))
        return 0

    if args.command == "email-send":
        result = email_router.send(args.context, args.to, args.subject, args.text, html=args.html)
        print(result)
        return 0

    if args.command == "email-list":
        messages = email_router.list_messages(args.context, limit=args.limit)
        print(messages)
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
