### How the workflow uses it (not part of the service)

The workflow passes this schema as `output_schema`, then checks `parsed` again itself before accepting it as `ticket_summary`:

```json
{
  "type": "object",
  "properties": {
    "summary": {"type": "string", "minLength": 1},
    "customer_request": {"type": "string", "minLength": 1},
    "missing_information": {"type": "array", "items": {"type": "string", "minLength": 1}}
  },
  "required": ["summary", "customer_request", "missing_information"],
  "additionalProperties": false
}
```