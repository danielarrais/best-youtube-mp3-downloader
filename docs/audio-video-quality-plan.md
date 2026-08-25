# Audio and Video Quality Plan

## Goals

- Use an audio target bitrate setting instead of treating the setting as a fixed YouTube format.
- Let users choose whether the app should always ask for audio and video quality.
- Default both "ask quality" settings to enabled.
- When not asking, automatically choose the closest available format to the configured target.
- Show the final file size in the queue after conversion/download completes.

## Audio

- Store a target bitrate in config, not a YouTube `format_id`.
- Supported initial targets: `128k`, `160k`, `192k`.
- When formats are available, choose the audio format with the bitrate closest to the target.
- Tie-breakers: higher bitrate first, then stable label ordering.
- If `ask_audio_quality` is true, open the audio source modal and preselect the closest format.
- If `ask_audio_quality` is false, skip the modal and enqueue the closest format automatically.

## Video

- Keep the existing target resolution setting.
- Add `ask_video_quality` to control whether the video format modal opens.
- If `ask_video_quality` is true, open the modal and preselect the closest format.
- If `ask_video_quality` is false, skip the modal and enqueue the closest format automatically.

## UI

- Settings should show the video quality select followed by a checkbox to always ask for video quality.
- Settings should show the audio bitrate target select followed by a checkbox to always ask for audio quality.
- Queue cards should show the final file size when an item is completed or skipped and `file_size` is available.

## Backend

- Add config fields for `audio_bitrate_target`, `ask_audio_quality`, and `ask_video_quality`.
- Normalize missing config values to safe defaults.
- Preserve existing persisted configs by deriving `audio_bitrate_target` from the legacy `quality` field when present.
