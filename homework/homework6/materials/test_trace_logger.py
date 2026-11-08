"""Basic tests for the supplied trace logger."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from trace_logger import TraceLogger


class TraceLoggerTests(unittest.TestCase):
    logger_type = TraceLogger

    def test_records_and_reads_one_trace(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "traces.jsonl"

            with self.logger_type(log_path) as trace_logger:
                trace_id = trace_logger.generate_trace_id()
                other_trace_id = trace_logger.generate_trace_id()

                UUID(trace_id)
                UUID(other_trace_id)
                self.assertNotEqual(trace_id, other_trace_id)

                trace_logger.record(
                    trace_id,
                    component="workflow",
                    event="started",
                )
                trace_logger.record(
                    trace_id,
                    component="retrieval",
                    event="completed",
                    elapsed_ms=12.5,
                    retrieved_chunk_ids=["article-1::chunk-1"],
                    details={"attempt": 1},
                )
                trace_logger.record(
                    other_trace_id,
                    component="workflow",
                    event="started",
                )

                records = trace_logger.read_trace(trace_id)
                self.assertEqual(len(records), 2)
                self.assertEqual(
                    [record["event"] for record in records],
                    ["started", "completed"],
                )
                self.assertTrue(
                    all(record["trace_id"] == trace_id for record in records)
                )
                self.assertEqual(records[1]["details"], {"attempt": 1})
                self.assertEqual(
                    trace_logger.read_trace("unknown-trace-id"),
                    [],
                )
                self.assertRegex(
                    records[0]["timestamp"],
                    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$",
                )

            lines = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 3)
            for line in lines:
                record = json.loads(line)
                self.assertIn("timestamp", record)
                self.assertIn("trace_id", record)

    def test_preserves_explicit_timestamp(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            with self.logger_type(Path(temporary_directory) / "traces.jsonl") as trace_logger:
                measurements = {
                    "elapsed_ms": 12.5,
                    "custom_measurement": {"attempt": 1, "values": [2, 3]},
                }
                trace_logger.record(
                    "fixture-trace",
                    timestamp="2025-01-02T03:04:05Z",
                    component="workflow",
                    **measurements,
                )
                expected = {
                    "trace_id": "fixture-trace",
                    "timestamp": "2025-01-02T03:04:05Z",
                    "component": "workflow",
                    **measurements,
                }
                self.assertEqual(trace_logger.read_trace("fixture-trace"), [expected])
                self.assertEqual(
                    json.loads(trace_logger.log_path.read_text(encoding="utf-8")),
                    expected,
                )

    def test_explicit_none_generates_utc_timestamp(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            with self.logger_type(Path(temporary_directory) / "traces.jsonl") as logger:
                logger.record("fixture-trace", timestamp=None, custom_count=7)
                record = logger.read_trace("fixture-trace")[0]
                self.assertRegex(
                    record["timestamp"],
                    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$",
                )
                self.assertEqual(record["custom_count"], 7)

    def test_preserves_positional_and_empty_timestamps(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            with self.logger_type(Path(temporary_directory) / "traces.jsonl") as logger:
                logger.record("fixture-trace", "2025-01-02T03:04:05+00:00")
                logger.record("fixture-trace", timestamp="")
                self.assertEqual(
                    [record["timestamp"] for record in logger.read_trace("fixture-trace")],
                    ["2025-01-02T03:04:05+00:00", ""],
                )


if __name__ == "__main__":
    unittest.main()
