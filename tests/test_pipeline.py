"""
Unit tests for Data Pipeline (app.pipeline).
"""

import sys
import tempfile
from pathlib import Path
import unittest
import pandas as pd

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.pipeline.exporters.dataset_exporter import DatasetExporter
from app.pipeline.features.feature_extractor import FeatureExtractor
from app.pipeline.normalizer.data_normalizer import DataNormalizer
from app.pipeline.parser.match_parser import MatchParser
from app.pipeline.runner import PipelineRunner
from app.pipeline.validator.data_validator import DataValidator


class TestDataPipeline(unittest.TestCase):
    """Tests for Parser, Normalizer, Validator, Feature Extractor, Exporter, and Pipeline Runner."""

    def setUp(self) -> None:
        self.sample_raw_match = {
            "matchInfo": {
                "matchId": "test-match-1001",
                "mapId": "/Game/Maps/Ascent/Ascent",
                "gameLengthMillis": 1800000,
                "gameStartMillis": 1700000000000,
                "gameMode": "competitive",
                "isCompleted": True,
                "queueId": "competitive",
            },
            "teams": [
                {"teamId": "Red", "won": True, "roundsWon": 13, "roundsPlayed": 20},
                {"teamId": "Blue", "won": False, "roundsWon": 7, "roundsPlayed": 20},
            ],
            "players": [
                {
                    "puuid": "player-1-puuid",
                    "gameName": "TenZ",
                    "tagLine": "SEN",
                    "teamId": "Red",
                    "characterId": "add6443a-41bd-e414-3278-e09d8f721345",
                    "stats": {
                        "score": 4500,
                        "roundsPlayed": 20,
                        "kills": 25,
                        "deaths": 10,
                        "assists": 5,
                        "playtimeMillis": 1800000,
                    },
                },
                {
                    "puuid": "player-2-puuid",
                    "gameName": "Chronicle",
                    "tagLine": "FNC",
                    "teamId": "Blue",
                    "characterId": "5f86a701-4be0-70a7-7701-9fbd560573f4",
                    "stats": {
                        "score": 3200,
                        "roundsPlayed": 20,
                        "kills": 15,
                        "deaths": 12,
                        "assists": 8,
                        "playtimeMillis": 1800000,
                    },
                },
            ],
            "roundResults": [],
        }

    def test_parser(self) -> None:
        """Verifies raw JSON is parsed into ParsedMatchData accurately."""
        parser = MatchParser()
        parsed = parser.parse(self.sample_raw_match)

        self.assertEqual(parsed.match_id, "test-match-1001")
        self.assertEqual(parsed.map_id, "/Game/Maps/Ascent/Ascent")
        self.assertEqual(len(parsed.players), 2)
        self.assertEqual(parsed.players[0].game_name, "TenZ")
        self.assertEqual(parsed.players[0].kills, 25)

    def test_normalizer(self) -> None:
        """Verifies maps, agents, and timestamps are normalized."""
        parser = MatchParser()
        normalizer = DataNormalizer()

        parsed = parser.parse(self.sample_raw_match)
        normalized = normalizer.normalize(parsed)

        self.assertEqual(normalized.map_name, "Ascent")
        self.assertEqual(normalized.players[0].agent_name, "Jett")
        self.assertEqual(normalized.players[1].agent_name, "Cypher")
        self.assertEqual(normalized.winning_team, "Red")

    def test_validator(self) -> None:
        """Verifies DataValidator validates structural integrity."""
        parser = MatchParser()
        normalizer = DataNormalizer()
        validator = DataValidator()

        parsed = parser.parse(self.sample_raw_match)
        normalized = normalizer.normalize(parsed)
        val_result = validator.validate(normalized)

        self.assertTrue(val_result.is_valid)
        self.assertEqual(len(val_result.errors), 0)

    def test_feature_extractor(self) -> None:
        """Verifies combat, economy, objective, playstyle, and team features calculation."""
        parser = MatchParser()
        normalizer = DataNormalizer()
        extractor = FeatureExtractor()

        parsed = parser.parse(self.sample_raw_match)
        normalized = normalizer.normalize(parsed)
        features = extractor.extract_features(normalized)

        self.assertEqual(len(features), 2)
        tenz_feat = features[0]

        self.assertEqual(tenz_feat.match_id, "test-match-1001")
        self.assertEqual(tenz_feat.game_name, "TenZ")
        self.assertEqual(tenz_feat.kills, 25)
        self.assertEqual(tenz_feat.deaths, 10)
        self.assertEqual(tenz_feat.assists, 5)
        self.assertEqual(tenz_feat.kda_ratio, 3.0)  # (25 + 5) / 10
        self.assertEqual(tenz_feat.acs, 225.0)  # 4500 / 20
        self.assertEqual(tenz_feat.win, 1)

    def test_dataset_exporter(self) -> None:
        """Verifies DataFrame export to CSV and Parquet formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            exporter = DatasetExporter(output_dir=temp_path)

            df = pd.DataFrame([{"match_id": "test-1", "puuid": "p-1", "kills": 20, "win": 1}])
            summary = exporter.export(df, filename_prefix="test_features", export_format="both")

            self.assertEqual(summary.total_rows, 1)
            self.assertEqual(summary.total_columns, 4)
            self.assertIsNotNone(summary.csv_path)
            self.assertIsNotNone(summary.parquet_path)
            self.assertTrue(Path(summary.csv_path).exists())
            self.assertTrue(Path(summary.parquet_path).exists())

    def test_pipeline_runner(self) -> None:
        """Verifies end-to-end PipelineRunner execution and DataQualityReport generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            exporter = DatasetExporter(output_dir=temp_path)
            runner = PipelineRunner(exporter=exporter)

            df, report = runner.process_raw_matches(
                [self.sample_raw_match],
                dataset_name="test_pipeline_run",
                export_format="both",
            )

            self.assertEqual(len(df), 2)
            self.assertEqual(report.matches_processed, 1)
            self.assertEqual(report.players_processed, 2)
            self.assertEqual(report.rows_generated, 2)
            self.assertEqual(report.invalid_records_count, 0)
            self.assertGreater(report.processing_time_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
