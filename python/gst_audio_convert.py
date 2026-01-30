#!/usr/bin/env python3
"""Convert audio files using GStreamer."""

import argparse
import sys
from pathlib import Path

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

ENCODERS = {
    "flac": ("flacenc", "flac"),
    "mp3": ("lamemp3enc", "mp3"),
    "ogg": ("vorbisenc ! oggmux", "ogg"),
    "wav": ("wavenc", "wav"),
    "aac": ("faac ! mp4mux", "m4a"),
}


def print_progress(percent):
    bar_width = 40
    filled = int(bar_width * percent / 100)
    bar = '█' * filled + '░' * (bar_width - filled)
    print(f"\rProgress: [{bar}] {percent:5.1f}%", end='', flush=True)


def convert(input_file, output_file, codec):
    Gst.init(None)

    encoder, _ = ENCODERS[codec]
    pipeline_str = (
        f'filesrc location="{input_file}" '
        f'! decodebin ! audioconvert ! {encoder} '
        f'! filesink location="{output_file}"'
    )
    print(f"cmd: gst-launch-1.0 -e {pipeline_str}")

    pipeline = Gst.parse_launch(pipeline_str)
    if not pipeline:
        print("Error: Failed to create pipeline", file=sys.stderr)
        sys.exit(1)

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()

    error_msg = None

    def on_message(bus, message):
        nonlocal error_msg
        if message.type == Gst.MessageType.EOS:
            print_progress(100)
            print()
            loop.quit()
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            error_msg = f"{err.message}\n{debug}"
            loop.quit()

    bus.connect("message", on_message)

    def update_progress():
        if pipeline.get_state(0)[1] != Gst.State.PLAYING:
            return True
        success, duration = pipeline.query_duration(Gst.Format.TIME)
        if not success or duration <= 0:
            return True
        success, position = pipeline.query_position(Gst.Format.TIME)
        if success and position >= 0:
            percent = min(100.0, (position / duration) * 100)
            print_progress(percent)
        return True

    GLib.timeout_add(100, update_progress)

    pipeline.set_state(Gst.State.PLAYING)
    loop.run()
    pipeline.set_state(Gst.State.NULL)

    if error_msg:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Convert audio using GStreamer")
    parser.add_argument("input", help="Input audio file")
    parser.add_argument("--codec", choices=ENCODERS.keys(), default="flac")
    parser.add_argument("--output_filename", help="Output filename")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    if args.output_filename:
        output_path = Path(args.output_filename)
    else:
        ext = ENCODERS[args.codec][1]
        output_path = Path(f"{input_path.stem}.{ext}")

    convert(str(input_path), str(output_path), args.codec)
    print(f"Converted: {output_path}")


if __name__ == "__main__":
    main()
