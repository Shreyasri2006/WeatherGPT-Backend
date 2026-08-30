from app.models.schemas import ModelAgreement, ModelSnapshot


def _relative_similarity(a: float | None, b: float | None, floor: float) -> float:
    if a is None or b is None:
        return 0.5
    denominator = max(abs(a), abs(b), floor)
    return max(0.0, 1.0 - abs(a - b) / denominator)


def calculate_agreement(models: list[ModelSnapshot]) -> ModelAgreement:
    if len(models) < 2:
        return ModelAgreement(
            score=50,
            label="medium",
            summary="Only one model was available, so cross-model agreement could not be fully calculated.",
            models=models,
        )

    a, b = models[0], models[1]
    precipitation_similarity = _relative_similarity(a.precipitation_24h_mm, b.precipitation_24h_mm, 10.0)
    temperature_similarity = _relative_similarity(a.max_temperature_24h_c, b.max_temperature_24h_c, 5.0)
    wind_similarity = _relative_similarity(a.max_wind_24h_kmh, b.max_wind_24h_kmh, 20.0)

    score = round((precipitation_similarity * 0.5 + temperature_similarity * 0.25 + wind_similarity * 0.25) * 100)
    score = max(0, min(100, score))
    label = "high" if score >= 75 else "medium" if score >= 50 else "low"

    return ModelAgreement(
        score=score,
        label=label,
        summary=f"{models[0].model} and {models[1].model} show {label} agreement for the next 24 hours.",
        models=models,
    )
