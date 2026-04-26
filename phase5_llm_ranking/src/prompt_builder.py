import json
from typing import Any


def build_prompt(profile: dict[str, Any], candidates: list[dict[str, Any]], top_n: int) -> str:
    payload = {
        "task": "Rank restaurants and provide concise explanations",
        "top_n": top_n,
        "user_profile": profile,
        "candidates": candidates,
        "requirements": {
            "use_only_provided_candidate_data": True,
            "no_hallucinated_fields": True,
            "output_format": {
                "recommendations": [
                    {
                        "rank": 1,
                        "restaurant_name": "string",
                        "reason": "string",
                    }
                ],
                "summary": "string",
            },
        },
    }
    return json.dumps(payload, indent=2)
