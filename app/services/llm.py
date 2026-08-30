from __future__ import annotations

import re

import httpx

from app.config import get_settings


_NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?%?")


def _numeric_tokens(text: str) -> set[str]:
    return {token.replace("+", "") for token in _NUMBER_RE.findall(text)}


async def safe_rephrase(base_answer: str, user_message: str, language: str) -> tuple[str, bool]:
    """
    Optional OpenAI-compatible communication layer.

    Safety contract:
    - the deterministic decision engine creates the factual answer first;
    - the LLM is only asked to rephrase it;
    - if the LLM introduces a numeric token that was not in the base answer,
      the result is rejected and the deterministic answer is returned.

    The endpoint is fully optional; leave LLM_ENDPOINT empty for the default MVP.
    """
    settings = get_settings()
    if not settings.llm_endpoint or not settings.llm_model:
        return base_answer, False

    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    system = (
        "You are only the communication layer of WeatherGPT. Rephrase the supplied verified answer "
        "clearly in the requested language. Do not add, infer, calculate, or change any weather value, "
        "warning, source, risk, time, recommendation, or numeric quantity. Do not claim a derived alert "
        "is official. If information is absent, do not fill it in."
    )
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"Requested language: {language}\nOriginal user question: {user_message}\nVerified answer:\n{base_answer}",
            },
        ],
        "temperature": 0.1,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            response = await client.post(settings.llm_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        candidate = str(data["choices"][0]["message"]["content"]).strip()
        if not candidate:
            return base_answer, False

        allowed_numbers = _numeric_tokens(base_answer)
        introduced = _numeric_tokens(candidate) - allowed_numbers
        if introduced:
            return base_answer, False
        return candidate, True
    except Exception:
        return base_answer, False
