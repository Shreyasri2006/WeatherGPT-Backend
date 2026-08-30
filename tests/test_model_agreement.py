from app.models.schemas import ModelSnapshot
from app.services.model_agreement import calculate_agreement


def test_close_models_produce_high_agreement():
    result = calculate_agreement([
        ModelSnapshot(model="GFS", precipitation_24h_mm=20, max_temperature_24h_c=31, max_wind_24h_kmh=25),
        ModelSnapshot(model="ECMWF", precipitation_24h_mm=22, max_temperature_24h_c=30, max_wind_24h_kmh=27),
    ])
    assert result.score >= 75
    assert result.label == "high"
