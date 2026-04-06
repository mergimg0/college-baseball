#!/usr/bin/env python3
"""Standalone pyannote diarization script.

Runs in the .venv-pyannote Python 3.12 environment. Called as a subprocess
by enriched_batch.py since pyannote/torch require Python 3.12.

Usage:
    .venv-pyannote/bin/python3 scripts/pyannote_diarize.py \
        --audio data/recordings/Ryan_McCarthy_complete.wav \
        --output data/pyannote_segments.json \
        --max-speakers 3 \
        --hf-token <token>

Output JSON format:
    [{"start": 0.12, "end": 3.45, "speaker": "SPEAKER_00"}, ...]
"""

from __future__ import annotations

import argparse
import json
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="pyannote speaker diarization")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--max-speakers", type=int, default=3)
    parser.add_argument("--hf-token", default="", help="HuggingFace token")
    parser.add_argument("--hf-token-file", default="", help="Path to HF token file")
    args = parser.parse_args()

    # Resolve token
    hf_token = args.hf_token
    if not hf_token and args.hf_token_file:
        with open(args.hf_token_file) as f:
            hf_token = f.read().strip()

    if not hf_token:
        print("ERROR: No HuggingFace token provided", file=sys.stderr)
        return 1

    t0 = time.time()

    # Import pyannote (this is why we need the 3.12 venv)
    from pyannote.audio import Pipeline

    print(f"pyannote import: {time.time() - t0:.1f}s", file=sys.stderr)

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token,
    )
    print(f"Pipeline loaded: {time.time() - t0:.1f}s", file=sys.stderr)

    # Run diarization
    print(f"Diarizing: {args.audio} (max_speakers={args.max_speakers})", file=sys.stderr)
    diarization = pipeline(args.audio, max_speakers=args.max_speakers)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": round(turn.start, 3),
            "end": round(turn.end, 3),
            "speaker": speaker,
        })

    elapsed = time.time() - t0
    print(f"Done: {len(segments)} segments in {elapsed:.1f}s", file=sys.stderr)

    # Speaker summary
    from collections import Counter
    speaker_time = Counter()
    speaker_count = Counter()
    for s in segments:
        speaker_time[s["speaker"]] += s["end"] - s["start"]
        speaker_count[s["speaker"]] += 1

    for sid in sorted(speaker_time.keys()):
        dur = speaker_time[sid]
        cnt = speaker_count[sid]
        print(f"  {sid}: {dur:.0f}s ({dur / 60:.1f}min), {cnt} segments", file=sys.stderr)

    # Write output
    with open(args.output, "w") as f:
        json.dump(segments, f, indent=2)

    # Also write to stdout for subprocess capture
    print(json.dumps({"segments": len(segments), "elapsed_s": round(elapsed, 1)}))

    return 0


if __name__ == "__main__":
    sys.exit(main())
