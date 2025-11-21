# app/ai_match.py
import os
import json
from flask import Blueprint, request, jsonify
from openai import OpenAI
from app.models import LostItem, FoundItem

ai_bp = Blueprint("ai", __name__)

def build_item_text(item, tag):
    """
    하나의 물품 정보를 텍스트 한 줄로 변환합니다.
    tag: 'lost' 또는 'found'
    """
    return (
        f"[{tag}] "
        f"name={item.name or ''}; "
        f"category={item.category or ''}; "
        f"place={item.place or ''}; "
        f"date={item.date or ''}; "
        f"description={item.description or ''}"
    )

@ai_bp.route("/ai/match", methods=["POST"])
def ai_match():
    """
    경량 AI 매칭 기능 (OpenAI 사용)
    요청: {"text": "..."}
    응답: [{ "type": "lost|found", "name": "...", "score": 0.87 }, ...]
    """
    data = request.get_json() or {}
    user_text = (data.get("text") or "").strip()

    if not user_text:
        return jsonify([])

    # DB 의 모든 물품을 텍스트 형태로 변환
    lines = []
    for item in LostItem.query.all():
        lines.append(build_item_text(item, "lost"))
    for item in FoundItem.query.all():
        lines.append(build_item_text(item, "found"))

    if not lines:
        return jsonify([])

    db_text = "\n".join(lines)

    # 프롬프트 생성
    prompt = f"""
당신은 분실물 자동 매칭 도우미입니다.
사용자가 입력한 설명을 보고 DB 목록에서 가장 유사한 최대 5개 물품을 찾으세요.

### 출력 형식
- 반드시 **JSON 배열만** 출력하세요.
- 배열의 각 항목은 다음을 포함해야 합니다:
  - "type": "lost" 또는 "found"
  - "name": 물품 이름
  - "score": 0~1 사이 숫자 (유사도)

### 사용자 입력
{user_text}

### DB 목록
{db_text}
"""

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "JSON 형식만 반환하는 분실물 매칭 도우미입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        content = resp.choices[0].message.content.strip()

        # JSON 파싱 시도
        try:
            results = json.loads(content)
            if not isinstance(results, list):
                results = []
        except Exception:
            results = []

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

