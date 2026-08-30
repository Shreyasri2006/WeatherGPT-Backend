# WeatherGPT Backend API

Base prefix: `/api/v1`

## `GET /locations/search?q=Mysuru`
Searches a location using Open-Meteo geocoding.

## `GET /weather/bundle`
Parameters: `latitude`, `longitude`, optional `location_name`, optional `days`.

Returns:
- current weather
- daily forecast
- derived alerts plus any configured official alerts
- GFS/ECMWF model-agreement score
- explainable risk score
- source/provenance metadata
- historical climate context if the Kaggle CSV is configured

## `POST /chat`
Example body:

```json
{
  "message": "Can I spray pesticide tomorrow morning?",
  "latitude": 12.2958,
  "longitude": 76.6394,
  "location_name": "Mysuru",
  "persona": "farmer",
  "language": "en"
}
```

The decision engine uses structured weather values. It does not ask an LLM to invent forecast numbers.

## `POST /route-risk`
Interpolates 3–8 points along a straight-line route and evaluates weather risk at each point. This is an MVP demonstration, not a road-routing engine.

## `GET /replay/scenarios`
Returns demonstration replay timelines. Replace illustrative timelines with verified historical IMD/event data before calling them historical reconstructions.

## Official IMD warning adapter contract

Set `IMD_WARNING_URL` to a service that returns either an array or `{ "alerts": [...] }` with normalized items such as:

```json
{
  "alerts": [
    {
      "id": "imd-123",
      "severity": "severe",
      "hazard": "heavy_rain",
      "title": "Orange warning",
      "message": "Heavy to very heavy rainfall likely...",
      "source": "India Meteorological Department",
      "issued_at": "2026-08-30T08:00:00+05:30",
      "valid_until": "2026-08-31T08:00:00+05:30",
      "safety_actions": ["Avoid waterlogged roads"]
    }
  ]
}
```

The backend marks data from this adapter as `official=true`; locally derived hazards remain explicitly `official=false`.
