"""Make an original soundtrack for the launch video: music and sound effects in one mix.

  python3 scripts/make_audio.py --duration 20 --out VWORK/audio.wav \
      --cuts 2.5,6,10.5,15 --clicks 7.2,8.1 [--mood bright|calm] [--bpm 112]

Everything is generated here from sine waves and noise, so there is no licence to check.
--cuts are scene changes (a soft swell lands on each); --clicks are on-screen clicks or taps
(a quiet tick). Effects are tuned to the music's key and mixed under it.
Python standard library only.
"""

import argparse
import math
import random
import struct
import wave

RATE = 44100
MOODS = {
    # chord roots as semitones from A3 (220 Hz), and chord shape
    "bright": {"chords": [3, 10, 0, 8], "shape": [(0, 4, 7), (0, 4, 7), (0, 3, 7), (0, 4, 7)], "kick_every": 1},
    "calm": {"chords": [0, 8, 3, 10], "shape": [(0, 3, 7), (0, 4, 7), (0, 4, 7), (0, 4, 7)], "kick_every": 2},
}


def freq(semi):
    return 220.0 * 2 ** (semi / 12)


def build(duration, bpm, mood, cuts, clicks, seed=7):
    rnd = random.Random(seed)
    n = int(duration * RATE)
    out = [0.0] * n
    beat = 60.0 / bpm
    bar = beat * 4
    m = MOODS[mood]

    def add(start, samples, gain):
        i0 = int(start * RATE)
        for k, s in enumerate(samples):
            j = i0 + k
            if 0 <= j < n:
                out[j] += s * gain

    # Pad: one chord per bar, slow attack and release, two detuned partials per note
    t = 0.0
    idx = 0
    while t < duration:
        root = m["chords"][idx % 4] - 12
        notes = [freq(root + iv) for iv in m["shape"][idx % 4]]
        length = int(bar * RATE)
        pad = []
        for k in range(length):
            x = k / RATE
            env = min(1.0, x / 0.6) * min(1.0, (bar - x) / 0.5)
            s = sum(math.sin(2 * math.pi * f * x) + 0.3 * math.sin(2 * math.pi * f * 2.003 * x) for f in notes)
            pad.append(env * s / len(notes))
        add(t, pad, 0.16)
        # Pluck arpeggio on eighth notes, an octave up
        for e in range(8):
            f = notes[e % 3] * 2
            dur = int(0.35 * RATE)
            pl = [math.exp(-k / RATE * 9) * (math.sin(2 * math.pi * f * k / RATE)
                  + 0.25 * math.sin(4 * math.pi * f * k / RATE)) for k in range(dur)]
            add(t + e * beat / 2, pl, 0.07)
        t += bar
        idx += 1

    # Kick and hats from the second bar, so the hook opens light
    b = 0
    while b * beat < duration:
        start = b * beat
        if start >= bar * 0.5:
            if b % m["kick_every"] == 0:
                kick = []
                for k in range(int(0.25 * RATE)):
                    x = k / RATE
                    f = 50 + 70 * math.exp(-x * 30)
                    kick.append(math.exp(-x * 14) * math.sin(2 * math.pi * f * x))
                add(start, kick, 0.32)
            hat = [math.exp(-k / RATE * 60) * (rnd.random() * 2 - 1) for k in range(int(0.05 * RATE))]
            add(start + beat / 2, hat, 0.035)
        b += 1

    # Swell into each cut: rising filtered noise plus a note in key
    for c in cuts:
        length = 0.45
        sw, prev = [], 0.0
        for k in range(int(length * RATE)):
            x = k / RATE
            alpha = 0.02 + 0.3 * (x / length) ** 2
            prev += alpha * ((rnd.random() * 2 - 1) - prev)
            sw.append(prev * (x / length) ** 2)
        add(c - length, sw, 0.25)
        f = freq(m["chords"][0] + 12)
        hit = [math.exp(-k / RATE * 6) * math.sin(2 * math.pi * f * k / RATE) for k in range(int(0.6 * RATE))]
        add(c, hit, 0.06)

    # Click: a short tick tuned to the key
    for c in clicks:
        f = freq(m["chords"][0] + 36)
        tick = [math.exp(-k / RATE * 90) * math.sin(2 * math.pi * f * k / RATE) for k in range(int(0.08 * RATE))]
        add(c, tick, 0.05)

    # Fade in and out, then a soft limiter
    fade_in, fade_out = int(0.3 * RATE), int(1.2 * RATE)
    for k in range(n):
        g = min(1.0, k / fade_in, (n - k) / fade_out)
        out[k] = math.tanh(out[k] * g * 1.4) * 0.8
    return out


def write(path, samples):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = bytearray()
        for s in samples:
            v = int(max(-1.0, min(1.0, s)) * 32767)
            frames += struct.pack("<hh", v, v)
        w.writeframes(bytes(frames))


def times(text):
    return [float(x) for x in (text or "").split(",") if x.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cuts", help="scene-change times in seconds, comma-separated")
    ap.add_argument("--clicks", help="click or tap times in seconds, comma-separated")
    ap.add_argument("--mood", choices=sorted(MOODS), default="bright")
    ap.add_argument("--bpm", type=int, default=112)
    args = ap.parse_args(argv)
    samples = build(args.duration, args.bpm, args.mood, times(args.cuts), times(args.clicks))
    write(args.out, samples)
    print(f"Wrote {args.out}: {args.duration:g}s, {args.mood}, {args.bpm} bpm")


if __name__ == "__main__":
    main()
