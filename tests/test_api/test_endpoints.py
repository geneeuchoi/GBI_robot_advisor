import pytest


NOAH_PAYLOAD = {
    "goal_amount": 1_0000_0000,
    "time_horizon_months": 60,
    "monthly_contribution": 150_0000,
    "initial_principal": 0,
    "eligible_youth_savings": True,
}


class TestGapAnalysisEndpoint:
    def test_gap_analysis(self, client):
        resp = client.post("/api/v1/gap-analysis", json=NOAH_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["optimization_needed"] is True
        assert data["gap"] > 0


class TestAssetsEndpoint:
    def test_list_assets_without_youth(self, client):
        resp = client.get("/api/v1/assets")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5
        names = [a["asset_class"] for a in data]
        assert "youth_savings" not in names

    def test_list_assets_with_youth(self, client):
        resp = client.get("/api/v1/assets?eligible_youth_savings=true")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 6
        names = [a["asset_class"] for a in data]
        assert "youth_savings" in names


class TestOptimizeEndpoint:
    def test_optimize_noah(self, client):
        resp = client.post("/api/v1/optimize", json=NOAH_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["allocations"]) > 0
        total_weight = sum(a["weight"] for a in data["allocations"])
        assert abs(total_weight - 1.0) < 0.01

    def test_optimize_easy_goal(self, client):
        easy = {
            "goal_amount": 1000_0000,
            "time_horizon_months": 60,
            "monthly_contribution": 150_0000,
        }
        resp = client.post("/api/v1/optimize", json=easy)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["message"] == "안전자산만으로 목표 달성 가능합니다."


class TestSimulateEndpoint:
    def test_simulate_noah(self, client):
        payload = {
            "goal_amount": 1_0000_0000,
            "time_horizon_months": 60,
            "monthly_contribution": 150_0000,
            "initial_principal": 0,
            "eligible_youth_savings": True,
        }
        resp = client.post("/api/v1/simulate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 4
        assert data["base_rate"] == 0.035


class TestValidation:
    def test_invalid_goal_amount(self, client):
        payload = {**NOAH_PAYLOAD, "goal_amount": -100}
        resp = client.post("/api/v1/optimize", json=payload)
        assert resp.status_code == 422
