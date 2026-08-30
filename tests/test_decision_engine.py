from app.models.schemas import (
    CurrentWeather,
    DailyForecast,
    Location,
    ModelAgreement,
    RiskAssessment,
    SourceInfo,
    WeatherBundle,
)
from app.services.decision_engine import build_decision_answer


def make_bundle(rain_probability=85, rain_mm=18, wind=24):
    return WeatherBundle(
        location=Location(name="Mysuru", latitude=12.2958, longitude=76.6394),
        current=CurrentWeather(temperature_c=28, wind_speed_kmh=12),
        forecast=[
            DailyForecast(
                date="2026-08-30",
                temperature_max_c=30,
                temperature_min_c=21,
                precipitation_probability_max_pct=20,
                precipitation_sum_mm=1,
                wind_speed_max_kmh=12,
            ),
            DailyForecast(
                date="2026-08-31",
                temperature_max_c=29,
                temperature_min_c=20,
                precipitation_probability_max_pct=rain_probability,
                precipitation_sum_mm=rain_mm,
                wind_speed_max_kmh=wind,
            ),
        ],
        alerts=[],
        agreement=ModelAgreement(score=82, label="high", summary="High agreement", models=[]),
        risk=RiskAssessment(score=45, level="moderate", factors=[], explanation="test"),
        sources=[SourceInfo(name="test", type="test", fetched_at="2026-08-30T00:00:00Z")],
    )


def test_pesticide_advisory_rejects_rainy_window():
    bundle = make_bundle()
    parsed = {"intent": "activity_advisory", "activity": "pesticide spraying", "time_window": "tomorrow"}
    answer, action, override = build_decision_answer(bundle, parsed, "farmer", "en")
    assert action == "not_recommended"
    assert not override
    assert "Rain probability" in answer
