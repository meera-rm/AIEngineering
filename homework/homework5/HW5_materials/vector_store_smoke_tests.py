"""Smoke tests for the supplied Homework 5 VectorStore class."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable
from unittest.mock import patch

import VectorStore as supplied_helper
from VectorStore import VectorStore
from huggingface_hub.errors import LocalEntryNotFoundError


RECORDS = [
    {
        "chunk_id": "printer-wireless-0",
        "embedding_text": "Connect a Canon printer to a 2.4 GHz wireless network.",
        "content": "The printer must be connected to a 2.4 GHz Wi-Fi network.",
        "metadata": {
            "article_id": "printer-wireless",
            "title": "Connect a Printer to Wi-Fi",
            "chunk_position": 0,
            7: ["numeric key", None, True],
            1.25: {"nested": {2: "nested numeric key", "label": "mixed keys"}},
            None: "null key",
            False: ("tuple", "becomes a list"),
        },
    },
    {
        "chunk_id": "duplicate-charge-0",
        "embedding_text": "Request a refund after a duplicate credit card charge.",
        "content": "Send duplicate-charge details to the billing support team.",
        "metadata": {
            "article_id": "duplicate-charge",
            "title": "Resolve a Duplicate Charge",
            "chunk_position": 0,
        },
    },
    {
        "chunk_id": "password-reset-0",
        "embedding_text": "Reset a forgotten account password.",
        "content": "Use the Forgot Password link on the sign-in page.",
        "metadata": {
            "article_id": "password-reset",
            "title": "Reset an Account Password",
            "chunk_position": 0,
        },
    },
]


def assert_raises(
    exception_type: type[Exception],
    function: Callable[..., object],
    *args: object,
    **kwargs: object,
) -> None:
    """Assert that calling a function raises the expected exception."""
    try:
        function(*args, **kwargs)
    except exception_type:
        return
    raise AssertionError(f"Expected {exception_type.__name__} to be raised")


def run_smoke_tests() -> None:
    """Exercise the VectorStore API against a temporary persisted database."""
    run_embedder_tests()
    scratch_path = Path(__file__).resolve().parents[3] / "ai_scratch"
    scratch_path.mkdir(exist_ok=True)
    with TemporaryDirectory(
        prefix="homework5_vector_store_", dir=scratch_path
    ) as temporary_directory:
        database_path = Path(temporary_directory) / "database"
        vector_store = VectorStore(database_path)

        assert_raises(ValueError, vector_store.build, [])
        assert_raises(ValueError, vector_store.build, [RECORDS[0], RECORDS[0]])

        vector_store.build(RECORDS)

        query = "My Canon printer will not connect to my 2.4 GHz Wi-Fi."
        results = vector_store.query(query, top_k=2)

        assert len(results) == 2
        assert results[0]["chunk_id"] == "printer-wireless-0"
        assert [result["rank"] for result in results] == [1, 2]
        assert results[0]["distance"] <= results[1]["distance"]
        assert results[0]["content"] == RECORDS[0]["content"]
        expected_metadata = json.loads(json.dumps(RECORDS[0]["metadata"]))
        assert results[0]["metadata"] == expected_metadata

        default_results = vector_store.query(query)
        assert len(default_results) == len(RECORDS)

        assert_raises(ValueError, vector_store.query, "   ")
        assert_raises(ValueError, vector_store.query, query, top_k=0)

        # A new instance proves that records can be queried after reopening the database.
        reopened_store = VectorStore(database_path)
        reopened_results = reopened_store.query(query, top_k=1)
        assert reopened_results[0]["chunk_id"] == "printer-wireless-0"
        assert reopened_results[0]["metadata"] == expected_metadata

        reference_helper = load_reference_helper()
        if reference_helper is not None:
            model_path = supplied_helper.snapshot_download(
                repo_id=supplied_helper.MODEL_REPOSITORY,
                revision=supplied_helper.MODEL_REVISION,
                allow_patterns=supplied_helper.MODEL_FILES,
                local_files_only=True,
            )
            with patch.object(
                reference_helper, "MODEL_PATH", Path(model_path)
            ):
                reference_store = reference_helper.VectorStore(database_path)
                reference_results = reference_store.query(query, top_k=2)
            assert reference_results == results

        # Rebuilding replaces the table instead of appending duplicate or stale records.
        reopened_store.build([RECORDS[1]])
        rebuilt_results = reopened_store.query("I was charged twice.", top_k=5)
        assert len(rebuilt_results) == 1
        assert rebuilt_results[0]["chunk_id"] == "duplicate-charge-0"


def load_reference_helper():
    """Load the packaged query helper separately when running in the course repo."""
    reference_path = (
        Path(__file__).resolve().parents[2]
        / "homework7" / "sample_output" / "task2" / "VectorStore.py"
    )
    if not reference_path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("reference_vector_store", reference_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_embedder_tests() -> None:
    """Check exact revision resolution and ensure FastEmbed never downloads a model."""
    assert supplied_helper.MODEL_REPOSITORY == "qdrant/bge-small-en-v1.5-onnx-q"
    assert supplied_helper.MODEL_REVISION == "52398278842ec682c6f32300af41344b1c0b0bb2"
    snapshot_path = str(Path("ai_scratch") / "mock_pinned_snapshot")
    pinned_arguments = {
        "repo_id": supplied_helper.MODEL_REPOSITORY,
        "revision": supplied_helper.MODEL_REVISION,
        "allow_patterns": supplied_helper.MODEL_FILES,
    }
    with (
        patch.object(supplied_helper.lancedb, "connect"),
        patch.object(supplied_helper, "snapshot_download") as download,
        patch.object(supplied_helper, "TextEmbedding") as embedder,
    ):
        download.return_value = snapshot_path
        VectorStore("unused")
        download.assert_called_once_with(**pinned_arguments, local_files_only=True)
        embedder.assert_called_once_with(
            model_name=supplied_helper.MODEL_NAME,
            specific_model_path=snapshot_path,
            cache_dir=snapshot_path,
            local_files_only=True,
        )

        download.reset_mock()
        embedder.reset_mock()
        download.side_effect = [LocalEntryNotFoundError("not cached"), snapshot_path]
        VectorStore("unused")
        assert download.call_count == 2
        assert download.call_args_list[0].kwargs == {
            **pinned_arguments, "local_files_only": True,
        }
        assert download.call_args_list[1].kwargs == pinned_arguments
        assert embedder.call_args.kwargs["specific_model_path"] == snapshot_path

        download.reset_mock()
        embedder.reset_mock()
        download.side_effect = [LocalEntryNotFoundError("not cached"), OSError("offline")]
        assert_raises(OSError, VectorStore, "unused")
        assert download.call_count == 2
        embedder.assert_not_called()

    reference_helper = load_reference_helper()
    if reference_helper is not None:
        assert reference_helper.MODEL_NAME == supplied_helper.MODEL_NAME
        assert reference_helper.MODEL_REPOSITORY == supplied_helper.MODEL_REPOSITORY
        assert reference_helper.MODEL_REVISION == supplied_helper.MODEL_REVISION
        assert reference_helper.MODEL_FILES == supplied_helper.MODEL_FILES
        with (
            patch.object(reference_helper.lancedb, "connect"),
            patch.object(reference_helper, "TextEmbedding") as embedder,
        ):
            reference_helper.VectorStore("unused")
            embedder.assert_called_once_with(
                model_name=supplied_helper.MODEL_NAME,
                specific_model_path=str(reference_helper.MODEL_PATH),
                cache_dir=str(reference_helper.MODEL_PATH),
                local_files_only=True,
            )
            embedder.side_effect = OSError("missing packaged model")
            assert_raises(OSError, reference_helper.VectorStore, "unused")

        # Execute the image's download command with a mock, without fetching files.
        dockerfile = Path(reference_helper.__file__).with_name("Dockerfile").read_text()
        command = next(
            line.removeprefix('RUN python -c "').removesuffix('"')
            for line in dockerfile.splitlines()
            if line.startswith('RUN python -c "')
        )
        with (
            patch("huggingface_hub.snapshot_download") as download,
            patch.dict("sys.modules", {"VectorStore": reference_helper}),
        ):
            exec(command, {})
            download.assert_called_once_with(
                **pinned_arguments, local_dir=reference_helper.MODEL_PATH
            )
        assert "ENV HF_HUB_OFFLINE=1" in dockerfile


if __name__ == "__main__":
    run_smoke_tests()
    print("All VectorStore smoke tests passed.")
