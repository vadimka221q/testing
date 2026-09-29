"""Procedural sound design for the xerg reel.

Every sound is synthesised (sines, FM, filtered noise), with no samples, and is
placed on the same timeline as index.html (see SCENES there).

    python3 sound.py            -> out/xerg_sfx.wav
Then mux:  ffmpeg -i out/xerg.mp4 -i out/xerg_sfx.wav -c:v copy -c:a aac -b:a 256k out/xerg_sound.mp4
"""
import os
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
DUR = 9.2
N = int(SR * (DUR + 0.2))
L = np.zeros(N)
R = np.zeros(N)
rs = np.random.default_rng(7)


# ---------------------------------------------------------------- helpers
def tt(d):
    return np.arange(int(d * SR)) / SR

def env(d, a=0.002, k=8.0):
    """attack then exponential decay (k = decays per second)."""
    t = tt(d)
    e = np.exp(-k * t)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e

def osc(freq, d, shape='sine'):
    t = tt(d)
    f = np.broadcast_to(freq if np.ndim(freq) else np.full(len(t), freq), t.shape)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if shape == 'sine':
        return np.sin(ph)
    if shape == 'saw':
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if shape == 'square':
        return np.sign(np.sin(ph))

def noise(d):
    return rs.standard_normal(int(d * SR))

def filt(x, kind, f, order=2):
    f = np.clip(np.atleast_1d(f), 20, SR / 2 - 100)
    sos = butter(order, f if len(f) > 1 else f[0], btype=kind, fs=SR, output='sos')
    return sosfilt(sos, x)

def sweep_bp(x, f0, f1, q=2.0):
    """band-pass whose centre glides f0->f1 (state-variable filter, per sample)."""
    n = len(x)
    fc = np.geomspace(f0, f1, n)
    g = np.tan(np.pi * fc / SR)
    k = 1 / q
    y = np.zeros(n)
    ic1 = ic2 = 0.0
    for i in range(n):
        gi = g[i]
        a1 = 1 / (1 + gi * (gi + k))
        v3 = x[i] - ic2
        v1 = a1 * ic1 + gi * a1 * v3
        v2 = ic2 + gi * v1
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        y[i] = v1
    return y

def put(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    s = sig[: N - i] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(s)] += s * l * 1.414
    R[i:i + len(s)] += s * r * 1.414

def note(n):  # midi -> Hz
    return 440 * 2 ** ((n - 69) / 12)


# ---------------------------------------------------------------- instruments
def kick(g=1.0, t0=0):
    d = 0.6
    f = 45 + 110 * np.exp(-tt(d) * 28)
    s = osc(f, d) * env(d, 0.001, 6.5)
    c = filt(noise(0.02), 'highpass', 2500) * env(0.02, 0.0005, 200) * 0.4
    s[:len(c)] += c
    put(np.tanh(s * 1.6), t0, g)

def impact(t0, g=1.0, tail=1.2):
    kick(g, t0)
    n = filt(noise(0.5), 'lowpass', 2800) * env(0.5, 0.001, 9)
    put(n, t0, 0.35 * g)
    sub = osc(38, tail) * env(tail, 0.01, 2.2)
    put(sub, t0, 0.55 * g)
    rev_send(n * 0.5 + osc(90, 0.5) * env(0.5, 0.001, 10) * 0.2, t0, 0.5 * g)

def tick(t0, f=3600, g=0.25, pan=0.0):
    d = 0.018
    put(osc(f, d) * env(d, 0.0003, 260), t0, g, pan)

def blip(t0, f, g=0.3, d=0.09, pan=0.0):
    s = osc(f, d) * 0.8 + osc(f * 2, d) * 0.2
    put(s * env(d, 0.002, 38), t0, g, pan)
    rev_send(s * env(d, 0.002, 38), t0, g * 0.25)

def pluck(t0, f, g=0.4, pan=0.0):
    d = 0.9
    t = tt(d)
    mod = np.sin(2 * np.pi * f * 2 * t) * 1.8 * np.exp(-t * 9)
    s = np.sin(2 * np.pi * f * t + mod) * env(d, 0.002, 5.5)
    put(s, t0, g, pan)
    rev_send(s, t0, g * 0.45)

def whoosh(t0, d, f0=300, f1=5000, g=0.5, pan0=-0.6, pan1=0.6):
    x = noise(d)
    y = sweep_bp(x, f0, f1, q=1.6)
    a = np.sin(np.linspace(0, np.pi, len(y))) ** 1.5
    y *= a
    half = len(y) // 2
    put(y[:half], t0, g, pan0)
    put(y[half:], t0 + half / SR, g, pan1)
    rev_send(y, t0, g * 0.3)

def riser(t0, t1, g=0.5):
    d = t1 - t0
    x = sweep_bp(noise(d), 250, 7000, q=1.2)
    tone = osc(np.geomspace(110, 880, int(d * SR)), d, 'saw')
    tone = filt(tone, 'lowpass', 2500) * 0.25
    a = np.linspace(0, 1, len(x)) ** 2.4
    put((x + tone) * a, t0, g)
    rev_send((x + tone) * a, t0, g * 0.35)

def glitch(t0, d, g=0.35, seed=1):
    r = np.random.default_rng(seed)
    y = np.zeros(int(d * SR))
    step = int(SR / 60)
    for i in range(0, len(y), step):
        if r.random() < 0.55:
            seg = min(step, len(y) - i)
            f = r.choice([220, 440, 660, 1320, 2640, 5280])
            hold = r.integers(4, 40)
            n = r.standard_normal(seg // hold + 1).repeat(hold)[:seg]
            sq = np.sign(np.sin(2 * np.pi * f * np.arange(seg) / SR))
            y[i:i + seg] = (n * 0.6 + sq * 0.4) * r.uniform(0.3, 1)
    y = np.round(y * 6) / 6  # bitcrush
    put(filt(y, 'highpass', 150), t0, g, r.uniform(-0.5, 0.5))

def servo(t0, d, f0=500, f1=1500, g=0.18):
    f = np.geomspace(f0, f1, int(d * SR))
    s = osc(f, d, 'square')
    s = filt(s, 'bandpass', [f0 * 0.8, f1 * 2]) * np.linspace(0.2, 1, len(s))
    put(s * 0.5, t0, g)

def shutter(t0, g=0.3):
    for k, dt in enumerate((0, 0.028)):
        n = filt(noise(0.03), 'bandpass', [1500, 9000]) * env(0.03, 0.0003, 160)
        put(n, t0 + dt, g * (1 if k == 0 else 0.7), -0.2 + 0.4 * k)

def keys(t0, t1, rate=26, g=0.08, seed=3):
    r = np.random.default_rng(seed)
    t = t0
    while t < t1:
        n = filt(noise(0.012), 'bandpass', [2000, 7000]) * env(0.012, 0.0002, 350)
        put(n, t, g * r.uniform(0.5, 1), r.uniform(-0.4, 0.4))
        t += r.uniform(0.6, 1.4) / rate

def chatter(t0, t1, rate=22, g=0.1, seed=5):
    r = np.random.default_rng(seed)
    t = t0
    while t < t1:
        tick(t, r.choice([2400, 3200, 4200, 5600, 7000]), g * r.uniform(0.3, 1), r.uniform(-0.8, 0.8))
        t += r.exponential(1 / rate)

def ping(t0, f=1320, g=0.3):
    s = osc(f, 0.5) * env(0.5, 0.002, 9)
    for k in range(4):
        put(s, t0 + k * 0.16, g * 0.55 ** k, (-0.5, 0.5)[k % 2])
    rev_send(s, t0, g * 0.4)

def chord(t0, notes, d=2.6, g=0.25, bright=2200):
    s = np.zeros(int(d * SR))
    for i, n in enumerate(notes):
        for det in (-0.07, 0.07):
            s += osc(note(n + det), d, 'saw') * (0.9 ** i)
    s = filt(s, 'lowpass', bright)
    a = env(d, 0.03, 1.4)
    put(s * a / len(notes), t0, g)
    rev_send(s * a / len(notes), t0, g * 0.8)

# ---------------------------------------------------------------- reverb bus
RV = np.zeros(N)
def rev_send(sig, t0, g):
    i = int(t0 * SR)
    if i >= N:
        return
    s = sig[: N - i] * g
    RV[i:i + len(s)] += s

def apply_reverb():
    d = 2.2
    t = tt(d)
    for ch, seed in ((L, 11), (R, 12)):
        ir = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 3.2)
        ir = filt(ir, 'lowpass', 6000)
        ir /= np.sqrt(np.sum(ir ** 2))
        wet = fftconvolve(RV, ir)[:N]
        ch += filt(wet, 'highpass', 200) * 0.9


# ================================================================= SCORE
# bed: low drone + air, ducked by the hits
t = np.arange(N) / SR
bed = (np.sin(2 * np.pi * 55 * t) * 0.5 + np.sin(2 * np.pi * 82.4 * t) * 0.18
       + filt(rs.standard_normal(N), 'bandpass', [400, 1800]) * 0.05)
bed *= np.clip(t / 0.4, 0, 1) * np.clip((DUR - t) / 0.4, 0, 1) * (1 + 0.25 * np.sin(2 * np.pi * 0.35 * t))
duck = np.ones(N)
for h in (0.46, 1.4, 2.55, 4.2, 5.35, 5.98, 6.5, 7.95):
    i = int(h * SR)
    k = len(t) - i
    duck[i:] *= 1 - 0.7 * np.exp(-(t[i:] - h) * 5)
BED = bed * duck * 0.12

# S1: reticle lock
servo(0.02, 0.5, 300, 1400, 0.14)
blip(0.52, 1760, 0.22, pan=-0.2); blip(0.57, 2640, 0.18, pan=0.2)
for i in range(15):
    tick(0.3 + i * 0.012, 4200, 0.07, -0.6 + i * 0.08)
for i, dt in enumerate((0.28, 0.32, 0.36)):
    tick(dt, 2800 + 600 * i, 0.16)
glitch(0.36, 0.1, 0.32, seed=2)
impact(0.46, 0.75, tail=0.8)
for i, n in enumerate((74, 78, 81, 86)):
    blip(0.6 + i * 0.05, note(n), 0.12, 0.07, -0.3 + 0.2 * i)
keys(0.45, 1.05, 30, 0.05)
tick(0.72, 3000, 0.15)
shutter(0.9, 0.28)
whoosh(1.08, 0.34, 400, 6000, 0.42)

# S2: photo + lenses
impact(1.4, 0.9)
chatter(1.42, 2.1, 20, 0.09)
for i, lt in enumerate((1.56, 1.64, 1.72, 1.8)):
    blip(lt, (1320, 1480, 1660, 1980)[i], 0.2, 0.06, (-0.5, 0.4, -0.2, 0.6)[i])
    servo(lt - 0.05, 0.05, 900, 1800, 0.06)
put(filt(noise(0.06), 'highpass', 1200) * env(0.06, 0.0005, 60), 2.03, 0.25)
glitch(2.15, 0.36, 0.22, seed=9)
riser(2.2, 2.55, 0.32)

# S3: anatomy cards -> logo lockup
impact(2.55, 0.8)
whoosh(2.64, 0.4, 250, 4500, 0.4, -0.7, 0.7)
whoosh(3.06, 0.36, 400, 5000, 0.28, 0.6, -0.6)
put(osc(np.geomspace(500, 900, int(0.35 * SR)), 0.35) * np.sin(np.linspace(0, np.pi, int(0.35 * SR))), 2.86, 0.05)
for i, (gt, n) in enumerate(zip((3.5, 3.58, 3.66, 3.76), (62, 66, 69, 74))):
    pluck(gt, note(n), 0.32, -0.45 + 0.3 * i)
    tick(gt, 5200, 0.1)
chord(3.88, [50, 57, 62, 66, 69, 73], 2.0, 0.22)
kick(0.45, 3.88)

# S4: CONTROL PLANE / AGENT ECONOMICS
impact(4.2, 0.7)
for i in range(13):
    tick(4.2 + (i % 5) * 0.03 + (0.05 if i > 7 else 0) + i * 0.004, 3000 + 150 * i, 0.12, -0.6 + i * 0.1)
servo(4.42, 0.28, 500, 1600, 0.12)
blip(4.71, 1760, 0.2); blip(4.75, 2640, 0.15)
keys(4.5, 4.8, 34, 0.05, seed=8)
riser(4.85, 5.35, 0.55)
whoosh(4.9, 0.45, 600, 8000, 0.25)

# S5: FROM INSTALL / TO GOVERNANCE
impact(5.35, 0.9)
for bt in (5.85, 6.35):
    kick(0.5, bt)
for i in range(14):
    tick(5.35 + i / 12, 7000, 0.04, (-0.7, 0.7)[i % 2])
ping(5.72, 1320, 0.26)
put(sweep_bp(noise(0.26), 2000, 400, 3) * np.sin(np.linspace(0, np.pi, int(0.26 * SR))), 5.72, 0.25)
impact(5.98, 0.6, tail=0.6)
glitch(6.05, 0.1, 0.3, seed=4)
d = 0.45
spin = sweep_bp(noise(d), 300, 3000, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * np.geomspace(6, 22, int(d * SR)) * tt(d)))
put(spin * np.sin(np.linspace(0, np.pi, len(spin))), 6.05, 0.4)

# S6: IDENTITY + photo swaps + billboard
impact(6.5, 0.85)
for i in range(8):
    tick(6.5 + i * 0.03, 2600 + 200 * i, 0.1, -0.7 + 0.2 * i)
for st in (6.86, 7.06, 7.24):
    shutter(st, 0.3)
riser(7.28, 7.92, 0.6)
whoosh(7.35, 0.5, 300, 9000, 0.3)

# S7: end card
impact(7.95, 1.0, tail=1.4)
chord(7.95, [38, 50, 57, 62, 64, 69], 1.3, 0.28, 1800)
for i, n in enumerate((81, 86, 88, 93)):
    blip(8.08 + i * 0.06, note(n), 0.12, 0.12, -0.4 + 0.27 * i)
servo(8.0, 0.52, 400, 1300, 0.1)
blip(8.55, 1760, 0.16); blip(8.6, 2640, 0.12)
keys(8.3, 9.05, 30, 0.04, seed=6)

# ---------------------------------------------------------------- master
apply_reverb()
L += BED
R += BED
mix = np.stack([L, R], 1)[: int(DUR * SR)]
fade = int(0.25 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix /= np.max(np.abs(mix)) / 0.89
os.makedirs('out', exist_ok=True)
wavfile.write('out/xerg_sfx.wav', SR, (mix * 32767).astype(np.int16))
print('wrote out/xerg_sfx.wav', mix.shape[0] / SR, 's')
