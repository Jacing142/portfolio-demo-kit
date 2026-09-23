# How this demo was made safe

This demo was built from a private project with portfolio-demo-kit, an open-source tool. Every decision
below was proposed by the tool and confirmed or changed by the owner. The source project was not published.

## What was found

| # | What (described, not copied) | Group | Decision | Why |
|---|---|---|---|---|
| 1 | Staff names, work emails and employee IDs in the responses sheet | PERSONAL | FAKE | Real people. Replaced with invented first names; emails and IDs are not needed |
| 2 | Free-text comments written by staff | PERSONAL | FAKE | Written by real people. New comments invented |
| 3 | Each person's answers to the eight questions | PERSONAL | FAKE | Invented answers on the same 1 to 5 scale |
| 4 | The company's name and the owner's contact person | PROPRIETARY | REMOVE | Identifies the client |
| 5 | The questionnaire's own name | PROPRIETARY | REMOVE | The client's in-house instrument; called "a four-trait workstyle questionnaire" instead |
| 6 | Role titles and role descriptions | PROPRIETARY | FAKE | They reveal the industry; four invented roles instead |
| 7 | Target value for each role and trait | PROPRIETARY | FAKE | The client's own targets; invented values in the same range |
| 8 | The four trait names and what each one means | PROPRIETARY | KEEP | Approved by the owner: they explain the method and reveal nothing about the client |
| 9 | Industry examples of high and low traits | PROPRIETARY | REMOVE | They reveal the industry |
| 10 | The eight writing rules in the prompt | PROPRIETARY | KEEP | The owner wants them featured; the two opening lines naming the company and questionnaire were replaced |
| 11 | Scoring and gap-band logic, and the labels the script puts in the prompt | SAFE | KEEP | Generic averaging and banding |
| 12 | An API key in the script | SECRET | REMOVE | Never shown |
| 13 | The spreadsheet ID and link | SECRET | REMOVE | Private link |
| 14 | The deployed web app link | SECRET | REMOVE | Private link |
| 15 | The nightly schedule and the person who checks each note | UNSURE | KEEP | Confirmed by the owner, who is happy for both to be stated |

Groups: PERSONAL (about people), PROPRIETARY (the client's own know-how or wording), SECRET (keys,
passwords, private links and IDs), SAFE (generic, fine to show), UNSURE (the owner decided).

## Decisions the owner made

- Keep the trait names and what they mean; fake the roles, the targets and all people.
- Feature the writing rules and the way gaps are described in words.
- State that a member of the people team checks each note before it goes out, and that the run is nightly.
- Do not mention the company, its industry, the contact person or how many staff used it.

## How the demo data was made

- Invented inputs were generated from the structure of the real data (the same eight questions on a 1 to 5 scale, one role per person, an optional comment), never by editing real rows.
- Edge cases: someone on target for every trait (the prompt's stretch-goal rule), someone with two large gaps and no comment, a very long comment, and a role the script does not recognise.
- The project's own JavaScript scored the invented answers and assembled the prompts shown on the page.
- No API key was available, so every note is labelled "Illustrative, written by Claude": a written example that follows the project's eight writing rules, not a real run.

## Leak scan results

Before this demo was packaged, a scanner compared every file in it against the private project:
exact strings, runs of 6 or more words, secret patterns (keys, emails, private links, IDs) and
ten planted "canary" strings that must never appear. As a self-test, it also planted one real
string in a copy of the demo and confirmed it was caught.

The first scan found 42 problems: wording carried over from the prompt's opening lines, a phrase from the real role descriptions that had crept into an invented one, and the script's own labels, which the owner had kept but which had not been listed as kept. They were fixed in two rounds. The table below is the final scan.

| Check | Result |
|---|---|
| Files in this demo scanned | 5 |
| Strings from the private project checked against the demo | 166 |
| Exact copies found | 0 |
| Copied runs of words found | 0 |
| Secret patterns found (keys, emails, private links, IDs) | 0 |
| Canaries (planted fake strings) found | 0 of 10 |
| Scanner self-test | passed |
| Possible rewording warnings reviewed by a person | 0 |

## What this demo does NOT show

- The company's name, industry or size
- Real staff, their answers or their comments
- The real roles, role descriptions and target values
- The questionnaire's own name
- Any key, spreadsheet link or web app link

## Limits

Automated checks reduce risk; they do not guarantee that nothing sensitive remains. Publishing
was a manual step taken by the owner after reading this demo.
