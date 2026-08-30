from typing import Literal
from pydantic import BaseModel, Field

Persona = Literal["citizen", "farmer", "fisherman", "traveller", "disaster_officer", "researcher", "aviation"]
Language = Literal["en", "hi", "kn"]


class Location(BaseModel):
    name: str = "Selected location"
    latitude: float
    longitude: float
    country: str | None = None
    admin1: str | None = None


class SourceInfo(BaseModel):
    name: str
    type: str
    official: bool = False
    fetched_at: str
    url: str | None = None
    note: str | None = None


class CurrentWeather(BaseModel):
    temperature_c: float | None = None
    apparent_temperature_c: float | None = None
    humidity_pct: float | None = None
    precipitation_mm: float | None = None
    rain_mm: float | None = None
    weather_code: int | None = None
    wind_speed_kmh: float | None = None
    wind_gust_kmh: float | None = None
    wind_direction_deg: float | None = None
    is_day: int | None = None
    observed_at: str | None = None


class DailyForecast(BaseModel):
    date: str
    weather_code: int | None = None
    temperature_max_c: float | None = None
    temperature_min_c: float | None = None
    precipitation_probability_max_pct: float | None = None
    precipitation_sum_mm: float | None = None
    wind_speed_max_kmh: float | None = None
    wind_gust_max_kmh: float | None = None
    uv_index_max: float | None = None


class WeatherAlert(BaseModel):
    id: str
    severity: Literal["low", "moderate", "high", "severe", "extreme"]
    hazard: str
    title: str
    message: str
    official: bool = False
    source: str
    issued_at: str
    valid_until: str | None = None
    safety_actions: list[str] = Field(default_factory=list)


class ModelSnapshot(BaseModel):
    model: str
    precipitation_24h_mm: float | None = None
    max_temperature_24h_c: float | None = None
    max_wind_24h_kmh: float | None = None


class ModelAgreement(BaseModel):
    score: int = Field(ge=0, le=100)
    label: Literal["low", "medium", "high"]
    summary: str
    models: list[ModelSnapshot]


class RiskFactor(BaseModel):
    name: str
    contribution: int
    detail: str


class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    level: Literal["low", "moderate", "high", "severe", "extreme"]
    factors: list[RiskFactor]
    explanation: str


class ClimateContext(BaseModel):
    available: bool
    status: str
    metric: str | None = None
    current_value: float | None = None
    historical_normal: float | None = None
    anomaly: float | None = None
    sample_size: int | None = None
    note: str | None = None


class WeatherBundle(BaseModel):
    location: Location
    current: CurrentWeather
    forecast: list[DailyForecast]
    alerts: list[WeatherAlert]
    agreement: ModelAgreement
    risk: RiskAssessment
    sources: list[SourceInfo]
    climate: ClimateContext | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1200)
    latitude: float
    longitude: float
    location_name: str = "Selected location"
    persona: Persona = "citizen"
    language: Language = "en"
    activity: str | None = None


class ChatResponse(BaseModel):
    answer: str
    action: Literal["recommended", "caution", "not_recommended", "information"]
    safety_override: bool
    parsed_intent: dict
    bundle: WeatherBundle
    llm_used: bool = False


class RouteRequest(BaseModel):
    origin_latitude: float
    origin_longitude: float
    destination_latitude: float
    destination_longitude: float
    origin_name: str = "Origin"
    destination_name: str = "Destination"
    samples: int = Field(default=5, ge=3, le=8)


class RoutePointRisk(BaseModel):
    name: str
    latitude: float
    longitude: float
    risk_score: int
    risk_level: str
    precipitation_probability_pct: float | None = None
    wind_speed_kmh: float | None = None


class ReplayScenario(BaseModel):
    id: str
    title: str
    location: str
    note: str
    timeline: list[dict]
