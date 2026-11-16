export interface UserProfile {
  business_stage?: string;
  industry?: string;
  current_goal?: string;
  experience_level?: string;
  preferred_formats?: string[];
}
export interface RecommendationRequest {
  user_profile: UserProfile;
  history: { material_id: string; event_type?: string }[];
  limit?: number;
}
export interface Recommendation {
  material_id: string;
  title: string;
  material_type: string;
  topic: string | null;
  is_paid: boolean | null;
  score: number;
  reasons: string[];
  next_step: string;
  description?: string | null;
  url?: string | null;
}
export interface RecommendationResponse {
  recommendations: Recommendation[];
  metadata: {
    cold_start: boolean;
    strategy: string;
    limit: number;
    returned: number;
    catalog_source?: string;
  };
}
