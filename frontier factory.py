# @title 🤠 The Frontier Engine (Math Edition)
# @markdown Click Play to generate your Deterministic "Dark Country" Library.

import os
import csv
import zipfile
import math
import time

print("Installing Audio Engine...")
!pip install mido > /dev/null
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
from google.colab import files

# ======================================================
# 1. THE MATH CONSTANTS
# ======================================================

KEYS = {"E_Minor": 40, "A_Minor": 45, "D_Minor": 38, "B_Minor": 47}
BPMS = range(65, 87, 2)

# GRIT: Probability of percussive subdivision (0.0 - 1.0)
GRIT_CONSTANTS = [0.4, 0.7, 0.95]

# SLIDE MAGNITUDE: How wide the pitch arc is (Pitch Wheel Units)
# 8192 is max bend.
SLIDE_MAGNITUDES = [2000, 4000, 8000]

OUTPUT_DIR = "/content/Panek_Blues_Library"

# ======================================================
# 2. THE ENGINE
# ======================================================

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_blues_track(key_name, root, bpm, grit_k, slide_mag, filename):
    mid = MidiFile()

    # TRACK SETUP
    track_stomp = MidiTrack(); mid.tracks.append(track_stomp)
    track_rhythm = MidiTrack(); mid.tracks.append(track_rhythm)
    track_slide = MidiTrack(); mid.tracks.append(track_slide)
    track_bass = MidiTrack(); mid.tracks.append(track_bass)

    # TEMPO & PATCHES
    track_stomp.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
    track_rhythm.append(Message('program_change', program=25, time=0)) # Steel Guitar
    track_slide.append(Message('program_change', program=29, time=0))  # Overdrive
    track_bass.append(Message('program_change', program=32, time=0))   # Acoustic Bass

    # --- THE LOGIC ---
    bars = 12
    ticks = 120
    total_steps = bars * 16

    # Set Theory: Minor Pentatonic + Tritone (6)
    scale = [0, 3, 5, 6, 7, 10, 12]

    # 12-Bar Progression Logic
    progression = [0,0,0,0, 5,5,0,0, 7,5,0,7]

    events_stomp, events_rhythm, events_slide, events_bass = [], [], [], []

    for i in range(total_steps):
        t = i * ticks

        # Current Chord Root
        bar_idx = min((i // 16), 11)
        current_root = root + progression[bar_idx]
        beat = i % 16

        # --- A. BOOLEAN RHYTHM GATE (The Stomp) ---
        # Equation: G(i) = (i % 8 == 0) OR (i % 4 == 0 AND K > 0.5)

        # The Kick (Downbeat)
        if beat % 8 == 0:
            events_stomp.append({'n': 35, 'v': 110, 't': t, 'd': 100})
            events_bass.append({'n': current_root - 12, 'v': 100, 't': t, 'd': 200})

        # The Clap (Backbeat) with Grit Probability
        # Deterministic Grit Check: (i * Grit_K) % 1 > 0.3
        grit_check = (i * grit_k) % 1.0

        if beat == 4 or beat == 12:
            if grit_check > 0.3:
                events_stomp.append({'n': 39, 'v': 100, 't': t, 'd': 50})

        # --- B. HARMONIC CONSTRAINT (Rhythm Gtr) ---
        # Play on the "and" of the beat (Syncopation)
        if beat % 4 == 2:
             events_rhythm.append({'n': current_root, 'v': 85, 't': t, 'd': 100})
             events_rhythm.append({'n': current_root+7, 'v': 85, 't': t, 'd': 100})

        # --- C. CONTINUOUS PITCH GEOMETRY (Slide Lead) ---
        # We define a "Call" period every 4 bars
        if i % 64 == 0:
            # Generate a 4-note lick based on Sine Mapping
            for k in range(4):
                step_offset = k * 4
                local_t = t + (step_offset * ticks)

                # Math: Index = abs( sin(k) ) scaled to scale length
                idx = int(abs(math.sin(k + bar_idx)) * len(scale))
                note = current_root + scale[idx % len(scale)] + 12

                # Apply Slide Flag
                events_slide.append({
                    'n': note, 'v': 100, 't': local_t, 'd': 400,
                    'bend': True, 'mag': slide_mag
                })

    # WRITE FUNCTION (Implementing P(t) = P0 + M*sin(t))
    def write(track, events):
        events.sort(key=lambda x: x['t'])
        last_t = 0
        for e in events:
            dt = max(0, e['t'] - last_t)

            if 'bend' in e:
                # 1. Start Pitch Low (Geometric Approach)
                track.append(Message('pitchwheel', pitch=-e['mag'], time=0))
                # 2. Note On
                track.append(Message('note_on', note=e['n'], velocity=e['v'], time=dt))
                # 3. Slide Up (Simulating the Sine Curve Apex)
                track.append(Message('pitchwheel', pitch=0, time=int(e['d'])))
                # 4. Note Off
                track.append(Message('note_off', note=e['n'], velocity=0, time=0))
                # 5. Reset
                track.append(Message('pitchwheel', pitch=0, time=0))
                last_t = e['t'] + e['d']
            else:
                track.append(Message('note_on', note=e['n'], velocity=e['v'], time=dt))
                track.append(Message('note_off', note=e['n'], velocity=0, time=e['d']))
                last_t = e['t'] + e['d']

    write(track_stomp, events_stomp)
    write(track_rhythm, events_rhythm)
    write(track_slide, events_slide)
    write(track_bass, events_bass)

    mid.save(filename)

# ======================================================
# 3. EXECUTION
# ======================================================

print("--- STARTING FRONTIER FACTORY ---")
ensure_dir(OUTPUT_DIR)
csv_name = "/content/Panek_Blues_Manifest.csv"

with open(csv_name, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Filename", "Key", "BPM", "GritConstant", "SlideMagnitude", "Author"])

    count = 0
    for key, root in KEYS.items():
        for bpm in BPMS:
            for grit in GRIT_CONSTANTS:
                for slide in SLIDE_MAGNITUDES:
                    fname = f"Blues_{key}_{bpm}_{grit}_{slide}.mid"
                    path = os.path.join(OUTPUT_DIR, fname)

                    generate_blues_track(key, root, bpm, grit, slide, path)
                    writer.writerow([fname, key, bpm, grit, slide, "Nick Panek"])
                    count += 1
                    if count % 100 == 0: print(f"Forged {count} tracks...")

print(f"TOTAL: {count} assets created.")
print("--- ZIPPING ---")
zip_name = "/content/NickPanek_Blues_Collection.zip"
with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(csv_name, arcname="Panek_Blues_Manifest.csv")
    for r, d, fnames in os.walk(OUTPUT_DIR):
        for f in fnames:
            z.write(os.path.join(r, f), arcname=f)

print(f"DONE. Downloading {zip_name}...")
files.download(zip_name)
