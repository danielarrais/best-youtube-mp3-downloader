package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
)

const (
	defaultVideoContainer = "mp4"
	defaultVideoQuality   = "1080p"
	defaultAudioBitrate   = "192k"
	defaultTheme          = "dark"
	maxParallelDownloads  = 8
	FileDeletionDelete    = "delete"
	FileDeletionAsk       = "ask"
	FileDeletionKeep      = "keep"
)

type Config struct {
	DownloadDir        string `json:"download_dir"`
	Quality            string `json:"quality"`
	AudioBitrateTarget string `json:"audio_bitrate_target"`
	VideoContainer     string `json:"video_container"`
	VideoQuality       string `json:"video_quality"`
	AskAudioQuality    bool   `json:"ask_audio_quality"`
	AskVideoQuality    bool   `json:"ask_video_quality"`
	FileDeletion       string `json:"file_deletion"`
	Language           string `json:"language"`
	Theme              string `json:"theme"`
	ParallelDownloads  int    `json:"parallel_downloads"`
}

func defaultConfig(home string) Config {
	return Config{
		DownloadDir:        filepath.Join(home, "Downloads", "YouTube-MP3"),
		Quality:            defaultAudioBitrate,
		AudioBitrateTarget: defaultAudioBitrate,
		VideoContainer:     defaultVideoContainer,
		VideoQuality:       defaultVideoQuality,
		AskAudioQuality:    true,
		AskVideoQuality:    true,
		FileDeletion:       FileDeletionAsk,
		Language:           "pt-BR",
		Theme:              defaultTheme,
		ParallelDownloads:  defaultParallelDownloads(),
	}
}

func defaultParallelDownloads() int {
	cores := runtime.NumCPU()
	if cores < 2 {
		return 1
	}
	return normalizeParallelDownloads(cores/2, 1)
}

func normalizeParallelDownloads(value, fallback int) int {
	if fallback < 1 {
		fallback = 1
	}
	if fallback > maxParallelDownloads {
		fallback = maxParallelDownloads
	}
	if value < 1 {
		return fallback
	}
	if value > maxParallelDownloads {
		return maxParallelDownloads
	}
	return value
}

func normalizeConfig(config, defaults Config) Config {
	if config.DownloadDir == "" {
		config.DownloadDir = defaults.DownloadDir
	}
	switch config.Quality {
	case "128k", "160k", "192k":
	default:
		config.Quality = defaults.Quality
	}
	if config.AudioBitrateTarget == "" {
		config.AudioBitrateTarget = config.Quality
	}
	switch config.AudioBitrateTarget {
	case "128k", "160k", "192k":
	default:
		config.AudioBitrateTarget = defaults.AudioBitrateTarget
	}
	config.Quality = config.AudioBitrateTarget
	switch config.VideoContainer {
	case "mp4", "webm", "mkv":
	default:
		config.VideoContainer = defaults.VideoContainer
	}
	if config.VideoContainer == "" {
		config.VideoContainer = defaultVideoContainer
	}
	switch config.VideoQuality {
	case "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p":
	default:
		config.VideoQuality = defaults.VideoQuality
	}
	if config.VideoQuality == "" {
		config.VideoQuality = defaultVideoQuality
	}
	switch config.FileDeletion {
	case FileDeletionDelete, FileDeletionAsk, FileDeletionKeep:
	default:
		config.FileDeletion = defaults.FileDeletion
	}
	if config.FileDeletion == "" {
		config.FileDeletion = FileDeletionAsk
	}
	if config.Language != "en-US" && config.Language != "pt-BR" {
		config.Language = defaults.Language
	}
	switch config.Theme {
	case "dark", "light":
	default:
		config.Theme = defaults.Theme
	}
	if config.Theme == "" {
		config.Theme = defaultTheme
	}
	config.ParallelDownloads = normalizeParallelDownloads(config.ParallelDownloads, defaults.ParallelDownloads)
	return config
}

func loadConfigFile(path string, defaults Config) (Config, error) {
	data, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return defaults, nil
	}
	if err != nil {
		return Config{}, err
	}

	var config Config
	if err := json.Unmarshal(data, &config); err != nil {
		return Config{}, fmt.Errorf("configuração inválida: %w", err)
	}
	var raw map[string]json.RawMessage
	if err := json.Unmarshal(data, &raw); err == nil {
		if _, ok := raw["ask_audio_quality"]; !ok {
			config.AskAudioQuality = defaults.AskAudioQuality
		}
		if _, ok := raw["ask_video_quality"]; !ok {
			config.AskVideoQuality = defaults.AskVideoQuality
		}
	}
	return normalizeConfig(config, defaults), nil
}

func saveConfigFile(path string, config Config) error {
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0644)
}
