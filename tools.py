"""Tool Calling 데모에서 쓰는 mock 도구 모음.

실제 외부 API를 호출하지 않고, 결정적인 가짜 데이터를 돌려준다.
이렇게 하면 API 키나 네트워크 없이도 Tool Calling의 전체 흐름
(모델이 도구를 고르고 -> 함수가 실행되고 -> 결과를 답변에 반영)을
항상 동일하게 재현할 수 있다. 나중에 함수 본문만 실제 API 호출로
교체하면 그대로 진짜 봇이 된다.
"""


# --- 실제 실행 함수 (mock) ---

# 도시별 가짜 날씨. 목록에 없는 도시는 기본값으로 대응한다.
_WEATHER = {
    "서울": {"날씨": "맑음", "기온": 24, "체감": 25, "습도": 45},
    "부산": {"날씨": "구름 조금", "기온": 26, "체감": 28, "습도": 60},
    "제주": {"날씨": "비", "기온": 21, "체감": 22, "습도": 80},
    "도쿄": {"날씨": "흐림", "기온": 19, "체감": 18, "습도": 55},
    "파리": {"날씨": "맑음", "기온": 17, "체감": 16, "습도": 40},
}


def get_weather(location: str) -> str:
    """도시 이름을 받아 가짜 날씨 정보를 문자열로 돌려준다."""
    city = location.strip()
    data = _WEATHER.get(city)
    if data is None:
        # 모르는 도시는 적당한 기본값으로 답한다 (데모가 끊기지 않도록).
        return (
            f"{city}의 날씨 정보는 데이터에 없어 임의값으로 답합니다. "
            "맑음, 기온 20도, 습도 50%."
        )
    return (
        f"{city} 날씨: {data['날씨']}, 기온 {data['기온']}도 "
        f"(체감 {data['체감']}도), 습도 {data['습도']}%."
    )


def web_search(query: str) -> str:
    """검색어를 받아 가짜 검색 결과 3건을 문자열로 돌려준다."""
    q = query.strip()
    results = [
        f"[1] {q} 개요 — {q}에 대한 기본 설명과 핵심 정리.",
        f"[2] {q} 최신 동향 — 최근 자주 언급되는 내용 요약.",
        f"[3] {q} 자주 묻는 질문 — 입문자가 헷갈려 하는 지점 정리.",
    ]
    return "\n".join(results)


# --- 모델에게 넘길 도구 스키마 ---
# name 은 아래 dispatch 의 함수 이름과 정확히 일치해야 한다.

TOOLS = [
    {
        "name": "get_weather",
        "description": (
            "특정 도시의 현재 날씨를 조회한다. 사용자가 날씨, 기온, "
            "비/눈 여부 등을 물을 때 호출한다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "도시 이름. 예: 서울, 부산, 도쿄",
                }
            },
            "required": ["location"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "웹을 검색해 관련 정보를 찾는다. 모델이 모르거나 최신 정보가 "
            "필요한 주제를 사용자가 물을 때 호출한다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색할 키워드 또는 질문",
                }
            },
            "required": ["query"],
        },
    },
]


# 이름 -> 실제 함수 매핑. main 의 tool-use 루프가 이걸로 실행한다.
_DISPATCH = {
    "get_weather": get_weather,
    "web_search": web_search,
}


def run_tool(name: str, tool_input: dict) -> str:
    """모델이 고른 도구 이름과 입력을 받아 실제 함수를 실행한다."""
    func = _DISPATCH.get(name)
    if func is None:
        return f"알 수 없는 도구입니다: {name}"
    try:
        return func(**tool_input)
    except TypeError as e:
        # 모델이 스키마와 다른 인자를 넘긴 경우의 방어 코드.
        return f"도구 입력이 올바르지 않습니다: {e}"
