# =====================================================
# 🧮 utils.py — 공통 상수 / 통계 함수
# =====================================================

from collections import defaultdict
from .models import db, LostItem, FoundItem

# 🔹 카테고리 목록 (원하는 대로 수정 가능)
CATEGORIES = [
    "지갑", "카드", "열쇠", "전자기기", "가방", "신분증", "의류", "기타"
]

# 🔹 장소 예시 (검색/통계용, 필요한 만큼 추가 가능)
LOCATIONS = [
    "도서관", "강의실", "기숙사", "식당", "체육관", "행정실", "카페", "기타"
]


def statistics_data():
    """
    전체 분실물/습득물 통계 데이터를 계산하는 함수
    반환:
      total_lost, total_found,
      lost_stats (카테고리별 분실 수),
      found_stats (카테고리별 습득 수),
      location_stats = { 장소: {"lost": x, "found": y} }
    """
    # 전체 개수
    total_lost = LostItem.query.count()
    total_found = FoundItem.query.count()

    # 카테고리별 통계
    lost_stats = defaultdict(int)
    found_stats = defaultdict(int)

    for item in LostItem.query.all():
        lost_stats[item.category or "기타"] += 1

    for item in FoundItem.query.all():
        found_stats[item.category or "기타"] += 1

    # 장소별 통계
    location_stats = defaultdict(lambda: {"lost": 0, "found": 0})

    for item in LostItem.query.all():
        key = item.place or "기타"
        location_stats[key]["lost"] += 1

    for item in FoundItem.query.all():
        key = item.place or "기타"
        location_stats[key]["found"] += 1

    # dict 로 변환해서 반환
    return (
        total_lost,
        total_found,
        dict(lost_stats),
        dict(found_stats),
        dict(location_stats)
    )

