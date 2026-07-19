# ai_suggester.py
# Handles ALL communication with Ollama AI
# Completely separate from business logic
# If we switch AI provider later → only change this file

import json
from typing import List, Optional

import httpx

from app.core.config import settings


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
        """
        Send vendor data to Ollama and get back
        the best combination within budget.

        Returns a dict with:
        - selected_vendors: list of chosen vendors
        - total_price: sum of selected vendor prices
        - reasoning: why AI chose these vendors
        """
        # Build the prompt
        prompt = self._build_prompt(
            budget=budget,
            guest_count=guest_count,
            event_type=event_type,
            style=style,
            vendors=vendors,
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        # Tell Ollama to return JSON
                        "format": "json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                # Parse AI response
                ai_response = json.loads(data["response"])
                return ai_response

        except httpx.TimeoutException:
            # If AI times out, fall back to algorithmic selection
            return self._fallback_selection(budget, vendors)
        except Exception:
            # Any other error — use fallback
            return self._fallback_selection(budget, vendors)

    def _build_prompt(
        self,
        budget: float,
        guest_count: int,
        event_type: Optional[str],
        style: Optional[str],
        vendors: List[dict],
    ) -> str:
        """
        Build a clear prompt for the AI.
        The better the prompt → the better the suggestion.
        """
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

            RULES:
            1. Total price MUST be under ${budget}
            2. Select ONE vendor per category maximum
            3. Prioritize vendors with higher ratings
            4. Match the style preference if possible
            5. Make sure venue capacity fits guest count

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
                "total_price": 5000.00,
                "reasoning": "Overall explanation of your choices"
            }}
            """

    def _fallback_selection(
        self,
        budget: float,
        vendors: List[dict],
    ) -> dict:
        """
        Algorithmic fallback when AI is unavailable.
        Selects best rated vendor per category within budget.
        This ensures the API works even without Ollama.
        """
        # Group vendors by category
        by_category = {}
        for vendor in vendors:
            cat = vendor["vendor_category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(vendor)

        # Sort each category by rating
        for cat in by_category:
            by_category[cat].sort(
                key=lambda x: x["rating"], reverse=True
            )

        # Greedily select best vendor per category
        selected = []
        total = 0.0

        for cat, cat_vendors in by_category.items():
            for vendor in cat_vendors:
                price = vendor["min_price"]
                if total + price <= budget:
                    selected.append({
                        "vendor_id": vendor["vendor_id"],
                        "vendor_name": vendor["vendor_name"],
                        "vendor_category": cat,
                        "price": price,
                        "notes": f"Selected by budget optimizer"
                    })
                    total += price
                    break

        return {
            "selected_vendors": selected,
            "total_price": total,
            "reasoning": "Selected by budget optimizer (AI unavailable)"
        }