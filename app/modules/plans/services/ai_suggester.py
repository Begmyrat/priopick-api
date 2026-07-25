import json
import logging
from typing import List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AISuggester:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL

    async def suggest_plan(
        self,
        budget: float,
        guest_count: int,
        event_type: Optional[str],
        style: Optional[str],
        vendors: List[dict],
    ) -> dict:
        prompt = self._build_prompt(
            budget=budget,
            guest_count=guest_count,
            event_type=event_type,
            style=style,
            vendors=vendors,
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()
            raw_result = json.loads(data["response"])

            # Sanitize and strictly validate the AI output
            return self._validate_and_sanitize(raw_result, budget)

    def _validate_and_sanitize(self, ai_result: dict, budget: float) -> dict:
        """
        Cleans LLM hallucinations, deduplicates categories, 
        and recalculates actual total price.
        """
        raw_vendors = ai_result.get("selected_vendors", [])
        clean_vendors = []
        seen_categories = set()
        actual_total = 0.0

        for item in raw_vendors:
            notes = (item.get("notes") or "").lower()
            category = item.get("vendor_category")

            if "remove" in notes or "too expensive" in notes or "skip" in notes:
                continue

            if category in seen_categories:
                continue

            try:
                price = float(item.get("price", 0.0))
            except (ValueError, TypeError):
                continue

            seen_categories.add(category)
            actual_total += price
            clean_vendors.append(item)

        if actual_total > budget:
            raise ValueError(
                f"AI generated plan exceeding budget (${actual_total:.2f} > ${budget:.2f})"
            )

        if not clean_vendors:
            raise ValueError("AI failed to select any valid vendors.")

        return {
            "selected_vendors": clean_vendors,
            "total_price": actual_total,
            "reasoning": ai_result.get("reasoning", "AI selected plan."),
        }

    def _build_prompt(
        self,
        budget: float,
        guest_count: int,
        event_type: Optional[str],
        style: Optional[str],
        vendors: List[dict],
    ) -> str:
        vendors_text = json.dumps(vendors, indent=2)

        return f"""
            You are an expert event planner. Select the best combination
            of vendors for this event.

            EVENT DETAILS:
            - Budget: ${budget}
            - Guests: {guest_count}
            - Type: {event_type or "general event"}
            - Style: {style or "any"}

            AVAILABLE VENDORS:
            {vendors_text}

            STRICT RULES:
            1. Total price MUST BE LESS THAN OR EQUAL TO ${budget}.
            2. Select AT MOST ONE vendor per category.
            3. Do NOT include rejected or removed vendors in the output list.
            4. Only return finalized selections.

            Respond ONLY with valid JSON in this exact format:
            {{
                "selected_vendors": [
                    {{
                        "vendor_id": "uuid here",
                        "vendor_name": "name here",
                        "vendor_category": "category here",
                        "price": 1000.00,
                        "notes": "why you chose this vendor"
                    }}
                ],
                "total_price": 1000.00,
                "reasoning": "Overall explanation of choices"
            }}
            """