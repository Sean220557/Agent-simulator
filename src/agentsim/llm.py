import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
import google.generativeai as genai

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").lower()

aclient = None
gemini_model = None

if LLM_PROVIDER == "deepseek":
    API_KEY = os.getenv("DEEPSEEK_API_KEY")
    BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    if not API_KEY:
        raise RuntimeError("LLM_PROVIDER=deepseek, 但 DEEPSEEK_API_KEY 未设置。")
    aclient = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    print("--- LLM Provider: DeepSeek ---")

elif LLM_PROVIDER == "gemini":
    API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not API_KEY:
        raise RuntimeError("LLM_PROVIDER=gemini, 但 GEMINI_API_KEY 未设置。")
    genai.configure(api_key=API_KEY)
    # Gemini 安全设置，防止因内容审查而中断
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    gemini_model = genai.GenerativeModel(MODEL, safety_settings=safety_settings)
    print("--- LLM Provider: Gemini ---")

else:
    raise RuntimeError(f"不支持的 LLM_PROVIDER: {LLM_PROVIDER}")



class LLMError(Exception):
    pass

async def _call_llm(
    messages: List[ChatCompletionMessageParam],
    temperature: float,
    max_tokens: Optional[int],
) -> str:
    """
    根据全局配置调用相应的 LLM 服务并返回文本响应。
    """
    if LLM_PROVIDER == "deepseek":
        if not aclient:
            raise RuntimeError("DeepSeek 客户端未初始化。")
        resp = await aclient.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()

    elif LLM_PROVIDER == "gemini":
        if not gemini_model:
            raise RuntimeError("Gemini 模型未初始化。")
        
        # Gemini 的消息格式与 OpenAI 不同，需要转换
        gemini_messages = []
        for msg in messages:
            # 忽略 system message，将其内容合并到第一个 user message 中
            if msg["role"] == "system":
                continue
            role = "user" if msg["role"] == "user" else "model"
            if gemini_messages and gemini_messages[-1]["role"] == role:
                gemini_messages[-1]["parts"].append(msg["content"])
            else:
                gemini_messages.append({"role": role, "parts": [msg["content"]]})
        
        # 将 system prompt 的内容加到第一个 user prompt 前面
        system_prompt = next((m['content'] for m in messages if m['role'] == 'system'), None)
        if system_prompt and gemini_messages:
            gemini_messages[0]['parts'].insert(0, f"{system_prompt}\n\n---\n\n")

        resp = await gemini_model.generate_content_async(gemini_messages)
        return resp.text.strip()
    
    else:
        raise RuntimeError(f"LLM_PROVIDER 配置错误: {LLM_PROVIDER}")


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
        content = await _call_llm(msgs, temperature, max_tokens)
    except Exception as e:
        raise LLMError(str(e))

    # 直接尝试 JSON 解析
    try:
        return json.loads(content)
    except Exception as first_err:
        # 尝试提取可能被截断的JSON（去掉末尾不完整部分）
        try:
            # 找到最后一个完整的 '}' 或 ']'，尝试截断后解析
            for i in range(len(content)-1, -1, -1):
                if content[i] in ('}', ']'):
                    truncated = content[:i+1]
                    try:
                        return json.loads(truncated)
                    except Exception:
                        continue
        except Exception:
            pass
        
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
            content2 = await _call_llm(fix_msgs, 0.0, max_tokens)
            return json.loads(content2)
        except Exception as e:
            raise LLMError(f"JSON 解析失败：{e}")