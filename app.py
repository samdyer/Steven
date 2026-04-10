from llm_wrapper import LLMWrapper

llm = LLMWrapper()


def process_user_request(user_input: str) -> str:
    return llm.generate_content(user_input)


if __name__ == "__main__":
    print(process_user_request("Hello!"))
