from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import ChatRequest, ChatResponse, RoutePointRisk, RouteRequest, WeatherBundle
from app.services.bundle import build_weather_bundle
from app.services.decision_engine import build_decision_answer
from app.services.open_meteo import OpenMeteoService
from app.services.llm import safe_rephrase
from app.services.query_parser import parse_query
from app.services.replay import list_scenarios
from app.services.route_service import route_risk

router = APIRouter()


@router.get("/locations/search")
async def search_locations(q: str = Query(min_length=2, max_length=80)):
    try:
        return await OpenMeteoService().search_locations(q)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Location service unavailable: {exc}") from exc


@router.get("/weather/bundle", response_model=WeatherBundle)
async def weather_bundle(
    latitude: float,
    longitude: float,
    location_name: str = "Selected location",
    days: int = Query(default=7, ge=1, le=16),
):
    try:
        return await build_weather_bundle(latitude, longitude, location_name, days)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather data unavailable: {exc}") from exc


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        bundle = await build_weather_bundle(request.latitude, request.longitude, request.location_name, 7)
        parsed = parse_query(request.message, request.activity)
        answer, action, safety_override = build_decision_answer(bundle, parsed, request.persona, request.language)
        answer, llm_used = await safe_rephrase(answer, request.message, request.language)
        return ChatResponse(
            answer=answer,
            action=action,
            safety_override=safety_override,
            parsed_intent=parsed,
            bundle=bundle,
            llm_used=llm_used,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"WeatherGPT could not complete the request: {exc}") from exc


@router.post("/route-risk", response_model=list[RoutePointRisk])
async def get_route_risk(request: RouteRequest):
    try:
        return await route_risk(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Route weather unavailable: {exc}") from exc


@router.get("/replay/scenarios")
async def replay_scenarios():
    return list_scenarios()
