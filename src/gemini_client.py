import os
from typing import List, Dict
import google.generativeai as genai

# 从环境变量中获取并配置 Gemini API 密钥
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # 如果未设置密钥，只打印警告而不是直接报错，以便用户仍然可以使用 deepseek
    print("警告: 环境变量 GEMINI_API_KEY 未设置。Gemini 客户端将不可用。")
    model = None
else:
    genai.configure(api_key=api_key)

    # 配置并创建模型，使用 gemini-1.5-flash 以获得较好的速度和成本效益
    # 注意：Gemini 对安全设置更严格，这里放宽限制以适应模拟需求
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
    
    注意：Gemini 的消息格式与 OpenAI/DeepSeek 不同，这里做了转换。
    Gemini 不希望连续出现相同角色的消息。
    """
    if not model:
        raise RuntimeError("Gemini 模型未初始化，请检查 GEMINI_API_KEY。")

    # 将 DeepSeek/OpenAI 格式的消息转换为 Gemini 格式
    # Gemini 的 'user' 和 'model' 角色必须交替出现
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
        # 捕获并打印潜在的 API 错误，例如内容被阻止
        print(f"调用 Gemini API 时出错: {e}")
        # 返回一个空的 JSON 字符串，让上层逻辑进行重试
        return "{}"