# Homework 1 - Acquire, Inspect, and Augment

## Goal

Find and assess a public support-ticket dataset for this intended use:

> Given the text of a newly arrived support ticket, route it to the appropriate
> support team.

You will identify the closest eligible dataset, assess its limitations, and
build a small deterministic synthetic-data generator targeting one important
gap. An exact dataset match is not expected.

## Target Dataset Specification

### Dataset content

| Area | Desired content |
| --- | --- |
| Record | One support request or ticket |
| Required input | Natural-language ticket text available at arrival |
| Required target | Department, queue, team, or another categorical routing label |
| Useful context | Priority, tags, timestamp, channel, customer/product context, and resolution information |
| Coverage | Multiple examples across several routing classes; no fixed minimum size |

Only ticket text and a routing label are required. Additional context fields are
optional but desirable.

### Dataset metadata and source

| Area | Requirement |
| --- | --- |
| Language | Primarily English |
| Usage terms | Publicly downloadable without approval; no stated terms prohibit educational analysis |
| Provenance | Identifiable source page or dataset card |
| Version | A published version or recorded retrieval date |

No starter dataset or code is provided.
A pinned dependency list for Python 3.14.7 is provided in `requirements.txt`.

## Task 1 - Find and Select a Dataset

### 1.1 Find three candidates

Find three public datasets relevant to the target dataset specification.

For each candidate, record:

- Name and source URL.
- Version or retrieval date.
- Stated usage terms and relevant restrictions, or **not found**.
- Available required fields: ticket text and routing label.
- Available optional context fields that could help with classification, such as
  priority, tags, timestamp, channel, or customer/product context.
- Number of usable records (e.g. English records in a multi-lingual dataset).

### 1.2 Select one dataset

Choose one dataset for the remaining tasks. It must contain ticket text and a
categorical routing label. Briefly justify your selection.

### Notes

Commercial and redistribution rights are not required. Record missing usage
terms as **not found**, and do not select a dataset whose terms prohibit
educational analysis.

### Deliverables

- A three-row table comparing the candidates.
- A couple sentences justifying your selection.

## Task 2 - Inspect and Profile the Dataset

### 2.1 Inspect source record sample

Select 20 source records using a method you state. Record each `record_id` and
your observations.

### 2.2 Profile the dataset

Write reproducible code that writes a report to a file containing:

- Total number of records and columns.
- Number of records after basic filtering (e.g. language).
- Record grain (what one row represents).
- Ticket-text and routing-label fields.
- Missing-value counts and proportions for relevant fields.
- Routing-label counts and proportions.
- Ticket-text-length summary and suspiciously short examples.
- Number of exact duplicate ticket texts.

Some fields are duplicated from 1.1; this is intentional.
The first is a quick check, while this is a profiling report.

### Notes

If the dataset lacks a stable identifier, derive one deterministically. Use
stable record IDs for all record-level observations.

### Deliverables

- Notes from the 20-record inspection.
- Re-runnable profiling code.
- Saved profile results.

## Task 3 - Create and Inspect Synthetic Data

### 3.1 Plan the augmentation

Write a short augmentation plan. Choose one gap observed in Task 2 that
synthetic data can reasonably address, then record:

- The gap.
- The population or slice to add.
- The generation approach and why it fits the gap.

### 3.2 Generate 50 synthetic records

Write local code that:

- Generates exactly 50 records using the source dataset as seed material.
- Runs locally without an LLM and produces the same output each time.
- Gives every record a stable, unique `record_id` and marks its `provenance` as
  synthetic.
- Does not copy complete source ticket text into a generated record.

### 3.3 Inspect generated records

Inspect 10 generated records:

- Select five randomly.
- Select five because they look suspicious, repetitive, or extreme.

For each record, report its `record_id`, whether it is acceptable, and any
concrete issue you observe.

Based on the inspection, list the changes you would make to improve the
generator.

### Notes

If seed records have mistakes, synthetic records will reproduce those mistakes.
Choose seed records carefully, and avoid records with unclear text or
questionable routing labels.

### Deliverables

- An augmentation plan describing the gap, population or slice to add, and
  generation approach.
- Generator code.
- Generated file containing exactly 50 records.
- Notes from the 10-record inspection and proposed generator changes.
