package main

import (
	"context"
	"os"
	"path/filepath"
	"testing"
)

const youtubeProgressLabURL = "https://www.youtube.com/watch?v=Oi0LJg-4A6o"

func TestParseYTDLPProgressTemplateLine(t *testing.T) {
	progress, ok := parseYTDLPProgress("download: 76.5%|26921257|NA|35209545.10507247|2122410.036104719|4.349968950666312")
	if !ok {
		t.Fatal("progress line was not parsed")
	}
	if progress.Percent != 76.5 {
		t.Fatalf("percent = %v, want 76.5", progress.Percent)
	}
	if progress.DownloadedBytes != 26921257 {
		t.Fatalf("downloaded bytes = %d, want 26921257", progress.DownloadedBytes)
	}
	if progress.TotalBytes != 35209545 {
		t.Fatalf("total bytes = %d, want 35209545", progress.TotalBytes)
	}
	if progress.Speed == "---" || progress.ETA == "---" {
		t.Fatalf("speed/eta were not preserved: speed=%q eta=%q", progress.Speed, progress.ETA)
	}
}

func TestParseYTDLPDefaultDownloadLine(t *testing.T) {
	progress, ok := parseYTDLPProgress("[download]  42.7% of ~  33.83MiB at    2.10MiB/s ETA 00:09")
	if !ok {
		t.Fatal("default download line was not parsed")
	}
	if progress.Percent != 42.7 {
		t.Fatalf("percent = %v, want 42.7", progress.Percent)
	}
	if progress.Speed != "2.10MiB/s" {
		t.Fatalf("speed = %q, want 2.10MiB/s", progress.Speed)
	}
	if progress.ETA != "00:09" {
		t.Fatalf("eta = %q, want 00:09", progress.ETA)
	}
}

func TestYTDLPProgressLab(t *testing.T) {
	if os.Getenv("YOUTUBE_PROGRESS_LAB") == "" {
		t.Skip("set YOUTUBE_PROGRESS_LAB=1 to run this lab integration test")
	}

	outputTemplate := filepath.Join(t.TempDir(), "audio.%(ext)s")
	var events int
	var maxPercent float64
	path, err := downloadAudioWithYTDLP(context.Background(), youtubeProgressLabURL, &AudioFormat{FormatID: "234"}, outputTemplate, func(progress mediaDownloadProgress) {
		if progress.Percent > 0 {
			events++
		}
		if progress.Percent > maxPercent {
			maxPercent = progress.Percent
		}
	})
	if err != nil {
		t.Fatalf("downloadAudioWithYTDLP error: %v", err)
	}
	if path == "" {
		t.Fatal("yt-dlp did not return output path")
	}
	if events == 0 {
		t.Fatal("yt-dlp did not emit progress events above zero")
	}
	if maxPercent < 90 {
		t.Fatalf("max progress = %.1f, want at least 90", maxPercent)
	}

	var conversionEvents int
	var maxConversionPercent float64
	err = ConvertToMp3WithProgress(context.Background(), path, filepath.Join(t.TempDir(), "audio.mp3"), "192k", nil, "", func(percent float64) {
		if percent > 0 {
			conversionEvents++
		}
		if percent > maxConversionPercent {
			maxConversionPercent = percent
		}
	})
	if err != nil {
		t.Fatalf("ConvertToMp3WithProgress error: %v", err)
	}
	if conversionEvents == 0 {
		t.Fatal("ffmpeg did not emit conversion progress events above zero")
	}
	if maxConversionPercent < 90 {
		t.Fatalf("max conversion progress = %.1f, want at least 90", maxConversionPercent)
	}
}
