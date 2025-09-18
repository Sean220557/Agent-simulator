import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

if not API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY 未设置。请在 .env 中填写你的 Key。")

aclient = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)


class LLMError(Exception):
    pass


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=0.8, min=1, max=8),
    retry=retry_if_exception_type(LLMError),
)
async def chat_json(
    messages: List[ChatCompletionMessageParam],
    temperature: float = 0.7,
    max_tokens: Optional[int] = 512,
    system: Optional[str] = None,
) -> Dict[str, Any]:
    """
    期望 LLM 输出严格 JSON；若非 JSON，尝试二次纠正（让模型自我纠错）。
    """
    msgs: List[ChatCompletionMessageParam] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)

    try:
        resp = await aclient.chat.completions.create(
            model=MODEL,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise LLMError(str(e))

    content = (resp.choices[0].message.content or "").strip()
    # 直接尝试 JSON 解析
    try:
        return json.loads(content)
    except Exception:
        # 让模型把上条回答转成 JSON
        fix_msgs: List[ChatCompletionMessageParam] = msgs + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": (
                    "上面不是严格 JSON。"
                    "请只输出一个 JSON 对象，不要包含解释或代码块。"
                ),
            },
        ]
        try:
            resp2 = await aclient.chat.completions.create(
                model=MODEL,
                messages=fix_msgs,
                temperature=0.0,
                max_tokens=max_tokens,
            )
            return json.loads((resp2.choices[0].message.content or "").strip())
        except Exception as e:
            raise LLMError(f"JSON 解析失败：{e}")
