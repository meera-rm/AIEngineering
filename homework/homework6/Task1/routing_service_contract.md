# Routing Service Contract

**Contract parts:** purpose, entry point, request schema, response schema, errors.

**Purpose:** Classify a ticket body into exactly one of the ten allowed departments using the classifier from earlier homeworks.
**Entry point:** `RoutingService.route_ticket(request: dict) -> dict` (classifier loaded once in `__init__`, reused per call)

## Request schema

| Field | Type | Required | Rules |
|---|---|---|---|
| `body` | str | yes | At least one non-whitespace character. Passed to the classifier exactly as received; the service does not trim, lowercase, or otherwise modify it. |

The request must be a dictionary. Extra fields are ignored.


## Response schema (success)

| Field | Type | Required | Rules |
|---|---|---|---|
| `recommended_department` | str | yes | One of the 10 allowed departments (listed below). |
| `class_scores` | dict[str, float] | yes | Exactly the 10 allowed departments as keys. Every value is a finite number (no NaN/±inf). The score of `recommended_department` equals the maximum score (ties allowed, see below). |


Allowed departments: `Billing and Payments`, `Customer Service`, `General Inquiry`, `Human Resources`, `IT Support`, `Product Support`, `Returns and Exchanges`, `Sales and Pre-Sales`, `Service Outages and Maintenance`, `Technical Support`.

The classifier's `recommended_department` and `class_scores` are returned as produced, not re-labelled or renormalized.

Scores are rounded by the classifier (2 decimals in the HW4 model), so two departments can tie for the top score. `recommended_department` must have a score equal to the maximum score; if tied, it may be any of the tied departments.

## Error handling

| Error | When | Retryable? |
|---|---|---|
| `InvalidRequestError` | The request is not a dict, or `body` is missing, has the wrong type, or breaks a rule in the request schema. The classifier is not called. | No. The same input fails the same way. |
| `RoutingServiceError` | The classifier cannot be set up: the saved classifier file is missing, corrupt, not a `TicketRouter`, or not fitted. | No. The file will not fix itself; someone has to repair it. |
| `RoutingServiceError` | The classifier raises an exception while scoring a request, or its output breaks the response schema rules. | No. The classifier is deterministic, so the same text gives the same result. |

- **No success-shaped fallback:** the service **never** returns a default department (e.g. `General Inquiry`) or made-up scores when it fails.
- Error messages never contain the ticket body or any part of it.
- Before returning, the service validates the classifier's output against the response schema above.
- Routing runs inside the same Python program with no network call, so it has no temporary failures. The workflow does not retry it, because the same input would give the same result.
