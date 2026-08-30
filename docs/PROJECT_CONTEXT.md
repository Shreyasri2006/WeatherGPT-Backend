# WeatherGPT SIH26068 — Project Context

## Product direction

This repository implements the backend for a **Safety-First Weather Decision Copilot**, not a generic weather chatbot.

The core flow is:

`weather/NWP data -> validation + provenance -> model agreement + risk -> safety override -> persona/activity decision -> conversational explanation`

## Why this direction

Existing weather applications already provide current conditions, forecasts, maps, alerts and even chat/voice interfaces. The stronger SIH opportunity is to convert authoritative multi-source weather information into trusted, explainable action.

## Five primary differentiators

1. Official warning override / safety layer
2. Multi-model weather agreement
3. Persona + activity decision engine
4. Explainable risk
5. Disaster replay mode

## Important rules

- The LLM is a communication layer, not the meteorological source of truth.
- Derived hazards must never be presented as official IMD warnings.
- "Model agreement" must not be marketed as calibrated forecast confidence until validated against historical observations.
- Kaggle/historical data is used for climate context and experiments, not tomorrow's live forecast.
- Replace illustrative disaster replays with verified historical data before calling them historical reconstructions.

## MVP personas

Prioritize:
- Citizen
- Farmer
- Disaster Officer

Then extend to fisherman, traveller, research and aviation use cases.
