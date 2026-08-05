"""
GamePulse Core & Riot API Constants.

Centralizes platform routing, regional cluster mappings, API endpoint paths,
and system-wide pagination / query limits.
Ensures magic numbers and strings are never hardcoded throughout the codebase.
"""

from typing import Dict

# System Pagination & Query Limits
DEFAULT_PAGE_SIZE = 100
DEFAULT_OFFSET = 0
DEFAULT_MATCH_LIMIT = 20
DEFAULT_COLLECT_MAX_MATCHES = 5

# Regional Routing Clusters (Used for Account-V1, Match-V1, etc.)
REGION_AMERICAS = "americas"
REGION_ASIA = "asia"
REGION_EUROPE = "europe"
REGION_ESPORTS = "esports"

# Platform Routing Codes (Used for Status, Leaderboards, etc.)
PLATFORM_AP = "ap"
PLATFORM_NA = "na"
PLATFORM_EU = "eu"
PLATFORM_KR = "kr"
PLATFORM_BR = "br"
PLATFORM_LATAM = "latam"

# Mapping from Platform Region to Regional Cluster Routing
PLATFORM_TO_REGION_MAP: Dict[str, str] = {
    PLATFORM_AP: REGION_ASIA,
    PLATFORM_KR: REGION_ASIA,
    PLATFORM_NA: REGION_AMERICAS,
    PLATFORM_BR: REGION_AMERICAS,
    PLATFORM_LATAM: REGION_AMERICAS,
    PLATFORM_EU: REGION_EUROPE,
}

# Riot API Endpoint Template Strings

# Account-V1 Endpoints (Uses Regional Routing, e.g., asia.api.riotgames.com)
ACCOUNT_BY_RIOT_ID_ENDPOINT = "/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
ACCOUNT_BY_PUUID_ENDPOINT = "/riot/account/v1/accounts/by-puuid/{puuid}"

# VAL-Status-V1 Endpoints (Uses Platform Routing, e.g., ap.api.riotgames.com)
VAL_STATUS_ENDPOINT = "/val/status/v1/platform-data"

# VAL-Match-V1 Endpoints (Uses Platform / Regional Routing)
VAL_MATCHLIST_BY_PUUID_ENDPOINT = "/val/match/v1/matchlists/by-puuid/{puuid}"
VAL_MATCH_BY_ID_ENDPOINT = "/val/match/v1/matches/{match_id}"

# VAL-Ranked-V1 Endpoints (Uses Platform Routing)
VAL_LEADERBOARD_ENDPOINT = "/val/ranked/v1/leaderboards/by-act/{act_id}"
