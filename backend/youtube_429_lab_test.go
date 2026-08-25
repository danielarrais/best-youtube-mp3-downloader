package main

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/kkdai/youtube/v2"
)

const youtube429LabURL = "https://www.youtube.com/watch?v=ImD7KZ7cfek"

func TestYouTube429LabDownloadAudioAndVideo(t *testing.T) {
	if os.Getenv("YOUTUBE_429_LAB") == "" {
		t.Skip("set YOUTUBE_429_LAB=1 to run this lab integration test")
	}

	t.Run("audio", func(t *testing.T) {
		app := newYouTube429LabApp(t)
		item := newYouTube429LabItem("audio", MediaTypeAudio)

		registerYouTube429LabItem(app, item)
		app.processDownload(context.Background(), item)
		assertYouTube429LabCompleted(t, app, item, ".mp3")
	})

	t.Run("video", func(t *testing.T) {
		app := newYouTube429LabApp(t)
		formats, err := app.GetVideoFormats(youtube429LabURL)
		if err != nil {
			t.Fatalf("GetVideoFormats error: %v", err)
		}
		format, ok := liveMuxFormat(formats.Formats)
		if !ok {
			t.Fatal("no compatible video format available for lab test")
		}

		item := newYouTube429LabItem("video", MediaTypeVideo)
		item.VideoFormat = &format

		registerYouTube429LabItem(app, item)
		app.processDownload(context.Background(), item)
		assertYouTube429LabCompleted(t, app, item, "."+format.Extension)
	})
}

func TestYouTube429LabClientMatrix(t *testing.T) {
	if os.Getenv("YOUTUBE_429_LAB") == "" {
		t.Skip("set YOUTUBE_429_LAB=1 to run this lab integration test")
	}

	tests := []struct {
		name   string
		client youtube.ClientInfo
	}{
		{name: "android_vr", client: youtube.AndroidVRClient},
		{name: "android", client: youtube.AndroidClient},
		{name: "ios", client: youtube.IOSClient},
		{name: "web", client: youtube.WebClient},
		{name: "embedded", client: youtube.EmbeddedClient},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			clientInfo := test.client
			previousDefaultClient := youtube.DefaultClient
			youtube.DefaultClient = clientInfo
			defer func() { youtube.DefaultClient = previousDefaultClient }()

			session := NewYouTubeSession()
			video, err := session.GetVideo(context.Background(), youtube429LabURL)
			if err != nil {
				t.Fatalf("GetVideoContext error: %v", err)
			}
			if video.Title == "" || len(video.Formats) == 0 {
				t.Fatalf("unexpected video payload: title=%q formats=%d", video.Title, len(video.Formats))
			}
			t.Logf("title=%q formats=%d", video.Title, len(video.Formats))
		})
	}
}

func newYouTube429LabApp(t *testing.T) *App {
	t.Helper()

	root := t.TempDir()
	dataDir := filepath.Join(root, "data")
	downloadDir := filepath.Join(root, "downloads")
	if err := os.MkdirAll(dataDir, 0755); err != nil {
		t.Fatalf("MkdirAll(data) error: %v", err)
	}
	if err := os.MkdirAll(downloadDir, 0755); err != nil {
		t.Fatalf("MkdirAll(downloads) error: %v", err)
	}

	app := NewAppWithPaths(dataDir, downloadDir)
	if err := os.MkdirAll(app.cacheDir, 0755); err != nil {
		t.Fatalf("MkdirAll(cache) error: %v", err)
	}
	return app
}

func newYouTube429LabItem(id string, mediaType MediaType) *DownloadItem {
	return &DownloadItem{
		ID:        id,
		URL:       youtube429LabURL,
		Quality:   "192k",
		MediaType: mediaType,
		Status:    StatusFetching,
		CreatedAt: time.Now().Format(time.RFC3339),
		StartedAt: time.Now().Format(time.RFC3339),
		Progress:  DownloadProgress{Speed: "---", ETA: "---"},
	}
}

func registerYouTube429LabItem(app *App, item *DownloadItem) {
	app.mu.Lock()
	app.items[item.ID] = item
	app.queueOrder = append(app.queueOrder, item.ID)
	app.ensureActiveMapLocked()
	app.active[item.ID] = func() {}
	app.mu.Unlock()
}

func assertYouTube429LabCompleted(t *testing.T, app *App, item *DownloadItem, wantSuffix string) {
	t.Helper()

	defer func() {
		app.mu.Lock()
		delete(app.active, item.ID)
		app.mu.Unlock()
	}()

	if item.Status == StatusFailed {
		t.Fatalf("download failed before assertions: %s", item.Error)
	}
	if item.Status != StatusCompleted {
		t.Fatalf("status = %q, want %q (error=%q)", item.Status, StatusCompleted, item.Error)
	}
	if item.FilePath == "" {
		t.Fatal("completed item did not record an output file")
	}
	if !strings.HasSuffix(strings.ToLower(item.FilePath), strings.ToLower(wantSuffix)) {
		t.Fatalf("output path = %q, want suffix %q", item.FilePath, wantSuffix)
	}
	info, err := os.Stat(item.FilePath)
	if err != nil {
		t.Fatalf("output stat error: %v", err)
	}
	if info.Size() == 0 {
		t.Fatal("output file is empty")
	}
	if item.FileSize != info.Size() {
		t.Fatalf("recorded size = %d, actual size = %d", item.FileSize, info.Size())
	}
	if item.Progress.Percent != 100 {
		t.Fatalf("progress = %v, want 100", item.Progress.Percent)
	}
	if item.Error != "" {
		t.Fatalf("completed item still has error %q", item.Error)
	}
}
