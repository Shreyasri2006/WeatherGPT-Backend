from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.schemas import CurrentWeather, DailyForecast, RiskAssessment, RiskFactor, WeatherAlert


def derive_alerts(current: CurrentWeather, forecast: list[DailyForecast]) -> list[WeatherAlert]:
    """Prototype derived hazards. These are NOT official IMD warnings."""
    alerts: list[WeatherAlert] = []
    now = datetime.now(timezone.utc)
    today = forecast[0] if forecast else None

    rain_prob = today.precipitation_probability_max_pct if today else None
    rain_sum = today.precipitation_sum_mm if today else None
    gust = max(
        [x for x in [current.wind_gust_kmh, today.wind_gust_max_kmh if today else None] if isinstance(x, (int, float))]
        or [0]
    )
    code = today.weather_code if today else current.weather_code

    if code in {95, 96, 99}:
        alerts.append(
            WeatherAlert(
                id=str(uuid4()),
                severity="high",
                hazard="thunderstorm",
                title="Thunderstorm risk detected",
                message="Forecast data indicates thunderstorm conditions. Check official IMD warnings before outdoor activity.",
                official=False,
                source="WeatherGPT derived risk",
                issued_at=now.isoformat(),
                valid_until=(now + timedelta(hours=24)).isoformat(),
                safety_actions=["Avoid exposed outdoor areas during lightning", "Check official local warnings"],
            )
        )
    if (rain_prob or 0) >= 80 and (rain_sum or 0) >= 25:
        alerts.append(
            WeatherAlert(
                id=str(uuid4()),
                severity="high" if (rain_sum or 0) < 60 else "severe",
                hazard="heavy_rain",
                title="Heavy-rain risk detected",
                message=f"Forecast suggests about {rain_sum:.1f} mm rain with {rain_prob:.0f}% maximum daily probability.",
                official=False,
                source="WeatherGPT derived risk",
                issued_at=now.isoformat(),
                valid_until=(now + timedelta(hours=24)).isoformat(),
                safety_actions=["Avoid waterlogged routes", "Monitor official flood/rain warnings"],
            )
        )
    if gust >= 55:
        alerts.append(
            WeatherAlert(
                id=str(uuid4()),
                severity="high" if gust < 75 else "severe",
                hazard="strong_wind",
                title="Strong-wind risk detected",
                message=f"Wind gusts may reach around {gust:.0f} km/h.",
                official=False,
                source="WeatherGPT derived risk",
                issued_at=now.isoformat(),
                valid_until=(now + timedelta(hours=24)).isoformat(),
                safety_actions=["Secure loose outdoor objects", "Use caution on exposed roads"],
            )
        )
    if today and (today.temperature_max_c or 0) >= 40:
        alerts.append(
            WeatherAlert(
                id=str(uuid4()),
                severity="high",
                hazard="heat",
                title="High-heat risk detected",
                message=f"Maximum temperature may reach {today.temperature_max_c:.1f}°C.",
                official=False,
                source="WeatherGPT derived risk",
                issued_at=now.isoformat(),
                valid_until=(now + timedelta(hours=24)).isoformat(),
                safety_actions=["Limit strenuous afternoon activity", "Hydrate frequently"],
            )
        )
    return alerts


def assess_risk(current: CurrentWeather, forecast: list[DailyForecast], alerts: list[WeatherAlert]) -> RiskAssessment:
    today = forecast[0] if forecast else None
    factors: list[RiskFactor] = []
    score = 5

    if today:
        rain = today.precipitation_sum_mm or 0
        rain_prob = today.precipitation_probability_max_pct or 0
        if rain >= 20 or rain_prob >= 75:
            contribution = min(30, round(rain * 0.4 + rain_prob * 0.15))
            score += contribution
            factors.append(RiskFactor(name="Rainfall", contribution=contribution, detail=f"{rain:.1f} mm / {rain_prob:.0f}% probability"))

        gust = today.wind_gust_max_kmh or current.wind_gust_kmh or 0
        if gust >= 35:
            contribution = min(25, round((gust - 25) * 0.45))
            score += contribution
            factors.append(RiskFactor(name="Wind", contribution=contribution, detail=f"Gusts up to {gust:.0f} km/h"))

        if today.weather_code in {95, 96, 99}:
            score += 25
            factors.append(RiskFactor(name="Thunderstorm", contribution=25, detail="Thunderstorm weather code present"))

        if (today.temperature_max_c or 0) >= 40:
            score += 20
            factors.append(RiskFactor(name="Heat", contribution=20, detail=f"Max {today.temperature_max_c:.1f}°C"))

    official_severe = [a for a in alerts if a.official and a.severity in {"severe", "extreme"}]
    if official_severe:
        score = max(score, 90)
        factors.append(RiskFactor(name="Official warning", contribution=35, detail="Severe/extreme official warning active"))

    score = max(0, min(100, score))
    level = "low" if score < 25 else "moderate" if score < 50 else "high" if score < 70 else "severe" if score < 90 else "extreme"
    explanation = "Risk is calculated from forecast rainfall, wind, thunderstorm/heat signals and any official severe warning."
    return RiskAssessment(score=score, level=level, factors=factors, explanation=explanation)
