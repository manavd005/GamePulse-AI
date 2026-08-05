"""
Data Normalization Module.

Standardizes map names, agent character IDs, timestamps, queue types, and missing values
from parsed match data objects.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

from app.pipeline.parser.match_parser import ParsedMatchData, ParsedPlayerData

logger = logging.getLogger("gamepulse.pipeline.normalizer")

# Map path to clean display name mapping
MAP_NAME_MAPPING: Dict[str, str] = {
    "/game/maps/ascent/ascent": "Ascent",
    "/game/maps/duality/duality": "Bind",
    "/game/maps/bonsai/bonsai": "Split",
    "/game/maps/triad/triad": "Haven",
    "/game/maps/port/port": "Icebox",
    "/game/maps/foxtrot/foxtrot": "Breeze",
    "/game/maps/canyon/canyon": "Fracture",
    "/game/maps/pitt/pitt": "Pearl",
    "/game/maps/jam/jam": "Lotus",
    "/game/maps/juju/juju": "Sunset",
    "/game/maps/hurm/hurm_yard": "District",
    "ascent": "Ascent",
    "bind": "Bind",
    "split": "Split",
    "haven": "Haven",
    "icebox": "Icebox",
    "breeze": "Breeze",
    "fracture": "Fracture",
    "pearl": "Pearl",
    "lotus": "Lotus",
    "sunset": "Sunset",
}

# Character ID UUID to Agent Name mapping
AGENT_UUID_MAPPING: Dict[str, str] = {
    "add6443a-41bd-e414-3278-e09d8f721345": "Jett",
    "5f86a701-4be0-70a7-7701-9fbd560573f4": "Cypher",
    "f949ee45-41d5-763b-f78b-3455a408713d": "Raze",
    "1e58d037-4376-496e-88e6-384704f2b604": "Killjoy",
    "7f23e612-413a-872e-8752-7ab6e02cfd60": "Omen",
    "5609f273-4860-1220-d808-627187381a90": "Sova",
    "eb93330a-4490-8202-b989-b891cd640441": "Phoenix",
    "41fb69c1-4189-7b37-f117-bcaf1e96f1bf": "Brimstone",
    "8e250072-4737-a45d-1b36-9930b7219f6d": "Astra",
    "9f0d8ba9-4140-b941-57d3-a7ad57564b3c": "Viper",
    "707e5d8a-4777-64d3-a963-6b956cc80884": "Sage",
    "11794782-4172-3a22-4a36-049121d74d2b": "Yoru",
    "2b8588f9-47fe-0d56-72e9-b6a4ea21c2b3": "REAYNE",
    "a3bf188f-40ea-054f-4540-a196d019175d": "Reyna",
    "bb2a4828-46eb-8a28-d77d-79807102e3ef": "Breach",
    "e370fa57-4757-3604-3648-499e1f642d3f": "Gekko",
    "cc8b0a4f-4b41-8400-0441-f498f1898034": "Fade",
    "0e38b542-4189-7b37-f117-bcaf1e96f1bf": "Iso",
    "bfed3da8-43f9-719e-e3b9-1d8d3f6630f3": "Deadlock",
    "1db3b35f-476e-3474-0f2c-5f9175f3a097": "Clove",
}


@dataclass
class NormalizedPlayerData:
    """Normalized Player attributes."""
    puuid: str
    game_name: str
    tag_line: str
    agent_name: str
    team_id: str
    won: bool
    score: int
    rounds_played: int
    kills: int
    deaths: int
    assists: int
    playtime_seconds: float
    competitive_tier: int
    headshots: int
    bodyshots: int
    legshots: int
    damage_dealt: int
    econ_spent: int
    first_bloods: int
    clutches: int
    plants: int
    defuses: int


@dataclass
class NormalizedMatchData:
    """Normalized Match attributes."""
    match_id: str
    map_name: str
    queue_id: str
    game_start_iso: str
    game_start_timestamp: int
    game_length_seconds: float
    rounds_played: int
    winning_team: str
    is_completed: bool
    players: List[NormalizedPlayerData]


class DataNormalizer:
    """
    Normalizes parsed match attributes into standardized formats.
    Single Responsibility: Data Cleaning & Normalization.
    """

    def normalize_map_name(self, raw_map: str) -> str:
        """Translates raw map paths into standard display names."""
        clean_map = raw_map.lower().strip()
        return MAP_NAME_MAPPING.get(clean_map, raw_map.split("/")[-1].title())

    def normalize_agent_name(self, character_id: str) -> str:
        """Translates agent UUIDs into human-readable Agent names."""
        return AGENT_UUID_MAPPING.get(character_id.lower().strip(), f"Agent_{character_id[:8]}")

    def normalize_timestamp(self, millis: int) -> tuple[str, int]:
        """Converts epoch milliseconds to ISO string and seconds integer."""
        if millis <= 0:
            millis = int(datetime.now(timezone.utc).timestamp() * 1000)
        seconds = millis // 1000
        iso_str = datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
        return iso_str, seconds

    def normalize(self, parsed: ParsedMatchData) -> NormalizedMatchData:
        """
        Normalizes a ParsedMatchData object.

        Args:
            parsed (ParsedMatchData): Parsed raw match object.

        Returns:
            NormalizedMatchData: Standardized normalized match object.
        """
        map_name = self.normalize_map_name(parsed.map_id)
        start_iso, start_timestamp = self.normalize_timestamp(parsed.game_start_millis)
        length_seconds = round(parsed.game_length_millis / 1000.0, 2)
        queue_id = parsed.queue_id.lower().strip() if parsed.queue_id else "unrated"

        # Determine winning team and total rounds played
        winning_team = "Draw"
        total_rounds = 0
        for t_id, team_data in parsed.teams.items():
            if team_data.rounds_played > total_rounds:
                total_rounds = team_data.rounds_played
            if team_data.won:
                winning_team = t_id

        # Normalize players
        norm_players: List[NormalizedPlayerData] = []
        for p in parsed.players:
            agent_name = self.normalize_agent_name(p.character_id)
            team_info = parsed.teams.get(p.team_id)
            won = team_info.won if team_info else False

            norm_players.append(
                NormalizedPlayerData(
                    puuid=p.puuid,
                    game_name=p.game_name or "Unknown",
                    tag_line=p.tag_line or "0000",
                    agent_name=agent_name,
                    team_id=p.team_id,
                    won=won,
                    score=p.score,
                    rounds_played=p.rounds_played if p.rounds_played > 0 else total_rounds,
                    kills=max(0, p.kills),
                    deaths=max(0, p.deaths),
                    assists=max(0, p.assists),
                    playtime_seconds=round(p.playtime_millis / 1000.0, 2),
                    competitive_tier=max(0, p.competitive_tier),
                    headshots=max(0, p.headshots),
                    bodyshots=max(0, p.bodyshots),
                    legshots=max(0, p.legshots),
                    damage_dealt=max(0, p.damage_dealt),
                    econ_spent=max(0, p.econ_spent),
                    first_bloods=max(0, p.first_bloods),
                    clutches=max(0, p.clutches),
                    plants=max(0, p.plants),
                    defuses=max(0, p.defuses),
                )
            )

        logger.debug(f"Normalized match '{parsed.match_id}' on map '{map_name}'.")
        return NormalizedMatchData(
            match_id=parsed.match_id,
            map_name=map_name,
            queue_id=queue_id,
            game_start_iso=start_iso,
            game_start_timestamp=start_timestamp,
            game_length_seconds=length_seconds,
            rounds_played=total_rounds,
            winning_team=winning_team,
            is_completed=parsed.is_completed,
            players=norm_players,
        )
