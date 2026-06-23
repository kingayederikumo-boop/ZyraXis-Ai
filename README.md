# ZyraXis AI

## Overview
ZyraXis is a Telegram-based AI system with monetization, enforcement, and ops monitoring layers.

## Version
V1.3 Ops Layer

## Core Modules

### Orchestrator
- Handles AI request routing
- Enforces usage limits
- Uses DB as single source of truth

### Gateway
- Authentication (User + Premium state)
- Usage enforcement (Gatekeeper)

### Monetization
- Telegram Stars integration
- Payment idempotency system

### Ops Layer (NEW)
- Logging system (`OpsLogger`)
- Analytics system (`OpsAnalytics`)
- Admin control system (`OpsAdmin`)

## Features

- Telegram bot interface
- OpenRouter AI integration
- Daily usage limits
- Premium subscription via Telegram Stars
- Admin premium control
- Usage analytics
- Event logging

## Deployment

### Local
```
python app/main.py
```

### Docker
```
docker build -t zyraxis .
docker run zyraxis
```

## Environment Variables
```
TELEGRAM_BOT_TOKEN=
OPENROUTER_API_KEY=
DATABASE_URL=
```

## Ops Layer Usage

### Logging
```python
from app.ops.logger import OpsLogger
logger = OpsLogger()
logger.event("request", telegram_id)
```

### Analytics
```python
from app.ops.analytics import OpsAnalytics
analytics = OpsAnalytics()
analytics.get_daily_usage(telegram_id)
```

### Admin
```python
from app.ops.admin import OpsAdmin
admin = OpsAdmin()
admin.set_premium(telegram_id, True)
```

## Status
Production-ready core with ops observability layer.