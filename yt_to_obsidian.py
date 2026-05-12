#!/usr/bin/env python3
"""
YouTube Transcript → Obsidian
Fetches YouTube transcripts and saves them as markdown notes in your Obsidian vault.

Features:
  - Single, Batch, and Channel modes (toggle anytime)
  - Subfolders per channel
  - Video duration in note metadata
  - Timestamps preserved in transcript
  - Channel mode fetches every video from a channel (no API key needed)
"""

import sys
import os
import re
import time
import random
from datetime import datetime

try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
except ImportError:
    print("\n[ERROR] Missing dependency. Run this first:")
    print("  pip install youtube-transcript-api requests yt-dlp")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("\n[ERROR] Missing dependency. Run this first:")
    print("  pip install youtube-transcript-api requests yt-dlp")
    sys.exit(1)

try:
    import yt_dlp
except ImportError:
    print("\n[ERROR] yt-dlp not installed. Run this first:")
    print("  pip install yt-dlp")
    sys.exit(1)


# ── Configuration ─────────────────────────────────────────────────────────────

VAULT_PATH = r"C:\Path\To\Your\Obsidian\Vault\YouTube Transcripts"

# Delay between requests to avoid YouTube rate limiting (in seconds)
# Randomized so it looks more like human browsing behavior
DELAY_MIN = 60
DELAY_MAX = 90

# ──────────────────────────────────────────────────────────────────────────────


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    if re.match(r"^[0-9A-Za-z_-]{11}$", url.strip()):
        return url.strip()
    return None


def is_channel_url(url: str) -> bool:
    """Detect if a URL points to a YouTube channel rather than a video."""
    patterns = [
        r"youtube\.com\/@",
        r"youtube\.com\/channel\/",
        r"youtube\.com\/c\/",
        r"youtube\.com\/user\/",
    ]
    return any(re.search(p, url) for p in patterns)


def get_channel_video_ids(channel_url: str) -> tuple[list[str], str]:
    """
    Use yt-dlp to extract all video IDs from a channel.
    Returns (video_ids, channel_name).
    """
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "no_warnings": True,
    }

    print("  Scanning channel for videos (this may take a moment)...", flush=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    channel_name = info.get("channel") or info.get("uploader") or "Unknown Channel"
    entries = info.get("entries", [])

    video_ids = []
    for entry in entries:
        if entry is None:
            continue
        if entry.get("_type") == "playlist":
            for sub in entry.get("entries", []):
                if sub and sub.get("id"):
                    video_ids.append(sub["id"])
        elif entry.get("id"):
            video_ids.append(entry["id"])

    return video_ids, channel_name


def get_video_metadata(video_id: str) -> tuple[str, str]:
    """Fetch video title and channel name via oEmbed (no API key needed)."""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", f"YouTube Video ({video_id})")
            channel = data.get("author_name", "")
            return title, channel
    except Exception:
        pass
    return f"YouTube Video ({video_id})", ""


def sanitize_filename(name: str) -> str:
    """Remove characters that are invalid in Windows filenames."""
    invalid = r'\/:*?"<>|'
    for ch in invalid:
        name = name.replace(ch, "")
    name = name.strip(". ")
    return name[:100]


def format_duration(seconds: float) -> str:
    """Convert seconds to human-readable duration string."""
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_timestamp(seconds: float) -> str:
    """Convert seconds to [HH:MM:SS] or [MM:SS] timestamp string."""
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours > 0:
        return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"
    else:
        return f"[{minutes:02d}:{secs:02d}]"


def get_transcript_entries(video_id: str) -> tuple[list[dict], str]:
    """
    Fetch transcript entries with timestamps.
    Returns (entries, language) where each entry has 'start' and 'text'.
    Uses new youtube-transcript-api v1.0+ style only.
    """
    api = YouTubeTranscriptApi()

    # Try English first
    try:
        fetched = api.fetch(video_id, languages=["en", "en-US", "en-GB"])
        entries = [{"start": s.start, "text": s.text.replace("\n", " ")} for s in fetched]
        return entries, "English"
    except Exception:
        pass

    # Fall back to any available language
    fetched = api.fetch(video_id)
    entries = [{"start": s.start, "text": s.text.replace("\n", " ")} for s in fetched]
    return entries, "Auto-detected"


def build_transcript_text(entries: list[dict]) -> tuple[str, float]:
    """
    Build formatted transcript string with timestamps.
    Returns (transcript_text, total_duration_seconds).
    """
    lines = [f"{format_timestamp(e['start'])} {e['text']}" for e in entries]
    duration = entries[-1]["start"] if entries else 0
    return "\n".join(lines), duration


def format_note(title: str, channel: str, video_id: str, transcript: str,
                language: str, duration: float) -> str:
    """Format the Obsidian markdown note with YAML frontmatter for Dataview and Smart Connections."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    date = datetime.now().strftime("%Y-%m-%d")
    time_saved = datetime.now().strftime("%H:%M")
    display_title = f"{title} - {channel}" if channel else title
    duration_str = format_duration(duration) if duration else "Unknown"

    return f"""---
title: "{title.replace('"', "'")}"
channel: "{channel}"
source: "{url}"
duration: "{duration_str}"
date_saved: {date}
language: "{language}"
type: youtube-transcript
---

# {display_title}

## Transcript

{transcript}
"""


def save_note(content: str, channel: str, filename: str) -> str:
    """
    Save the note into a channel subfolder within the vault.
    Returns the full file path.
    """
    folder = os.path.join(VAULT_PATH, sanitize_filename(channel)) if channel else VAULT_PATH
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    # Skip if file already exists — return None to signal duplicate
    if os.path.exists(filepath):
        return None

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def process_video(video_id: str, label: str = "") -> bool:
    """
    Process a single video. Returns True on success, "exists" if already saved, False on failure.
    label is used for batch/channel display e.g. '[2/5]'.
    """
    prefix = f"  {label} " if label else "  "

    print(f"{prefix}Fetching title...", end=" ", flush=True)
    title, channel = get_video_metadata(video_id)
    display = f"{title} - {channel}" if channel else title
    print(f"'{display}'")

    print(f"{prefix}Fetching transcript...", end=" ", flush=True)
    try:
        entries, language = get_transcript_entries(video_id)
        transcript, duration = build_transcript_text(entries)
        word_count = len(transcript.split())
        print(f"done ({word_count:,} words, {format_duration(duration)})")
    except TranscriptsDisabled:
        print("\n  [!] Transcripts are disabled for this video. Skipping.")
        return False
    except NoTranscriptFound:
        print("\n  [!] No transcript found for this video. Skipping.")
        return False
    except Exception as e:
        print(f"\n  [!] Error: {e}. Skipping.")
        return False

    note = format_note(title, channel, video_id, transcript, language, duration)
    base_title = f"{title} - {channel}" if channel else title
    filename = sanitize_filename(base_title) + ".md"

    try:
        filepath = save_note(note, channel, filename)
        if filepath is None:
            print(f"{prefix}— Already exists, skipping.")
            return "exists"
        print(f"{prefix}✓ Saved: {filepath}")
        return True
    except Exception as e:
        print(f"{prefix}[!] Error saving: {e}")
        return False


def run_single_mode() -> str:
    """Interactive single-URL mode. Returns next mode or 'quit'."""
    print("\n  Mode: Single  —  type 'batch' or 'channel' to switch, 'q' to quit\n")
    while True:
        raw = input("Paste YouTube URL: ").strip()

        if raw.lower() in ("q", "quit", "exit"):
            return "quit"
        if raw.lower() in ("batch", "channel"):
            return raw.lower()
        if not raw:
            continue

        video_id = extract_video_id(raw)
        if not video_id:
            print("  [!] Couldn't find a valid YouTube video ID. Try again.\n")
            continue

        print(f"  Video ID: {video_id}")
        process_video(video_id)
        print()


def run_batch_mode() -> str:
    """Batch mode — paste multiple URLs, process all at once. Returns next mode or 'quit'."""
    print("\n  Mode: Batch  —  type 'single' or 'channel' to switch, 'q' to quit")
    print("  Paste one URL per line. Type 'go' when done.\n")

    while True:
        urls = []
        while True:
            raw = input("  URL (or 'go'): ").strip()
            if raw.lower() in ("q", "quit", "exit"):
                return "quit"
            if raw.lower() in ("single", "channel"):
                return raw.lower()
            if raw.lower() == "go":
                break
            if raw:
                urls.append(raw)

        if not urls:
            print("  [!] No URLs entered.\n")
            continue

        jobs = []
        for url in urls:
            vid = extract_video_id(url)
            if vid:
                jobs.append(vid)
            else:
                print(f"  [!] Skipping invalid URL: {url}")

        if not jobs:
            print("  [!] No valid URLs found.\n")
            continue

        print(f"\n  Processing {len(jobs)} video(s)...\n")
        print("  (Press Ctrl+C at any time to stop and see a summary)\n")
        success = 0
        existing = 0
        failed = 0
        try:
            for i, video_id in enumerate(jobs, 1):
                print(f"  [{i}/{len(jobs)}] Video ID: {video_id}")
                result = process_video(video_id, label=f"[{i}/{len(jobs)}]")
                if result is True:
                    success += 1
                elif result == "exists":
                    existing += 1
                else:
                    failed += 1
                if i < len(jobs):
                    delay = random.uniform(DELAY_MIN, DELAY_MAX)
                    print(f"  Waiting {delay:.1f}s before next request...")
                    time.sleep(delay)
                print()
        except KeyboardInterrupt:
            print(f"\n\n  ⚠ Interrupted by user.")

        parts = [f"{success} saved"]
        if existing: parts.append(f"{existing} already existed")
        if failed: parts.append(f"{failed} failed")
        print(f"  ✓ Batch complete: {', '.join(parts)}.\n")


def run_channel_mode() -> str:
    """Channel mode — paste a channel URL and process every video. Returns next mode or 'quit'."""
    print("\n  Mode: Channel  —  type 'single' or 'batch' to switch, 'q' to quit\n")

    while True:
        raw = input("Paste YouTube channel URL: ").strip()

        if raw.lower() in ("q", "quit", "exit"):
            return "quit"
        if raw.lower() in ("single", "batch"):
            return raw.lower()
        if not raw:
            continue

        if not is_channel_url(raw):
            print("  [!] That doesn't look like a channel URL.")
            print("      Expected formats: youtube.com/@handle, /channel/ID, /c/name\n")
            continue

        try:
            video_ids, channel_name = get_channel_video_ids(raw)
        except Exception as e:
            print(f"  [!] Error fetching channel: {e}\n")
            continue

        if not video_ids:
            print("  [!] No videos found for that channel.\n")
            continue

        print(f"  Found {len(video_ids)} videos from '{channel_name}'")

        confirm = input(f"  Proceed with all {len(video_ids)} videos? (y/n): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.\n")
            continue

        print(f"\n  Processing {len(video_ids)} video(s)...\n")
        print("  (Press Ctrl+C at any time to stop and see a summary)\n")
        success = 0
        existing = 0
        failed = 0
        try:
            for i, video_id in enumerate(video_ids, 1):
                print(f"  [{i}/{len(video_ids)}] Video ID: {video_id}")
                result = process_video(video_id, label=f"[{i}/{len(video_ids)}]")
                if result is True:
                    success += 1
                elif result == "exists":
                    existing += 1
                else:
                    failed += 1
                if i < len(video_ids):
                    delay = random.uniform(DELAY_MIN, DELAY_MAX)
                    print(f"  Waiting {delay:.1f}s before next request...")
                    time.sleep(delay)
                print()
        except KeyboardInterrupt:
            print(f"\n\n  ⚠ Interrupted by user.")

        parts = [f"{success} saved"]
        if existing: parts.append(f"{existing} already existed")
        if failed: parts.append(f"{failed} failed")
        print(f"  ✓ Channel complete: {', '.join(parts)}.\n")


def main():
    print("=" * 50)
    print("  YouTube Transcript → Obsidian")
    print("=" * 50)
    print(f"  Vault: {VAULT_PATH}")
    print("\n  Choose mode:")
    print("  [1] Single  — process one URL at a time")
    print("  [2] Batch   — paste multiple URLs, process all at once")
    print("  [3] Channel — paste a channel URL, get every video")

    while True:
        choice = input("\n  Enter 1, 2, or 3: ").strip()
        if choice in ("1", "single"):
            mode = "single"
            break
        elif choice in ("2", "batch"):
            mode = "batch"
            break
        elif choice in ("3", "channel"):
            mode = "channel"
            break
        else:
            print("  Please enter 1, 2, or 3.")

    while True:
        if mode == "single":
            result = run_single_mode()
        elif mode == "batch":
            result = run_batch_mode()
        elif mode == "channel":
            result = run_channel_mode()
        else:
            result = "quit"

        if result == "quit":
            print("Bye!")
            break
        else:
            mode = result


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBye!")
