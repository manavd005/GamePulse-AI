"""
Raw Riot Match Data Parser Module.

Transforms raw Riot API match JSON dictionaries into clean internal dataclass structures.
Extracts match metadata, team statistics, player stats, and round telemetry without altering values or performing feature engineering.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gamepulse.pipeline.parser")


@dataclass
class ParsedPlayerData:
    """Structured representation of raw player match data."""
    puuid: str
    game_name: str
    tag_line: str
    team_id: str
    party_id: str
    character_id: str
    score: int
    rounds_played: int
    kills: int
    deaths: int
    assists: int
    playtime_millis: int
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
class ParsedTeamData:
    """Structured representation of team match outcome and round statistics."""
    team_id: str
    won: bool
    rounds_won: int
    rounds_played: int


@dataclass
class ParsedRoundData:
    """Structured representation of single round telemetry."""
    round_num: int
    winning_team: str
    bomb_planter: Optional[str] = None
    bomb_defuser: Optional[str] = None


@dataclass
class ParsedMatchData:
    """Structured representation of full parsed match payload."""
    match_id: str
    map_id: str
    game_length_millis: int
    game_start_millis: int
    provisioning_flow_id: str
    game_mode: str
    is_completed: bool
    queue_id: str
    season_id: str
    platform_id: str
    teams: Dict[str, ParsedTeamData] = field(default_factory=dict)
    players: List[ParsedPlayerData] = field(default_factory=list)
    rounds: List[ParsedRoundData] = field(default_factory=list)
    raw_payload: Dict[str, Any] = field(default_factory=dict)


class MatchParser:
    """
    Parser for Riot Developer API Match V1 JSON objects.
    Single Responsibility: Parsing raw JSON payloads into ParsedMatchData objects.
    """

    def parse(self, raw_json: Dict[str, Any]) -> ParsedMatchData:
        """
        Parses a raw Riot match JSON dictionary into a ParsedMatchData object.

        Args:
            raw_json (dict): Raw JSON object returned by Riot Match-V1 API.

        Returns:
            ParsedMatchData: Standardized internal parsed representation.
        """
        match_info = raw_json.get("matchInfo", {})
        match_id = match_info.get("matchId", "")
        map_id = match_info.get("mapId", "Unknown")
        game_length_millis = match_info.get("gameLengthMillis", 0)
        game_start_millis = match_info.get("gameStartMillis", 0)
        provisioning_flow_id = match_info.get("provisioningFlowId", "")
        game_mode = match_info.get("gameMode", "")
        is_completed = match_info.get("isCompleted", True)
        queue_id = match_info.get("queueId", "unrated")
        season_id = match_info.get("seasonId", "")
        platform_id = match_info.get("platformId", "AP")

        # Parse Teams
        parsed_teams: Dict[str, ParsedTeamData] = {}
        for raw_team in raw_json.get("teams", []):
            t_id = raw_team.get("teamId", "Red")
            parsed_teams[t_id] = ParsedTeamData(
                team_id=t_id,
                won=raw_team.get("won", False),
                rounds_won=raw_team.get("roundsWon", 0),
                rounds_played=raw_team.get("roundsPlayed", 0),
            )

        # Parse Round Results (Spike plants/defuses, winning team per round)
        parsed_rounds: List[ParsedRoundData] = []
        plant_events_by_round: Dict[int, str] = {}
        defuse_events_by_round: Dict[int, str] = {}

        raw_round_results = raw_json.get("roundResults", [])
        for idx, raw_round in enumerate(raw_round_results):
            winning_team = raw_round.get("winningTeam", "")
            planter = raw_round.get("bombPlanter")
            defuser = raw_round.get("bombDefuser")
            
            if planter:
                plant_events_by_round[idx] = planter
            if defuser:
                defuse_events_by_round[idx] = defuser

            parsed_rounds.append(
                ParsedRoundData(
                    round_num=idx + 1,
                    winning_team=winning_team,
                    bomb_planter=planter,
                    bomb_defuser=defuser,
                )
            )

        # Count plants, defuses, first bloods per player
        player_plants: Dict[str, int] = {}
        player_defuses: Dict[str, int] = {}
        player_first_bloods: Dict[str, int] = {}
        player_clutches: Dict[str, int] = {}

        for raw_round in raw_round_results:
            planter = raw_round.get("bombPlanter")
            defuser = raw_round.get("bombDefuser")
            if planter:
                player_plants[planter] = player_plants.get(planter, 0) + 1
            if defuser:
                player_defuses[defuser] = player_defuses.get(defuser, 0) + 1

            # Extract first blood
            player_stats_list = raw_round.get("playerStats", [])
            for p_stat in player_stats_list:
                for kill_evt in p_stat.get("kills", []):
                    # Check if first blood
                    if kill_evt.get("timeSinceGameStartMillis", 0) > 0 and kill_evt.get("victim") != kill_evt.get("killer"):
                        killer_puuid = kill_evt.get("killer")
                        if killer_puuid and kill_evt.get("isFirstKill", False):
                            player_first_bloods[killer_puuid] = player_first_bloods.get(killer_puuid, 0) + 1

        # Parse Players
        parsed_players: List[ParsedPlayerData] = []
        for raw_player in raw_json.get("players", []):
            puuid = raw_player.get("puuid", "")
            game_name = raw_player.get("gameName", raw_player.get("title", ""))
            tag_line = raw_player.get("tagLine", "")
            team_id = raw_player.get("teamId", "Red")
            party_id = raw_player.get("partyId", "")
            character_id = raw_player.get("characterId", "")
            stats = raw_player.get("stats", {})
            score = stats.get("score", 0)
            rounds_played = stats.get("roundsPlayed", 0)
            kills = stats.get("kills", 0)
            deaths = stats.get("deaths", 0)
            assists = stats.get("assists", 0)
            playtime_millis = stats.get("playtimeMillis", 0)
            competitive_tier = raw_player.get("competitiveTier", 0)

            # Aggregate damage, shots, economy from player round stats
            total_headshots = 0
            total_bodyshots = 0
            total_legshots = 0
            total_damage = 0
            total_spent = 0

            # Scan raw_player.stats or roundResults for damage and shots
            for raw_round in raw_round_results:
                for p_stat in raw_round.get("playerStats", []):
                    if p_stat.get("puuid") == puuid:
                        econ = p_stat.get("economy", {})
                        total_spent += econ.get("spent", 0)
                        for dmg in p_stat.get("damage", []):
                            total_damage += dmg.get("damage", 0)
                            total_headshots += dmg.get("headshots", 0)
                            total_bodyshots += dmg.get("bodyshots", 0)
                            total_legshots += dmg.get("legshots", 0)

            parsed_players.append(
                ParsedPlayerData(
                    puuid=puuid,
                    game_name=game_name,
                    tag_line=tag_line,
                    team_id=team_id,
                    party_id=party_id,
                    character_id=character_id,
                    score=score,
                    rounds_played=rounds_played,
                    kills=kills,
                    deaths=deaths,
                    assists=assists,
                    playtime_millis=playtime_millis,
                    competitive_tier=competitive_tier,
                    headshots=total_headshots,
                    bodyshots=total_bodyshots,
                    legshots=total_legshots,
                    damage_dealt=total_damage,
                    econ_spent=total_spent,
                    first_bloods=player_first_bloods.get(puuid, 0),
                    clutches=player_clutches.get(puuid, 0),
                    plants=player_plants.get(puuid, 0),
                    defuses=player_defuses.get(puuid, 0),
                )
            )

        logger.debug(f"Successfully parsed match '{match_id}' with {len(parsed_players)} players.")
        return ParsedMatchData(
            match_id=match_id,
            map_id=map_id,
            game_length_millis=game_length_millis,
            game_start_millis=game_start_millis,
            provisioning_flow_id=provisioning_flow_id,
            game_mode=game_mode,
            is_completed=is_completed,
            queue_id=queue_id,
            season_id=season_id,
            platform_id=platform_id,
            teams=parsed_teams,
            players=parsed_players,
            rounds=parsed_rounds,
            raw_payload=raw_json,
        )
