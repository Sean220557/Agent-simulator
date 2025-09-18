import argparse
import os
from dotenv import load_dotenv
from src.deepseek_client import chat_once, chat_stream  # ← 关键修改

load_dotenv()

DEFAULT_SYSTEM = os.getenv("SYSTEM_PROMPT", "You are a helpful assistant.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DeepSeek Chat CLI")
    p.add_argument("prompt", type=str, nargs="?", help="要发送给 LLM 的提示词；若省略则从标准输入读取")
    p.add_argument("-s", "--stream", action="store_true", help="启用流式输出")
    p.add_argument("-t", "--temperature", type=float, default=0.7, help="随机性（0.0-2.0）")
    p.add_argument("-m", "--max-tokens", type=int, default=None, help="生成的最大 token 数")
    p.add_argument("--system", type=str, default=DEFAULT_SYSTEM,
                   help="系统提示词（可覆盖 .env 中的 SYSTEM_PROMPT）")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.prompt:
        try:
            args.prompt = input("请输入 prompt：")
        except KeyboardInterrupt:
            return

    if args.stream:
        for piece in chat_stream(
            prompt=args.prompt,
            system=args.system,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        ):
            print(piece, end="", flush=True)
        print()  # 换行
    else:
        text = chat_once(
            prompt=args.prompt,
            system=args.system,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        print(text)


if __name__ == "__main__":
    main()
