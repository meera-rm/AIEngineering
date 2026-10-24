# Profile: Tobi-Bueck customer support tickets
Source: `Tobi-Bueck/customer-support-tickets` @ `ddf1c81a5475992c4fa6752bf1e8b4e31f07bbeb` (file `tobi_bueck_ddf1c81a.parquet`)

**Grain:** One row = one customer support ticket: the customer's subject and body, the agent's answer, and ticket metadata (queue, priority, type, tags, language).

**Ticket text:** `subject + body` (answer excluded)  |  **Routing label:** `queue`

**Raw:** 61,765 records x 16 columns

**Record ID:** 'tb_' + first 12 hex chars of SHA-256 over 'column=value' lines for all raw columns (sorted by name, missing = <NULL>); identical rows get _1, _2, ...

## Filter funnel
- raw: 61,765
- language == 'en': 28,261
- non-empty ticket_text: 28,261
- non-empty queue: 28,261

## Language values (raw)
- de: 33,504
- en: 28,261

## Missing values (raw)
| field | count | proportion |
|---|---|---|
| subject | 5299 | 0.0858 |
| body | 2 | 0.0 |
| queue | 0 | 0.0 |
| answer | 13189 | 0.2135 |
| type | 13178 | 0.2134 |
| priority | 0 | 0.0 |
| version | 33178 | 0.5372 |
| language | 0 | 0.0 |
| tag_1 | 13178 | 0.2134 |
| tag_2 | 13237 | 0.2143 |
| tag_3 | 13409 | 0.2171 |
| tag_4 | 17775 | 0.2878 |
| tag_5 | 34129 | 0.5526 |
| tag_6 | 48540 | 0.7859 |
| tag_7 | 55797 | 0.9034 |
| tag_8 | 59293 | 0.96 |
| ticket_text | 0 | 0.0 |

## Missing values (after filtering)
| field | count | proportion |
|---|---|---|
| subject | 3639 | 0.1288 |
| body | 1 | 0.0 |
| queue | 0 | 0.0 |
| answer | 6 | 0.0002 |
| type | 0 | 0.0 |
| priority | 0 | 0.0 |
| version | 11923 | 0.4219 |
| language | 0 | 0.0 |
| tag_1 | 0 | 0.0 |
| tag_2 | 16 | 0.0006 |
| tag_3 | 113 | 0.004 |
| tag_4 | 2584 | 0.0914 |
| tag_5 | 11960 | 0.4232 |
| tag_6 | 20353 | 0.7202 |
| tag_7 | 24562 | 0.8691 |
| tag_8 | 26653 | 0.9431 |
| ticket_text | 0 | 0.0 |

## Routing-label distribution (10 labels, filtered)
| queue | count | proportion |
|---|---|---|
| Technical Support | 8149 | 0.2883 |
| Product Support | 5305 | 0.1877 |
| Customer Service | 4269 | 0.1511 |
| IT Support | 3333 | 0.1179 |
| Billing and Payments | 2897 | 0.1025 |
| Returns and Exchanges | 1402 | 0.0496 |
| Service Outages and Maintenance | 1106 | 0.0391 |
| Sales and Pre-Sales | 843 | 0.0298 |
| Human Resources | 553 | 0.0196 |
| General Inquiry | 404 | 0.0143 |

## Ticket-text length (filtered)
| stat | chars | words |
|---|---|---|
| count | 28261.0 | 28261.0 |
| mean | 410.2 | 60.4 |
| std | 203.5 | 31.3 |
| min | 4.0 | 1.0 |
| 1% | 70.0 | 9.0 |
| 5% | 106.0 | 14.0 |
| 25% | 244.0 | 35.0 |
| 50% | 404.0 | 59.0 |
| 75% | 568.0 | 83.0 |
| 95% | 697.0 | 107.0 |
| 99% | 972.0 | 149.0 |
| max | 1825.0 | 276.0 |

## Suspiciously short texts (<= 5 words): 32
- `tb_a77e5adba818` [Billing and Payments]: 'Help'
- `tb_53da7f0876bd` [Billing and Payments]: 'Support needed'
- `tb_67d47e89ce69` [Technical Support]: 'ConcernregardingSystemInvestmentAnalytics Thecompanyisincapableofaccessinginvestmentanalyticsduetosy'
- `tb_d34b503b8291` [Technical Support]: 'ConcernregardingSystemInvestmentAnalytics Thecompanyisincapableofaccessinginvestmentanalyticsduetosy'
- `tb_68d82e700a74` [Customer Service]: 'Hello support team'
- `tb_9ba3caca0605` [Customer Service]: 'Hello support team'
- `tb_1f2498603c00` [Billing and Payments]: 'Seeking assistance with billing'
- `tb_27152180519d` [Billing and Payments]: 'Seek assistance with billing'
- `tb_4f442ef23d69` [Billing and Payments]: 'Can you assist me?'
- `tb_542f663ac3cc` [Billing and Payments]: 'Seek assistance with billing'
- `tb_5d2594cbbb29` [Technical Support]: 'Issue Encountered Assistance Needed'
- `tb_7bed31fa5910` [Technical Support]: 'Issues with software integration'
- `tb_d09f37cf74e3` [Technical Support]: 'Several products are impacted'
- `tb_d8118414349d` [Billing and Payments]: 'Seeking assistance with billing'
- `tb_e7baa45bbdb8` [Technical Support]: 'Several products are impacted.'

## Exact duplicate ticket texts (filtered)
- rows_in_duplicate_groups: 9026
- redundant_rows (total - unique): 4513
- duplicate_groups: 4513
- groups_with_conflicting_labels: 0
- redundant_rows_after_case_whitespace_normalisation: 4514
- example_record_ids: ['tb_1cf596f7b345', 'tb_3be77f1776c2', 'tb_912088c7c220', 'tb_97b49eaa5b07', 'tb_0dd367fed317', 'tb_6847cf1764e1', 'tb_93a57f043a92', 'tb_bce75266b935', 'tb_1075ac3a0394', 'tb_c2a7f97ac819']

## 20-record inspection sample
Filtered English records shuffled with random_state=42; records then taken round-robin across 'queue' values (1st of each queue, then 2nd of each queue, ...) in shuffled order until n=20.
Record IDs: `tb_9f7be6738bab`, `tb_84b7d3d09f08`, `tb_b53536bbb13a`, `tb_8036c45b7fa8`, `tb_c2a1c0ab7224`, `tb_76e20cb17e4f`, `tb_8b3e787035fe`, `tb_0c13eadd7198`, `tb_8f26980acef2`, `tb_57dbdac5ce03`, `tb_f27f1d924928`, `tb_efdfac0dc865`, `tb_a9eae478e2fd`, `tb_6a8950b24ad7`, `tb_07cceb5cc5bc`, `tb_7fc4dae109d3`, `tb_2a0b2b37e0c6`, `tb_8e966b2c47de`, `tb_2f5e89e8c7a8`, `tb_3b1b360a8838`
