# app/ai_match.py
from flask import Blueprint, request, jsonify
from sentence_transformers import SentenceTransformer, util
from app.models import LostItem, FoundItem

ai_bp = Blueprint("ai", __name__)

# 加载句向量模型（轻量快速）
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

@ai_bp.route("/ai/match", methods=["POST"])
def ai_match():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify([])

    # 输入向量
    query_vec = model.encode(text)

    results = []

    # 遍历失物
    for item in LostItem.query.all():
        src = f"{item.name} {item.description or ''}"
        score = util.cos_sim(query_vec, model.encode(src)).item()
        results.append({
            "type": "lost",
            "name": item.name,
            "score": round(score, 4)
        })

    # 遍历拾得物
    for item in FoundItem.query.all():
        src = f"{item.name} {item.description or ''}"
        score = util.cos_sim(query_vec, model.encode(src)).item()
        results.append({
            "type": "found",
            "name": item.name,
            "score": round(score, 4)
        })

    # 按相似度排序并返回前5项
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:5]
    return jsonify(results)

