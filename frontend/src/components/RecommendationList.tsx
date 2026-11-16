import type { Recommendation } from "../types/recommendation";
import { RecommendationCard } from "./RecommendationCard";
export function RecommendationList({
  items,
  practicalSteps = false,
}: {
  items: Recommendation[];
  practicalSteps?: boolean;
}) {
  return (
    <div className="materials">
      {items.map((item) => (
        <RecommendationCard
          key={item.material_id}
          item={item}
          practicalStep={practicalSteps}
        />
      ))}
    </div>
  );
}
