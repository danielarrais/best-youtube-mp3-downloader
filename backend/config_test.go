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
	}
	got := normalizeConfig(Config{
		Quality:        "invalid",
		VideoContainer: "invalid",
		VideoQuality:   "invalid",
		FileDeletion:   "invalid",
		Language:       "invalid",
		Theme:          "invalid",
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
	if got.AudioBitrateTarget != "128k" || !got.AskAudioQuality || !got.AskVideoQuality {
		t.Fatalf("legacy config migration = %#v", got)
	}
}
