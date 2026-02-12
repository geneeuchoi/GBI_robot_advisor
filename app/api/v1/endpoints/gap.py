from fastapi import APIRouter

from app.models.gap import GapAnalysisResult
from app.models.goal import GoalInput
from app.services.gap_analyzer import analyze_gap

router = APIRouter()


@router.post("/gap-analysis", response_model=GapAnalysisResult)
def gap_analysis(goal: GoalInput) -> GapAnalysisResult:
    """Phase 2: 갭 분석 — 안전자산만으로 목표 달성이 가능한지 판단한다."""
    return analyze_gap(goal)
