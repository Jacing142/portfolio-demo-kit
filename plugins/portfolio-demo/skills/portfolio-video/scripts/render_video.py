"""Render the launch video from the scene page Claude wrote. Only the video WORK folder is reachable.

  python3 scripts/render_video.py --work VWORK --stills 0.5,2.4,3.1      # check frames first
  python3 scripts/render_video.py --work VWORK --out DEMO/video --poster 9.5 [--audio VWORK/audio.wav]

VWORK is the folder video_preflight.py made. It holds demo/ (a copy of the finished, scanned demo),
shots/ (screenshots of it) and scene/index.html (written by Claude). The scene must define:

  window.SCENE = {width, height, duration, fps}   (from video_preflight.py, in scene/scene.json)
  window.READY  a Promise that resolves when fonts and images have loaded
  window.render(t)  draws the frame at t seconds; a pure function of t

The page is served from VWORK by a local server on 127.0.0.1. Every other request (internet,
other folders) is blocked, so the video can only use the sanitised demo.
Needs: Python 3.11+, Playwright with Chromium, FFmpeg.
"""

import argparse
import functools
import http.server
import json
import shutil
import subprocess
import sys
import threading
from pathlib import Path


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(root):
    handler = functools.partial(QuietHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def open_scene(p, base, spec, blocked):
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": spec["width"], "height": spec["height"]}, device_scale_factor=1)

    def guard(route):
        url = route.request.url
        if url.startswith(base + "/") or url.startswith("data:") or url.startswith("blob:"):
            route.continue_()
        else:
            blocked.append(url)
            route.abort()

    page.route("**/*", guard)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{base}/scene/index.html", wait_until="load")
    if errors:
        raise SystemExit("The scene page has a script error:\n  " + "\n  ".join(errors[:5]))
    if not page.evaluate("typeof window.render === 'function'"):
        raise SystemExit("scene/index.html must define window.render(t).")
    page.evaluate("Promise.resolve(window.READY)")
    page.evaluate("document.fonts ? document.fonts.ready.then(() => true) : true")
    return browser, page


def frame(page, t):
    page.evaluate("t => window.render(t)", t)
    return page.screenshot(type="png")


def stills(page, times, folder):
    folder.mkdir(parents=True, exist_ok=True)
    for t in times:
        path = folder / f"t{t:06.2f}.png"
        path.write_bytes(frame(page, t))
        print(f"still {path}")


def render(page, spec, out_raw, audio, ffmpeg):
    fps, n = spec["fps"], round(spec["duration"] * spec["fps"])
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-"]
    if audio:
        cmd += ["-i", str(audio)]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-r", str(fps)]
    cmd += (["-c:a", "aac", "-b:a", "192k", "-shortest"] if audio else ["-an"]) + [str(out_raw)]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        enc.stdin.write(frame(page, i / fps))
        if i and i % (fps * 5) == 0:
            print(f"  {i / fps:.0f}s of {spec['duration']}s")
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit("FFmpeg could not encode the video.")


def bake_poster(raw, poster_t, out, ffmpeg):
    """Save the poster frame as launch.jpg and make it frame 0, so every player shows it as the thumbnail."""
    jpg, mp4 = out / "launch.jpg", out / "launch.mp4"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-ss", f"{poster_t}", "-i", str(raw),
                    "-frames:v", "1", "-q:v", "2", str(jpg)], check=True)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(raw), "-i", str(jpg), "-filter_complex",
                    "[0:v][1:v]overlay=enable='eq(n,0)'", "-c:v", "libx264", "-crf", "18", "-pix_fmt",
                    "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(mp4)], check=True)
    return mp4, jpg


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True, help="the video WORK folder from video_preflight.py")
    ap.add_argument("--out", help="where launch.mp4 and launch.jpg go (normally DEMO/video)")
    ap.add_argument("--stills", help="comma-separated times in seconds: save these frames to WORK/stills/ only")
    ap.add_argument("--audio", help="a WAV file to put under the video")
    ap.add_argument("--poster", type=float, help="time of the poster frame (a settled frame, not mid-transition)")
    args = ap.parse_args(argv)

    work = Path(args.work).resolve()
    spec = json.loads((work / "scene" / "scene.json").read_text(encoding="utf-8"))
    if not (work / "scene" / "index.html").exists():
        sys.exit(f"Write the scene first: {work / 'scene' / 'index.html'}")
    ffmpeg = shutil.which("ffmpeg")
    if not args.stills and not ffmpeg:
        sys.exit("FFmpeg is not installed. See the install steps in the README.")
    if not args.stills and not (args.out and args.poster is not None):
        sys.exit("A full render needs --out and --poster.")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright is not installed: python3 -m pip install playwright && python3 -m playwright install chromium")

    server, base = serve(work)
    blocked = []
    try:
        with sync_playwright() as p:
            browser, page = open_scene(p, base, spec, blocked)
            if args.stills:
                stills(page, [float(x) for x in args.stills.split(",") if x.strip()], work / "stills")
            else:
                raw = work / "render-raw.mp4"
                render(page, spec, raw, Path(args.audio).resolve() if args.audio else None, ffmpeg)
                out = Path(args.out)
                out.mkdir(parents=True, exist_ok=True)
                mp4, jpg = bake_poster(raw, args.poster, out, ffmpeg)
                print(f"Wrote {mp4} and {jpg}")
            browser.close()
    finally:
        server.shutdown()
    if blocked:
        print("Blocked requests outside the video folder (the scene must not use them):")
        for url in sorted(set(blocked))[:20]:
            print(f"  - {url}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
