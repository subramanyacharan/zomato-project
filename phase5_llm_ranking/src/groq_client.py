import json
from typing import Any

import requests

from p5_config import GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL


def call_groq(prompt: str, timeout_seconds: int = 60) -> dict[str, Any]:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Please set it before running Phase 5.")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a restaurant recommendation engine. "
                    "Return strict JSON only. Do not include markdown."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }

    response = requests.post(
        GROQ_API_URL, headers=headers, json=payload, timeout=timeout_seconds
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Groq response is not valid JSON: {content}") from exc
