---
name: portfolio-video
description: Make a 15-25 second launch video (MP4 with music, a thumbnail and share copy) of a finished portfolio demo made by the portfolio-demo skill. Built only from the sanitised demo folder, never from the private project. Use when someone asks for a launch video, promo video, LinkedIn video or "brag" video of their portfolio demo, or says "/portfolio-video".
argument-hint: "[demo folder] [--tone default|polished|playful|technical|<free text>] [--format landscape|vertical|square] [--duration 15-25]"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*), Bash(python ${CLAUDE_SKILL_DIR}/scripts/*), Bash(py ${CLAUDE_SKILL_DIR}/scripts/*), Bash(python3 ${CLAUDE_SKILL_DIR}/../portfolio-demo/scripts/*), Bash(python ${CLAUDE_SKILL_DIR}/../portfolio-demo/scripts/*), Bash(py ${CLAUDE_SKILL_DIR}/../portfolio-demo/scripts/*)
---

# Portfolio video

You make a short launch video of a portfolio demo, so the owner can post it. You write the story,
build the scenes as one web page, and render it with the scripts in this skill. Credit: the
structure and creative rules follow the open-source `/brag` skill (latent-spaces/brag, MIT).

Input: `$ARGUMENTS`. The first path is the finished demo folder (usually `<project>-portfolio-demo`
next to the project). If none is given and the portfolio-demo skill just finished in this
conversation, use its OUTPUT. Otherwise ask which demo folder.

Options, as flags or plain words:

| Option | Default |
|---|---|
| `--tone default\|polished\|playful\|technical\|<free text>` | `default` |
| `--format landscape\|vertical\|square` | landscape (1920x1080); vertical 1080x1920; square 1080x1080; 30 fps |
| `--duration <seconds>` | 20 (15 to 25) |

Output, always the same folder: `<demo folder>/video/` with `launch.mp4`, `launch.jpg` (thumbnail),
`share-copy.txt` and `video-plan.md`. It ships with the demo, so it is scanned with it.

On Windows, use `python` or `py` wherever this file says `python3`. `${CLAUDE_SKILL_DIR}` is this
skill's folder; the leak scanner is in the sibling `portfolio-demo` skill folder.

## Safety rules (these come first)

1. **Use only the demo folder.** Read nothing from the private project or its WORK copy, even if
   you know where it is. Your material is `VWORK/demo/` (a copy of the finished demo) and
   `VWORK/shots/` (screenshots of it). Every word in the video comes from `VWORK/demo/data.json`,
   `README.md` or the page, or is a short general line you write (a hook, a call to action).
2. **No new facts.** No client names, numbers, results, users or claims that the demo does not
   state. If the demo says outputs are illustrative, the video must not suggest real runs.
3. **Same labels as the demo.** If you show an output, show its label too ("Example" for
   illustrative, "Real run" for generated).
4. **No outside requests.** The scene page uses only files inside VWORK and system fonts. The
   renderer blocks everything else and reports it.
5. **Ask before installing** FFmpeg, Playwright or Chromium.

## 1. Preflight

Make a working folder outside any project, for example `VWORK=$(mktemp -d -t portfolio-video-XXXX)`.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/video_preflight.py --demo <DEMO> --work $VWORK --format landscape --duration 20
```

It refuses a folder that is not a finished, scanned demo, and lists any missing tool with the
install command for Windows, macOS and Linux. If a `video/` folder already exists, ask the owner,
then add `--replace`.

## 2. Plan

Read `VWORK/demo/data.json`, `VWORK/demo/README.md` and look at every image in `VWORK/shots/`.
Answer for yourself: what is it, in one sentence? Who is it for and what does it do for them?
What is the most striking thing a visitor sees in the demo? Which example (input to output) shows
it best? What is the one-line share caption?

Write `<DEMO>/video/video-plan.md`: the angle, the hook, 2-3 highlights, the closing line, tone,
colours (take them from the demo page), and a scene-by-scene storyboard with start times and
durations that add up to the target. Note which demo file each piece of text comes from.

Shape to start from: hook (2-3 s), what it is (2-4 s), 2-3 highlights (the example input, the
step that does the work, the output with its label, the diagram), close (2-4 s) with what it is
and that it is a portfolio demo. Adapt it.

## Creative rules

- **15-25 seconds.** 18-22 is best.
- **The hook decides it.** Plan the first 2 seconds first: the problem or the most surprising
  output, not the tech stack.
- **Clear to a stranger.** After one viewing, someone knows what the project does and for whom.
- **Show the real demo.** Use the demo's own text, example inputs and outputs, diagram and
  screenshots. Rebuild a panel in HTML when it needs to move (typing an input, an output
  appearing line by line); use screenshots for the rest. No abstract filler.
- **Specific.** Use the demo's own words. Banned: generic lines such as "streamline your workflow"
  or "unlock the power of AI".
- **Readable.** Any line the viewer must read stays fully on screen and still for about 0.3 s per
  word (at least 0.8 s for a short label), counted from when it has finished arriving. Keep pace
  with motion and cuts, never by taking text away early.
- **Alive.** Things appear one by one; inputs type in; outputs build; a cursor clicks. No static
  slides held for long.
- **Readable for colour blindness.** Never rely on red against green. Mark a person's step with
  text and a dashed outline, as the demo does. Keep strong contrast.
- **Every frame postable.** Any paused frame should look finished.

| Tone | Feel | Pacing |
|---|---|---|
| `default` | Clean, confident, friendly | 4-5 scenes, soft transitions |
| `polished` | Calm, elegant, restrained | 3-4 scenes, long holds, fades |
| `playful` | Bold type, quick and fun | 5-7 scenes, snappy cuts and zooms |
| `technical` | For engineers: prompt, logic and diagram up front | 4-5 scenes, monospace accents |

A free-text tone ("a calm museum audio guide") refines the nearest preset.

## 3. Build the scene page

Write `VWORK/scene/index.html`, one self-contained page:

- Size and length from `VWORK/scene/scene.json`. Set `window.SCENE` to that object.
- `window.render(t)` draws the frame at `t` seconds and depends on `t` only (no timers, no
  `requestAnimationFrame`, no randomness without a fixed seed). Compute each element's position,
  opacity and text from `t`.
- `window.READY` is a Promise that resolves when the images (`../shots/*.png`) and
  `document.fonts.ready` have loaded.
- Paths are relative: `../shots/page-desktop.png`, `../demo/diagram.svg`. Inline CSS and JS only.
  System fonts only (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`).

Check before rendering the whole video. Save stills from every scene and from the middle of every
transition, then look at each one:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_video.py --work $VWORK --stills 0.5,2.2,2.6,5.0,...
```

Fix text that overflows, overlaps or has low contrast. A crossfade between two busy layouts looks
muddy: move the old content out first, then bring the new in, or pass through the background.

## 4. Sound

Make an original soundtrack. `--cuts` are your scene-change times, `--clicks` any on-screen clicks:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/make_audio.py --duration 20 --cuts 2.5,6,10.5,15 --clicks 7.2 --mood bright --out $VWORK/audio.wav
```

`bright` suits default and playful, `calm` suits polished and technical. Skip it if the owner
asks for no sound.

## 5. Render

Pick the poster time: the strongest frame where everything has settled, not mid-transition.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_video.py --work $VWORK --out <DEMO>/video --audio $VWORK/audio.wav --poster 9.5
```

It writes `launch.mp4` (with the poster as frame 0, so it is the thumbnail everywhere) and
`launch.jpg`. If it reports blocked requests, the scene asked for something outside VWORK: fix the
scene and render again.

Write `<DEMO>/video/share-copy.txt`: 1-3 sentences, ready to post, specific to the project, in the
chosen tone. Say it is a portfolio demo with invented data. No "excited to share".

## 6. Scan

If this conversation still has the demo's WORK folder (the portfolio-demo skill just ran), run its
full phase 7 scan on the whole demo folder, with the scene page added:

```bash
python3 ${CLAUDE_SKILL_DIR}/../portfolio-demo/scripts/leak_scan.py scan --source $WORK/copy --output <DEMO> \
  --canaries $WORK/private/canaries.json --allow $WORK/decisions.json --also $VWORK/scene \
  --report $WORK/scan/report.json --markdown $WORK/scan/report.md
```

If WORK is gone (a video for an older demo), only the secret patterns can be checked:

```bash
python3 ${CLAUDE_SKILL_DIR}/../portfolio-demo/scripts/leak_scan.py patterns <DEMO>/video
python3 ${CLAUDE_SKILL_DIR}/../portfolio-demo/scripts/leak_scan.py patterns $VWORK/scene
```

Say which of the two ran. If anything is found, fix the scene, plan or share copy, render again and
rescan, up to 3 times. Do not present the video as ready while a scan fails.

## 7. Deliver

Tell the owner, briefly: where the video is (`<DEMO>/video/launch.mp4`), the thumbnail and share
copy next to it, the angle in one sentence, which scan ran, and that they should watch it once
before posting. Offer to redo a scene or try another tone or format. Delete VWORK when they are done.
