# yt-dlp Packaging Plan

## Goal

Ensure desktop releases can use `yt-dlp` without requiring users to install it on their systems.

## Decisions

- Use official standalone `yt-dlp` binaries instead of installing Python packages on user machines.
- Package `yt-dlp` in Linux and Windows desktop releases.
- Keep an automatic download/cache fallback for local builds and damaged/missing release files.
- Verify downloaded binaries with the official `SHA2-256SUMS` file.

## Backend Design

- Add a `CheckAndDownloadYTDLP` resolver similar to `CheckAndDownloadFFmpeg`.
- Resolve `yt-dlp` in this order:
  - executable directory
  - user cache directory
  - system `PATH`
  - verified download from GitHub releases
- Validate candidate binaries by running `yt-dlp --version`.
- Replace direct `exec.LookPath("yt-dlp")` calls with the resolver.

## Packaging

- Linux DEB includes `/opt/youtube-mp3-downloader/yt-dlp`.
- Windows installer includes `yt-dlp.exe` next to the application executable.
- Release workflows download and checksum-verify the selected official asset before packaging.

## Tests

- Asset selection by OS/architecture.
- Checksum parsing.
- Resolver preference for bundled, cached, system, then downloaded binaries.
- Release workflow checks for installed `yt-dlp` binaries.

## Documentation

- README documents bundled desktop `yt-dlp` and automatic fallback download for local builds.
