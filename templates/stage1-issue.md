<!--
Stage 1 issue template. The agent fills it and writes it to work/issue.md.
Never paste a secret value into the issue: describe it and mask it (first 4 characters, then ...).
Personal data: describe the column or field, give at most one masked example.
-->

## What your project does

{{Exactly 5 short lines in plain English. No jargon. Line 1 says what it is for; lines 2-5 say how it works, step by step.}}

**Detected:** {{stack}} · **Files read:** {{n}} · **Folder:** `{{folder}}`

## What I found

Each row is one thing I found. I have proposed what to do with it. You decide.

- **KEEP**: show it as it is.
- **FAKE**: replace it with invented data of the same shape.
- **REMOVE**: leave it out of the demo entirely.

### PERSONAL (about real people)

| # | What | Where | Proposed | Why |
|---|---|---|---|---|
| P1 | {{e.g. Employee names}} | {{file, column}} | FAKE | {{one line}} |

### PROPRIETARY (your client's own know-how, wording or data)

| # | What | Where | Proposed | Why |
|---|---|---|---|---|

### SECRET (keys, passwords, private links, IDs)

| # | What | Where | Proposed | Why |
|---|---|---|---|---|

### SAFE (generic, fine to show)

| # | What | Where | Proposed | Why |
|---|---|---|---|---|

### UNSURE (I need you to decide)

| # | What | Where | Proposed | Why |
|---|---|---|---|---|

## Questions the code cannot answer

1. **Steps outside the code.** {{Ask about specific gaps you noticed, e.g. "The script writes drafts to a sheet. Does a person review them before they are sent? Are there other scripts or manual steps before or after this one?"}}
2. **What to feature.** {{e.g. "Which part are you proudest of, or most want a client to see?"}}
3. **Production details.** {{e.g. "Is there anything about how this runs in production (volumes, results, who uses it) you do not want stated publicly? Anything you do want stated?"}}
{{4-6. Any other specific question the files raised.}}

## What to do next

Reply to this issue in plain words. For example:

> Keep the trait names, fake the role descriptions. P3 is fine to keep. QA was a manual review by the team lead. Feature the writing rules. Don't mention how many staff used it.

You can reply as many times as you like. When you are happy, add a comment that says **/build** on its own line.
Only people with write access to this repository can start the build.
