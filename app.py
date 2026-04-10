import argparse
import sys

from llm_wrapper import LLMWrapper

llm = LLMWrapper()


def process_user_request(user_input: str) -> str:
    """Send a user prompt through the LLM wrapper and return the result."""
    return llm.generate_content(user_input)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a prompt through the LLM wrapper.")
    parser.add_argument("prompt", nargs="?", help="Prompt to send to the model")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    prompt = args.prompt
    if not prompt:
        prompt = sys.stdin.read().strip()

    if not prompt:
        parser.error("a prompt is required either as an argument or via stdin")

    print(process_user_request(prompt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
