"""Stub-service tests for TicketWorkflow. Run from Task5:  python -m unittest test_workflow -v"""
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import workflow as w

_real_sleep = time.sleep   # the retry patch below replaces time.sleep, so stubs keep the real one
from workflow import TicketWorkflow, DEPARTMENTS

SECRET = "SECRET-TICKET-TEXT-12345"
GOOD_BODY = "My invoice shows a charge I do not recognize."


def good_routing():
    return {"recommended_department": DEPARTMENTS[0],
            "class_scores": {d: (0.9 if d == DEPARTMENTS[0] else 0.01) for d in DEPARTMENTS}}


def good_evidence():
    return {"results": [{"rank": 1, "chunk_id": "a#1", "distance": 0.3, "content": "text",
                         "metadata": {"title": "T", "section_heading": "H"}}]}


def good_llm():
    return {"model": "m", "text": "{}", "duration_ms": 1,
            "parsed": {"summary": "s", "customer_request": "c", "missing_information": []}}


class StubRouting:
    def __init__(self, result=None, error=None, delay=0):
        self.result, self.error, self.delay, self.calls = result, error, delay, 0
    def route_ticket(self, request):
        self.calls += 1
        _real_sleep(self.delay)
        if self.error:
            raise self.error
        return self.result if self.result is not None else good_routing()


class StubRetrieval:
    def __init__(self, results=None, delay=0):
        # results: list of items; an Exception instance is raised, anything else returned
        self.results, self.delay, self.calls = results or [good_evidence()], delay, 0
    def retrieve_evidence(self, request):
        _real_sleep(self.delay)
        item = self.results[min(self.calls, len(self.results) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


class StubLLM:
    def __init__(self, results=None, delay=0):
        self.results, self.delay, self.calls, self.last_request = results or [good_llm()], delay, 0, None
    def call_llm(self, request):
        _real_sleep(self.delay)
        self.last_request = request
        item = self.results[min(self.calls, len(self.results) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


_LOG_DIR = tempfile.mkdtemp()


def make(routing=None, retrieval=None, llm=None):
    return TicketWorkflow(routing or StubRouting(), retrieval or StubRetrieval(), llm or StubLLM(),
                          log_path=Path(_LOG_DIR) / "trace.jsonl")


@mock.patch.object(w.time, "sleep", lambda s: None)   # no real waiting during retries
class WorkflowTests(unittest.TestCase):

    def ok(self, request=None):
        return make().process_ticket(request or {"ticket_id": 1, "Body": GOOD_BODY})

    # ---- happy path / contract shape
    def test_success_shape(self):
        out = self.ok()
        self.assertEqual(out["terminal_status"], "summary_ready_for_review")
        self.assertEqual(set(out), {"ticket_id", "workflow_record_id", "terminal_status",
                                    "recommended_department", "class_scores", "ticket_body",
                                    "ticket_summary", "retrieved_evidence", "trace_id", "error"})
        self.assertEqual(out["ticket_body"], GOOD_BODY)
        self.assertEqual(out["ticket_id"], 1)
        self.assertIsNone(out["error"])

    def test_record_id_unique_and_never_from_client(self):
        a = make().process_ticket({"ticket_id": 1, "Body": GOOD_BODY, "workflow_record_id": "evil"})
        b = self.ok()
        self.assertNotEqual(a["workflow_record_id"], "evil")
        self.assertNotEqual(a["workflow_record_id"], b["workflow_record_id"])

    def test_body_kept_exactly(self):
        body = "  keep   spacing\n and newlines  "
        self.assertEqual(self.ok({"ticket_id": 1, "Body": body})["ticket_body"], body)

    def test_llm_gets_model_options_schema(self):
        llm = StubLLM()
        make(llm=llm).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        r = llm.last_request
        self.assertEqual(r["model"], w.MODEL)
        self.assertEqual(r["options"], w.OPTIONS)
        self.assertEqual(r["output_schema"], w.SUMMARY_SCHEMA)
        self.assertEqual([m["role"] for m in r["messages"]], ["system", "user"])
        self.assertIn(GOOD_BODY, r["messages"][1]["content"])

    # ---- input rejection
    def test_input_rejected(self):
        bad = [None, "x", [], {"Body": GOOD_BODY}, {"ticket_id": 0, "Body": GOOD_BODY},
               {"ticket_id": -3, "Body": GOOD_BODY}, {"ticket_id": True, "Body": GOOD_BODY},
               {"ticket_id": "1", "Body": GOOD_BODY}, {"ticket_id": 1},
               {"ticket_id": 1, "Body": ""}, {"ticket_id": 1, "Body": "   \n"},
               {"ticket_id": 1, "Body": 5}]
        for request in bad:
            with self.subTest(request=request):
                routing, retrieval, llm = StubRouting(), StubRetrieval(), StubLLM()
                out = make(routing, retrieval, llm).process_ticket(request)
                self.assertEqual(out["terminal_status"], "input_rejected")
                self.assertTrue(out["error"])
                self.assertIsNone(out["ticket_summary"])
                self.assertEqual(out["retrieved_evidence"], [])
                self.assertEqual((routing.calls, retrieval.calls, llm.calls), (0, 0, 0))

    # ---- retries
    def test_retrieval_retries_then_succeeds(self):
        retrieval = StubRetrieval([w.RetrievalUnavailableError("x"), w.RetrievalUnavailableError("x"), good_evidence()])
        out = make(retrieval=retrieval).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        self.assertEqual(out["terminal_status"], "summary_ready_for_review")
        self.assertEqual(retrieval.calls, 3)

    def test_retrieval_gives_up_after_two_retries(self):
        retrieval = StubRetrieval([w.RetrievalUnavailableError("x")])
        out = make(retrieval=retrieval).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        self.assertEqual(out["terminal_status"], "workflow_failed")
        self.assertEqual(retrieval.calls, 3)

    def test_llm_retries_then_succeeds(self):
        llm = StubLLM([w.LLMUnavailableError("x"), w.LLMUnavailableError("x"), good_llm()])
        out = make(llm=llm).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        self.assertEqual(out["terminal_status"], "summary_ready_for_review")
        self.assertEqual(llm.calls, 3)

    def test_llm_gives_up_after_two_retries(self):
        llm = StubLLM([w.LLMUnavailableError("x")])
        out = make(llm=llm).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        self.assertEqual(out["terminal_status"], "workflow_failed")
        self.assertEqual(llm.calls, 3)

    def test_non_retryable_errors_not_retried(self):
        llm = StubLLM([RuntimeError(SECRET)])
        retrieval = StubRetrieval([ValueError(SECRET)])
        routing = StubRouting(error=RuntimeError(SECRET))
        out = make(routing, retrieval, llm).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        self.assertEqual(out["terminal_status"], "workflow_failed")
        self.assertEqual((routing.calls, retrieval.calls), (1, 1))
        self.assertEqual(llm.calls, 0)   # retrieval failed first, LLM never reached

    # ---- failure paths: no default values, no leaked text
    def assert_failed(self, out):
        self.assertEqual(out["terminal_status"], "workflow_failed")
        self.assertTrue(out["error"])
        self.assertNotIn(SECRET, out["error"])
        self.assertIsNone(out["recommended_department"])
        self.assertIsNone(out["class_scores"])
        self.assertIsNone(out["ticket_body"])
        self.assertIsNone(out["ticket_summary"])
        self.assertEqual(out["retrieved_evidence"], [])

    def test_routing_failure(self):
        self.assert_failed(make(routing=StubRouting(error=RuntimeError(SECRET))).process_ticket(
            {"ticket_id": 1, "Body": GOOD_BODY}))

    def test_retrieval_failure(self):
        self.assert_failed(make(retrieval=StubRetrieval([RuntimeError(SECRET)])).process_ticket(
            {"ticket_id": 1, "Body": GOOD_BODY}))

    def test_llm_failure(self):
        self.assert_failed(make(llm=StubLLM([RuntimeError(SECRET)])).process_ticket(
            {"ticket_id": 1, "Body": GOOD_BODY}))

    def test_both_paths_fail_reports_both(self):
        out = make(routing=StubRouting(error=RuntimeError(SECRET)),
                   llm=StubLLM([RuntimeError(SECRET)])).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        self.assert_failed(out)
        self.assertIn("routing", out["error"])
        self.assertIn("LLM", out["error"])

    # ---- bad service responses must fail, not pass through
    def test_bad_routing_responses(self):
        r = good_routing()
        cases = {
            "not a dict": "oops",
            "extra key": {**r, "extra": 1},
            "missing key": {"recommended_department": DEPARTMENTS[0]},
            "wrong dept set": {**r, "class_scores": {**{d: 0.1 for d in DEPARTMENTS[:-1]}, "Other": 0.1}},
            "bool score": {**r, "class_scores": {**r["class_scores"], DEPARTMENTS[1]: True}},
            "nan score": {**r, "class_scores": {**r["class_scores"], DEPARTMENTS[1]: float("nan")}},
            "unknown rec": {**r, "recommended_department": "Nope"},
            "rec not max": {**r, "recommended_department": DEPARTMENTS[1]},
        }
        for name, bad in cases.items():
            with self.subTest(name):
                out = make(routing=StubRouting(result=bad)).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
                self.assertEqual(out["terminal_status"], "workflow_failed")

    def test_bad_retrieval_responses(self):
        rec = good_evidence()["results"][0]
        cases = {
            "not a dict": [],
            "empty results": {"results": []},
            "six records": {"results": [rec] * 6},
            "extra key": {"results": [{**rec, "score": 1}]},
            "missing key": {"results": [{k: v for k, v in rec.items() if k != "rank"}]},
            "blank content": {"results": [{**rec, "content": "  "}]},
            "bad metadata": {"results": [{**rec, "metadata": "x"}]},
            "extra top key": {"results": [rec], "x": 1},
        }
        for name, bad in cases.items():
            with self.subTest(name):
                out = make(retrieval=StubRetrieval([bad])).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
                self.assertEqual(out["terminal_status"], "workflow_failed")

    def test_bad_llm_responses(self):
        p = good_llm()["parsed"]
        cases = {
            "not a dict": "oops",
            "no parsed": {"text": "x"},
            "parsed None": {"parsed": None},
            "missing field": {"parsed": {"summary": "s", "customer_request": "c"}},
            "extra field": {"parsed": {**p, "x": 1}},
            "blank summary": {"parsed": {**p, "summary": " "}},
            "missing_info not list": {"parsed": {**p, "missing_information": "none"}},
            "blank item": {"parsed": {**p, "missing_information": [""]}},
        }
        for name, bad in cases.items():
            with self.subTest(name):
                out = make(llm=StubLLM([bad])).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
                self.assertEqual(out["terminal_status"], "workflow_failed")

    # ---- parallelism
    def test_routing_and_summary_run_in_parallel(self):
        routing = StubRouting(delay=0.5)
        retrieval, llm = StubRetrieval(delay=0.25), StubLLM(delay=0.25)
        start = time.perf_counter()
        out = make(routing, retrieval, llm).process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        elapsed = time.perf_counter() - start
        self.assertEqual(out["terminal_status"], "summary_ready_for_review")
        # sequential would be ~1.0 s; parallel is ~0.5 s
        self.assertLess(elapsed, 0.85, f"took {elapsed:.2f}s - paths look sequential")

    def test_routing_failure_still_waits_for_summary(self):
        llm = StubLLM()
        make(routing=StubRouting(error=RuntimeError(SECRET)), llm=llm).process_ticket(
            {"ticket_id": 1, "Body": GOOD_BODY})
        self.assertEqual(llm.calls, 1)

    # ---- tracing
    def trace_of(self, flow, out):
        return flow.tracer.read_trace(out["trace_id"])

    def test_trace_id_in_every_response(self):
        self.assertTrue(self.ok()["trace_id"])
        rejected = make().process_ticket({"ticket_id": 0, "Body": GOOD_BODY})
        self.assertTrue(rejected["trace_id"])
        self.assertNotEqual(self.ok()["trace_id"], self.ok()["trace_id"])

    def test_success_trace_events(self):
        flow = make()
        out = flow.process_ticket({"ticket_id": 7, "Body": GOOD_BODY})
        records = self.trace_of(flow, out)
        events = [(r["event"], r.get("service")) for r in records]
        self.assertEqual(events[0], ("workflow_started", None))
        self.assertEqual(events[-1], ("workflow_completed", None))
        for service in ("routing", "retrieval", "llm"):
            self.assertIn(("service_started", service), events)
            self.assertIn(("service_completed", service), events)
        self.assertTrue(all(r["trace_id"] == out["trace_id"] for r in records))
        done = records[-1]
        self.assertEqual(done["terminal_status"], "summary_ready_for_review")
        self.assertIsInstance(done["duration_ms"], float)
        for r in records:
            if r["event"] == "service_completed":
                self.assertIsInstance(r["duration_ms"], float)
        self.assertEqual(next(r for r in records if r["event"] == "routing_result")["recommended_department"],
                         DEPARTMENTS[0])
        self.assertEqual(next(r for r in records if r["event"] == "retrieval_result")["chunk_ids"], ["a#1"])

    def test_failure_trace(self):
        flow = make(llm=StubLLM([RuntimeError(SECRET)]))
        out = flow.process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        records = self.trace_of(flow, out)
        failed = [r for r in records if r["event"] == "service_failed"]
        self.assertEqual([r["service"] for r in failed], ["llm"])
        self.assertEqual(failed[0]["error_type"], "RuntimeError")
        self.assertEqual(records[-1]["terminal_status"], "workflow_failed")

    def test_each_retry_attempt_is_traced(self):
        flow = make(retrieval=StubRetrieval([w.RetrievalUnavailableError("x"), good_evidence()]))
        out = flow.process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        records = self.trace_of(flow, out)
        starts = [r for r in records if r["event"] == "service_started" and r["service"] == "retrieval"]
        self.assertEqual(len(starts), 2)

    def test_log_never_contains_sensitive_text(self):
        body = f"private {SECRET} ticket text"
        flow = make(routing=StubRouting(error=RuntimeError(body)),
                    retrieval=StubRetrieval([RuntimeError(body)]))
        flow.process_ticket({"ticket_id": 1, "Body": body})
        ok_flow = make()
        ok_flow.process_ticket({"ticket_id": 1, "Body": body})
        for f in (flow, ok_flow):
            f.tracer._handler.flush()
            text = f.tracer.log_path.read_text()
            self.assertNotIn(SECRET, text)
            self.assertNotIn("text", [k for line in text.splitlines() for k in json.loads(line)] )
            for banned in ("ticket_body", "messages", "content", "summary", "customer_request"):
                self.assertNotIn(f'"{banned}"', text)

    def test_one_logger_reused(self):
        flow = make()
        first = flow.tracer
        flow.process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        flow.process_ticket({"ticket_id": 1, "Body": GOOD_BODY})
        self.assertIs(flow.tracer, first)


if __name__ == "__main__":
    unittest.main()
