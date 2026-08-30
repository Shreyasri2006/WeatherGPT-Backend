from __future__ import annotations

from app.models.schemas import WeatherBundle
from app.utils.weather_codes import describe_weather_code


TRANSLATIONS = {
    "hi": {
        "not_recommended": "अनुशंसित नहीं",
        "caution": "सावधानी",
        "recommended": "अनुशंसित",
        "information": "जानकारी",
        "official_warning": "आधिकारिक गंभीर मौसम चेतावनी सक्रिय है। सुरक्षा निर्देशों को प्राथमिकता दें।",
    },
    "kn": {
        "not_recommended": "ಶಿಫಾರಸು ಮಾಡಲಾಗುವುದಿಲ್ಲ",
        "caution": "ಎಚ್ಚರಿಕೆ",
        "recommended": "ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ",
        "information": "ಮಾಹಿತಿ",
        "official_warning": "ಅಧಿಕೃತ ಗಂಭೀರ ಹವಾಮಾನ ಎಚ್ಚರಿಕೆ ಸಕ್ರಿಯವಾಗಿದೆ. ಸುರಕ್ಷತಾ ಸೂಚನೆಗಳಿಗೆ ಆದ್ಯತೆ ನೀಡಿ.",
    },
}


def _forecast_day(bundle: WeatherBundle, time_window: str):
    if not bundle.forecast:
        return None
    return bundle.forecast[1] if time_window == "tomorrow" and len(bundle.forecast) > 1 else bundle.forecast[0]


def _activity_action(activity: str | None, bundle: WeatherBundle, day) -> tuple[str, list[str]]:
    if not day:
        return "information", ["Forecast data is not available for the requested period."]

    rain_prob = day.precipitation_probability_max_pct or 0
    rain = day.precipitation_sum_mm or 0
    wind = day.wind_speed_max_kmh or 0
    gust = day.wind_gust_max_kmh or 0
    code = day.weather_code
    thunder = code in {95, 96, 99}
    reasons: list[str] = []

    if activity == "pesticide spraying":
        if thunder or rain_prob >= 60 or rain >= 5 or wind >= 20:
            reasons.append(f"Rain probability is up to {rain_prob:.0f}% with around {rain:.1f} mm forecast precipitation.")
            if wind >= 20:
                reasons.append(f"Wind may reach {wind:.0f} km/h, increasing spray-drift risk.")
            if thunder:
                reasons.append("Thunderstorm conditions create an outdoor lightning risk.")
            return "not_recommended", reasons
        return "recommended", ["Rain and wind indicators are currently within the prototype's advisory thresholds."]

    if activity == "irrigation":
        if rain_prob >= 60 or rain >= 10:
            return "not_recommended", [f"About {rain:.1f} mm rain is forecast with up to {rain_prob:.0f}% probability; irrigation may be unnecessary."]
        return "recommended", ["No substantial forecast rainfall is currently indicated."]

    if activity == "fishing":
        if thunder or gust >= 40 or bundle.risk.level in {"high", "severe", "extreme"}:
            return "not_recommended", [f"Wind gusts may reach {gust:.0f} km/h and overall weather risk is {bundle.risk.level}."]
        return "caution", ["Marine decisions require official marine/fishermen bulletins; prototype land-model guidance alone is insufficient."]

    if activity in {"travel", "outdoor event"}:
        if thunder or bundle.risk.score >= 70:
            return "not_recommended", [f"Overall weather risk is {bundle.risk.level}; severe weather indicators are present."]
        if rain_prob >= 50 or bundle.risk.score >= 40:
            return "caution", [f"Rain probability reaches {rain_prob:.0f}%; allow extra time and monitor updates."]
        return "recommended", ["Current forecast signals show relatively low weather disruption risk."]

    if bundle.risk.score >= 70:
        return "caution", [f"Overall weather risk is currently {bundle.risk.level}."]
    return "information", ["No specific activity was identified, so this is an informational weather summary."]


def build_decision_answer(bundle: WeatherBundle, parsed: dict, persona: str, language: str) -> tuple[str, str, bool]:
    severe_official = [a for a in bundle.alerts if a.official and a.severity in {"high", "severe", "extreme"}]
    safety_override = bool(severe_official)
    day = _forecast_day(bundle, parsed.get("time_window", "today"))
    activity = parsed.get("activity")

    action, reasons = _activity_action(activity, bundle, day)
    if safety_override:
        action = "not_recommended"
        reasons.insert(0, "An official high/severe weather warning is active, so the safety layer overrides normal activity advice.")

    condition = describe_weather_code(day.weather_code if day else bundle.current.weather_code)
    location_name = bundle.location.name
    agreement = bundle.agreement

    if language == "en":
        header = action.replace("_", " ").upper()
        lines = [
            f"{header} — {location_name}",
            f"Forecast: {condition}.",
        ]
        if day:
            lines.append(
                f"Temperature {day.temperature_min_c if day.temperature_min_c is not None else '—'}–{day.temperature_max_c if day.temperature_max_c is not None else '—'}°C; "
                f"rain probability up to {day.precipitation_probability_max_pct if day.precipitation_probability_max_pct is not None else '—'}%."
            )
        lines.append(f"Model agreement: {agreement.score}% ({agreement.label}).")
        if reasons:
            lines.append("Why: " + " ".join(reasons))
        if bundle.alerts:
            official_count = sum(1 for x in bundle.alerts if x.official)
            lines.append(f"Alerts: {len(bundle.alerts)} active signal(s), {official_count} official.")
        lines.append("Weather values come from structured data sources; the language layer does not invent forecast numbers.")
        return "\n".join(lines), action, safety_override

    # Lightweight multilingual templates for prototype accessibility.
    t = TRANSLATIONS.get(language, TRANSLATIONS["hi"])
    header = t.get(action, action)
    if language == "hi":
        lines = [f"{header} — {location_name}", f"मौसम स्थिति: {condition}.", f"मॉडल सहमति: {agreement.score}% ({agreement.label})."]
        if safety_override:
            lines.append(t["official_warning"])
        lines.append("कारण: " + " ".join(reasons))
        lines.append("मौसम के संख्यात्मक मान संरचित डेटा स्रोतों से लिए गए हैं।")
        return "\n".join(lines), action, safety_override

    lines = [f"{header} — {location_name}", f"ಹವಾಮಾನ ಸ್ಥಿತಿ: {condition}.", f"ಮಾದರಿ ಒಪ್ಪಿಗೆ: {agreement.score}% ({agreement.label})."]
    if safety_override:
        lines.append(t["official_warning"])
    lines.append("ಕಾರಣ: " + " ".join(reasons))
    lines.append("ಹವಾಮಾನ ಸಂಖ್ಯೆಗಳು ರಚಿತ ಡೇಟಾ ಮೂಲಗಳಿಂದ ಬರುತ್ತವೆ.")
    return "\n".join(lines), action, safety_override
