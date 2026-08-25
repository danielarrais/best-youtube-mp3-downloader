# Go Backend Refactor Plan

## Goals

- Stop using the local `backend/third_party/youtube-v2` fork.
- Resolve `github.com/kkdai/youtube/v2` from the normal Go module cache.
- Keep current download, metadata, playlist, queue, and UI behavior unchanged.
- Apply small Go code quality refactors that reduce coupling without changing features.

## Steps

- Remove the `replace github.com/kkdai/youtube/v2 => ./third_party/youtube-v2` directive.
- Run `go mod tidy` from `backend/`.
- Delete `backend/third_party/youtube-v2` after the external module resolves correctly.
- Encapsulate download lookup inside `App` instead of reading `App` internals from the web handler.
- Make retry failure explicit by returning an error from `RetryDownload`.
- Centralize common download status predicates.
- Keep YouTube client global configuration isolated behind a single helper.
- Run backend tests after the refactor.
