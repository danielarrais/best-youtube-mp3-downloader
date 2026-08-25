package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestConfigFileRoundTrip(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config", "settings.json")
	want := Config{
		DownloadDir:        filepath.Join(t.TempDir(), "downloads"),
		Quality:            "160k",
		AudioBitrateTarget: "160k",
		VideoContainer:     "webm",
		VideoQuality:       "720p",
		AskAudioQuality:    false,
		AskVideoQuality:    false,
		FileDeletion:       FileDeletionKeep,
		Language:           "en-US",
		Theme:              defaultTheme,
		ParallelDownloads:  3,
	}
	if err := saveConfigFile(path, want); err != nil {
		t.Fatal(err)
	}
	got, err := loadConfigFile(path, defaultConfig(t.TempDir()))
	if err != nil {
		t.Fatal(err)
	}
	if got != want {
		t.Fatalf("loadConfigFile() = %#v, want %#v", got, want)
	}
}

func TestNormalizeConfigUsesDefaults(t *testing.T) {
	defaults := Config{
		DownloadDir:        "/downloads",
		Quality:            "192k",
		AudioBitrateTarget: "192k",
		VideoContainer:     "mp4",
		VideoQuality:       "1080p",
		AskAudioQuality:    true,
		AskVideoQuality:    true,
		FileDeletion:       FileDeletionAsk,
		Language:           "pt-BR",
		Theme:              defaultTheme,
		ParallelDownloads:  4,
	}
	got := normalizeConfig(Config{
		Quality:           "invalid",
		VideoContainer:    "invalid",
		VideoQuality:      "invalid",
		FileDeletion:      "invalid",
		Language:          "invalid",
		Theme:             "invalid",
		ParallelDownloads: -1,
	}, defaults)
	defaults.AskAudioQuality = false
	defaults.AskVideoQuality = false
	if got != defaults {
		t.Fatalf("normalizeConfig() = %#v, want %#v", got, defaults)
	}
}

func TestLoadConfigDefaultsMissingAskQualityFields(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config", "settings.json")
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(`{"download_dir":"/tmp/downloads","quality":"128k","video_container":"mp4","video_quality":"720p","file_deletion":"ask","language":"pt-BR","theme":"dark"}`), 0644); err != nil {
		t.Fatal(err)
	}
	got, err := loadConfigFile(path, defaultConfig(t.TempDir()))
	if err != nil {
		t.Fatal(err)
	}
	if got.AudioBitrateTarget != "128k" || !got.AskAudioQuality || !got.AskVideoQuality || got.ParallelDownloads != defaultParallelDownloads() {
		t.Fatalf("legacy config migration = %#v", got)
	}
}

func TestNormalizeParallelDownloadsClampsToSafeRange(t *testing.T) {
	if got := normalizeParallelDownloads(0, 3); got != 3 {
		t.Fatalf("zero parallel downloads = %d, want fallback", got)
	}
	if got := normalizeParallelDownloads(99, 3); got != maxParallelDownloads {
		t.Fatalf("large parallel downloads = %d, want %d", got, maxParallelDownloads)
	}
	if got := normalizeParallelDownloads(2, 3); got != 2 {
		t.Fatalf("valid parallel downloads = %d, want 2", got)
	}
}
