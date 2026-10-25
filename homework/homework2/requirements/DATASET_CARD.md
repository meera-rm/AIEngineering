
# IT Support Ticket Data

## Overview

This dataset contains support-ticket text, assigned departments, priorities,
and tags.

| Item | Value |
| --- | --- |
| Source | [IT Support Ticket Data on Kaggle](https://www.kaggle.com/datasets/parthpatil256/it-support-ticket-data) |
| Publisher | Parth Patil |
| Source version | Version 1, published June 14, 2025 |
| License | MIT |
| Retrieved | September 11, 2026 |
| Records | 29,651 |
| Columns | 5 |
| Routing classes | 10 |

## Record Grain

One row represents one historical support ticket and its assigned department.
The dataset does not document when or how `Priority` and `Tags` were created.

## Schema

All fields are read from the CSV as strings.

| Field | Role | Missing | Distinct values | Description |
| --- | --- | ---: | ---: | --- |
| `ticket_id` | Identifier | 0 | 29,651 | Stable one-based row number added for this course |
| `Body` | Ticket text | 1 | 25,055 | Natural-language support request |
| `Department` | Assignment | 0 | 10 | Assigned department |
| `Priority` | Source metadata | 0 | 3 | Source-provided ticket priority |
| `Tags` | Source metadata | 0 | 12,946 | Source-provided serialized ticket tags |

Distinct-value counts include the missing `Body` value.

## Routing Labels

| `Department` | Records |
| --- | ---: |
| Technical Support | 8,617 |
| Product Support | 5,539 |
| Customer Service | 4,482 |
| IT Support | 3,500 |
| Billing and Payments | 3,017 |
| Returns and Exchanges | 1,467 |
| Service Outages and Maintenance | 1,157 |
| Sales and Pre-Sales | 885 |
| Human Resources | 568 |
| General Inquiry | 419 |

The distribution is imbalanced; `Technical Support` is the largest class and
`General Inquiry` is the smallest.

## Known Data Facts

- Exactly one record has a missing `Body`.
- No record has a missing `ticket_id`, `Department`, `Priority`, or `Tags`.
- `ticket_id` is unique for every record.
- Repeated `Body` values exist.
- The counts above describe the supplied CSV.

## Preparation

The Kaggle CSV contained an unnamed exported row-index column. It was replaced
with `ticket_id` values from 1 through 29,651. The other four fields and all
source rows were preserved without cleaning or correction.