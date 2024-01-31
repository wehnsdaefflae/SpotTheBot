import re
import time
from typing import Generator, Collection

import openai
from loguru import logger


class PromptOpenAI:
    @staticmethod
    def chunk_text(text: str, max_len: int = 1_000, overlap: int = 100) -> Generator[str, None, None]:
        len_text = len(text)
        start = 0
        end = max_len
        while True:
            if end >= len_text:
                yield text[start:]
                break
            yield text[start:end]
            start += max_len - overlap
            end += max_len - overlap

    def __init__(self, config: dict[str, any]) -> None:
        self._client = openai.AsyncOpenAI(api_key=config["key"])
        self._config = config["parameters"]

    async def summarize(self, text: str, max_len_input: int = 10_000, max_len_summary: int = 500) -> str:
        len_text = len(text)
        if len_text < max_len_summary:
            return text

        summaries = list()
        for each_chunk in self.chunk_text(text, max_len=max_len_input):
            summary = await self.summarize(each_chunk, max_len_input=max_len_input, max_len_summary=max_len_summary)
            summaries.append(summary)
        text = "\n".join(summaries)

        prompt = (
            f"```text\n"
            f"{text}\n"
            f"```\n"
            f"\n"
            f"Summarize the text above in about {max_len_summary} characters keeping its original language."
        )
        response = await self.reply_to_prompt(prompt)
        return response

    async def reply_to_prompt(self, prompt: str, **kwargs: any) -> str:
        logger.info(prompt)

        arguments = dict(self._config)
        arguments.update(kwargs)

        reply = ""
        while True:
            try:
                messages = [{"role": "user", "content": prompt}]
                response = await self._client.chat.completions.create(messages=messages, **arguments)
                choice, = response.choices
                message = choice.message
                reply = message.content
                break

            except Exception as e:
                logger.error(e)
                time.sleep(1)
                continue

        logger.info(reply)
        return reply.strip()


def extract_code_blocks(text: str, code_type: str = "") -> tuple[str, ...]:
    """
    Extracts all code blocks that contain the specified keyword from a string using regular expressions.

    :param text: The string to search within.
    :param code_type: The optional keyword to filter the code blocks.
    :return: A list of strings, each representing a found code block.
    """
    # If a code type is specified, include it in the pattern
    if code_type:
        pattern = r"```" + re.escape(code_type) + r"\n(.*?)\n```"
    else:
        pattern = r"```(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    return tuple(match.strip() for match in matches)


async def get_fake_comments(
        open_ai: PromptOpenAI, comments: Collection[str],
        output_comments: int = 3) -> Collection[str]:

    len_comments = len(comments)
    if output_comments >= len_comments:
        raise ValueError(f"`output_comments` must be smaller than the number of `comments`.")

    fenced_examples = (
        (
            f"```json\n"
            f"{each_comment.strip()}\n"
            f"```\n"
        ) for each_comment in comments)

    examples = "\n".join(fenced_examples)
    prompt = (
        f"{examples}"
        f"\n"
        f"Generate {output_comments} JSON objects based on the examples above. Make sure to include all keys present "
        f"in the examples. Generate values indistinguishable in form, style, and content. Use the "
        f"same language as the examples. Do not copy segments from the examples or the examples themselves.\n"
        f"\n"
        f"IMPORTANT: Incorporate typos and factual errors similar to the ones present in the examples. Write in a "
        f"style that is characteristic for YouTube comments, including inconsistent spaces and capitalization, typos, "
        f"abbreviations, emojis, and occasional references to video time stamps.\n"
        f"\n"
        f"Wrap each of the {output_comments} generated JSON objects in a fenced JSON code block according to the "
        f"following pattern:\n"
        f"```json\n"
        f"[first object]\n"
        f"```\n"
        f"\n"
        f"```json\n"
        f"[second object]\n"
        f"```\n"
        f"\n"
        f"```json\n"
        f"[third object]\n"
        f"```\n"
        f"[...]"
    )

    open_ai_response = await open_ai.reply_to_prompt(prompt)
    fake_comments = extract_code_blocks(open_ai_response, code_type="json")
    return fake_comments
