# How this demo was made safe

This demo was built from a private project with portfolio-demo-kit, an open-source tool. Every decision
below was proposed by the tool and confirmed or changed by the owner. The source project was not published.

## What was found

| # | What (described, not copied) | Group | Decision | Why |
|---|---|---|---|---|
| 1 | Customer names, email addresses and the text of their emails | PERSONAL | FAKE | Real customers. Six new emails invented |
| 2 | Customer email addresses in the order table | PERSONAL | FAKE | Real customers |
| 3 | First names of the two support staff | PERSONAL | REMOVE | Real people. Called 'the support team' |
| 4 | The manager's email address used for escalations | PERSONAL | REMOVE | A real person's address |
| 5 | The shop's name | PROPRIETARY | REMOVE | Identifies the client. Called 'an online homeware shop' |
| 6 | Order numbers and their format | PROPRIETARY | FAKE | The prefix is the shop's initials. Invented numbers in an EX- format |
| 7 | Products, order values and dates | PROPRIETARY | FAKE | Invented orders of the same kind |
| 8 | The sorting prompt: topics, urgency levels and the safety rule | PROPRIETARY | KEEP | Owner wants it featured. The opening line naming the shop is replaced |
| 9 | The reply prompt: house style and refund, delivery and safety policy | PROPRIETARY | FAKE | The shop's own policy. Summarised in new words, never quoted |
| 10 | The order value above which an email is escalated | PROPRIETARY | REMOVE | Owner does not want the exact figure stated. Described as 'a high-value order' |
| 11 | Order lookup, escalation logic and prompt assembly in the script | SAFE | KEEP | Generic code, run on the invented data, including the fixed text it adds to the prompts |
| 12 | An API key in the settings file | SECRET | REMOVE | Never shown |
| 13 | An internal helpdesk link | SECRET | REMOVE | Private link |
| 14 | The private network address of the office computer that runs it | SECRET | REMOVE | Private network detail |
| 15 | How often it runs and where it runs | UNSURE | REMOVE | Owner prefers not to state it |
| 16 | A person reviews each draft before it goes out | UNSURE | KEEP | Confirmed by the owner |

Groups: PERSONAL (about people), PROPRIETARY (the client's own know-how or wording), SECRET (keys,
passwords, private links and IDs), SAFE (generic, fine to show), UNSURE (the owner decided).

## Decisions the owner made

- Fake all customers, their emails and the orders.
- Keep and feature the sorting prompt, especially the rule that any safety problem is always most urgent.
- The refund, delivery and safety policy belongs to the shop: summarise it, never quote it.
- State that a person reviews each draft before it goes out, and that urgent emails go to a manager.
- Do not mention how often it runs, the computer it runs on, the escalation figure or any staff names.

## How the demo data was made

- Invented emails and orders follow the structure of the real ones (the same columns, topics, statuses and order-number shape), never by editing real rows. Order numbers use an invented EX- prefix, so the order-number pattern in the script was changed to match; nothing else in the code was changed.
- Edge cases: a safety problem written calmly, an email with no order number, an angry fourth email with a complaint threat, a high-value order, and an email in French.
- The project's own Python code looked up each order, applied the escalation rule and assembled the prompts shown on the page.
- No API key was available, so every sorting result and draft reply is labelled "Illustrative, written by Claude": a written example that follows the project's prompts and the shop's policy, not a real run.

## Leak scan results

Before this demo was packaged, a scanner compared every file in it against the private project:
exact strings, runs of 6 or more words, secret patterns (keys, emails, private links, IDs) and
ten planted "canary" strings that must never appear. As a self-test, it also planted one real
string in a copy of the demo and confirmed it was caught.

The first scan found 12 problems, including a phrase copied from the shop's private reply prompt and a fixed message from the script that the owner had kept but which had not been listed as kept. They were fixed in one round. The table below is the final scan.

| Check | Result |
|---|---|
| Files in this demo scanned | 5 |
| Strings from the private project checked against the demo | 136 |
| Exact copies found | 0 |
| Copied runs of words found | 0 |
| Secret patterns found (keys, emails, private links, IDs) | 0 |
| Canaries (planted fake strings) found | 0 of 10 |
| Scanner self-test | passed |
| Possible rewording warnings reviewed by a person | 0 |

## What this demo does NOT show

- The shop's name, customers, orders or staff
- The wording of the shop's refund, delivery and safety policy
- The order value that triggers escalation
- How often it runs and the computer it runs on
- Any key, private link or network address

## Limits

Automated checks reduce risk; they do not guarantee that nothing sensitive remains. Publishing
was a manual step taken by the owner after reading this demo.
