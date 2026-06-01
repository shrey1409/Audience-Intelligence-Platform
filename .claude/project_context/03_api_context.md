# API Context — Audience Intelligence Platform

## Endpoints (Phase 8)

**Current Status:** Not yet implemented (Phase 8 planned)

**Planned Signatures:**
- `GET /v1/personas/{user_id}` → PersonaResponse
- `GET /v1/personas/batch` → List[PersonaResponse] (max 1000 users)
- `GET /v1/propensity/{user_id}` → PropensityResponse
- `POST /v1/inference/trigger` → InferenceStatusResponse (manual batch trigger)

## Redis Key Schema

**Persona Cache:**
- Key: `persona:{user_id}` (string)
- Value: JSON serialized PersonaResponse
- TTL: 86400 (24 hours)

**Propensity Cache:**
- Key: `propensity:{user_id}` (string)
- Value: JSON serialized PropensityResponse
- TTL: 3600 (1 hour, fresher than personas)

**Inference Lock:**
- Key: `inference:lock` (distributed lock)
- Value: timestamp
- TTL: 300 (5 minutes, prevents concurrent inference runs)

## API Authentication

**Header:** `X-API-Key` (required on all endpoints)
**Validation:** Lookup in api_keys table (Phase 8), revoke via admin endpoint
**Rate Limits:** 10K req/min per key (throttle at API gateway, not in-app)

## Response Schemas

### PersonaResponse
```json
{
  "user_id": "uuid",
  "persona_id": 5,
  "persona_name": "Mobile-First Engaged",
  "confidence": 0.87,
  "features": {
    "session_count": 42,
    "rfm_score": 0.72,
    "engagement_rate": 0.91,
    "churn_risk": 0.12
  },
  "activation_strategy": "native_ads, content_personalization",
  "updated_at": "2026-06-01T10:30:00Z"
}
```

### PropensityResponse
```json
{
  "user_id": "uuid",
  "purchase_propensity": 0.65,
  "churn_propensity": 0.18,
  "reactivation_propensity": 0.42,
  "top_recommendation": "purchase_nudge",
  "computed_at": "2026-06-01T10:30:00Z"
}
```

### InferenceStatusResponse
```json
{
  "run_id": "inference_20260601_103000",
  "status": "in_progress|completed|failed",
  "users_processed": 1000,
  "total_users": 1000,
  "started_at": "2026-06-01T10:30:00Z",
  "completed_at": "2026-06-01T10:45:00Z"
}
```

## Cold-Start Response Fields
For users with <30 days data:
- `confidence: 0.40` (instead of 0.87)
- `confidence_reduced_reason: "cold_start"` (metadata field)
- `activation_strategy: null` (only for established personas)
- Use lookalike persona if seed_match=true, else return null persona

## Validation Rules
- user_id: UUID v4, non-null
- max batch size: 1000 (return 400 if exceeded)
- invalid user_id: return 404 (not 200 with null persona)
- missing X-API-Key: return 401
