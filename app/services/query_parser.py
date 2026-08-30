from __future__ import annotations

import re


ACTIVITY_PATTERNS = {
    "pesticide spraying": ["pesticide", "spray", "spraying", "medicine on crop", "कीटनाशक", "ಸಿಂಪಡ"],
    "irrigation": ["irrigat", "watering crop", "पानी देना", "ನೀರಾವರಿ"],
    "travel": ["travel", "drive", "trip", "road", "यात्र", "ಪ್ರಯಾಣ"],
    "fishing": ["fish", "fishing", "sea", "boat", "मछली", "ಮೀನು"],
    "outdoor event": ["wedding", "cricket", "match", "event", "cycling", "walk", "शादी", "ಮದುವೆ"],
}


def parse_query(message: str, explicit_activity: str | None = None) -> dict:
    text = message.lower().strip()
    activity = explicit_activity
    if not activity:
        for candidate, patterns in ACTIVITY_PATTERNS.items():
            if any(p in text for p in patterns):
                activity = candidate
                break

    time_window = "today"
    if re.search(r"\btomorrow\b|कल|ನಾಳೆ", text):
        time_window = "tomorrow"
    elif "tonight" in text or "आज रात" in text:
        time_window = "tonight"
    elif "week" in text or "7 day" in text:
        time_window = "next_7_days"

    intent = "weather_information"
    if activity:
        intent = "activity_advisory"
    if any(word in text for word in ["warning", "alert", "cyclone", "flood", "lightning", "चेतावनी", "ಎಚ್ಚರಿಕೆ"]):
        intent = "hazard_check"
    if any(word in text for word in ["trend", "historical", "climate", "normal", "anomaly"]):
        intent = "climate_analysis"

    return {"intent": intent, "activity": activity, "time_window": time_window}
