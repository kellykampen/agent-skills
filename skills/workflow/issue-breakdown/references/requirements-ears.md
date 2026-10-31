# Requirements: EARS form + ISO/IEC/IEEE 29148 quality rules

Read this when you write the **Requirements** section of an issue. Write each requirement in EARS form, number it, and check it against the 29148 rules below. Use STE wording ([ste-writing.md](ste-writing.md)) for all words outside the EARS keywords.

## Numbering

- Number requirements `REQ-001`, `REQ-002`, … in each issue. Never reuse a number.
- One requirement per ID. If a sentence has "and" between two behaviors, make two REQs.
- Use "shall" for a requirement. Do not use "must", "should", or "may" in a REQ (29148: "should" is a goal, "may" is an allowance).

## EARS patterns

EARS (Easy Approach to Requirements Syntax, Mavin et al., Rolls-Royce, 2009). Keywords: **While**, **When**, **If … then**, **Where**.

| Pattern | Template | Example |
| --- | --- | --- |
| Ubiquitous (always true) | The `<system>` shall `<response>`. | REQ-001: The export service shall write files in UTF-8. |
| Event-driven | **When** `<trigger>`, the `<system>` shall `<response>`. | REQ-002: When an admin selects "Archive", the system shall move the selected members to Archived. |
| State-driven | **While** `<state>`, the `<system>` shall `<response>`. | REQ-003: While the import runs, the system shall disable the "Import" button. |
| Unwanted behavior | **If** `<unwanted condition>`, **then** the `<system>` shall `<response>`. | REQ-004: If a non-admin calls the archive endpoint, then the API shall return 403. |
| Optional feature | **Where** `<feature is included>`, the `<system>` shall `<response>`. | REQ-005: Where SSO is enabled, the system shall hide the password field. |

Complex requirements can combine keywords, in this order: Where → While → When/If. Keep it to one response.

## ISO/IEC/IEEE 29148:2018 checks

Each requirement (clause 5.2.5) shall be:

| Characteristic | Check |
| --- | --- |
| Necessary | Remove it. Does something important break? If no, delete it. |
| Appropriate | The detail fits the level (issue, not code). It does not dictate the design. |
| Unambiguous | Only one interpretation. No "fast", "easy", "user-friendly", "etc.", "and/or". |
| Complete | It needs no other text to understand it. Give units and limits. |
| Singular | One capability, constraint, or quality. |
| Feasible | The team can build it in the estimate (≤3 points). |
| Verifiable | A test or check can prove it. Give a measurable value. |
| Correct | It states the real need of the user story. |
| Conforming | It uses the EARS template and the REQ numbering above. |

The set of REQs in an issue (clause 5.2.6) shall be complete, consistent (no conflicts, same terms), feasible, comprehensible, and able to be validated.

29148 also says: use active voice, and prefer positive statements to "shall not". The EARS unwanted-behavior pattern gives a positive response to a bad condition.
