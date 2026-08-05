# GamePulse AI Architecture

## High-Level System Flow

```
Riot Developer API / Gameplay Telemetry Data
↓
RiotClient (HTTP Transport & Retry Engine)
↓
Domain Services (AccountService, MatchService, StatusService)
↓
RiotDataCollector (Raw JSON Persistence under data/raw/players/)
↓
Data Preprocessing & Feature Engineering
↓
Machine Learning Models (Churn, Skill Tier, Segmentation, Anomaly)
↓
FastAPI Backend REST Services
↓
PostgreSQL Database
↓
React Dashboard Interface
```

---

## Architecture Layers

### Layer 1 – Core Configuration & Constants (`app.core`)
- **Pydantic Settings**: Centralized configuration management using `pydantic-settings` (`BaseSettings`).
- **Endpoint Constants**: Centralized endpoint definitions and regional cluster mappings (`PLATFORM_TO_REGION_MAP`).
- **Logging**: Structured application-wide stream logger.
- **Exceptions**: Exception hierarchy (`GamePulseException`, `RiotAPIException`, `RiotRateLimitError`, `ServiceError`).

### Layer 2 – Low-Level Transport (`RiotClient`)
- Dedicated HTTP transport layer utilizing `requests.Session` for connection pooling.
- Header authentication using `X-Riot-Token`.
- Retry Engine: Automatic handling of HTTP 429 using `Retry-After` headers and exponential backoff for transient 5xx server errors up to `RIOT_MAX_RETRIES`.

### Layer 3 – Pydantic Schemas & DTOs (`app.schemas`)
- Type-safe data transfer objects: `AccountDTO`, `MatchlistDTO`, `MatchDetailsDTO`, `PlatformStatusDTO`, `HealthCheckResult`, `ConnectionResult`.

### Layer 4 – Modular Service Layer (`app.services.riot`)
- **`AccountService`**: Player lookup by Riot ID (gameName#tagLine) and PUUID with automatic regional routing.
- **`MatchService`**: Match history querying and match telemetry detail fetching.
- **`StatusService`**: Valorant platform operational status and health probes.
- **`RiotDataCollector`**: Orchestrates services to collect and persist raw telemetry into structured directories (`data/raw/players/{game_name}_{tag_line}/`).

### Layer 5 – Data Storage & Preprocessing
- Raw JSON persistence under `data/raw/`.
- Future PostgreSQL application store and ML data pipeline.