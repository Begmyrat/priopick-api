from typing import Dict, List, Optional


class PlanOptimizer:
    def calculate_vendor_score(
        self,
        vendor: dict,
        preferred_style: Optional[str],
        event_type: Optional[str],
    ) -> float:
        base_score = (vendor.get("rating") or 0.0) * 12.0

        style_score = 0.0
        event_score = 0.0

        tags_str = (vendor.get("style_tags") or "").lower()
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        if preferred_style and preferred_style.lower() in tags:
            style_score = 20.0

        if event_type and event_type.lower() in tags_str:
            event_score = 20.0

        return base_score + style_score + event_score

    def suggest_plan(
        self,
        budget: float,
        guest_count: int,
        event_type: Optional[str],
        style: Optional[str],
        vendors: List[dict],
    ) -> dict:
        by_category: Dict[str, List[dict]] = {}

        for v in vendors:
            min_cap = v.get("min_capacity")
            max_cap = v.get("max_capacity")

            if min_cap is not None and guest_count < min_cap:
                continue
            if max_cap is not None and guest_count > max_cap:
                continue

            v_copy = dict(v)
            v_copy["score"] = self.calculate_vendor_score(v_copy, style, event_type)
            v_copy["price"] = v_copy["min_price"]

            cat = v_copy["vendor_category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(v_copy)

        for cat in by_category:
            by_category[cat].sort(key=lambda x: x["price"])

        selected_indices: Dict[str, int] = {}
        total_price = 0.0

        for cat, cat_vendors in by_category.items():
            if not cat_vendors:
                continue
            cheapest = cat_vendors[0]
            if total_price + cheapest["price"] <= budget:
                selected_indices[cat] = 0
                total_price += cheapest["price"]

        while True:
            best_upgrade_cat = None
            best_efficiency = -1.0
            best_upgrade_cost = 0.0

            remaining_budget = budget - total_price

            for cat, current_idx in selected_indices.items():
                cat_vendors = by_category[cat]
                if current_idx + 1 < len(cat_vendors):
                    current_vendor = cat_vendors[current_idx]
                    candidate_vendor = cat_vendors[current_idx + 1]

                    cost_diff = candidate_vendor["price"] - current_vendor["price"]
                    score_diff = candidate_vendor["score"] - current_vendor["score"]

                    if 0 < cost_diff <= remaining_budget and score_diff > 0:
                        efficiency = score_diff / cost_diff
                        if efficiency > best_efficiency:
                            best_efficiency = efficiency
                            best_upgrade_cat = cat
                            best_upgrade_cost = cost_diff

            if best_upgrade_cat is not None:
                selected_indices[best_upgrade_cat] += 1
                total_price += best_upgrade_cost
            else:
                break

        final_vendors = []
        for cat, idx in selected_indices.items():
            v = by_category[cat][idx]
            final_vendors.append({
                "vendor_id": v["vendor_id"],
                "vendor_name": v["vendor_name"],
                "vendor_category": cat,
                "price": v["price"],
                "notes": f"Selected via Marginal Gain Optimizer (Score: {v['score']:.1f}/100)"
            })

        return {
            "selected_vendors": final_vendors,
            "total_price": total_price,
            "reasoning": (
                f"Optimized using Marginal Gain Knapsack. Selected {len(final_vendors)} "
                f"vendors for total ${total_price:.2f} under ${budget:.2f} budget."
            )
        }