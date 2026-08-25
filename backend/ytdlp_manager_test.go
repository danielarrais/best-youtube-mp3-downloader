package main

import (
	"context"
	"crypto/sha256"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

func TestYTDLPArtifactFor(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name       string
		goos       string
		goarch     string
		filename   string
		binaryName string
		wantErr    bool
	}{
		{name: "linux amd64", goos: "linux", goarch: "amd64", filename: "yt-dlp_linux", binaryName: "yt-dlp"},
		{name: "linux arm64", goos: "linux", goarch: "arm64", filename: "yt-dlp_linux_aarch64", binaryName: "yt-dlp"},
		{name: "windows amd64", goos: "windows", goarch: "amd64", filename: "yt-dlp.exe", binaryName: "yt-dlp.exe"},
		{name: "windows arm64", goos: "windows", goarch: "arm64", filename: "yt-dlp_arm64.exe", binaryName: "yt-dlp.exe"},
		{name: "unsupported", goos: "darwin", goarch: "amd64", wantErr: true},
	}

	for _, test := range tests {
		test := test
		t.Run(test.name, func(t *testing.T) {
			t.Parallel()
			artifact, err := ytDLPArtifactFor(test.goos, test.goarch)
			if test.wantErr {
				if err == nil {
					t.Fatal("expected an error")
				}
				return
			}
			if err != nil {
				t.Fatalf("ytDLPArtifactFor() error = %v", err)
			}
			if artifact.filename != test.filename || artifact.binaryName != test.binaryName {
				t.Fatalf("ytDLPArtifactFor() = %#v", artifact)
			}
		})
	}
}

func TestParseYTDLPChecksum(t *testing.T) {
	t.Parallel()

	filename := "yt-dlp_linux"
	checksum := fmt.Sprintf("%x", sha256.Sum256([]byte("binary")))
	contents := "invalid line\n" + checksum + "  " + filename + "\n"

	got, err := parseYTDLPChecksum(contents, filename)
	if err != nil {
		t.Fatalf("parseYTDLPChecksum() error = %v", err)
	}
	if got != checksum {
		t.Fatalf("parseYTDLPChecksum() = %q, want %q", got, checksum)
	}
}

func TestDownloadAndInstallYTDLPVerifiesChecksum(t *testing.T) {
	originalValidate := ytDLPValidateBinary
	ytDLPValidateBinary = func(path string) error {
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		if string(data) != "yt-dlp binary" {
			return fmt.Errorf("unexpected binary: %q", data)
		}
		return nil
	}
	t.Cleanup(func() { ytDLPValidateBinary = originalValidate })

	binary := []byte("yt-dlp binary")
	checksum := fmt.Sprintf("%x", sha256.Sum256(binary))
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/SHA2-256SUMS":
			_, _ = fmt.Fprintf(w, "%s  yt-dlp_linux\n", checksum)
		case "/yt-dlp_linux":
			_, _ = w.Write(binary)
		default:
			http.NotFound(w, r)
		}
	}))
	t.Cleanup(server.Close)

	targetPath := filepath.Join(t.TempDir(), "yt-dlp")
	artifact := ytDLPArtifact{filename: "yt-dlp_linux", binaryName: "yt-dlp"}
	if err := downloadAndInstallYTDLP(context.Background(), server.Client(), server.URL, artifact, targetPath); err != nil {
		t.Fatalf("downloadAndInstallYTDLP() error = %v", err)
	}
	data, err := os.ReadFile(targetPath)
	if err != nil {
		t.Fatal(err)
	}
	if string(data) != string(binary) {
		t.Fatalf("installed binary = %q", data)
	}
}

func TestCheckAndDownloadYTDLPUsesBundledBinaryFirst(t *testing.T) {
	originalCached := cachedYTDLPPath
	originalExecutable := ytDLPExecutablePath
	originalLookPath := ytDLPLookPath
	originalValidate := ytDLPValidateBinary
	cachedYTDLPPath = ""
	t.Cleanup(func() {
		cachedYTDLPPath = originalCached
		ytDLPExecutablePath = originalExecutable
		ytDLPLookPath = originalLookPath
		ytDLPValidateBinary = originalValidate
	})

	dir := t.TempDir()
	executablePath := filepath.Join(dir, "youtube-mp3-downloader")
	bundledPath := filepath.Join(dir, ytDLPBinaryName(runtime.GOOS))
	ytDLPExecutablePath = func() (string, error) { return executablePath, nil }
	ytDLPLookPath = func(string) (string, error) { return "", os.ErrNotExist }
	ytDLPValidateBinary = func(path string) error {
		if path == bundledPath {
			return nil
		}
		return os.ErrNotExist
	}

	got, err := CheckAndDownloadYTDLP()
	if err != nil {
		t.Fatalf("CheckAndDownloadYTDLP() error = %v", err)
	}
	if got != bundledPath {
		t.Fatalf("CheckAndDownloadYTDLP() = %q, want bundled path %q", got, bundledPath)
	}
}
