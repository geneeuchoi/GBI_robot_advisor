import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.goal import GoalInput


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def noah_goal():
    """노아 페르소나: 25세 신입사원, 5년 뒤 1억 목표, 월 150만원."""
    return GoalInput(
        goal_amount=1_0000_0000,
        time_horizon_months=60,
        monthly_contribution=150_0000,
        initial_principal=0,
        eligible_youth_savings=True,
    )
