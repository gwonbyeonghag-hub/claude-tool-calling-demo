# Tool Calling 미니 데모 — 날씨·검색 대화 봇

Claude API의 **Tool Calling(도구 호출)** 을 써서, 자연어 질문에 답할 때
필요한 함수(날씨 조회·웹 검색)를 모델이 스스로 골라 부르는 작은 CLI 대화 봇이다.

> 필수 요건 두 가지를 실제로 충족한다: **(1) LLM API 활용**, **(2) Tool Calling**.
> 도구는 외부 키 없이 동작하는 mock 함수라, 키만 있으면 데모가 항상 재현된다.

## 무엇을 보여주는가

- 사용자가 `"서울 날씨 어때?"`라고 물으면 → 모델이 `get_weather` 도구를
  호출 → 결과를 받아 자연스러운 한국어 문장으로 답한다.
- `"트랜스포머 검색해줘"` → `web_search` 도구 호출 → 검색 결과를 정리해 답한다.
- 이전 대화 맥락을 기억하는 **multi-turn** 대화.

## Tool Calling 흐름 (핵심)

모델 혼자서는 날씨를 모른다. 대신 "이런 도구가 있다"고 알려주면, 모델이
필요할 때 도구를 **호출하겠다는 신호**를 보내고, 우리가 실행한 결과를 다시
넘겨주면 그제야 최종 답을 만든다. 한 번의 질문이 보통 이 4단계를 거친다.

```
1) 사용자 질문        "서울 날씨 어때?"
        │
2) 모델: tool_use     get_weather(location="서울") 를 부르겠다고 응답
        │             (stop_reason == "tool_use")
        │
3) 우리 코드          run_tool 로 실제 함수 실행 →
   : tool_result      "서울 날씨: 맑음, 기온 24도..." 를 모델에게 돌려줌
        │
4) 모델: 최종 답변     도구 결과를 녹여 자연스러운 문장으로 답
                      (stop_reason == "end_turn")
```

`main.py`의 `chat_once()`가 2~3단계를 `stop_reason`이 `tool_use`인 동안
계속 도는 루프로 구현한다. 그래서 모델이 도구를 여러 번 연달아 불러도 된다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `main.py` | CLI 대화 루프 + tool-use 루프 + 자연스러운 한국어 system 프롬프트 |
| `tools.py` | `get_weather`, `web_search` mock 함수와 도구 스키마(`TOOLS`) |
| `requirements.txt` | 의존성 (`anthropic`) |
| `.env.example` | API 키 설정 예시 |
| `demo.html` | iMessage 스타일 시각 데모 (API 없이 브라우저로 흐름 재생) |

## 빠르게 보기 (API 불필요)

`demo.html`을 브라우저로 열면, 위 흐름이 iMessage 스타일 화면에서 타이핑
애니메이션과 함께 재생된다. 가운데 회색 칩이 모델이 도구를 호출하는 순간을
보여준다. 키도 비용도 필요 없으니 스크린샷·GIF용으로 좋다. (시각용 목업이며
실제 API는 호출하지 않는다.)

```bash
open demo.html        # macOS
```

## 실행 방법 (실제 봇)

```bash
# 1) 의존성 설치 (가상환경 권장)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) API 키 설정 (둘 중 하나)
cp .env.example .env                    # .env 에 키를 넣으면 자동으로 읽는다
# 또는: export ANTHROPIC_API_KEY=sk-ant-...
# 키가 없으면 크래시하지 않고 설정 방법을 안내한 뒤 종료한다

# 3) 실행
python main.py
```

실행 예시:

```
나: 서울 날씨 어때?
  [도구 호출] get_weather({'location': '서울'})
봇: 지금 서울은 맑고 기온은 24도예요. 체감은 25도라 나들이하기 좋겠네요.

나: 트랜스포머 모델이 뭔지 검색해줘
  [도구 호출] web_search({'query': '트랜스포머 모델'})
봇: 찾아보니 트랜스포머는 ... (검색 결과를 정리해 답변)
```

## 설계 메모

- **모델**: `claude-opus-4-8` 기본값. 비용을 줄이려면 `main.py`의 `MODEL`을
  `claude-haiku-4-5`로 바꾸면 된다.
- **mock 도구**: 외부 API·키 없이 동작하도록 가짜 데이터를 돌려준다.
  실제 서비스로 만들려면 `tools.py`의 함수 본문만 진짜 API 호출(예: 날씨는
  키가 필요 없는 Open-Meteo)로 교체하면 된다.
- **자연스러운 답변**: 번역투·기계적 나열·AI 관용구·장식 남용을 피하도록
  system 프롬프트로 유도한다.
- **키 없을 때**: 크래시하지 않고 설정 방법을 안내한 뒤 종료한다.

## 다음으로 해볼 만한 것

- 도구 결과를 실시간으로 흘려보내는 **streaming** 응답
- 날씨를 실제 API로 연결 (mock → 진짜)
- 도구 추가 (환율, 시간대, 계산기 등)
