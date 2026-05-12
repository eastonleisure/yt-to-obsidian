# yt-to-obsidian

A terminal tool that fetches YouTube transcripts and saves them as structured Markdown notes directly into your Obsidian vault - no API keys, no accounts, no cost.

---

## Features

- **Three modes** - Single URL, Batch (multiple URLs), and Channel (every video from a channel)
- **Switch modes mid-session** - type `single`, `batch`, or `channel` at any prompt
- **Timestamps preserved** - every line of the transcript includes its video timestamp
- **Channel subfolders** - notes are automatically organized by channel name
- **Duplicate detection** - existing notes are skipped, never overwritten
- **YAML frontmatter** - structured metadata for Obsidian Dataview and Smart Connections
- **Graceful interruption** - press `Ctrl+C` at any time to stop and see a summary
- **Rate limit protection** - randomized 60-90 second delays between requests
- **No API key required** - uses public endpoints only

---

## Output Format

Each saved note looks like this:

```markdown
---
title: "How To Build Better Habits"
channel: "ExampleChannel"
source: "https://www.youtube.com/watch?v=xxxxxxxx"
duration: "47m 12s"
date_saved: 2026-04-01
language: "English"
type: youtube-transcript
---

# How To Build Better Habits - ExampleChannel

## Transcript

[00:00] So today we're talking about why your brain...
[00:42] The first thing you need to understand...
```

Notes are saved into channel subfolders:

```
Your Vault/
└── YouTube Transcripts/
    ├── ExampleChannel/
    │   ├── How To Build Better Habits - ExampleChannel.md
    │   └── The Science Of Deep Work - ExampleChannel.md
    └── AnotherChannel/
        └── Why Most People Never Succeed - AnotherChannel.md
```

---

## Requirements

- Python 3.10 or higher
- Windows, macOS, or Linux

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/yt-to-obsidian.git
cd yt-to-obsidian
```

**2. Install dependencies**

```bash
pip install youtube-transcript-api requests yt-dlp
```

**3. Set your vault path**

Open `yt_to_obsidian.py` and update the `VAULT_PATH` variable at the top of the file:

```python
# ── Configuration ─────────────────────────────────────────────────────────────

VAULT_PATH = r"C:\Path\To\Your\Obsidian\Vault\YouTube Transcripts"
```

Use the full path to the folder inside your vault where you want transcripts saved. The folder will be created automatically if it doesn't exist.

**Examples:**

Windows:
```python
VAULT_PATH = r"C:\Users\YourName\Documents\MyVault\YouTube Transcripts"
```

macOS / Linux:
```python
VAULT_PATH = "/Users/yourname/Documents/MyVault/YouTube Transcripts"
```

---

## Usage

**Run the script:**

```bash
python yt_to_obsidian.py
```

You'll see a mode selection menu:

```
==================================================
  YouTube Transcript → Obsidian
==================================================
  Vault: /path/to/your/vault

  Choose mode:
  [1] Single  - process one URL at a time
  [2] Batch   - paste multiple URLs, process all at once
  [3] Channel - paste a channel URL, get every video

  Enter 1, 2, or 3:
```

---

### Single Mode

Process one video at a time. Paste a URL and hit Enter.

```
Paste YouTube URL: https://www.youtube.com/watch?v=xxxxxxxx
  Video ID: xxxxxxxx
  Fetching title... 'How To Build Better Habits - ExampleChannel'
  Fetching transcript... done (8,432 words, 47m 12s)
  ✓ Saved: /path/to/vault/ExampleChannel/How To Build Better Habits - ExampleChannel.md
```

Supported URL formats:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- Raw video ID (11 characters)

---

### Batch Mode

Paste multiple URLs one per line, then type `go` to process them all.

```
  Mode: Batch - type 'single' or 'channel' to switch, 'q' to quit
  Paste one URL per line. Type 'go' when done.

  URL (or 'go'): https://www.youtube.com/watch?v=aaa
  URL (or 'go'): https://www.youtube.com/watch?v=bbb
  URL (or 'go'): https://youtu.be/ccc
  URL (or 'go'): go

  Processing 3 video(s)...
  (Press Ctrl+C at any time to stop and see a summary)

  [1/3] Fetching title... 'Video One - Channel Name'
  [1/3] Fetching transcript... done (5,210 words, 28m 4s)
  [1/3] ✓ Saved: /path/to/vault/...
  Waiting 73.4s before next request...

  ✓ Batch complete: 3 saved.
```

---

### Channel Mode

Paste a channel URL to fetch transcripts for every video on the channel.

```
Paste YouTube channel URL: https://www.youtube.com/@ChannelName

  Scanning channel for videos (this may take a moment)...
  Found 106 videos from 'Channel Name'
  Proceed with all 106 videos? (y/n): y

  Processing 106 video(s)...
  (Press Ctrl+C at any time to stop and see a summary)

  [1/106] Fetching title... 'Video Title - Channel Name'
  [1/106] Fetching transcript... done (6,100 words, 32m 18s)
  [1/106] ✓ Saved: /path/to/vault/...
  Waiting 81.2s before next request...

  ✓ Channel complete: 89 saved, 17 failed.
```

Supported channel URL formats:
- `https://www.youtube.com/@handle`
- `https://www.youtube.com/channel/CHANNEL_ID`
- `https://www.youtube.com/c/channelname`
- `https://www.youtube.com/user/username`

**Note:** Large channels (100+ videos) can take 2-3 hours due to rate limit delays. The script is designed to run unattended - start it and come back later.

---

### Switching Modes

At any prompt, type the mode name to switch without restarting:

```
Paste YouTube URL: batch
```

```
  URL (or 'go'): channel
```

```
Paste YouTube channel URL: single
```

---

### Stopping Mid-Run

Press `Ctrl+C` at any time. The script will stop immediately and show a summary of what was saved before you stopped. All files already saved remain in your vault.

```
  [23/89] Fetching transcript... done
  [23/89] ✓ Saved: ...
  Waiting 74.3s...
^C

  ⚠ Interrupted by user.
  ✓ Channel complete: 23 saved, 1 failed.

Bye!
```

---

### Re-running on a Channel

The script never overwrites existing notes. When you re-run on a channel after new videos have been posted, it skips everything already saved and only fetches new ones:

```
  ✓ Channel complete: 5 saved, 87 already existed.
```

---

## Configuration

All configuration is at the top of `yt_to_obsidian.py`:

```python
# ── Configuration ─────────────────────────────────────────────────────────────

VAULT_PATH = r"C:\Path\To\Your\Obsidian\Vault\YouTube Transcripts"

# Delay between requests to avoid YouTube rate limiting (in seconds)
DELAY_MIN = 60
DELAY_MAX = 90
```

`DELAY_MIN` and `DELAY_MAX` control the randomized wait between requests. The defaults (60-90 seconds) are conservative and safe for large runs. Lowering these increases speed but raises the risk of IP blocks from YouTube.

---

## How It Works

The script uses three public endpoints - no API keys or authentication required:

| Request | What It Does | Tool Used |
|---|---|---|
| oEmbed | Fetches video title and channel name | `requests` |
| Transcript fetch | Fetches timestamped transcript text | `youtube-transcript-api` |
| Channel scan | Lists all video IDs from a channel | `yt-dlp` |

Transcripts are read from the same public data YouTube uses to display the "Show transcript" panel on any video. The script does not download video files.

---

## Rate Limiting

YouTube may temporarily block your IP if too many requests are made in a short period. The script mitigates this with randomized delays between requests.

If you encounter an IP block:

1. **Wait 30-60 minutes** - blocks are always temporary
2. **Restart your router** - if your ISP assigns dynamic IPs, this gives you a fresh IP immediately
3. **Use a VPN** - switch servers to get a new IP instantly

The script will display a clear error message if your IP is blocked:

```
  [!] Error: YouTube is blocking requests from your IP. Skipping.
```

---

## Obsidian Integration

Notes are saved with YAML frontmatter compatible with:

- **Dataview** - query and filter your transcript library by channel, date, duration, or any other field
- **Smart Connections** - semantically search across all your transcripts using AI embeddings

Example Dataview query to list all transcripts:

```dataview
TABLE channel, duration, date_saved
FROM "YouTube Transcripts"
SORT date_saved DESC
```

Filter by channel:

```dataview
TABLE duration, date_saved
FROM "YouTube Transcripts"
WHERE channel = "ExampleChannel"
SORT date_saved DESC
```

---

## Troubleshooting

**`ModuleNotFoundError`**
Run `pip install youtube-transcript-api requests yt-dlp` and try again.

**`YouTubeTranscriptApi has no attribute 'list_transcripts'`**
Update the library: `pip install --upgrade youtube-transcript-api`

**Transcript not available for a video**
Some videos have captions disabled by the creator, or are too new for auto-captions to have been generated (allow 12-24 hours for new videos).

**IP blocked by YouTube**
Wait 30-60 minutes or restart your router. See Rate Limiting section above.

**File opens in an IDE instead of running**
Open Command Prompt manually (Windows key + R → `cmd`) and run `python yt_to_obsidian.py` directly.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `youtube-transcript-api` | ≥ 1.0.0 | Fetching transcripts |
| `requests` | any | oEmbed metadata fetch |
| `yt-dlp` | any | Channel video listing |

---

## License

MIT License. Use freely for personal use.

---

## Disclaimer

This tool is intended for personal use only. It reads publicly available transcript data from YouTube. Use responsibly and in accordance with YouTube's Terms of Service. The author is not responsible for any misuse.
