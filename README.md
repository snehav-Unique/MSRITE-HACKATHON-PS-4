# Creator Content Posting Optimization System

## Team Information
- **Team Name**: Debug duo
- **Year**: 1
- **All-Female Team**: Yes

## Architecture Overview
OPTIMETRIC/
│
├── app.py                          # Flask entry point, app factory, CORS, blueprint registration
├── models.py                       # SQLAlchemy models: ContentItem, ScheduleItem, StrategyConfig, AppSettings
├── seed_data.py                    # CSV loader & optimizer: reads data/raw/, computes scores, seeds DB
├── requirements.txt                # Flask, Flask-CORS, Flask-SQLAlchemy
├── optimizer.py                    # Standalone scoring engine (base × activity × history)
│
├── routes/                         # API Blueprints
│   ├── dashboard.py                # /api/dashboard - metrics, content table, distribution
│   ├── analytics.py                # /api/analytics - platform accuracy, top content, heatmap, trends
│   ├── schedule.py                 # /api/schedule - weekly calendar, queue, add content
│   ├── settings.py                 # /api/settings - user preferences CRUD
│   └── strategy.py                 # /api/strategy - threshold config, simulation, rescoring
│
├── data/
│   └── raw/                        # Source CSV files
│       ├── content.csv             # 100 items with creator_id, type, timestamp, sensitivity
│       ├── creators.csv            # 50 creators with base_engagement, cooldown_hours
│       ├── historical_engagement.csv # 24×24×2×2 historical performance matrix
│       └── platform_activity.csv   # Activity scores per platform per hour (0.6/1.0)
│
├── templates/ (or static/)         # Frontend HTML files
│   ├── dashboard.html              # Home: KPI cards, distribution, content table with filters
│   ├── analytics.html              # Platform accuracy, top content, engagement trends, heatmap
│   ├── schedule.html               # Weekly calendar, unscheduled queue, list view
│   ├── strategy.html               # Logic weights, threshold tuning, platform rules
│   └── settings.html               # Account, preferences, API keys, danger zone
│
└── optimetric.db                   # SQLite database (auto-created on first run)

**Instructions**: Describe your approach in 200 words or less. Address the following:

Our system determines optimal posting time by scoring all 24 hourly slots using a multiplicative formula: Base Engagement × Activity Score × Historical Engagement. For each content item, we evaluate every platform-hour combination, selecting the highest-scoring slot. Platform selection is intrinsic to this search—each candidate (Instagram or YouTube) is scored independently, and the platform with the highest score automatically wins. This ensures data-driven, not arbitrary, cross-platform decisions. To balance platform activity patterns with creator history, we multiply a universal platform-activity curve (peak hours 18-23 for Instagram, 20-23 for YouTube) against creator-specific historical engagement per platform, content type, and hour. This weights real creator past performance more heavily than generic platform trends. The decision between immediate posting vs. scheduling uses an adaptive threshold (default 0.87). Content scoring above the threshold triggers "post now" for maximum real-time impact; lower-scoring content is scheduled for its predicted optimal future slot, preserving engagement potential. Time-sensitive content receives boosts (High: +30%, Medium: +15%) to increase urgency. All thresholds and boost multipliers are user-configurable via the strategy dashboard, allowing real-time tuning without redeployment.

---



**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
