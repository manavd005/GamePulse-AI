"""
Data Validation Module.

Validates normalized match objects and player attributes against strict domain rules,
ensuring invalid, incomplete, or duplicate records are caught and logged prior to feature extraction.
"""

import logging
from dataclasses import dataclass, field
from typing import List

from app.pipeline.normalizer.data_normalizer import NormalizedMatchData, NormalizedPlayerData

logger = logging.getLogger("gamepulse.pipeline.validator")


@dataclass
class ValidationResult:
    """Validation report summary."""
    is_valid: bool
    match_id: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DataValidator:
    """
    Validates normalized records for structural integrity, correct value ranges, and duplicate IDs.
    Single Responsibility: Schema & Rule Validation.
    """

    def validate_player(self, player: NormalizedPlayerData, match_id: str) -> List[str]:
        """Validates individual player attributes."""
        errors = []
        if not player.puuid or not player.puuid.strip():
            errors.append(f"Match '{match_id}': Player missing required PUUID.")

        if player.kills < 0 or player.deaths < 0 or player.assists < 0:
            errors.append(f"Match '{match_id}' Player '{player.puuid}': Invalid negative stat counts (K/D/A).")

        if player.headshots < 0 or player.bodyshots < 0 or player.legshots < 0:
            errors.append(f"Match '{match_id}' Player '{player.puuid}': Invalid negative shot counts.")

        if player.econ_spent < 0 or player.damage_dealt < 0:
            errors.append(f"Match '{match_id}' Player '{player.puuid}': Invalid negative econ or damage values.")

        return errors

    def validate(self, match: NormalizedMatchData) -> ValidationResult:
        """
        Validates a NormalizedMatchData object.

        Args:
            match (NormalizedMatchData): Normalized match object.

        Returns:
            ValidationResult: Validation outcome detailing validity, errors, and warnings.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Validate required match metadata
        if not match.match_id or not match.match_id.strip():
            errors.append("Match missing required match_id identifier.")

        if not match.map_name or not match.map_name.strip():
            errors.append(f"Match '{match.match_id}': Missing required map_name.")

        if match.game_length_seconds <= 0:
            warnings.append(f"Match '{match.match_id}': Game length is <= 0 seconds.")

        if match.rounds_played <= 0:
            warnings.append(f"Match '{match.match_id}': Total rounds played is <= 0.")

        if len(match.players) == 0:
            errors.append(f"Match '{match.match_id}': No player records found in match payload.")

        # 2. Check for duplicate player PUUIDs
        seen_puuids = set()
        for p in match.players:
            if p.puuid in seen_puuids:
                errors.append(f"Match '{match.match_id}': Duplicate player PUUID '{p.puuid}' detected.")
            else:
                seen_puuids.add(p.puuid)

            # Validate player individual attributes
            p_errors = self.validate_player(p, match.match_id)
            errors.extend(p_errors)

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Validation failed for match '{match.match_id}' with {len(errors)} errors.")
            for err in errors:
                logger.error(f"Validation Error: {err}")
        else:
            logger.debug(f"Validation passed cleanly for match '{match.match_id}'.")

        return ValidationResult(
            is_valid=is_valid,
            match_id=match.match_id,
            errors=errors,
            warnings=warnings,
        )
