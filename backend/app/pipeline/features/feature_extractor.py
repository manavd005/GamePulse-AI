"""
Feature Engineering Module for GamePulse AI.

Transforms normalized and validated player-match observations into rich, deterministic
feature vectors suitable for downstream analytics and Machine Learning model training.

Engineers:
- Combat Metrics (KDA, ADR, Headshot %, ACS, Clutches, First Bloods)
- Economy Metrics (Econ Spent, Avg Spent per Round)
- Objective Metrics (Spike Plants, Defuses, Interactions)
- Consistency Metrics (Win Indicator, Variance Metrics)
- Playstyle Metrics (Aggression Score, Support Score, Survival Rate, Entry Frequency)
- Team Metrics (Avg Team ACS, Team Economy Rating, Team Win Rate)
"""

import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, List
import numpy as np

from app.pipeline.normalizer.data_normalizer import NormalizedMatchData, NormalizedPlayerData

logger = logging.getLogger("gamepulse.pipeline.features")


@dataclass
class PlayerMatchFeatureRow:
    """
    Complete tabular observation row representing a single player's performance in one match.
    """

    # Identifiers & Context Metadata
    match_id: str
    puuid: str
    game_name: str
    tag_line: str
    agent_name: str
    map_name: str
    queue_id: str
    game_start_iso: str
    game_start_timestamp: int
    team_id: str

    # Match General Stats
    game_length_seconds: float
    rounds_played: int
    win: int

    # Combat Features
    kills: int
    deaths: int
    assists: int
    kda_ratio: float
    score: int
    acs: float
    total_damage: int
    adr: float
    headshots: int
    bodyshots: int
    legshots: int
    total_shots: int
    headshot_pct: float
    first_bloods: int
    clutches: int

    # Economy Features
    econ_spent: int
    avg_econ_spent_per_round: float

    # Objective Features
    plants: int
    defuses: int
    spike_interactions: int

    # Consistency & Playstyle Features
    aggression_score: float
    support_score: float
    entry_frequency: float
    survival_rate: float
    kill_variance: float

    # Team Context Features
    team_win: int
    avg_team_acs: float
    team_econ_rating: float


class FeatureExtractor:
    """
    Computes deterministic statistical features from normalized match data.
    Single Responsibility: Feature Engineering.
    """

    def extract_features(self, match: NormalizedMatchData) -> List[PlayerMatchFeatureRow]:
        """
        Extracts feature vectors for every player in a normalized match.

        Args:
            match (NormalizedMatchData): Validated normalized match payload.

        Returns:
            List[PlayerMatchFeatureRow]: List of tabular feature observations (one per player).
        """
        feature_rows: List[PlayerMatchFeatureRow] = []
        rounds = max(1, match.rounds_played)

        # Pre-compute team-level aggregates for contextual team features
        team_scores: Dict[str, List[float]] = {}
        team_econs: Dict[str, List[float]] = {}

        for p in match.players:
            t_id = p.team_id
            player_acs = p.score / rounds
            player_avg_econ = p.econ_spent / rounds

            if t_id not in team_scores:
                team_scores[t_id] = []
                team_econs[t_id] = []

            team_scores[t_id].append(player_acs)
            team_econs[t_id].append(player_avg_econ)

        avg_team_acs_map = {t: float(np.mean(scores)) for t, scores in team_scores.items()}
        team_econ_rating_map = {t: float(np.mean(econs)) for t, econs in team_econs.items()}

        for p in match.players:
            # Combat Computations
            kills = p.kills
            deaths = p.deaths
            assists = p.assists
            kda_ratio = round((kills + assists) / max(1, deaths), 2)
            acs = round(p.score / rounds, 2)
            total_damage = p.damage_dealt
            adr = round(total_damage / rounds, 2)

            total_shots = p.headshots + p.bodyshots + p.legshots
            headshot_pct = round((p.headshots / max(1, total_shots)) * 100.0, 2)

            # Economy Computations
            econ_spent = p.econ_spent
            avg_econ_spent = round(econ_spent / rounds, 2)

            # Objective Computations
            plants = p.plants
            defuses = p.defuses
            spike_interactions = plants + defuses

            # Playstyle & Consistency Computations
            win_val = 1 if p.won else 0
            aggression_score = round((p.first_bloods * 2.0 + kills) / rounds, 2)
            support_score = round((assists * 1.5 + defuses * 2.0 + plants * 1.0) / rounds, 2)
            entry_frequency = round(p.first_bloods / rounds, 3)
            survival_rate = round(max(0, rounds - deaths) / rounds, 3)

            # Variance metric simulation based on score/round consistency
            kill_variance = round(float(np.var([kills, deaths, assists])), 2)

            # Team Context Computations
            t_id = p.team_id
            avg_team_acs = round(avg_team_acs_map.get(t_id, acs), 2)
            team_econ_rating = round(team_econ_rating_map.get(t_id, avg_econ_spent), 2)

            row = PlayerMatchFeatureRow(
                match_id=match.match_id,
                puuid=p.puuid,
                game_name=p.game_name,
                tag_line=p.tag_line,
                agent_name=p.agent_name,
                map_name=match.map_name,
                queue_id=match.queue_id,
                game_start_iso=match.game_start_iso,
                game_start_timestamp=match.game_start_timestamp,
                team_id=p.team_id,
                game_length_seconds=match.game_length_seconds,
                rounds_played=match.rounds_played,
                win=win_val,
                kills=kills,
                deaths=deaths,
                assists=assists,
                kda_ratio=kda_ratio,
                score=p.score,
                acs=acs,
                total_damage=total_damage,
                adr=adr,
                headshots=p.headshots,
                bodyshots=p.bodyshots,
                legshots=p.legshots,
                total_shots=total_shots,
                headshot_pct=headshot_pct,
                first_bloods=p.first_bloods,
                clutches=p.clutches,
                econ_spent=econ_spent,
                avg_econ_spent_per_round=avg_econ_spent,
                plants=plants,
                defuses=defuses,
                spike_interactions=spike_interactions,
                aggression_score=aggression_score,
                support_score=support_score,
                entry_frequency=entry_frequency,
                survival_rate=survival_rate,
                kill_variance=kill_variance,
                team_win=win_val,
                avg_team_acs=avg_team_acs,
                team_econ_rating=team_econ_rating,
            )
            feature_rows.append(row)

        logger.debug(f"Engineered {len(feature_rows)} feature rows for match '{match.match_id}'.")
        return feature_rows

    def rows_to_dicts(self, rows: List[PlayerMatchFeatureRow]) -> List[Dict[str, Any]]:
        """Converts feature dataclass rows to dictionaries."""
        return [asdict(r) for r in rows]
