import os
from typing import List, Dict
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("警告: 环境变量 GEMINI_API_KEY 未设置。Gemini 客户端将不可用。")
    model = None
else:
    genai.configure(api_key=api_key)

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        safety_settings=safety_settings
    )

def prompt(messages: List[Dict[str, str]]) -> str:
    """
    向 Gemini 模型发送提示并返回响应内容。
    
    Gemini 不希望连续出现相同角色的消息。
    """
    if not model:
        raise RuntimeError("Gemini 模型未初始化，请检查 GEMINI_API_KEY。")

    gemini_messages = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        # 如果新消息的角色与上一条相同，则将内容合并
        if gemini_messages and gemini_messages[-1]["role"] == role:
            gemini_messages[-1]["parts"].append(msg["content"])
        else:
            gemini_messages.append({"role": role, "parts": [msg["content"]]})

    try:
        response = model.generate_content(gemini_messages)
        return response.text
    except Exception as e:
        print(f"调用 Gemini API 时出错: {e}")
        return "{}"