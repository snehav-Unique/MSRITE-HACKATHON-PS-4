# Creator Content Posting Optimization System

## Team Information
- **Team Name**: Debug duo
- **Year**: 1
- **All-Female Team**: Yes

## Architecture Overview
System Architecture & Approach

Our system determines optimal posting time by scoring all 24 hourly slots using a multiplicative formula: Base Engagement × Activity Score × Historical Engagement. For each content item, we evaluate every platform-hour combination (Instagram and YouTube across 24 hours), selecting the highest-scoring slot. Platform selection is intrinsic to this search—each platform is scored independently, and the platform with the highest score automatically wins, ensuring data-driven cross-platform decisions.

To balance platform activity patterns with creator history, we multiply a universal platform-activity curve (peak hours 18-23 for Instagram, 20-23 for YouTube) against creator-specific historical engagement per platform, content type, and hour. This weights real creator past performance more heavily than generic platform trends.

The decision between immediate posting vs. scheduling uses an adaptive threshold (default 0.87). Content scoring above the threshold triggers "post now" for maximum real-time impact; lower-scoring content is scheduled for its predicted optimal future slot. Time-sensitive content receives boosts (High: +30%, Medium: +15%) to increase urgency. All thresholds and multipliers are user-configurable via the strategy dashboard, enabling real-time tuning without redeployment.

## Backend Architecture

> Flask · SQLAlchemy · SQLite

### Decision engine

The core of OptiMetric is a multi-signal scoring engine that runs at startup
and re-executes on every strategy update. For each content item, it exhaustively
evaluates all `platform × hour` combinations (Instagram and YouTube across 24
time slots) and selects the pair that maximises
`platform_activity_score × creator_historical_engagement`. It then computes a
composite score:

A **time-sensitivity multiplier** is applied before the threshold check —
`1.3×` for high-sensitivity content, `1.15×` for medium — capped at `1.0`.
The final score is compared against a configurable threshold (default `0.87`)
to emit a binary decision: **`post_now`** or **`schedule`**.

### Live retuning

`PUT /api/strategy/` accepts a new threshold and immediately re-scores every
content item in the database — no restart required. `POST /api/strategy/simulate`
runs the same logic as a dry run, returning a full diff of changed decisions
without committing anything, enabling what-if analysis before any config change
goes live.

### Schedule distribution

The top 12 highest-scoring items are spread across the current week by rank,
with `posted` or `queued` status derived automatically from whether the
scheduled day has already passed.

### API surface

| Blueprint | Prefix | Responsibility |
|---|---|---|
| `dashboard_bp` | `/api/dashboard` | Metrics, content list, hourly density |
| `analytics_bp` | `/api/analytics` | Accuracy, heatmap, engagement trend |
| `schedule_bp` | `/api/schedule` | Weekly calendar, today focus, queue |
| `strategy_bp` | `/api/strategy` | Config CRUD + simulate |
| `settings_bp` | `/api/settings` | Key-value app settings |

**Instructions**: Describe your approach in 200 words or less. Address the following:

Our system determines optimal posting time by scoring all 24 hourly slots using a multiplicative formula: Base Engagement × Activity Score × Historical Engagement. For each content item, we evaluate every platform-hour combination, selecting the highest-scoring slot. Platform selection is intrinsic to this search—each candidate (Instagram or YouTube) is scored independently, and the platform with the highest score automatically wins. This ensures data-driven, not arbitrary, cross-platform decisions. To balance platform activity patterns with creator history, we multiply a universal platform-activity curve (peak hours 18-23 for Instagram, 20-23 for YouTube) against creator-specific historical engagement per platform, content type, and hour. This weights real creator past performance more heavily than generic platform trends. The decision between immediate posting vs. scheduling uses an adaptive threshold (default 0.87). Content scoring above the threshold triggers "post now" for maximum real-time impact; lower-scoring content is scheduled for its predicted optimal future slot, preserving engagement potential. Time-sensitive content receives boosts (High: +30%, Medium: +15%) to increase urgency. All thresholds and boost multipliers are user-configurable via the strategy dashboard, allowing real-time tuning without redeployment.


---



**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
