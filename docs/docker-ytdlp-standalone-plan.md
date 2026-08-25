# Docker yt-dlp Standalone Plan

## Goal

Use the official standalone `yt-dlp` binary in the Docker image instead of installing `yt-dlp` through Python and `pip`.

## Decisions

- Download `yt-dlp` in a dedicated build stage.
- Verify the binary with the official `SHA2-256SUMS` file.
- Use architecture-specific Linux assets:
  - `linux/amd64`: `yt-dlp_linux`
  - `linux/arm64`: `yt-dlp_linux_aarch64`
- Remove Python, virtualenv, pip, and Node.js from the final runtime image.
- Keep only runtime dependencies needed by the Go app, TLS, FFmpeg, and `yt-dlp`.

## Validation

- Run `yt-dlp --version` during image build.
- Build the Docker image locally.
- Run the container healthcheck command from the built image.
- Keep the backend fallback resolver unchanged so local/non-release builds still have a verified download path.
