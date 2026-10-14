"""Check a finished demo folder and set up the video WORK folder.

  python3 scripts/video_preflight.py --demo <project>-portfolio-demo --work VWORK \
      [--format landscape|vertical|square] [--duration 20] [--replace]

Refuses unless the demo folder looks like a finished, scanned portfolio-demo-kit demo: only the
allowed files, and a SANITISATION.md with the scan results filled in. Then it:
  - copies the demo (without any old video/) to VWORK/demo/: the only material the video may use;
  - takes screenshots of the demo page and diagram into VWORK/shots/;
  - writes VWORK/scene/scene.json (size, length, frame rate) for the scene page;
  - checks that FFmpeg, Playwright and its Chromium are installed, and says how to install them.
The video goes to <demo>/video/.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

FORMATS = {"landscape": (1920, 1080), "vertical": (1080, 1920), "square": (1080, 1080)}
DEMO_FILES = {"index.html", "data.json", "diagram.svg", "diagram.html", "README.md", "SANITISATION.md"}
VIDEO_FILES = {"launch.mp4", "launch.jpg", "share-copy.txt", "video-plan.md"}
UNFILLED = "<!-- PDK:SCAN_RESULTS -->"

INSTALL = {
    "ffmpeg": {"Windows (PowerShell)": "winget install Gyan.FFmpeg   (then close and reopen PowerShell)",
               "macOS": "brew install ffmpeg", "Linux": "sudo apt install ffmpeg"},
    "playwright": {"any": "python3 -m pip install playwright   (Windows: py -m pip install playwright)"},
    "chromium": {"any": "python3 -m playwright install chromium   (Windows: py -m playwright install chromium)"},
}


def check_demo(demo):
    problems = []
    if not (demo / "index.html").exists():
        problems.append("there is no index.html: run the portfolio-demo skill first")
    for p in sorted(demo.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(demo).as_posix()
        if rel.startswith("video/") and rel[len("video/"):] in VIDEO_FILES:
            continue
        if rel not in DEMO_FILES:
            problems.append(f"{rel} is not a demo file: this folder may not be a finished demo")
    report = demo / "SANITISATION.md"
    if not report.exists():
        problems.append("there is no SANITISATION.md")
    else:
        text = report.read_text(encoding="utf-8")
        if UNFILLED in text or "| Scanner self-test | passed |" not in text:
            problems.append("SANITISATION.md has no passed scan results: finish phase 8 of the demo first")
    return problems


def check_tools():
    missing = []
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return missing + ["playwright", "chromium"]
    try:
        with sync_playwright() as p:
            if not Path(p.chromium.executable_path).exists():
                missing.append("chromium")
    except Exception:
        missing.append("chromium")
    return missing


def screenshots(work, size):
    """Screenshots of the copied demo, for use as images in scenes. Network is blocked."""
    from playwright.sync_api import sync_playwright
    shots = work / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    demo = (work / "demo").as_uri()
    targets = [("page-desktop", "index.html", (1440, 900), False), ("page-desktop-full", "index.html", (1440, 900), True),
               ("page-phone", "index.html", (390, 844), True)]
    if (work / "demo" / "diagram.html").exists():
        targets.append(("diagram", "diagram.html", (1600, 1000), False))
    svg = work / "demo" / "diagram.svg"
    if svg.exists():
        # An SVG opened on its own cannot be captured as a full page: size the window to its viewBox.
        m = re.search(r'viewBox="\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)', svg.read_text(encoding="utf-8"))
        vw, vh = (float(m.group(1)), float(m.group(2))) if m else (360.0, 800.0)
        targets.append(("diagram-svg", "diagram.svg", (round(vw), round(vh)), False))
    made = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, file, (w, h), full in targets:
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
            page.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:"))
                       else r.abort())
            page.goto(f"{demo}/{file}", wait_until="load")
            page.wait_for_timeout(1200)
            path = shots / f"{name}.png"
            page.screenshot(path=str(path), full_page=full)
            made.append(path.name)
            page.close()
        browser.close()
    return made


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", required=True, help="the finished demo folder (<project>-portfolio-demo)")
    ap.add_argument("--work", required=True, help="an empty working folder for the video, outside any project")
    ap.add_argument("--format", default="landscape", choices=sorted(FORMATS))
    ap.add_argument("--duration", type=float, default=20)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--replace", action="store_true", help="allow replacing an existing video/ folder")
    args = ap.parse_args(argv)

    demo, work = Path(args.demo).resolve(), Path(args.work).resolve()
    if not demo.is_dir():
        sys.exit(f"Demo folder not found: {demo}")
    try:
        work.relative_to(demo)
        sys.exit("The video WORK folder must be outside the demo folder.")
    except ValueError:
        pass
    problems = check_demo(demo)
    if problems:
        sys.exit("This folder is not ready for a video:\n  - " + "\n  - ".join(problems))
    video = demo / "video"
    if video.exists() and any(video.iterdir()) and not args.replace:
        sys.exit(f"{video} already has a video. Ask the owner, then rerun with --replace to make a new one.")
    if not 15 <= args.duration <= 25:
        sys.exit("Keep the video between 15 and 25 seconds.")

    missing = check_tools()
    if missing:
        lines = ["Missing tools. Ask the owner before installing:"]
        for m in missing:
            for where, cmd in INSTALL[m].items():
                lines.append(f"  - {m} ({where}): {cmd}")
        sys.exit("\n".join(lines))

    if (work / "demo").exists():
        shutil.rmtree(work / "demo")
    shutil.copytree(demo, work / "demo", ignore=shutil.ignore_patterns("video"))
    (work / "scene").mkdir(parents=True, exist_ok=True)
    w, h = FORMATS[args.format]
    spec = {"width": w, "height": h, "duration": args.duration, "fps": args.fps, "format": args.format}
    (work / "scene" / "scene.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    made = screenshots(work, (w, h))

    print(f"Demo checked: {demo}")
    print(f"Video WORK folder: {work}")
    print(f"  demo/   the only material the video may use (data.json has every text)")
    print(f"  shots/  {', '.join(made)}")
    print(f"  scene/  write index.html here; scene.json: {w}x{h}, {args.duration:g}s, {args.fps} fps")
    print(f"The video will go to: {video}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
