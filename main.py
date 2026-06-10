"""Claude API + Tool Calling 미니 데모 — CLI 대화 봇.

날씨/검색 mock 함수를 Tool Calling으로 호출해 자연어 질문에 답한다.
multi-turn 대화를 유지하며, 모델이 도구를 부르면 결과를 받아 다시
모델에게 넘기는 manual tool-use 루프를 돈다.

실행:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...   # 또는 .env 사용
    python main.py
"""

import os
import sys

import anthropic

from tools import TOOLS, run_tool

MODEL = "claude-opus-4-8"  # 비용을 줄이려면 "claude-haiku-4-5" 로 바꿔도 된다.
MAX_TOKENS = 2000

# system 프롬프트: 한국어가 자연스럽게 나오도록 유도한다.
# (윤문 하네스 지식을 반영 — 번역투/기계적 나열/AI 관용구/장식 남용을 피한다.)
SYSTEM = """너는 한국어로 대화하는 친근한 비서다. 날씨와 웹 검색 도구를 쓸 수 있다.

답변은 사람이 말하듯 자연스럽게 한다.
- 번역투를 쓰지 않는다: "~를 통해", "~에 의해", "~에 있어서" 같은 표현을 피한다.
- "첫째, 둘째, 셋째" 식 기계적 나열이나 "결론적으로", "~하는 바이다" 같은
  틀에 박힌 관용구를 쓰지 않는다.
- 이모지, 볼드, 불릿을 남발하지 않는다. 짧고 담백하게 답한다.
- 도구로 얻은 사실(날씨 수치, 검색 결과)은 자연스러운 문장에 녹여서 전한다.
- 모르면 모른다고 솔직히 말한다. 없는 수치를 지어내지 않는다.

날씨나 최신 정보가 필요한 질문은 반드시 도구를 먼저 호출하고, 그 결과를 바탕으로 답한다."""


def load_dotenv(path=".env"):
    """.env 파일이 있으면 KEY=VALUE 줄을 읽어 환경변수로 올린다.

    python-dotenv 같은 외부 의존성 없이 동작하도록 직접 파싱한다.
    이미 환경에 설정된 값은 덮어쓰지 않는다.
    """
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip("'\"")
            os.environ.setdefault(key, value)


def get_client():
    """API 키를 확인하고 Anthropic 클라이언트를 만든다.

    키가 없으면 친절히 안내하고 None을 돌려준다 (크래시 방지).
    """
    load_dotenv()  # .env 가 있으면 먼저 읽어들인다.
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("환경변수 ANTHROPIC_API_KEY가 없습니다.")
        print("  예) export ANTHROPIC_API_KEY=sk-ant-...")
        print("  키를 발급받아 설정한 뒤 다시 실행해 주세요.")
        return None
    return anthropic.Anthropic()


def chat_once(client, messages):
    """한 번의 사용자 발화에 대해 답할 때까지 tool-use 루프를 돈다.

    모델이 도구를 부르면(stop_reason == "tool_use") 실행 결과를 돌려주고,
    더 이상 도구를 부르지 않을 때까지 반복한다.
    messages 리스트는 호출 측에서 계속 재사용되며, 이 함수가 대화 기록을
    이어붙인다(multi-turn 유지).
    """
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        # 모델 응답(도구 호출 포함)을 기록에 남긴다.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        # 이번 응답에 들어 있는 모든 도구 호출을 실행한다.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [도구 호출] {block.name}({block.input})")
                result = run_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        # 도구 결과를 user 메시지로 돌려주고 루프를 계속한다.
        messages.append({"role": "user", "content": tool_results})

    # 최종 응답에서 텍스트만 모아 돌려준다.
    return "".join(b.text for b in response.content if b.type == "text")


def main():
    client = get_client()
    if client is None:
        sys.exit(1)

    print("날씨·검색 봇입니다. 무엇이든 물어보세요. (종료: quit 또는 Ctrl-C)")
    print('예) "서울 날씨 어때?", "트랜스포머 모델 검색해줘"\n')

    messages = []  # 대화 전체 기록 (multi-turn)
    while True:
        try:
            user_input = input("나: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n안녕히 가세요.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "종료"):
            print("안녕히 가세요.")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            answer = chat_once(client, messages)
        except anthropic.APIError as e:
            print(f"  [오류] API 호출 실패: {e}")
            continue

        print(f"봇: {answer}\n")


if __name__ == "__main__":
    main()
