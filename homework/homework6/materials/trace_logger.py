"""Structured JSONL trace logging for the Homework 6 workflow."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType
from typing import Any
from uuid import uuid4


class TraceLogger:
    """Write and retrieve structured workflow trace records."""

    def __init__(self, log_path: str | Path) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Keep each helper instance isolated from other logging configuration.
        self._logger = logging.getLogger(f"homework6.trace.{uuid4().hex}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        # Append only the serialized message so each line is one JSON record.
        self._handler = logging.FileHandler(
            self.log_path,
            mode="a",
            encoding="utf-8",
        )
        self._handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(self._handler)
        self._closed = False

    @staticmethod
    def generate_trace_id() -> str:
        """Return a new correlation identifier."""
        return str(uuid4())

    def record(
        self,
        trace_id: str,
        timestamp: str | None = None,
        **fields: Any,
    ) -> None:
        """Add correlation metadata and persist one structured record."""
        self._ensure_open()

        trace_record = dict(fields)
        trace_record["timestamp"] = timestamp if timestamp is not None else (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        trace_record["trace_id"] = trace_id
        json_line = json.dumps(
            trace_record,
            sort_keys=True,
            separators=(",", ":"),
            # JSONL should remain valid for parsers outside Python.
            allow_nan=False,
        )
        self._logger.info(json_line)

    def read_trace(self, trace_id: str) -> list[dict[str, Any]]:
        """Return all persisted records for one trace ID in file order."""
        self._ensure_open()
        # Make records written immediately before this lookup visible on disk.
        self._handler.flush()

        # Read the entire log file, and keep only those matching the trace ID.
        # Inefficient, but simple and works for our use case.
        records: list[dict[str, Any]] = []
        with self.log_path.open(encoding="utf-8") as log_file:
            for line_number, line in enumerate(log_file, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Invalid JSON in trace log at line {line_number}."
                    ) from error
                if not isinstance(record, dict):
                    raise ValueError(
                        f"Trace log line {line_number} must contain a JSON object."
                    )
                if record.get("trace_id") == trace_id:
                    records.append(record)
        return records

    def close(self) -> None:
        """Flush and close this logger's file handler."""
        if self._closed:
            return
        self._handler.flush()
        self._handler.close()
        self._logger.removeHandler(self._handler)
        self._closed = True

    def __enter__(self) -> TraceLogger:
        self._ensure_open()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("TraceLogger is closed.")
