"""Minimal sound design for the xerg shapes piece. It is synthesised, and the
event times match the rendered timeline in index.html (after SHIFT).

    python3 sound.py  -> out/sfx.wav
"""
import os
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR, DUR = 48000, 5.85
N = int(SR * (DUR + 1))
L, R, RV = np.zeros(N), np.zeros(N), np.zeros(N)
rs = np.random.default_rng(3)

def tt(d): return np.arange(int(d * SR)) / SR
def env(d, a=.002, k=8.):
    e = np.exp(-k * tt(d)); na = max(1, int(a * SR)); e[:na] *= np.linspace(0, 1, na); return e
def sine(f, d):
    f = np.broadcast_to(f, (int(d * SR),)) if np.ndim(f) else np.full(int(d * SR), f)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
def noise(d): return rs.standard_normal(int(d * SR))
def filt(x, kind, f): return sosfilt(butter(2, f, btype=kind, fs=SR, output='sos'), x)
def put(s, t0, g=1., pan=0., rev=0.):
    i = int(t0 * SR); s = s[:N - i] * g
    L[i:i + len(s)] += s * np.cos((pan + 1) * np.pi / 4) * 1.414
    R[i:i + len(s)] += s * np.sin((pan + 1) * np.pi / 4) * 1.414
    RV[i:i + len(s)] += s * rev
def swell(d, f0, f1):
    """noise through a band-pass gliding f0->f1, shaped by a half-sine."""
    x, out, n = noise(d), np.zeros(int(d * SR)), int(d * SR)
    blk = 512
    for s in range(0, n, blk):
        fc = f0 * (f1 / f0) ** (s / n)
        out[s:s + blk] = filt(x[s:s + blk], 'bandpass', [fc * .7, fc * 1.4])
    return out * np.sin(np.linspace(0, np.pi, n)) ** 1.4
def thump(g, t0):
    d = .55; f = 42 + 90 * np.exp(-tt(d) * 30)
    put(np.tanh(sine(f, d) * env(d, .001, 7) * 1.5), t0, g)
def blip(t0, f, g, pan=0.):
    d = .22; s = (sine(f, d) + .25 * sine(2 * f, d)) * env(d, .003, 16); put(s, t0, g, pan, .5)
def tick(t0, g=.12, pan=0.):
    d = .02; put(filt(noise(d), 'highpass', 3000) * env(d, .0003, 220), t0, g, pan, .15)
def note(m): return 440 * 2 ** ((m - 69) / 12)

# A — bars slide in: three soft swishes
for i, t0 in enumerate((0.0, .36, .68)):
    put(swell(.28, 900, 3200), t0, .16, (-.5, .5, -.3)[i], .2)
put(swell(.24, 500, 2500), .8, .2, 0, .2)            # window grows
# B — burst in: soft thump + airy bloom
thump(.55, 1.02)
put(swell(.9, 3000, 700), 1.02, .12, 0, .5)
# inhale, then the blast
put(swell(.26, 300, 1400), 2.05, .22, 0, .2)
thump(.8, 2.3)
put(filt(noise(.3), 'lowpass', 2500) * env(.3, .001, 12), 2.3, .25, 0, .6)
put(swell(.75, 400, 6500), 2.3, .3, -.4, .35)
put(swell(.75, 600, 5000), 2.34, .22, .4, .35)
# C — construction lines + grid: a few quiet ticks, not one per line
for i, t0 in enumerate((2.95, 3.01, 3.07, 3.3, 3.42, 3.58, 3.78)):
    tick(t0, .1, (-.5, .5, 0, -.3, .3, -.1, .1)[i])
# D — the mark builds row by row (ascending), then the logo lands
for j, m in enumerate((69, 74, 76, 81)):
    blip(4.6 + j * .0875, note(m), .13, -.3 + .2 * j)
tick(5.03, .14)
thump(.5, 5.1)
chord = sum(sine(note(m), 2.2) * (.9 ** k) for k, m in enumerate((50, 57, 62, 66, 69)))
put(filt(chord, 'lowpass', 1800) * env(2.2, .02, 1.6) * .22, 5.1, 1, 0, .8)
blip(5.12, note(88), .08, .2)

# reverb bus + master
t = tt(2.0)
for ch, sd in ((L, 1), (R, 2)):
    ir = np.random.default_rng(sd).standard_normal(len(t)) * np.exp(-t * 3.5)
    ir = filt(ir, 'lowpass', 5000); ir /= np.sqrt((ir ** 2).sum())
    ch += filt(fftconvolve(RV, ir)[:N], 'highpass', 180) * .8
mix = np.stack([L, R], 1)[:int(DUR * SR)]
f = int(.3 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None]
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix /= np.abs(mix).max() / .89
os.makedirs('out', exist_ok=True)
wavfile.write('out/sfx.wav', SR, (mix * 32767).astype(np.int16))
print('wrote out/sfx.wav')
