"""Homework 7, Task 6: end-to-end test of the deployed workflow service.

Submits ticket 28763 (canonical Homework 2 dataset) to POST /tickets/process and
checks the response against WORKFLOW_CONTRACT.md. Saves the result next to this file.

Run after `docker compose up --build -d`:
    pytest test_deployment.py -v
"""

import json
import math
import uuid
from pathlib import Path

import requests

WORKFLOW_URL = "http://localhost:8000"
TICKET_ID = 28763
TICKET_BODY = "Dear Customer Support Team,I hope this message finds you well. I am writing to report a concerning issue I am experiencing with my recently purchased Samsung QLED QN90A TV, which I bought from your 'Tech Online Store'. Having been a loyal customer, I expected nothing short of superior performance and reliability that Samsung products are renowned for. However, this particular unit seems to be presenting a rather persistent and distracting problem.The television has developed a flickering issue while in use, which occurs intermittently but frequently enough to hinder the viewing experience significantly. It started subtly but has become more pronounced over time, leading me to believe that it might be a hardware-related issue rather than something that could be adjusted with simple settings modifications. I understand these models are generally known for their impressive picture quality and advanced technology, so this flickering is both unexpected and disappointing.Given the nature of the problem, I suspect it might involve components relating to the display hardware, as no changes in external settings such as cables or power sources appear to affect or resolve the issue. Unfortunately, adjusting brightness levels or refreshing the support software has shown no improvement. Considering these attempts to troubleshoot the problem have been unsuccessful, I am compelled to seek your professional assistance to resolve this matter promptly.I would appreciate it if you could provide guidance on the next steps to take, possibly including instructions for an at-home diagnosis or arranging a qualified technician's assessment. Additionally, information about your repair policies and warranty coverage for such issues would be greatly appreciated. My hope is to have this resolved quickly to return to enjoying the high-quality viewing experience I anticipated upon purchase.Thank you for your attention to this matter. I look forward to your prompt response with advice on how we can proceed to rectify this issue with my Samsung QLED QN90A.Best regards,nameacc_num"
RESULT_PATH = Path(__file__).resolve().parent / "ticket_28763_result.json"  # sensitive: contains raw ticket text

DEPARTMENTS = {
    "Billing and Payments",
    "Customer Service",
    "General Inquiry",
    "Human Resources",
    "IT Support",
    "Product Support",
    "Returns and Exchanges",
    "Sales and Pre-Sales",
    "Service Outages and Maintenance",
    "Technical Support",
}
RESULT_KEYS = {
    "ticket_id", "workflow_record_id", "terminal_status", "recommended_department",
    "class_scores", "ticket_body", "ticket_summary", "retrieved_evidence", "trace_id", "error",
}
SUMMARY_KEYS = {"summary", "customer_request", "missing_information"}
EVIDENCE_KEYS = {"rank", "chunk_id", "distance", "content", "metadata"}


def _submit():
    response = requests.post(
        f"{WORKFLOW_URL}/tickets/process",
        json={"ticket_id": TICKET_ID, "Body": TICKET_BODY},
        timeout=600,  # the LLM step runs on CPU and can take minutes
    )
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.text[:200]}"
    return response.json()


def test_workflow_processes_ticket_28763():
    result = _submit()

    # Save the result before asserting, so a failing run still leaves a record.
    RESULT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # Exact top-level keys.
    assert set(result) == RESULT_KEYS

    assert result["ticket_id"] == TICKET_ID
    uuid.UUID(result["workflow_record_id"])  # raises if not a valid UUID
    assert isinstance(result["trace_id"], str) and result["trace_id"].strip()

    assert result["terminal_status"] == "summary_ready_for_review", result["error"]
    assert result["error"] is None

    # Exact body: no trimming, no case or whitespace changes.
    assert result["ticket_body"] == TICKET_BODY

    # Routing response.
    assert result["recommended_department"] in DEPARTMENTS
    scores = result["class_scores"]
    assert set(scores) == DEPARTMENTS
    for value in scores.values():
        assert isinstance(value, float) and math.isfinite(value)
    assert scores[result["recommended_department"]] == max(scores.values())

    # Summary.
    summary = result["ticket_summary"]
    assert set(summary) == SUMMARY_KEYS
    assert isinstance(summary["summary"], str) and summary["summary"].strip()
    assert isinstance(summary["customer_request"], str) and summary["customer_request"].strip()
    assert isinstance(summary["missing_information"], list)
    assert all(isinstance(item, str) and item.strip() for item in summary["missing_information"])

    # Retrieved evidence: 1 to 5 records, ranks counting up from 1.
    evidence = result["retrieved_evidence"]
    assert 1 <= len(evidence) <= 5
    for position, record in enumerate(evidence, start=1):
        assert set(record) == EVIDENCE_KEYS
        assert record["rank"] == position
        assert isinstance(record["content"], str) and record["content"].strip()
        assert isinstance(record["metadata"], dict)
