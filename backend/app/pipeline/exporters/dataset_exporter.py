"""
Dataset Exporter Module.

Exports processed pandas DataFrames containing engineered features into structured
CSV and Apache Parquet datasets within data/processed/ directory.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import pandas as pd

from app.core.settings import settings

logger = logging.getLogger("gamepulse.pipeline.exporter")


@dataclass
class ExportSummary:
    """Export operation summary report."""
    csv_path: Optional[str]
    parquet_path: Optional[str]
    total_rows: int
    total_columns: int
    csv_size_bytes: int
    parquet_size_bytes: int


class DatasetExporter:
    """
    Exports structured feature DataFrames to persistent CSV and Parquet files.
    Single Responsibility: Dataset Exporting & Persistence.
    """

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """
        Initializes the DatasetExporter with a target output directory.

        Args:
            output_dir (Path, optional): Directory to save processed datasets.
        """
        self.output_dir = output_dir or Path(settings.pipeline.PROCESSED_DATA_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        df: pd.DataFrame,
        filename_prefix: str = "valorant_features",
        export_format: Optional[str] = None,
    ) -> ExportSummary:
        """
        Exports a pandas DataFrame containing engineered features to CSV and/or Parquet format.

        Args:
            df (pd.DataFrame): DataFrame of engineered feature observations.
            filename_prefix (str): File name prefix.
            export_format (str, optional): 'csv', 'parquet', or 'both'. Defaults to settings format.

        Returns:
            ExportSummary: Summary detailing saved paths, row/column counts, and file sizes.
        """
        fmt = (export_format or settings.pipeline.DEFAULT_DATASET_FORMAT).lower()
        csv_path: Optional[Path] = None
        parquet_path: Optional[Path] = None
        csv_size = 0
        parquet_size = 0

        if df.empty:
            logger.warning("Attempted to export an empty DataFrame.")
            return ExportSummary(
                csv_path=None,
                parquet_path=None,
                total_rows=0,
                total_columns=0,
                csv_size_bytes=0,
                parquet_size_bytes=0,
            )

        # Export to CSV if requested or set to both
        if fmt in ("csv", "both"):
            csv_path = self.output_dir / f"{filename_prefix}.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8")
            csv_size = csv_path.stat().st_size
            logger.info(f"Successfully exported CSV dataset to '{csv_path}' ({csv_size} bytes)")

        # Export to Parquet if requested or set to both
        if fmt in ("parquet", "both"):
            parquet_path = self.output_dir / f"{filename_prefix}.parquet"
            df.to_parquet(parquet_path, index=False, engine="pyarrow", compression="snappy")
            parquet_size = parquet_path.stat().st_size
            logger.info(f"Successfully exported Parquet dataset to '{parquet_path}' ({parquet_size} bytes)")

        return ExportSummary(
            csv_path=str(csv_path) if csv_path else None,
            parquet_path=str(parquet_path) if parquet_path else None,
            total_rows=len(df),
            total_columns=len(df.columns),
            csv_size_bytes=csv_size,
            parquet_size_bytes=parquet_size,
        )
