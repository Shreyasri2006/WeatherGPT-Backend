from app.models.schemas import ReplayScenario


SCENARIOS = [
    ReplayScenario(
        id="coastal-cyclone-demo",
        title="Coastal Cyclone Warning Pipeline — Demo Replay",
        location="Odisha coast (illustrative)",
        note="Demonstration timeline for the SIH safety pipeline. Replace with verified historical IMD data before presenting it as a real-event reconstruction.",
        timeline=[
            {"minute": 0, "severity": "low", "title": "Normal monitoring", "detail": "Forecast feeds ingested; no high-priority alert."},
            {"minute": 1, "severity": "moderate", "title": "Model risk increasing", "detail": "Wind/rain signals strengthen across forecast inputs."},
            {"minute": 2, "severity": "high", "title": "Warning detected", "detail": "Official-warning adapter reports an elevated coastal hazard."},
            {"minute": 3, "severity": "severe", "title": "Safety override", "detail": "Normal chat recommendations are interrupted and protective actions are surfaced."},
            {"minute": 4, "severity": "severe", "title": "What changed?", "detail": "WeatherGPT summarizes stronger wind, heavier rainfall and upgraded warning status."},
        ],
    ),
    ReplayScenario(
        id="urban-heavy-rain-demo",
        title="Urban Heavy-Rain / Flood-Risk Pipeline — Demo Replay",
        location="Indian metro (illustrative)",
        note="Illustrative replay. Add verified rainfall, vulnerability and warning records for final judging.",
        timeline=[
            {"minute": 0, "severity": "low", "title": "Routine forecast", "detail": "Moderate rain expected."},
            {"minute": 1, "severity": "moderate", "title": "Rainfall rises", "detail": "Multi-model rainfall totals increase."},
            {"minute": 2, "severity": "high", "title": "Impact risk rises", "detail": "Rainfall + vulnerable-zone score crosses the high-risk threshold."},
            {"minute": 3, "severity": "high", "title": "Route advice changes", "detail": "Low-lying route is marked unsafe; alternate timing advised."},
        ],
    ),
]


def list_scenarios() -> list[ReplayScenario]:
    return SCENARIOS
