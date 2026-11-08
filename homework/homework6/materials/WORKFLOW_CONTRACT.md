# Ticket-Preparation Workflow Contract

Implement this contract in `workflow.py` through the `TicketWorkflow.process_ticket` method.
The internal routing, retrieval, and LLM service contracts are yours to design.

## Request

`process_ticket` accepts one dictionary with these required fields:

| Field | Type | Requirements |
| --- | --- | --- |
| `ticket_id` | integer | Must be a positive integer. A Boolean is not a valid integer identifier. |
| `Body` | string | Must contain at least one non-whitespace character. |

The request may contain additional fields. The workflow must not require them,
and routing and retrieval must both receive the same unaltered `Body`.
For successful processing, the workflow must return that exact `Body` as
`ticket_body`, preserving case and whitespace. `workflow_record_id` is
output-only: the workflow always generates it and must not use a value supplied
in the request.

If the request is not a dictionary or either required field is invalid, return
an `input_rejected` result without calling any service.

## Processing Behavior

For valid input:

1. Invoke the routing and retrieval services independently. A routing result must
   not control whether retrieval or LLM processing occurs.
2. Construct the prompt in the workflow using the ticket body, retrieved
   evidence, and the prompt-with-RAG developed in Homework 5.
3. Pass the constructed prompt to the LLM service.
4. Validate every service response against its student-defined contract.
5. Return a complete review package only after every required service succeeds.

The workflow may retry a failed operation, but it must not replace a failure
with a default route, empty retrieval result, fabricated summary, or other
success-shaped fallback.

## Response

`process_ticket` returns one dictionary with exactly these fields:

| Field | Type | Requirements |
| --- | --- | --- |
| `ticket_id` | integer or `null` | The accepted request identifier. May be `null` only when the identifier itself was invalid. |
| `workflow_record_id` | string | A non-empty UUID generated when `process_ticket` begins. It uniquely identifies this workflow invocation and is never supplied by the client. |
| `terminal_status` | string | One of the three statuses defined below. |
| `recommended_department` | string or `null` | An allowed department for a successful result; otherwise `null`. |
| `class_scores` | object or `null` | One finite numeric score for every allowed department for a successful result; otherwise `null`. |
| `ticket_body` | string or `null` | Exactly the unmodified input request `Body` for a successful result, preserving case and whitespace; otherwise `null`. |
| `ticket_summary` | object or `null` | The validated three-field summary for a successful result; otherwise `null`. |
| `retrieved_evidence` | array | The ordered evidence used to build the prompt for a successful result; otherwise an empty array. |
| `trace_id` | string or `null` | The correlation identifier added in Task 6. It may be `null` through Task 5 and must be a non-empty string after Task 6. |
| `error` | string or `null` | `null` for success; otherwise a concise, non-empty description of the rejection or failure. |

Do not include ticket text, prompts, retrieved content, generated summaries,
credentials, or hidden model reasoning in `error` or trace records outside the
dedicated `ticket_body` response field.

### Terminal Statuses

| Status | Meaning |
| --- | --- |
| `summary_ready_for_review` | Every service succeeded and the complete review package is valid. |
| `input_rejected` | The request failed validation and no service was called. |
| `workflow_failed` | A service, service-response validation, prompt construction, or workflow operation failed. |

### Successful Review Package

For `summary_ready_for_review`:

- `ticket_id` is the request's positive integer identifier.
- `recommended_department` is exactly one of:
  - `Billing and Payments`
  - `Customer Service`
  - `General Inquiry`
  - `Human Resources`
  - `IT Support`
  - `Product Support`
  - `Returns and Exchanges`
  - `Sales and Pre-Sales`
  - `Service Outages and Maintenance`
  - `Technical Support`
- `class_scores` contains exactly those ten departments with finite numeric
  values, and its highest-scoring department is `recommended_department`.
- `ticket_body` is exactly the request `Body`, preserving case and whitespace.
- `ticket_summary` contains exactly:

| Field | Type |
| --- | --- |
| `summary` | string |
| `customer_request` | string |
| `missing_information` | array of strings |

- `retrieved_evidence` contains the ordered records returned by
  `VectorStore.query()`. Each record contains `rank`, `chunk_id`, `distance`,
  `content`, and `metadata`.
- `error` is `null`.

The summary and customer request must remain grounded in the ticket body.
Retrieved evidence may inform `missing_information`.

### Non-Success Results

For `input_rejected` and `workflow_failed`:

- `workflow_record_id` is the UUID generated for this workflow invocation.
- `recommended_department` is `null`.
- `class_scores` is `null`.
- `ticket_body` is `null`.
- `ticket_summary` is `null`.
- `retrieved_evidence` is an empty array.
- `error` describes what prevented a complete review package.

A non-success result may not expose a partial review package. Partial progress
remains visible through the correlated log records added in Task 6.
