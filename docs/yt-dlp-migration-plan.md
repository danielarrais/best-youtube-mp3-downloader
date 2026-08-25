# yt-dlp Migration Plan

## Goal

Use `yt-dlp` as the default YouTube download backend while preserving:

- thumbnails
- playlist loading
- queue and persistence
- video quality selection
- final MP3 quality selection

## Architecture

1. Keep metadata and playlist logic in Go for now.
2. Move media download to `yt-dlp` by default.
3. Keep FFmpeg-based MP3 conversion, metadata, and cover embedding.
4. Keep the current Go downloader as a compatibility fallback.

## Download Strategy

1. Audio downloads use `yt-dlp` first.
2. Video downloads use `yt-dlp` first.
3. If `yt-dlp` is unavailable, fall back to the current Go stream downloader.
4. Prefer impersonation and JS runtime support when available.
5. Try browser cookies from Firefox when available.

## Audio Quality

1. Preserve the current final MP3 bitrate setting.
2. Download the best available source audio when no source is explicitly selected.
3. Add backend support for exposing available source audio qualities in a later step.

## Docker Runtime

The Docker runtime must include the tools needed by the new default path:

- `yt-dlp`
- `node`
- `python3`
- `ffmpeg`

This allows the container to use the same primary download backend as the desktop app.

## Rollout

1. Make `yt-dlp` the default backend for audio and video downloads.
2. Preserve existing API contracts for metadata, thumbnails, playlist, and selected video quality.
3. Keep the current Go downloader as a fallback path.
4. Validate backend build and Docker build.
5. Add first-class audio source selection later without breaking the current UI.
