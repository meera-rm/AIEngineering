# Homework 5, Task 2: Manually Applying the Rubric

Outputs scored: `homework4/Task6/task6_results.csv` (accepted prompt `homework4/Task5/prompt_v1.txt`, qwen2.5:1.5b-instruct-q4_K_M, temperature: 0, seed: 42, stream: false).
Rubric applied: `rubric.md` in this folder (starts as a copy of `../Task1/rubric.md`; frozen after this task).
Inputs scored: `hw4_outputs_for_scoring.csv` in this folder is the HW4 saved output for the five tickets, brought forward as the assignment asks, next to each ticket's unaltered `Body` from the canonical dataset.

## Rubric changes and justifications

| # | Change | Dimension | Why | Re-scored tickets |
|---|---|---|---|---|
| 1 | Added a rule for a wrong *type* of ask: right subject but wrong type (e.g. "send a plan and timeline" became "implement it") = 1; subject also wrong = 0. | 4. Request accuracy and completeness | 28921 turned “send a plan and timeline” into “implement it”, and the rubric didn’t say how to score that | 28907, 28763, 28571, 29206 re-checked: none had a type change, so no scores changed. |

## Scores at a glance

| Ticket | Dept | D1 | D2 | D3 | D4 | D5 | D6 | D7 |
|---|---|---|---|---|---|---|---|---|
| 28907 | Billing and Payments | Pass | 1 | 1 | 1 | 1 | 1 | 2 |
| 28921 | Human Resources | Pass | 2 | 1 | 1 | 0 | 2 | 1 |
| 28763 | Product Support | Pass | 2 | 2 | 1 | 1 | 0 | 1 |
| 28571 | Sales and Pre-Sales | Pass | 2 | 1 | 1 | 0 | 0 | 1 |
| 29206 | Technical Support | Pass | 1 | 1 | 1 | 1 | 2 | 2 |

## Per-ticket scoring

### Ticket 28907 — Billing and Payments

**Ticket body**

> Dear Customer Support Team,I hope this message finds you well. I am reaching out to request assistance with a billing adjustment related to our recent usage of the AWS Management Service, provided through your esteemed IT Services company. I represent Company and we have an account under the number acc_num that is associated with our ongoing AWS infrastructure operations.Upon reviewing our usage and subsequent billing statement for the last quarter, we noticed certain discrepancies which we would like to clarify. For the duration of the last quarter, our AWS Management Service was utilized to enhance various aspects of our operational infrastructure, yet the billing seems higher than initially anticipated.What I'd appreciate is a comprehensive review of the charges linked to our account. Specifically, the billing reflects charges that were not discussed or predicted in our previous correspondence regarding expected usage rates and associated expenses. My team conducted an internal audit and found differences in the projections versus the billed amounts in the billing documentation provided by you on date.It would be extremely beneficial if we could arrange a detailed breakdown of the billed items, accompanied by detailed usage metrics, and a written explanation for each charge where discrepancies have been noted. Additionally, I would like to inquire if there are any ongoing discounts or billing mechanisms that would better suit our usage patterns but were not applied to our account. Your guidance on any available options for invoicing adjustments under the current service agreement would be much appreciated.For quick resolution of this matter, I am available for further discussions at your earliest convenience. Please feel free to reach out to me directly via email or at my phone number, tel_num, anytime during business hours. Alternatively, my colleague name can be contacted in my absence for any clarifications needed.Thank you in advance for your attention to this matter. I anticipate your insights and hope to resolve this discrepancy in a timely fashion. Looking forward to your prompt response.Kind regards,namePositionCompanyAddressContact Information

**HW4 output**

- **summary:** Customer requests a detailed review of billing discrepancies related to AWS Management Service usage and an explanation of any discrepancies.
- **customer_request:** A comprehensive review of the charges linked to the account, including a detailed breakdown of billed items, usage metrics, and a written explanation for each charge where discrepancies have been noted.
- **missing_information:**
  - discrepancies in the projections versus the billed amounts in the billing documentation provided by the customer

| Dimension | Score | Rationale |
|---|---|---|
| 1. Format and constraint compliance (Pass/Fail) | Pass |Valid JSON with exactly the 3 fields (schema_valid = True in Task 6). Summary is 1 sentence, the item is a noun phrase rather than a full sentence, and no fix is proposed. |
| 2. Factual grounding (0-2) | 1 | Says the billing documentation was “provided by the customer”; the ticket says it was provided by support (“provided by you”). Everything else traces to the ticket. |
| 3. Summary describes the issue, not the ask (0-2) | 1 | The summary restates the request (“Customer requests a detailed review… and an explanation”) instead of the problem: last quarter’s bill was higher than projected. Both describe what the customer wants: a review plus an explanation.|
| 4. Request accuracy and completeness (0-2) | 1 | Main ask is captured: a review with an itemized breakdown, usage metrics and an explanation for each discrepancy. Two secondary asks are dropped: discounts that weren’t applied, and invoicing-adjustment options under the service agreement.|
| 5. Key context retained (0-2) | 1 | Keeps “billing discrepancies” and “AWS Management Service”, but drops “last quarter”, “higher than anticipated”, the internal audit, and that the charges weren’t in earlier correspondence. The core problem is still usable, just vague. |
| 6. Missing-information precision (0-2) | 1 | The projection-vs-billed differences are already stated in the body and the item says the documentation came from the customer when support provided it.|
| 7. Missing-information recall (0-2) | 2 | Which charges differ and how much is something the support can see in their records.The account number and date are reaplced with placeholders for privacy, not missing info|

### Ticket 28921 — Human Resources

**Ticket body**

> Dear IT Services Customer Support,I am writing to request a significant enhancement to our internal human resources management system, specifically targeting the user interface design and data analysis capabilities. Despite the comprehensive functions that your system currently offers, we believe improvements can be made to enhance user experience and provide more intuitive data handling processes for our team.Our personnel have reported some challenges when navigating through various modules and accessing crucial information, which often results in bottlenecks and decreased efficiency. A redesigned interface that is more user-friendly and visually intuitive could significantly aid in quicker data entry and easier retrieval of information. Furthermore, implementing advanced data analysis tools would allow our HR team to perform more detailed assessments and generate reports with greater ease.While the IT Consulting Service has offered us fantastic support so far, these enhancements could drive even greater value, facilitating smoother organizational workflows and fostering data-driven decision-making across different teams.Please treat this request with urgency, as optimizing these elements is essential to meet our evolving business needs. If possible, we would appreciate receiving information on your plan for tackling this request, including a timeline for implementation. Thank you for your prompt attention to this matter. Should you need any additional information, please do not hesitate to contact me directly at tel_num. I look forward to your response and the ongoing improvement of our HR management system. Sincerely,namename CorpAccount Number: acc_num

**HW4 output**

- **summary:** The customer requests enhancements to the internal human resources management system, focusing on improved user interface design and data analysis capabilities.
- **customer_request:** Implement a redesigned user interface and advanced data analysis tools to improve user experience and efficiency.
- **missing_information:**
  - (empty)

| Dimension | Score | Rationale |
|---|---|---|
| 1. Format and constraint compliance (Pass/Fail) | Pass | Valid JSON with the 3 fields |
| 2. Factual grounding (0-2) | 2 | Every claim (HR system, UI design, data-analysis tools, user experience, efficiency) appears in the ticket. Nothing is invented or misattributed. |
| 3. Summary describes the issue, not the ask (0-2) | 1 | The customer requests enhancements…” restates the ask. It leaves out the actual problem (navigation trouble, bottlenecks, slower work) and overlaps with customer_request |
| 4. Request accuracy and completeness (0-2) | 1 | Gets the subject right (a UI redesign and data-analysis tools), but changes the ask from “send your plan and implementation timeline” into “implement it”, so the plan/timeline request is lost. Scored 1 under the new wrong-type rule: right subject, wrong type |
| 5. Key context retained (0-2) | 0 | The stated urgency is gone entirely, and so is the navigation/bottleneck detail|
| 6. Missing-information precision (0-2) | 2 | The list is empty, so there are no bad items.|
| 7. Missing-information recall (0-2) | 1 | To give a plan and timeline, support needs to know which modules are hard to use and which reports or analyses are wanted. The ticket doesn’t say, and the model flagged nothing |

### Ticket 28763 — Product Support

**Ticket body**

> Dear Customer Support Team,I hope this message finds you well. I am writing to report a concerning issue I am experiencing with my recently purchased Samsung QLED QN90A TV, which I bought from your 'Tech Online Store'. Having been a loyal customer, I expected nothing short of superior performance and reliability that Samsung products are renowned for. However, this particular unit seems to be presenting a rather persistent and distracting problem.The television has developed a flickering issue while in use, which occurs intermittently but frequently enough to hinder the viewing experience significantly. It started subtly but has become more pronounced over time, leading me to believe that it might be a hardware-related issue rather than something that could be adjusted with simple settings modifications. I understand these models are generally known for their impressive picture quality and advanced technology, so this flickering is both unexpected and disappointing.Given the nature of the problem, I suspect it might involve components relating to the display hardware, as no changes in external settings such as cables or power sources appear to affect or resolve the issue. Unfortunately, adjusting brightness levels or refreshing the support software has shown no improvement. Considering these attempts to troubleshoot the problem have been unsuccessful, I am compelled to seek your professional assistance to resolve this matter promptly.I would appreciate it if you could provide guidance on the next steps to take, possibly including instructions for an at-home diagnosis or arranging a qualified technician's assessment. Additionally, information about your repair policies and warranty coverage for such issues would be greatly appreciated. My hope is to have this resolved quickly to return to enjoying the high-quality viewing experience I anticipated upon purchase.Thank you for your attention to this matter. I look forward to your prompt response with advice on how we can proceed to rectify this issue with my Samsung QLED QN90A.Best regards,nameacc_num

**HW4 output**

- **summary:** Customer reports a persistent flickering issue with their Samsung QLED QN90A TV, which has become more pronounced over time and is causing significant hindrance to the viewing experience.
- **customer_request:** Resolve the flickering issue with their Samsung QLED QN90A TV promptly.
- **missing_information:**
  - Details about the specific components causing the flickering issue
  - Information about the customer's account or order number

| Dimension | Score | Rationale |
|---|---|---|
| 1. Format and constraint compliance (Pass/Fail) | Pass | Valid JSON with the 3 fields, a 1-sentence summary |
| 2. Factual grounding (0-2) | 2 | Every claim (persistent flickering that’s getting worse and hurts viewing, the QN90A model, wanting it resolved promptly) appears in the ticket. Nothing is invented or misattributed. |
| 3. Summary describes the issue, not the ask (0-2) | 2 | Describes the problem (flickering that’s getting worse and spoiling viewing) and adds detail customer_request doesn’t have. |
| 4. Request accuracy and completeness (0-2) | 1 | "Resolve the flickering” roughly captures the main ask (help with next steps: diagnosis or a technician), but the request for repair-policy and warranty information is dropped.|
| 5. Key context retained (0-2) | 1 | The core problem is concrete, but everything the customer already tried (cables, power, brightness, software refresh) is gone, and so is the suspicion of hardware failure. Without it, an agent might repeat those same steps.|
| 6. Missing-information precision (0-2) | 0 | Two bad items.“Which components are causing the flickering” asks the customer to diagnose the fault, which is support’s job.|
| 7. Missing-information recall (0-2) | 1 | Misses the purchase date, which is needed to answer the warranty question. “Recently purchased” isn’t specific enough |

### Ticket 28571 — Sales and Pre-Sales

**Ticket body**

> Dear Customer Support,I hope this message finds you well. I am reaching out to obtain some clarifications regarding specific information and shipping options for the Cisco Router ISR4331, as I am considering it for a possible acquisition. It is important for me to verify that this model suits my requirements, so I would be thankful for expanded details about its technical specifications, particularly in terms of its effectiveness, compatibility, and any unique features it possesses.In addition, a key aspect of my inquiry pertains to the delivery timeline. As you may recognize, receiving the product promptly is essential for the current schedule of our project. Could you please furnish detailed information covering the following aspects: expected delivery time from the order date, choice of shipping methods, and whether there are any expedited service options available? Furthermore, will it be possible to track the package once it has been dispatched? Your information regarding expected durations for both regular and faster service would be highly beneficial.Lastly, I would appreciate details on the return policy in case the product does not meet our expectations. Understanding your support protocols for these situations is vital for fostering trust as we consider moving forward with this purchase.A prompt response would be invaluable, greatly aiding me in my decision-making. You can reach me at this email or by phone at tel_num during regular working hours.Thank you for your assistance.Kind regards,name

**HW4 output**

- **summary:** The customer is seeking clarification on technical specifications, delivery timeline, and return policy for the Cisco Router ISR4331.
- **customer_request:** Clarify technical specifications, delivery timeline, and return policy for the Cisco Router ISR4331.
- **missing_information:**
  - expected delivery time from the order date
  - choice of shipping methods
  - expedited service options available
  - details on tracking the package once dispatched
  - return policy

| Dimension | Score | Rationale |
|---|---|---|
| 1. Format and constraint compliance (Pass/Fail) | Pass | Valid JSON with the 3 fields; 1-sentence summary; all items are short phrases; no fix proposed. |
| 2. Factual grounding (0-2) | 2 | Router model, specs, delivery timeline and return policy all appear in the ticket. Nothing invented or misattributed. |
| 3. Summary describes the issue, not the ask (0-2) | 1 | Summary and customer_request are nearly word-for-word identical; does not say this is a pre-purchase decision tied to a project deadline. |
| 4. Request accuracy and completeness (0-2) | 1 | Covers the three main topics, but "delivery timeline" omits the specific asks about shipping methods, expedited options and tracking (which appear only, wrongly, in missing_information). |
| 5. Key context retained (0-2) | 0 | Stated urgency is dropped entirely (prompt delivery is essential to the project schedule), as is the fact that this is a buying decision. |
| 6. Missing-information precision (0-2) | 0 | All 5 items are the customer's own questions, not missing information: five bad items. |
| 7. Missing-information recall (0-2) | 1 | Misses the shipping destination (needed for a delivery estimate) and what the router must be compatible with ("my requirements" is never specified). |

### Ticket 29206 — Technical Support

**Ticket body**

> Dear Customer Support Team,I hope this message finds you well. I am reaching out on behalf of our team at company_name. We have been utilizing Jira Software 8.20 as an essential tool for managing our project workflows, and it has significantly enhanced our productivity and project management capabilities. However, due to recent changes in our internal company policies, we require modifications to our existing workflows to better accommodate the new guidelines regarding ticket prioritization.In line with our new company policies, we need the ability to adjust the prioritization settings within Jira to reflect the changes in how issues should be processed and managed. Specifically, we are looking to incorporate a customized priority field that aligns with our updated prioritization matrix. Additionally, we would like to implement a feature that allows for dynamic adjustments based on the real-time status of issues and overarching project goals.Our objective is to ensure that our projects are managed more efficiently by allowing team members to categorize issues with the appropriate level of urgency as dictated by our new policy framework. Thus, we foresee the need for creating new custom workflows or modifying existing ones to include additional statuses and transition conditions which can accurately reflect these prioritization strategies.Could you please provide guidance on the best approach for implementing these workflow modifications? We are particularly interested in understanding the technical feasibility, potential timelines, and any assistance you can provide in terms of configuration or necessary plugins which might need to be applied to support these changes. It would be extremely helpful to have any documentation or best practices from prior similar implementations to help us navigate this adjustment seamlessly.We appreciate your attention to this matter and are hopeful for your expert advice on how to move forward. Please let us know a suitable time for us to discuss this in greater detail or if there are any initial resources you could provide to kickstart this process.Thank you very much for your support.Best regards,nameposition, company_nameemail_addresstel_num

**HW4 output**

- **summary:** The customer team at company_name is seeking guidance on implementing modifications to Jira Software 8.20 to better align with their new company policies regarding ticket prioritization and project management.
- **customer_request:** Provide guidance on the best approach for implementing workflow modifications to Jira Software 8.20, including technical feasibility, potential timelines, and any necessary plugins or documentation.
- **missing_information:**
  - The specific details of the new company policies regarding ticket prioritization and project management.

| Dimension | Score | Rationale |
|---|---|---|
| 1. Format and constraint compliance (Pass/Fail) | Pass | Valid JSON with the 3 fields; 1-sentence summary; the item is a noun phrase (despite ending with a period); no fix proposed. |
| 2. Factual grounding (0-2) | 1 | Treats the placeholder company_name as a real company name ("the customer team at company_name"). Also says the policies cover "project management" when the ticket only says ticket prioritization (small overstatement). |
| 3. Summary describes the issue, not the ask (0-2) | 1 | Mostly restates the ask ("seeking guidance on implementing modifications"), close to customer_request; the only addition is the reason (new prioritization policies). |
| 4. Request accuracy and completeness (0-2) | 1 | Captures guidance, feasibility, timelines, plugins and documentation, but drops the request to schedule a discussion and the request for configuration help. |
| 5. Key context retained (0-2) | 1 | Loses the specific requirements (custom priority field, dynamic priority adjustment, new statuses and transitions), but the core problem (Jira workflows must change for new prioritization rules) is still usable. |
| 6. Missing-information precision (0-2) | 2 | The one item is a real gap: support can't configure a priority field around a prioritization matrix they haven't seen. |
| 7. Missing-information recall (0-2) | 2 | Catches the main gap (details of the prioritization matrix/policy). No other blocking gap is missed. |

## Rubric frozen

Rubric frozen on: 10/26/2026. No further edits before the RAG vs. no-RAG comparison (Task 7).
