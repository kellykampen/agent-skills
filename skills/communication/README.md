# communication

Skills for managing email and messaging inboxes from the command line.

- [gmail-inbox-zero-triage](#gmail-inbox-zero-triage)
- [gmail-oib-zero](#gmail-oib-zero)
- [whatsapp-triage](#whatsapp-triage)

---

## gmail-inbox-zero-triage

Daily Gmail triage toward inbox zero, with a suggested action per email.

**Install:**

```bash
npx skills add kellykampen/agent-skills --skill gmail-inbox-zero-triage
```

Try without installing:

```bash
npx skills use kellykampen/agent-skills --skill gmail-inbox-zero-triage --agent claude-code
```

**What it does**

Triages unread mail across the primary inbox and a secondary filtered label into four buckets — Urgent, Reply Soon, Waiting, FYI — with sender, subject, received time, a one-line reason, and a specific suggested action (Reply / Defer / Archive / Label / Delete) per email.

**Why it exists**

A daily triage pass only works if it's low-friction enough to actually happen every day, and safe enough that you don't have to double-check what it touched. This produces the report in one command and never executes a single action until you say which ones.

**How it works**

Wraps the `gog` CLI's Gmail commands in read-only mode to search and inspect, buckets everything into the four-part report, then waits. Approved actions (by item, by bucket, or in bulk) get translated into the exact `gog` write command and run only against the thread/message IDs already surfaced in the report — never a broader sweep unless explicitly asked for.

**Requirements**

Requires `gog` on `PATH` with Gmail auth configured.

Source: [`gmail-inbox-zero-triage/SKILL.md`](./gmail-inbox-zero-triage/SKILL.md)

---

## gmail-oib-zero

Bulk-clear a secondary Gmail label to zero, grouped by sender.

**Install:**

```bash
npx skills add kellykampen/agent-skills --skill gmail-oib-zero
```

Try without installing:

```bash
npx skills use kellykampen/agent-skills --skill gmail-oib-zero --agent claude-code
```

**What it does**

Pulls every message under a secondary filtered label (e.g. an "other inbox" label a Gmail filter routes mail into), groups them by sender/domain, and proposes one action per group — remove the label, trash, or "needs judgment" — instead of itemizing every message.

**Why it exists**

A label that accumulates hundreds of filtered newsletters and notifications isn't practical to clear one email at a time. Grouping by sender turns a 200-message backlog into a dozen approve/skip decisions.

**How it works**

Reads the full label population (not just unread) via `gog`, groups by sender domain with representative subject lines, and presents a ranked report. On approval, executes per group — either gathering thread IDs for a label-removal batch, or using `gog`'s query-based bulk trash. Can optionally offer to turn a repeatedly-approved sender into a standing Gmail filter, but only if asked.

**Requirements**

Requires `gog` on `PATH` with Gmail auth configured.

Source: [`gmail-oib-zero/SKILL.md`](./gmail-oib-zero/SKILL.md)

---

## whatsapp-triage

Triage personal WhatsApp unread chats, with a suggested action per chat.

**Install:**

```bash
npx skills add kellykampen/agent-skills --skill whatsapp-triage
```

Try without installing:

```bash
npx skills use kellykampen/agent-skills --skill whatsapp-triage --agent claude-code
```

**What it does**

Lists unread WhatsApp chats, pulls enough recent messages to understand what each is actually about, and buckets them into Urgent / Reply Soon / Waiting / FYI with a specific suggested action per chat (Reply / Defer / Archive / Mute / Mark read).

**Why it exists**

The same "report first, act only on approval" pattern as the Gmail triage skills, applied to WhatsApp — a daily unread-chat backlog is only worth clearing if the tool never risks sending or archiving something you didn't ask it to.

**How it works**

Wraps the `wacli` CLI in read-only mode to list and inspect chats, then waits for approval before running any write command — using the exact chat JID already surfaced in the report, never a name-based match (which can be ambiguous) unless the user is present to confirm it. Reply text is drafted and confirmed before any send.

**Requirements**

Requires `wacli` on `PATH` with `wacli auth` already completed and a synced local store.

Source: [`whatsapp-triage/SKILL.md`](./whatsapp-triage/SKILL.md)

---

[← Back to all skills](../../README.md)
