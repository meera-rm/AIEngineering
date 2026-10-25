# Task 7, Iteration 2: experiment log

**Decision: revert.** The change fixed some placeholder mistakes but created others, and the total did not go down. The prompt carried forward is the original (`../../Task5/prompt_v1.txt`).

Because Iteration 1 was rejected, this iteration starts from the original prompt. Prompt tested: `prompt_v3.txt`. Outputs for all 10 tickets: `outputs.json` and `outputs.csv`. Baseline for comparison: the original prompt's Task 6 outputs. Everything except the prompt is unchanged: model, `temperature` 0, `seed` 42, schema, request code, ticket bodies.

## Targeted failure pattern and why

**Pattern:** the model mishandles the anonymization placeholders in the tickets (`name`, `company_name`, `email`, `tel_num`, `acc_num`). It lists them as missing, or quotes them as if they were real values.

**Evidence in the Task 6 outputs (4 mistakes in 3 tickets):**
- Ticket 28736 lists "the customer's email address" and "the customer's phone number" as missing, but the ticket ends with `email` and `tel_num`.
- Ticket 28763 lists "the customer's account or order number" as missing, but the ticket ends with `acc_num`.
- Ticket 29206's summary says "The customer team at company_name", quoting the placeholder as a name.

I chose this pattern because it is clear and checkable ticket by ticket, and because the model cannot know these tokens are placeholders unless the prompt says so.

## Prompt change

Only the prompt changed (the lines starting with `-` are the original, `+` the new text):

```diff
--- prompt_v1.txt
+++ prompt_v3.txt
@@ -2,7 +2,7 @@
 
 TASK: Read one customer support ticket and summarize the reported issue, what the customer wants, and what details are missing.
 
-CONTEXT: Tickets are written by customers and may be long, informal, or contain several issues. Agents read your summary before opening the full ticket.
+CONTEXT: Tickets are written by customers and may be long, informal, or contain several issues. Agents read your summary before opening the full ticket. Tickets are anonymized: tokens such as name, company_name, email, email_address, tel_num and acc_num stand for real values that were removed. Treat these tokens as details that are present: do not list them as missing and do not quote them.
 
 CONSTRAINTS:
 - Use only information stated in the ticket. Do not invent names, products, dates, numbers, causes, or policies.
```

## Observed impact

All 10 outputs follow the JSON schema. The `missing_information` lists that changed:

| Ticket | Before | After |
|---|---|---|
| 28907 | ["discrepancies in the projections versus the billed amounts in the billing documentation provided by the customer"] | ["account number", "billing statement", "discrepancies details"] |
| 28399 | ["The specific details of the organization's current server management protocols and ticketing system configuration."] | [] |
| 28736 | ["The customer's email address", "The customer's phone number"] | ["The customer's email address", "The customer's phone number", "The customer's company name"] |
| 28763 | ["Details about the specific components causing the flickering issue", "Information about the customer's account or order number"] | ["details about the specific hardware components causing the flickering issue"] |
| 28571 | ["expected delivery time from the order date", "choice of shipping methods", "expedited service options available", "details on tracking the package once dispatched", "return policy"] | ["technical specifications", "delivery timeline", "return policy"] |
| 28642 | ["The scope of the maintenance", "The exact start times and duration of the maintenance activities", "Any critical actions to be taken prior to the maintenance"] | ["specific scope of the maintenance", "exact start times and duration of the maintenance activities", "critical actions to be taken prior to the maintenance"] |
| 29206 | ["The specific details of the new company policies regarding ticket prioritization and project management."] | [] |

**Improvements**
- Ticket 28763: the account or order number item is gone.
- Ticket 29206: the summary no longer quotes `company_name`.

**Not fixed**
- Ticket 28736 still lists the email and the phone number as missing, and now also lists "the customer's company name" (3 mistakes instead of 2).

**Regressions**
- Ticket 28907 now lists "account number" as missing (`acc_num` is in the ticket), plus "billing statement" and "discrepancies details". Before, the list had one confused item.
- Ticket 29206's `customer_request` changed from asking for guidance to "Implement a customized priority field and dynamic adjustment feature...", which misstates the request.

**Other changes not caused by the instruction:**
- Ticket 28571's list shrank from five items to three (technical specifications, delivery timeline, return policy), but these are still the customer's own questions.
- Tickets 28399 and 28563 changed slightly, with no clear gain or loss.

**Count of the targeted problem:** placeholder mistakes went from 4 (28736: 2, 28763: 1, 29206: 1) to 4 (28736: 3, 28907: 1). No net reduction.

## Keep-or-revert decision

**Revert.** Two mistakes were fixed (28763 and 29206), but two new ones appeared (28907 and an extra one in 28736), so the total stayed at 4. The change also coincided with a worse `customer_request` for ticket 29206. The original prompt remains the best of the three.

## What the two iterations show

Both revisions were rejected. The 1.5B model is sensitive to prompt wording: small additions moved outputs in tickets that the instruction did not concern (for example 28571 and 29206's request). Adding instructions did not reliably fix the targeted pattern, and examples inside a prompt can leak into the output.
