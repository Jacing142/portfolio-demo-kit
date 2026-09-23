# Questions and answers

## What is sent where?

| What | Where it goes | Who can see it |
|---|---|---|
| Files you upload to `input/` | Your private GitHub repository | You and anyone you add to the repository |
| The same files, while the workflows run | GitHub's servers running the workflow, then Anthropic's API, using your API key | Handled under your own agreements with GitHub and Anthropic |
| The issue the tool opens (summary, table, questions) | Your private repository | You and your collaborators. Secret values are masked; the tool refuses to post an issue that looks like it contains one. |
| The finished demo (`demo.zip`) | Attached to the workflow run in your private repository | You, until you publish it |
| The published demo | Wherever you put it (a new public repository, GitHub Pages, Vercel) | Everyone |

Nothing is sent to the people who made this tool. The tool never publishes anything for you.

## Which kinds of project work?

Anything made of text files: Python, JavaScript or TypeScript, Google Apps Script, SQL, prompt files,
settings files, and spreadsheets saved as CSV. Tested so far on the two examples in `examples/`.

Not supported: Excel files (save each sheet as CSV), images, PDFs, databases (export a small CSV
sample), and anything over 25 MB.

## How much does it cost?

The tool is free. You pay for your own API usage. It depends on how big your project is and how
many fix attempts are needed. After each stage the issue gets a comment with the tokens used and
an estimated cost. For exact figures, see Usage in your Anthropic Console.

To keep costs down: upload a sample of large sheets (30-50 rows), not full exports, and keep the
default model.

## How do I change the model?

Open `config.toml` in your repository, click the pencil icon, and change `agent` (the model that
reads your project and builds the demo) or `demo_outputs` (the model that runs your project's
prompts). Options: `claude-sonnet-5` (default) or `claude-fable-5-1` (most capable, costs more).
Commit the change. The next run uses it.

## Why must I never fork this repository?

A fork of a public repository is public, and GitHub does not let you make it private. Anything you
upload to a fork is visible to everyone. Always use **Use this template > Create a new repository >
Private**. The workflows stop if they detect a public repository.

## I uploaded something I should not have. What now?

Deleting the file removes it from the latest version, but it stays in the repository's history.
To remove it completely: download anything you want to keep, delete the repository (Settings >
General > Danger Zone > Delete this repository), and start again from the template. If it was a
password or API key, change it at the source straight away.

## The build says the scan did not pass. What now?

The comment lists what was found, masked. Usually something you chose to KEEP is close to
something private, or a piece of real text slipped into the demo. Reply in the issue with a change
(for example "fake the role descriptions too") and comment `/build` again.

## What are "canaries"?

Before the demo is built, the tool adds ten made-up strings (a name, an email, a key, an ID, a
sentence, twice each) to a private working copy of your project. They exist nowhere else. If any
of them shows up in the demo, real rows were copied instead of invented, and the demo is blocked.

## Can I change my answers after /build?

Yes. Reply in the same issue and comment `/build` again. Each build starts from scratch and reads
the whole conversation.

## How do I publish the demo?

1. Unzip `demo.zip` on your computer and open `index.html` in your browser. Read every word.
2. On GitHub, create a **new** repository (not a fork of your private one), set it to Public, and
   upload the files from the zip with **Add file > Upload files**.
3. Then either:
   - **GitHub Pages**: in the new repository go to Settings > Pages, choose "Deploy from a branch",
     pick `main` and `/ (root)`, and save. The address appears on that page after a minute or two.
   - **Vercel**: sign in at vercel.com, choose "Add New > Project", import the new repository,
     leave the framework as "Other" with no build command, and deploy.

Publishing is manual on purpose, so a person always looks at the demo first.

## Can I run it without GitHub Actions?

Yes, in Claude Code on your own computer. The same instructions are in
`.claude/skills/portfolio-demo/SKILL.md`, including the commands for each phase.

## How long is the demo kept?

The files attached to a run expire after the number of days set by `artifact_retention_days` in
`config.toml` (default 14). Run `/build` again to make a new one.
