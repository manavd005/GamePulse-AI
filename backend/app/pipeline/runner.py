"""
Data Pipeline Coordinator / Runner Module.

Orchestrates raw JSON discovery, parsing, normalization, validation, feature extraction,
dataset exporting, and machine-readable Data Quality Report generation.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from app.core.settings import settings
from app.pipeline.exporters.dataset_exporter import DatasetExporter, ExportSummary
from app.pipeline.features.feature_extractor import FeatureExtractor, PlayerMatchFeatureRow
from app.pipeline.normalizer.data_normalizer import DataNormalizer
from app.pipeline.parser.match_parser import MatchParser
from app.pipeline.validator.data_validator import DataValidator

logger = logging.getLogger("gamepulse.pipeline.runner")


@dataclass
class DataQualityReport:
    """Machine-readable Data Quality Report summary."""
    players_processed: int = 0
    matches_processed: int = 0
    rows_generated: int = 0
    missing_values_count: int = 0
    invalid_records_count: int = 0
    duplicate_records_count: int = 0
    processing_time_seconds: float = 0.0
    exported_files: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts DataQualityReport instance to dictionary."""
        return asdict(self)


class PipelineRunner:
    """
    Orchestrates end-to-end data pipeline operations.
    Combines Parser, Normalizer, Validator, FeatureExtractor, and Exporter.
    """

    def __init__(
        self,
        parser: Optional[MatchParser] = None,
        normalizer: Optional[DataNormalizer] = None,
        validator: Optional[DataValidator] = None,
        extractor: Optional[FeatureExtractor] = None,
        exporter: Optional[DatasetExporter] = None,
    ) -> None:
        """
        Initializes the PipelineRunner with pipeline stage dependencies.
        """
        self.parser = parser or MatchParser()
        self.normalizer = normalizer or DataNormalizer()
        self.validator = validator or DataValidator()
        self.extractor = extractor or FeatureExtractor()
        self.exporter = exporter or DatasetExporter()

    def process_raw_matches(
        self,
        raw_match_payloads: List[Dict[str, Any]],
        dataset_name: str = "valorant_features",
        export_format: Optional[str] = None,
    ) -> tuple[pd.DataFrame, DataQualityReport]:
        """
        Processes a list of raw match JSON payloads through the full pipeline.

        Args:
            raw_match_payloads (list[dict]): List of raw Riot match JSON payloads.
            dataset_name (str): Output filename prefix for exported dataset files.
            export_format (str, optional): 'csv', 'parquet', or 'both'.

        Returns:
            tuple[pd.DataFrame, DataQualityReport]: Processed DataFrame and Data Quality Report.
        """
        start_time = time.time()
        logger.info(f"Starting Data Pipeline processing for {len(raw_match_payloads)} match payloads...")

        all_feature_rows: List[PlayerMatchFeatureRow] = []
        players_set = set()
        matches_count = 0
        invalid_count = 0
        duplicate_count = 0
        missing_values_count = 0

        for raw_payload in raw_match_payloads:
            try:
                # 1. Parse
                parsed_match = self.parser.parse(raw_payload)

                # 2. Normalize
                normalized_match = self.normalizer.normalize(parsed_match)

                # 3. Validate
                val_result = self.validator.validate(normalized_match)
                if not val_result.is_valid:
                    invalid_count += 1
                    logger.warning(f"Skipping match '{normalized_match.match_id}' due to validation errors.")
                    continue

                # 4. Feature Extraction
                feature_rows = self.extractor.extract_features(normalized_match)
                all_feature_rows.extend(feature_rows)

                matches_count += 1
                for r in feature_rows:
                    players_set.add(r.puuid)

            except Exception as err:
                invalid_count += 1
                logger.error(f"Error processing raw match payload: {err}")

        # Convert feature rows to pandas DataFrame
        if all_feature_rows:
            dict_rows = self.extractor.rows_to_dicts(all_feature_rows)
            df = pd.DataFrame(dict_rows)
            missing_values_count = int(df.isna().sum().sum())
            duplicate_count = int(df.duplicated(subset=["match_id", "puuid"]).sum())
        else:
            df = pd.DataFrame()

        # 5. Export Dataset
        export_summary: ExportSummary = self.exporter.export(
            df,
            filename_prefix=dataset_name,
            export_format=export_format,
        )

        elapsed_time = round(time.time() - start_time, 4)

        report = DataQualityReport(
            players_processed=len(players_set),
            matches_processed=matches_count,
            rows_generated=len(df),
            missing_values_count=missing_values_count,
            invalid_records_count=invalid_count,
            duplicate_records_count=duplicate_count,
            processing_time_seconds=elapsed_time,
            exported_files={
                "csv_path": export_summary.csv_path,
                "parquet_path": export_summary.parquet_path,
                "csv_size_bytes": export_summary.csv_size_bytes,
                "parquet_size_bytes": export_summary.parquet_size_bytes,
            },
        )

        logger.info("==================================================")
        logger.info(" DATA PIPELINE EXECUTION COMPLETED")
        logger.info(f" Players Processed: {report.players_processed}")
        logger.info(f" Matches Processed: {report.matches_processed}")
        logger.info(f" Feature Rows Generated: {report.rows_generated}")
        logger.info(f" Invalid Records: {report.invalid_records_count}")
        logger.info(f" Execution Time: {report.processing_time_seconds}s")
        logger.info("==================================================")

        return df, report

    def run_from_directory(
        self,
        raw_dir: Optional[Path] = None,
        dataset_name: str = "valorant_features",
        export_format: Optional[str] = None,
    ) -> tuple[pd.DataFrame, DataQualityReport]:
        """
        Discovers raw JSON files in raw_dir and executes the pipeline.

        Args:
            raw_dir (Path, optional): Directory containing raw match JSON files.
            dataset_name (str): Target filename prefix.
            export_format (str, optional): Export format.

        Returns:
            tuple[pd.DataFrame, DataQualityReport]: Processed DataFrame and Data Quality Report.
        """
        target_dir = raw_dir or Path(settings.pipeline.RAW_DATA_DIR)
        logger.info(f"Searching raw JSON match files in directory '{target_dir}'...")

        raw_payloads: List[Dict[str, Any]] = []
        if target_dir.exists():
            for json_file in target_dir.glob("**/*.json"):
                if json_file.name.endswith("account.json"):
                    continue
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                        if isinstance(payload, dict) and "matchInfo" in payload:
                            raw_payloads.append(payload)
                except Exception as err:
                    logger.warning(f"Could not load JSON file '{json_file}': {err}")

        logger.info(f"Discovered {len(raw_payloads)} raw match JSON payloads.")
        return self.process_raw_matches(
            raw_payloads,
            dataset_name=dataset_name,
            export_format=export_format,
        )
