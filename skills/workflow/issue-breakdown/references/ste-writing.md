# Writing style for Linear: Simplified Technical English (ASD-STE100)

Read this before you write any text into Linear. ASD-STE100 is a controlled language specification. It was first made for aircraft maintenance documents. Its rules make text short, clear, and with one meaning. Source: [asd-ste100.org](https://www.asd-ste100.org/) (Issue 9, Part 1 writing rules, Part 2 dictionary).

## When to apply

- Apply to **all text you write into Linear**: issue titles, descriptions, user stories, acceptance criteria, comments, project descriptions, and project updates.
- Do **not** rewrite text that you quote verbatim (user text, error messages, logs, code, UI copy). Put it in quotes or a code block.
- Code, identifiers, numbers with units, and quoted strings count as one word each.
- The user-story form ("As a role, I want to action, so result.") stays. Write the role, action, and result in STE words.

## Checklist

- [ ] Instructions (steps, AC, requests in comments): max **20 words** per sentence.
- [ ] Descriptive text: max **25 words** per sentence; max **6 sentences** per paragraph; **one topic** per paragraph.
- [ ] One instruction per sentence (more only if the actions occur at the same time).
- [ ] Use the imperative (command) form for instructions: "Add the filter.", not "The filter should be added."
- [ ] Use active voice. Allowed verb forms: infinitive, imperative, simple present, simple past, simple future, past participle as an adjective.
- [ ] Do not use the progressive (-ing) as a verb, the perfect tenses, or the passive in instructions.
- [ ] Noun clusters: max **3 words**. Break longer clusters with "of", "for", "on", "in".
- [ ] Keep "the", "a", "an". Do not write in telegraph style.
- [ ] Use the same word for the same thing every time (one name per screen, field, or service).
- [ ] Put a condition before the instruction: "If the import fails, show the error banner."
- [ ] Use a vertical list for complex text, for example 3 or more items or steps.
- [ ] No semicolons. Use two sentences.

## Approved words vs words to avoid

| Avoid | Use |
| --- | --- |
| commence, initiate | start |
| utilize, leverage | use |
| ensure | make sure |
| prior to | before |
| approximately, ~ | about |
| in order to | to |
| replenish | fill |
| terminate | stop |
| facilitate | help, make … possible |
| additional | more |
| sufficient | enough |
| subsequently | then, after |

If you are not sure that a word is approved, use the most common simple word with one clear meaning.

## Before and after

**Issue title**

- Before: `Implementation of user notification preference persistence logic`
- After: `Save the notification settings of the user`

**Description (descriptive text)**

- Before: "We've been seeing that the export is failing intermittently, which is presumably being caused by the timeout that was configured prior to the migration."
- After: "The CSV export fails at random times. The cause is possibly the timeout value. The team set this value before the migration."

**Acceptance criteria**

- Before: `- [ ] Ensure that admins are able to utilize the bulk archive functionality`
- After: `- [ ] **AC-001 (REQ-001)** Given 3 members are selected, When the admin selects "Archive", Then the 3 members show under Archived.`

**Comment / project update**

- Before: "Have been working on the fix, should be wrapped up approximately EOD, in order to unblock QA."
- After: "I work on the fix now. The fix will be ready at about 18:00 today. Then QA can start the test."

## Warnings and cautions for risky changes

For a change that can cause data loss, downtime, a security risk, or a cost, put a warning at the **top** of the description. Write a clear, simple command first. Then give the risk.

```markdown
> **WARNING:** Do not run the migration on production before you make a backup. The migration deletes the old columns.

> **CAUTION:** Do not change the rate limit during peak hours. Users can get 429 errors.
```

- WARNING: a risk of injury, data loss, or a security problem.
- CAUTION: a risk of damage to systems, money, or the schedule.
- Keep each warning to the 20-word limit for each sentence.
