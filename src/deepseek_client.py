import os
from typing import Iterable, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # 读取 .env

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

if not DEEPSEEK_API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY 未设置。请在 .env 中填写你的 Key。")

_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL)


def chat_once(prompt: str,
              system: Optional[str] = None,
              temperature: float = 0.7,
              max_tokens: Optional[int] = None) -> str:
    """非流式：一次性返回完整回答。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )
    return resp.choices[0].message.content


def chat_stream(prompt: str,
                system: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: Optional[int] = None) -> Iterable[str]:
    """流式：逐块（token 增量）返回。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    with _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    ) as stream:
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

