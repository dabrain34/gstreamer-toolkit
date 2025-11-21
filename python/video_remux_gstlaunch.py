#!/usr/bin/env python3
"""
Video Remuxing Tool - GStreamer gst-launch Version
Converts video files between different container formats while copying codecs (no re-encoding).
Uses gst-launch-1.0 command-line tool to perform fast remuxing operations.
"""

import argparse
import subprocess
import sys
import os
import re
import json
from pathlib import Path


class VideoRemuxer:
    """Handles video remuxing operations using gst-launch-1.0."""

    # Common container formats and their GStreamer muxers
    MUXER_MAP = {
        'mp4': 'mp4mux',
        'mkv': 'matroskamux',
        'matroska': 'matroskamux',
        'webm': 'webmmux',
        'avi': 'avimux',
        'mov': 'qtmux',
        'ogv': 'oggmux',
        'ogg': 'oggmux',
        'flv': 'flvmux',
        'ts': 'mpegtsmux',
        '3gp': '3gppmux',
    }

    # Video codec mappings (FFmpeg-style names to GStreamer elements)
    VIDEO_ENCODER_MAP = {
        'libx264': 'x264enc',
        'h264': 'x264enc',
        'libx265': 'x265enc',
        'h265': 'x265enc',
        'hevc': 'x265enc',
        'libvpx-vp9': 'vp9enc',
        'vp9': 'vp9enc',
        'libvpx': 'vp8enc',
        'vp8': 'vp8enc',
        'h264_vaapi': 'vah264enc',
        'hevc_vaapi': 'vahevcenc',
        'vp9_vaapi': 'vavp9lpenc',
        'vp8_vaapi': 'vavp8enc',
        'av1': 'av1enc',
    }

    # Audio codec mappings
    AUDIO_ENCODER_MAP = {
        'aac': 'avenc_aac',
        'libopus': 'opusenc',
        'opus': 'opusenc',
        'libvorbis': 'vorbisenc',
        'vorbis': 'vorbisenc',
        'libmp3lame': 'lamemp3enc',
        'mp3': 'lamemp3enc',
        'ac3': 'avenc_ac3',
    }

    def __init__(self, input_file: str, output_file: str = None, output_format: str = None,
                 video_codec: str = None, audio_codec: str = None, vaapi_device: str = None,
                 preset: str = 'medium', resolution: str = None):
        """
        Initialize the remuxer.

        Args:
            input_file: Path to input video file
            output_file: Optional custom output filename
            output_format: Optional target container format (e.g., 'webm', 'mp4', 'mkv', 'matroska')
            video_codec: Optional video codec (e.g., 'libx264', 'libvpx-vp9'). If None, copies video stream.
            audio_codec: Optional audio codec (e.g., 'aac', 'libopus'). If None, copies audio stream.
            vaapi_device: Optional VAAPI device path (e.g., '/dev/dri/renderD129') for Intel hardware acceleration.
            preset: Encoding speed/quality preset ('fast', 'medium', 'slow'). Default: 'medium'.
            resolution: Optional output resolution in WIDTHxHEIGHT format (e.g., '1920x1080').
        """
        self.input_file = Path(input_file)
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.vaapi_device = vaapi_device
        self.preset = preset
        self.resolution = resolution

        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Determine output format and filename
        if output_file:
            self.output_file = Path(output_file)
            # Use output file extension as format if no format specified
            if not output_format:
                self.output_format = self.output_file.suffix.lstrip('.')
            else:
                self.output_format = output_format.lower().lstrip('.')
                # Update output file extension if format is specified and differs
                if self.output_file.suffix.lstrip('.') != self.output_format:
                    self.output_file = self.output_file.with_suffix(f'.{self.output_format}')
        elif output_format:
            # Format specified but no output file - generate filename in current directory
            self.output_format = output_format.lower().lstrip('.')
            output_name = f'{self.input_file.stem}.{self.output_format}'
            self.output_file = Path.cwd() / output_name
        else:
            # No output file or format - keep same format, add _copy suffix, save in current directory
            self.output_format = self.input_file.suffix.lstrip('.')
            output_name = f'{self.input_file.stem}_copy{self.input_file.suffix}'
            self.output_file = Path.cwd() / output_name

        # Get muxer name
        self.muxer = self.MUXER_MAP.get(self.output_format.lower())
        if not self.muxer:
            # Try to use format name directly as muxer
            self.muxer = f'{self.output_format}mux'

    def check_gstreamer(self) -> bool:
        """Check if gst-launch-1.0 is available in the system."""
        try:
            result = subprocess.run(
                ['gst-launch-1.0', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_video_info(self) -> dict:
        """Get information about the input video using gst-discoverer-1.0."""
        try:
            result = subprocess.run(
                ['gst-discoverer-1.0', '-v', str(self.input_file)],
                capture_output=True,
                text=True,
                check=True
            )

            info = {'streams': []}

            # Parse duration
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', result.stdout)
            if duration_match:
                hours, minutes, seconds, fraction = duration_match.groups()
                info['duration'] = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + float(f"0.{fraction}")

            # Parse streams
            for line in result.stdout.split('\n'):
                if 'video' in line.lower() and 'Stream' in line:
                    info['streams'].append({'codec_type': 'video', 'codec_name': line.strip()})
                elif 'audio' in line.lower() and 'Stream' in line:
                    info['streams'].append({'codec_type': 'audio', 'codec_name': line.strip()})

            return info
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {}

    def _get_video_encoder_element(self) -> str:
        """Get GStreamer video encoder element name."""
        if not self.video_codec:
            return None

        encoder = self.VIDEO_ENCODER_MAP.get(self.video_codec.lower())
        if not encoder:
            # Try to use codec name directly
            encoder = self.video_codec

        return encoder

    def _get_audio_encoder_element(self) -> str:
        """Get GStreamer audio encoder element name."""
        if not self.audio_codec:
            return None

        encoder = self.AUDIO_ENCODER_MAP.get(self.audio_codec.lower())
        if not encoder:
            # Try to use codec name directly
            encoder = self.audio_codec

        return encoder

    def _get_encoder_properties(self, encoder_name: str) -> str:
        """Get encoder-specific properties based on preset."""
        props = []

        # VAAPI encoders
        if encoder_name.startswith('va'):
            # target-usage parameter (1-7, lower = faster/lower quality for Intel)
            quality_map = {
                'fast': 1,
                'medium': 4,
                'slow': 7
            }
            props.append(f'target-usage={quality_map[self.preset]}')

        # x264enc
        elif encoder_name == 'x264enc':
            preset_map = {
                'fast': 'veryfast',
                'medium': 'medium',
                'slow': 'slow'
            }
            props.append(f'speed-preset={preset_map[self.preset]}')

        # x265enc
        elif encoder_name == 'x265enc':
            preset_map = {
                'fast': 'veryfast',
                'medium': 'medium',
                'slow': 'slow'
            }
            props.append(f'speed-preset={preset_map[self.preset]}')

        # vp9enc
        elif encoder_name == 'vp9enc':
            # cpu-used: 0=slowest/best, 5=fastest/worst
            cpu_used_map = {
                'fast': 4,
                'medium': 2,
                'slow': 0
            }
            props.append(f'cpu-used={cpu_used_map[self.preset]}')
            props.append('deadline=1')  # 1 = good quality

        # vp8enc
        elif encoder_name == 'vp8enc':
            cpu_used_map = {
                'fast': 4,
                'medium': 2,
                'slow': 0
            }
            props.append(f'cpu-used={cpu_used_map[self.preset]}')

        return ' '.join(props) if props else ''

    def _build_pipeline(self) -> str:
        """Build gst-launch-1.0 pipeline string."""
        pipeline_parts = []

        # Use uridecodebin for automatic decoding
        uri = f"file://{self.input_file.resolve()}"
        pipeline_parts.append(f'uridecodebin uri="{uri}" name=dec')

        # Video branch
        video_elements = []

        video_encoder = self._get_video_encoder_element()
        using_vaapi = video_encoder and video_encoder.startswith('va')

        # Video processing
        if video_encoder:
            # Video encoding pipeline
            video_elements.append('videoconvert')

            # Resolution scaling
            if self.resolution:
                try:
                    width, height = self.resolution.split('x')
                    video_elements.append('videoscale')
                    video_elements.append(f'video/x-raw,width={width},height={height}')
                except ValueError:
                    print(f"Warning: Invalid resolution format '{self.resolution}', expected WIDTHxHEIGHT", file=sys.stderr)

            # Video encoder with properties
            encoder_props = self._get_encoder_properties(video_encoder)
            if encoder_props:
                video_elements.append(f'{video_encoder} {encoder_props}')
            else:
                video_elements.append(video_encoder)

        video_elements.append('queue')
        video_branch = 'dec. ! ' + ' ! '.join(video_elements) + ' ! mux.'

        # Audio branch
        audio_elements = []

        audio_encoder = self._get_audio_encoder_element()

        if audio_encoder:
            # Audio encoding pipeline
            audio_elements.append('audioconvert')
            audio_elements.append('audioresample')
            audio_elements.append(audio_encoder)

        audio_elements.append('queue')
        audio_branch = 'dec. ! ' + ' ! '.join(audio_elements) + ' ! mux.'

        # Muxer
        muxer_part = f'{self.muxer} name=mux'

        # Sink
        sink_part = f'mux. ! filesink location="{self.output_file}"'

        # Combine all parts
        pipeline = ' '.join([
            ' '.join(pipeline_parts),
            video_branch,
            audio_branch,
            muxer_part,
            sink_part
        ])

        return pipeline

    def remux(self, verbose: bool = False, overwrite: bool = False) -> bool:
        """
        Perform the remuxing operation.

        Args:
            verbose: Show detailed gst-launch output
            overwrite: Overwrite output file if it exists

        Returns:
            True if successful, False otherwise
        """
        if not self.check_gstreamer():
            print("Error: gst-launch-1.0 is not installed or not in PATH", file=sys.stderr)
            return False

        # Check if output file exists
        if self.output_file.exists() and not overwrite:
            print(f"Error: Output file already exists: {self.output_file}", file=sys.stderr)
            print("Use --overwrite flag to overwrite existing files", file=sys.stderr)
            return False

        # Get total duration for progress calculation
        duration_seconds = 0
        info = self.get_video_info()
        if info and 'duration' in info:
            duration_seconds = info['duration']

        video_encoder = self._get_video_encoder_element()
        audio_encoder = self._get_audio_encoder_element()
        using_vaapi = video_encoder and video_encoder.startswith('va')

        print(f"Remuxing: {self.input_file.name} -> {self.output_file.name}")
        print(f"Format: {self.input_file.suffix} -> .{self.output_format} (muxer: {self.muxer})")

        if video_encoder:
            print(f"Video codec: {video_encoder} (preset: {self.preset})")
            if using_vaapi and self.vaapi_device:
                print(f"VAAPI device: {self.vaapi_device}")
            if self.resolution:
                print(f"Resolution: {self.resolution}")
        else:
            print("Video codec: copy (no re-encoding)")

        if audio_encoder:
            print(f"Audio codec: {audio_encoder}")
        else:
            print("Audio codec: copy (no re-encoding)")

        # Build pipeline
        pipeline = self._build_pipeline()

        # Build command
        quiet_flag = '-q' if not verbose else ''
        cmd = f'gst-launch-1.0 {quiet_flag} {pipeline}'.strip()

        # Add VAAPI device environment variable if needed
        env = os.environ.copy()
        if using_vaapi and self.vaapi_device:
            env['LIBVA_DRIVER_NAME'] = 'iHD'  # or 'i965' for older Intel GPUs
            # Note: VAAPI device path is typically set via GST_VAAPI_DRM_DEVICE or element property
            # For simplicity, we'll use the default device selection

        if verbose:
            print(f"\nCommand: {cmd}\n")

        try:
            # Run gst-launch
            if verbose:
                # Verbose mode - show all output
                result = subprocess.run(cmd, env=env, shell=True, check=True)
            else:
                # Run with progress monitoring
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )

                # GStreamer progress is harder to parse from gst-launch, so we'll use a simpler approach
                # Monitor stderr for any output and show a simple spinner or status
                stderr_output = []
                import time
                start_time = time.time()

                print()  # New line before progress

                # Simple progress indicator
                spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
                spinner_idx = 0

                while True:
                    # Check if process is still running
                    retcode = process.poll()
                    if retcode is not None:
                        break

                    # Read any available stderr (non-blocking would be better, but this works)
                    # We'll just show a spinner for now
                    elapsed = time.time() - start_time
                    print(f"\r{spinner[spinner_idx % len(spinner)]} Processing... ({elapsed:.1f}s elapsed)", end='', flush=True)
                    spinner_idx += 1
                    time.sleep(0.1)

                # Capture any remaining output
                stdout, stderr = process.communicate()
                if stderr:
                    stderr_output.append(stderr)

                print()  # New line after progress

                if process.returncode != 0:
                    print(f"\nError: gst-launch exited with code {process.returncode}", file=sys.stderr)
                    if stderr_output:
                        print("\n--- GStreamer Error Output ---", file=sys.stderr)
                        print(''.join(stderr_output), file=sys.stderr)
                        print("--- End of Error Output ---\n", file=sys.stderr)
                    return False

            print(f"✓ Successfully created: {self.output_file}")

            # Show file sizes
            if self.output_file.exists():
                input_size = self.input_file.stat().st_size
                output_size = self.output_file.stat().st_size
                print(f"  Input size:  {self._format_size(input_size)}")
                print(f"  Output size: {self._format_size(output_size)}")
            else:
                print("Warning: Output file was not created", file=sys.stderr)
                return False

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error during remuxing: {e}", file=sys.stderr)
            if hasattr(e, 'stderr') and e.stderr:
                print(e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr, file=sys.stderr)
            return False
        except KeyboardInterrupt:
            print("\nOperation cancelled by user", file=sys.stderr)
            # Try to kill the process
            if 'process' in locals():
                process.terminate()
                process.wait()
            return False

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='Convert video files between container formats using GStreamer (gst-launch-1.0)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert MP4 to WebM via output filename
  %(prog)s input.mp4 -o output.webm

  # Convert using -f flag to specify format
  %(prog)s input.mp4 -f mkv

  # Convert to MP4 with H.264 video codec
  %(prog)s input.mkv -f mp4 --video-codec libx264

  # Convert to WebM with VP9 video and Opus audio
  %(prog)s input.mp4 -o output.webm --video-codec libvpx-vp9 --audio-codec libopus

  # Re-encode video to H.265 but copy audio
  %(prog)s input.mp4 -f mp4 --video-codec libx265 -o output_h265.mp4 --overwrite

  # Use Intel VAAPI hardware encoding for VP9 (WebM) with fast preset
  %(prog)s input.mp4 -f webm --video-codec vp9_vaapi --audio-codec libopus --vaapi-device /dev/dri/renderD129 --preset fast

  # Use Intel VAAPI hardware encoding for H.264 with slow preset (higher quality)
  %(prog)s input.mkv -f mp4 --video-codec h264_vaapi --vaapi-device /dev/dri/renderD128 --preset slow

  # Software VP9 encoding with fast preset
  %(prog)s input.mp4 -f webm --video-codec libvpx-vp9 --audio-codec libopus --preset fast

  # Scale to 720p with VAAPI VP9 encoding
  %(prog)s input.mp4 -f webm --video-codec vp9_vaapi --audio-codec libopus --vaapi-device /dev/dri/renderD129 --resolution 1280x720

  # Just copy streams without format change
  %(prog)s input.avi -o output_copy.avi

Supported formats:
  mp4, mkv, webm, avi, mov, ogv, ogg, flv, ts, 3gp

Common codecs:
  Video (Software): libx264 (H.264), libx265 (H.265/HEVC), libvpx-vp9 (VP9), libvpx (VP8)
  Video (Intel VAAPI): h264_vaapi, hevc_vaapi, vp9_vaapi, vp8_vaapi
  Audio: aac, libopus, libvorbis, libmp3lame, ac3

Note:
  - Output files are saved to the current working directory by default
  - Output format is determined by: -o extension, -f flag, or input extension
  - VAAPI encoders require --vaapi-device (check available devices: ls /dev/dri/)
  - Codec compatibility depends on the target container format
  - Requires gst-launch-1.0 and gst-discoverer-1.0 (part of GStreamer)
        """
    )

    parser.add_argument(
        'input',
        help='Input video file'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file path (if not specified, output saves to current directory with input filename)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed gst-launch output'
    )

    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite output file if it exists'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Show input file information and exit (does not perform remuxing)'
    )

    parser.add_argument(
        '--video-codec',
        help='Video codec to use (e.g., libx264, libx265, libvpx-vp9). If not specified, video stream is copied without re-encoding.'
    )

    parser.add_argument(
        '--audio-codec',
        help='Audio codec to use (e.g., aac, libopus, libvorbis). If not specified, audio stream is copied without re-encoding.'
    )

    parser.add_argument(
        '-f', '--format',
        dest='output_format',
        help='Output container format (e.g., mp4, mkv, webm).'
    )

    parser.add_argument(
        '--vaapi-device',
        help='VAAPI device path for Intel hardware acceleration (e.g., /dev/dri/renderD128 or /dev/dri/renderD129). Required when using VAAPI encoders like vp9_vaapi.'
    )

    parser.add_argument(
        '--preset',
        choices=['fast', 'medium', 'slow'],
        default='medium',
        help='Encoding speed/quality preset (default: medium). Fast = faster encoding/lower quality, Slow = slower encoding/higher quality.'
    )

    parser.add_argument(
        '--resolution',
        help='Output resolution in WIDTHxHEIGHT format (e.g., 1920x1080, 1280x720). If not specified, keeps original resolution.'
    )

    args = parser.parse_args()

    try:
        remuxer = VideoRemuxer(args.input, output_file=args.output, output_format=args.output_format,
                              video_codec=args.video_codec, audio_codec=args.audio_codec,
                              vaapi_device=args.vaapi_device, preset=args.preset,
                              resolution=args.resolution)

        # Show video info if requested
        if args.info:
            print("Input file information:")
            info = remuxer.get_video_info()
            if info:
                if 'duration' in info:
                    print(f"  Duration: {info['duration']:.2f} seconds")
                print(f"  Streams: {len(info.get('streams', []))}")
                for i, stream in enumerate(info.get('streams', [])):
                    codec_type = stream.get('codec_type', 'unknown')
                    codec_name = stream.get('codec_name', 'unknown')
                    print(f"    Stream {i}: {codec_type} ({codec_name})")
            print()
            sys.exit(0)  # Exit after showing info, don't perform remux

        # Perform remuxing
        success = remuxer.remux(verbose=args.verbose, overwrite=args.overwrite)
        sys.exit(0 if success else 1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
