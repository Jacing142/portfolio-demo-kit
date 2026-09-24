# Leak scan report

Before this demo was published, a scanner compared every file in this folder with the private
project it came from. This is what it checked, in plain words.

| What was checked | Result |
|---|---|
| Every questionnaire statement from the real questionnaire, word for word | 0 found |
| Any run of 6 words in a row copied from a real questionnaire statement | 0 found |
| The real question codes | 0 found |
| The example statements inside the real prompt | 0 found |
| Any run of 10 words in a row copied from the real role descriptions | 0 found |
| Any run of 10 words in a row copied from the real generated feedback | 0 found |
| Every invented target answer, compared cell by cell with the real answer key for the same trait and role: each one had to be different | 0 matches |
| Anything that looks like an API key, sheet ID or script ID, in the source or in the demo | 0 found |
| Links to anything other than public websites | 0 found |

**Result: 0 found.**

## What was allowed on purpose

- The trait names and trait definitions, which the client approved for publication.
- Answer wording such as "Strongly Agree", and generic role titles such as "Pilot".
- The shape of the prompt template and the fixed opening sentence for reverse-worded items,
  because they show the method rather than the client's data.

## How we know the scan worked

The scanner was tested by planting known real strings into a copy of the demo. It caught them.
So "0 found" means the checks ran and found nothing, not that they never ran.

## Checked again when this folder was added to portfolio-demo-kit

The folder was searched again for API keys, email addresses, long ID-like strings and vendor or
instrument names. None were found.
