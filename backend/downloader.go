package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"mime"
	"net"
	"net/http"
	"os"
	"os/exec"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/kkdai/youtube/v2"
)

var invalidFilenameCharacters = regexp.MustCompile(`[\\/*?:"<>|]`)

type MusicMetadata struct {
	Song     string
	Artist   string
	Album    string
	CoverURL string
}

type watchPagePlayerResponse struct {
	PlayabilityStatus struct {
		Status string `json:"status"`
		Reason string `json:"reason"`
	} `json:"playabilityStatus"`
	StreamingData struct {
		Formats         []watchPageFormat `json:"formats"`
		AdaptiveFormats []watchPageFormat `json:"adaptiveFormats"`
		DashManifestURL string            `json:"dashManifestUrl"`
		HLSManifestURL  string            `json:"hlsManifestUrl"`
	} `json:"streamingData"`
	VideoDetails struct {
		Title            string `json:"title"`
		ShortDescription string `json:"shortDescription"`
		Author           string `json:"author"`
		ChannelID        string `json:"channelId"`
		ViewCount        string `json:"viewCount"`
		LengthSeconds    string `json:"lengthSeconds"`
		Thumbnail        struct {
			Thumbnails youtube.Thumbnails `json:"thumbnails"`
		} `json:"thumbnail"`
	} `json:"videoDetails"`
	Microformat struct {
		PlayerMicroformatRenderer struct {
			LengthSeconds   string `json:"lengthSeconds"`
			OwnerProfileURL string `json:"ownerProfileUrl"`
			PublishDate     string `json:"publishDate"`
		} `json:"playerMicroformatRenderer"`
	} `json:"microformat"`
}

type watchPageFormat struct {
	ItagNo           int    `json:"itag"`
	URL              string `json:"url"`
	MimeType         string `json:"mimeType"`
	Quality          string `json:"quality"`
	SignatureCipher  string `json:"signatureCipher"`
	Cipher           string `json:"cipher"`
	Bitrate          int    `json:"bitrate"`
	FPS              int    `json:"fps"`
	Width            int    `json:"width"`
	Height           int    `json:"height"`
	LastModified     string `json:"lastModified"`
	ContentLength    int64  `json:"contentLength,string"`
	QualityLabel     string `json:"qualityLabel"`
	ProjectionType   string `json:"projectionType"`
	AverageBitrate   int    `json:"averageBitrate"`
	AudioQuality     string `json:"audioQuality"`
	ApproxDurationMs string `json:"approxDurationMs"`
	AudioSampleRate  string `json:"audioSampleRate"`
	AudioChannels    int    `json:"audioChannels"`
	InitRange        *struct {
		Start string `json:"start"`
		End   string `json:"end"`
	} `json:"initRange"`
	IndexRange *struct {
		Start string `json:"start"`
		End   string `json:"end"`
	} `json:"indexRange"`
	AudioTrack *struct {
		DisplayName    string `json:"displayName"`
		ID             string `json:"id"`
		AudioIsDefault bool   `json:"audioIsDefault"`
	} `json:"audioTrack"`
}

var (
	ytInitialDataPattern   = regexp.MustCompile(`var ytInitialData\s*=\s*(\{.+?\});`)
	ytInitialPlayerPattern = regexp.MustCompile(`var ytInitialPlayerResponse\s*=\s*(\{.+?\});`)
)

var watchPageClient = &http.Client{
	Timeout: 30 * time.Second,
}

func fetchWatchPage(ctx context.Context, videoID string) ([]byte, error) {
	var lastErr error
	for attempt := 0; attempt < 3; attempt++ {
		if attempt > 0 {
			delay := time.Duration(1<<uint(attempt)) * time.Second
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(delay):
			}
		}

		req, err := http.NewRequestWithContext(ctx, http.MethodGet, "https://www.youtube.com/watch?v="+videoID, nil)
		if err != nil {
			return nil, err
		}
		req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
		req.Header.Set("Origin", "https://www.youtube.com")
		req.Header.Set("Sec-Fetch-Mode", "navigate")
		req.AddCookie(&http.Cookie{
			Name:  "CONSENT",
			Value: "YES+cb.20210328-17-p0.en+FX+111",
		})

		resp, err := watchPageClient.Do(req)
		if err != nil {
			lastErr = err
			continue
		}

		body, readErr := io.ReadAll(resp.Body)
		resp.Body.Close()

		if resp.StatusCode == http.StatusOK {
			return body, readErr
		}
		if resp.StatusCode == http.StatusTooManyRequests {
			lastErr = fmt.Errorf("watch page returned HTTP %d", resp.StatusCode)
			continue
		}
		return nil, fmt.Errorf("watch page returned HTTP %d", resp.StatusCode)
	}
	return nil, lastErr
}

func ExtractMusicMetadata(ctx context.Context, videoID string) (*MusicMetadata, error) {
	html, err := fetchWatchPage(ctx, videoID)
	if err != nil {
		return nil, err
	}

	return parseMusicMetadataFromHTML(html)
}

func parseMusicMetadataFromHTML(html []byte) (*MusicMetadata, error) {
	match := ytInitialDataPattern.FindSubmatch(html)
	if len(match) < 2 {
		return nil, nil
	}

	var data map[string]interface{}
	if err := json.Unmarshal(match[1], &data); err != nil {
		return nil, err
	}

	panels, ok := data["engagementPanels"].([]interface{})
	if !ok {
		return nil, nil
	}

	for _, p := range panels {
		panel, ok := p.(map[string]interface{})
		if !ok {
			continue
		}
		section, ok := panel["engagementPanelSectionListRenderer"].(map[string]interface{})
		if !ok {
			continue
		}
		content, ok := section["content"].(map[string]interface{})
		if !ok {
			continue
		}
		desc, ok := content["structuredDescriptionContentRenderer"].(map[string]interface{})
		if !ok {
			continue
		}
		items, ok := desc["items"].([]interface{})
		if !ok {
			continue
		}
		for _, item := range items {
			itemMap, ok := item.(map[string]interface{})
			if !ok {
				continue
			}
			cards, ok := itemMap["horizontalCardListRenderer"].(map[string]interface{})
			if !ok {
				continue
			}
			if meta := parseMusicCards(cards); meta != nil {
				return meta, nil
			}
		}
	}

	return nil, nil
}

func parseMusicCards(cards map[string]interface{}) *MusicMetadata {
	cardList, _ := cards["cards"].([]interface{})
	if len(cardList) == 0 {
		return nil
	}

	card, ok := cardList[0].(map[string]interface{})
	if !ok {
		return nil
	}
	vm, ok := card["videoAttributeViewModel"].(map[string]interface{})
	if !ok {
		return nil
	}

	meta := &MusicMetadata{}

	if v, ok := vm["title"].(string); ok {
		meta.Song = v
	}
	if v, ok := vm["subtitle"].(string); ok {
		meta.Artist = v
	}
	if sec, ok := vm["secondarySubtitle"].(map[string]interface{}); ok {
		if v, ok := sec["content"].(string); ok {
			meta.Album = v
		}
	}

	if img, ok := vm["image"].(map[string]interface{}); ok {
		sources, _ := img["sources"].([]interface{})
		if len(sources) > 0 {
			if src, ok := sources[0].(map[string]interface{}); ok {
				if url, ok := src["url"].(string); ok {
					meta.CoverURL = url
				}
			}
		}
	}

	if meta.Song == "" && meta.Artist == "" {
		return nil
	}
	return meta
}

func DownloadCoverArt(ctx context.Context, url, destPath string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}

	resp, err := watchPageClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("cover art download returned HTTP %d", resp.StatusCode)
	}

	file, err := os.Create(destPath)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = io.Copy(file, resp.Body)
	return err
}

type androidVRTransport struct {
	base           http.RoundTripper
	mu             sync.RWMutex
	playerResponse []byte
	watchPageHTML  []byte
}

type retryTransport struct {
	base        http.RoundTripper
	maxAttempts int
}

type YouTubeSession struct {
	client    *youtube.Client
	transport *androidVRTransport
}

func (t *androidVRTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	if req.Method == http.MethodGet && req.URL.Host == "www.youtube.com" && req.URL.Path == "/watch" {
		t.mu.RLock()
		playerResponse := append([]byte(nil), t.playerResponse...)
		t.mu.RUnlock()

		if len(playerResponse) > 0 {
			req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
			resp, err := t.base.RoundTrip(req)
			if err != nil {
				return nil, err
			}
			if resp.StatusCode == http.StatusOK {
				body, readErr := io.ReadAll(resp.Body)
				resp.Body.Close()
				if readErr == nil {
					t.mu.Lock()
					t.watchPageHTML = append(t.watchPageHTML[:0], body...)
					t.mu.Unlock()
					resp.Body = io.NopCloser(bytes.NewReader(body))
					return resp, nil
				}
				return nil, readErr
			}
			return resp, nil
		}
	}

	if req.Method == http.MethodPost && req.URL.Path == "/youtubei/v1/player" {
		req.Header.Set("X-Youtube-Client-Name", "28")
	}

	response, err := t.base.RoundTrip(req)
	if err != nil || response.StatusCode != http.StatusOK ||
		req.Method != http.MethodPost || req.URL.Path != "/youtubei/v1/player" {
		return response, err
	}

	body, readErr := io.ReadAll(response.Body)
	response.Body.Close()
	if readErr != nil {
		return nil, readErr
	}
	response.Body = io.NopCloser(bytes.NewReader(body))

	t.mu.Lock()
	t.playerResponse = append(t.playerResponse[:0], body...)
	t.mu.Unlock()

	return response, nil
}

func (t *androidVRTransport) WatchPageHTML() []byte {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return append([]byte(nil), t.watchPageHTML...)
}

func (t *retryTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	for attempt := 0; attempt < t.maxAttempts; attempt++ {
		currentRequest := req.Clone(req.Context())
		if attempt > 0 && req.Body != nil {
			if req.GetBody == nil {
				return t.base.RoundTrip(req)
			}
			body, err := req.GetBody()
			if err != nil {
				return nil, err
			}
			currentRequest.Body = body
		}

		response, err := t.base.RoundTrip(currentRequest)
		if err != nil {
			return nil, err
		}
		if response.StatusCode != http.StatusTooManyRequests &&
			response.StatusCode < http.StatusInternalServerError {
			return response, nil
		}
		if attempt == t.maxAttempts-1 {
			return response, nil
		}

		delay := retryDelay(response.Header.Get("Retry-After"), attempt)
		response.Body.Close()
		select {
		case <-req.Context().Done():
			return nil, req.Context().Err()
		case <-time.After(delay):
		}
	}
	return nil, errors.New("HTTP retry loop ended unexpectedly")
}

func retryDelay(value string, attempt int) time.Duration {
	if seconds, err := strconv.Atoi(value); err == nil && seconds >= 0 {
		return time.Duration(seconds) * time.Second
	}
	if date, err := http.ParseTime(value); err == nil {
		if delay := time.Until(date); delay > 0 {
			return delay
		}
	}
	return time.Duration(attempt+1) * time.Second
}

func SanitizeFilename(filename string) string {
	filename = invalidFilenameCharacters.ReplaceAllString(filename, "_")
	filename = strings.Trim(filename, " .")
	if filename == "" {
		return "audio"
	}
	return filename
}

func newMetadataHTTPClient() (*http.Client, *androidVRTransport) {
	baseTransport := &http.Transport{
		Proxy:                 http.ProxyFromEnvironment,
		ForceAttemptHTTP2:     true,
		DialContext:           (&net.Dialer{Timeout: 15 * time.Second, KeepAlive: 30 * time.Second}).DialContext,
		TLSHandshakeTimeout:   10 * time.Second,
		ResponseHeaderTimeout: 20 * time.Second,
		IdleConnTimeout:       60 * time.Second,
	}
	transport := &androidVRTransport{base: baseTransport}
	return &http.Client{
		Timeout:   30 * time.Second,
		Transport: &retryTransport{base: transport, maxAttempts: 3},
	}, transport
}

func newStreamingHTTPClient() *http.Client {
	baseTransport := &http.Transport{
		Proxy:                 http.ProxyFromEnvironment,
		ForceAttemptHTTP2:     true,
		DialContext:           (&net.Dialer{Timeout: 15 * time.Second, KeepAlive: 30 * time.Second}).DialContext,
		TLSHandshakeTimeout:   10 * time.Second,
		ResponseHeaderTimeout: 30 * time.Second,
		IdleConnTimeout:       90 * time.Second,
	}
	return &http.Client{
		Transport: &retryTransport{base: baseTransport, maxAttempts: 3},
	}
}

func NewYouTubeSession() *YouTubeSession {
	youtube.DefaultClient = configuredYouTubeClientInfo(youtube.DefaultClient)
	httpClient, transport := newMetadataHTTPClient()
	return &YouTubeSession{
		client:    &youtube.Client{HTTPClient: httpClient, MaxRoutines: 1},
		transport: transport,
	}
}

func configuredYouTubeClientInfo(client youtube.ClientInfo) youtube.ClientInfo {
	if client.Name == "" {
		client = youtube.AndroidVRClient
	}
	if client.Key == "" {
		client.Key = youtubeAPIKey
	}
	return client
}

func getClient() *youtube.Client {
	return NewYouTubeSession().client
}

func GetVideoInfo(url string) (*youtube.Video, error) {
	return GetVideoInfoContext(context.Background(), url)
}

func GetVideoInfoContext(ctx context.Context, url string) (*youtube.Video, error) {
	return NewYouTubeSession().GetVideo(ctx, url)
}

func (s *YouTubeSession) GetVideo(ctx context.Context, url string) (*youtube.Video, error) {
	var lastErr error
	for attempt := 0; attempt < 3; attempt++ {
		video, err := s.client.GetVideoContext(ctx, url)
		if err == nil {
			s.enrichVideoFromWatchPage(video)
			return video, nil
		}
		lastErr = err
		if !isTransientYouTubeError(err) || attempt == 2 {
			break
		}

		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(time.Duration(attempt+1) * time.Second):
		}
	}
	return nil, lastErr
}

func (s *YouTubeSession) enrichVideoFromWatchPage(video *youtube.Video) {
	if s.transport == nil {
		return
	}
	html := s.transport.WatchPageHTML()
	if len(html) == 0 {
		return
	}
	watchVideo, err := parseWatchPageVideo(html, video.ID)
	if err != nil {
		return
	}
	if watchVideo.PublishDate != (time.Time{}) {
		video.PublishDate = watchVideo.PublishDate
	}
	if len(watchVideo.Thumbnails) > 0 {
		video.Thumbnails = watchVideo.Thumbnails
	}
}

func (s *YouTubeSession) ExtractMusicMetadata() *MusicMetadata {
	if s.transport == nil {
		return nil
	}
	html := s.transport.WatchPageHTML()
	if len(html) == 0 {
		return nil
	}
	meta, _ := parseMusicMetadataFromHTML(html)
	return meta
}

func parseWatchPageVideo(html []byte, videoID string) (*youtube.Video, error) {
	match := ytInitialPlayerPattern.FindSubmatch(html)
	if len(match) < 2 {
		return nil, errors.New("no ytInitialPlayerResponse found in watch page")
	}

	var response watchPagePlayerResponse
	if err := json.Unmarshal(match[1], &response); err != nil {
		return nil, err
	}
	if response.PlayabilityStatus.Status != "" && response.PlayabilityStatus.Status != "OK" {
		return nil, fmt.Errorf("watch page status: %s", response.PlayabilityStatus.Status)
	}

	video := &youtube.Video{
		ID:              videoID,
		Title:           response.VideoDetails.Title,
		Description:     response.VideoDetails.ShortDescription,
		Author:          response.VideoDetails.Author,
		ChannelID:       response.VideoDetails.ChannelID,
		Thumbnails:      response.VideoDetails.Thumbnail.Thumbnails,
		DASHManifestURL: response.StreamingData.DashManifestURL,
		HLSManifestURL:  response.StreamingData.HLSManifestURL,
	}
	video.Formats = append(video.Formats, convertWatchPageFormats(response.StreamingData.Formats)...)
	video.Formats = append(video.Formats, convertWatchPageFormats(response.StreamingData.AdaptiveFormats)...)
	if seconds, _ := strconv.Atoi(response.VideoDetails.LengthSeconds); seconds > 0 {
		video.Duration = time.Duration(seconds) * time.Second
	}
	if seconds, _ := strconv.Atoi(response.Microformat.PlayerMicroformatRenderer.LengthSeconds); seconds > 0 {
		video.Duration = time.Duration(seconds) * time.Second
	}
	if views, _ := strconv.Atoi(response.VideoDetails.ViewCount); views > 0 {
		video.Views = views
	}
	if str := response.Microformat.PlayerMicroformatRenderer.PublishDate; str != "" {
		if publishDate, err := time.Parse(time.RFC3339, str); err == nil {
			video.PublishDate = publishDate.UTC()
		}
	}
	sort.SliceStable(video.Formats, func(i, j int) bool {
		return video.Formats[i].Bitrate > video.Formats[j].Bitrate
	})
	return video, nil
}

func convertWatchPageFormats(formats []watchPageFormat) []youtube.Format {
	converted := make([]youtube.Format, 0, len(formats))
	for _, format := range formats {
		cipher := format.SignatureCipher
		if cipher == "" {
			cipher = format.Cipher
		}
		converted = append(converted, youtube.Format{
			ItagNo:           format.ItagNo,
			URL:              format.URL,
			MimeType:         format.MimeType,
			Quality:          format.Quality,
			Cipher:           cipher,
			Bitrate:          format.Bitrate,
			FPS:              format.FPS,
			Width:            format.Width,
			Height:           format.Height,
			LastModified:     format.LastModified,
			ContentLength:    format.ContentLength,
			QualityLabel:     format.QualityLabel,
			ProjectionType:   format.ProjectionType,
			AverageBitrate:   format.AverageBitrate,
			AudioQuality:     format.AudioQuality,
			ApproxDurationMs: format.ApproxDurationMs,
			AudioSampleRate:  format.AudioSampleRate,
			AudioChannels:    format.AudioChannels,
			InitRange:        format.InitRange,
			IndexRange:       format.IndexRange,
			AudioTrack:       format.AudioTrack,
		})
	}
	return converted
}

func (s *YouTubeSession) GetVideoFormats(ctx context.Context, url string) (VideoInfo, error) {
	video, err := s.GetVideo(ctx, url)
	if err != nil {
		return VideoInfo{}, err
	}
	audioFormats, title, thumbnailURL := availableAudioFormats(ctx, url, video)
	if title == "" {
		title = video.Title
	}
	if thumbnailURL == "" {
		thumbnailURL = largestVideoThumbnail(video.Thumbnails)
	}
	return VideoInfo{
		Title:        title,
		ThumbnailURL: thumbnailURL,
		Formats:      AvailableVideoFormats(video),
		AudioFormats: audioFormats,
	}, nil
}

func availableAudioFormats(ctx context.Context, url string, video *youtube.Video) ([]AudioFormat, string, string) {
	if info, err := listAudioFormatsWithYTDLP(ctx, url); err == nil && len(info.AudioFormats) > 0 {
		return info.AudioFormats, info.Title, info.ThumbnailURL
	}
	audioFormats := video.Formats.Type("audio")
	formats := make([]AudioFormat, 0, len(audioFormats))
	seen := map[int]struct{}{}
	for _, format := range audioFormats {
		if _, ok := seen[format.ItagNo]; ok {
			continue
		}
		seen[format.ItagNo] = struct{}{}
		container, codec := formatDetails(format)
		label := strings.ToUpper(container)
		if format.Bitrate > 0 {
			label += fmt.Sprintf(" - %dk", format.Bitrate/1000)
		}
		if codec != "" {
			label += " - " + codec
		}
		formats = append(formats, AudioFormat{
			FormatID:   strconv.Itoa(format.ItagNo),
			Container:  container,
			Extension:  container,
			AudioCodec: codec,
			Bitrate:    format.Bitrate / 1000,
			Label:      label,
		})
	}
	sort.SliceStable(formats, func(i, j int) bool {
		return formats[i].Bitrate > formats[j].Bitrate
	})
	return formats, "", ""
}

func largestVideoThumbnail(thumbnails youtube.Thumbnails) string {
	var largest youtube.Thumbnail
	for _, thumbnail := range thumbnails {
		if thumbnail.URL == "" {
			continue
		}
		if thumbnail.Width*thumbnail.Height > largest.Width*largest.Height {
			largest = thumbnail
		}
	}
	return largest.URL
}

func AvailableVideoFormats(video *youtube.Video) []VideoFormat {
	audioFormats := video.Formats.Type("audio")
	formats := make([]VideoFormat, 0)
	for _, videoFormat := range video.Formats.Type("video") {
		videoContainer, videoCodec := formatDetails(videoFormat)
		if videoContainer == "" {
			continue
		}

		format := VideoFormat{
			VideoItag:  videoFormat.ItagNo,
			Container:  videoContainer,
			Extension:  videoContainer,
			Resolution: videoFormat.QualityLabel,
			FPS:        videoFormat.FPS,
			VideoCodec: videoCodec,
			Size:       videoFormat.ContentLength,
		}
		if format.Resolution == "" {
			format.Resolution = videoFormat.Quality
		}

		if videoFormat.AudioChannels == 0 {
			audioFormat, found := selectAudioFormat(audioFormats, videoContainer)
			if !found {
				continue
			}
			audioContainer, audioCodec := formatDetails(audioFormat)
			format.AudioItag = audioFormat.ItagNo
			format.AudioCodec = audioCodec
			format.Size += audioFormat.ContentLength
			if audioContainer != videoContainer {
				format.Container = "mkv"
				format.Extension = "mkv"
			}
		} else {
			_, format.AudioCodec = formatDetails(videoFormat)
		}
		format.Label = videoFormatLabel(format)
		formats = append(formats, format)
	}
	sort.SliceStable(formats, func(i, j int) bool {
		leftHeight, rightHeight := videoHeight(formats[i].Resolution), videoHeight(formats[j].Resolution)
		if leftHeight != rightHeight {
			return leftHeight > rightHeight
		}
		if formats[i].FPS != formats[j].FPS {
			return formats[i].FPS > formats[j].FPS
		}
		return formats[i].Size > formats[j].Size
	})
	return formats
}

func selectAudioFormat(formats youtube.FormatList, container string) (youtube.Format, bool) {
	var selected youtube.Format
	found := false
	for _, format := range formats {
		formatContainer, _ := formatDetails(format)
		if formatContainer != container {
			continue
		}
		if !found || format.Bitrate > selected.Bitrate {
			selected, found = format, true
		}
	}
	if found {
		return selected, true
	}
	for _, format := range formats {
		if !found || format.Bitrate > selected.Bitrate {
			selected, found = format, true
		}
	}
	return selected, found
}

func formatDetails(format youtube.Format) (string, string) {
	mediaType, params, err := mime.ParseMediaType(format.MimeType)
	if err != nil {
		return "", ""
	}
	parts := strings.SplitN(mediaType, "/", 2)
	if len(parts) != 2 {
		return "", ""
	}
	codecs := strings.Split(params["codecs"], ",")
	for index := range codecs {
		codecs[index] = strings.TrimSpace(codecs[index])
	}
	return parts[1], strings.Join(codecs, ", ")
}

func videoHeight(resolution string) int {
	height := strings.TrimSuffix(strings.ToLower(resolution), "p")
	value, _ := strconv.Atoi(height)
	return value
}

func videoFormatLabel(format VideoFormat) string {
	label := format.Resolution
	if format.FPS > 0 {
		label += fmt.Sprintf(" %d fps", format.FPS)
	}
	if format.VideoCodec != "" {
		label += " - " + format.VideoCodec
	}
	return label + " (" + strings.ToUpper(format.Container) + ")"
}

func videoFormatByItag(video *youtube.Video, itag int) (*youtube.Format, bool) {
	for index := range video.Formats {
		if video.Formats[index].ItagNo == itag {
			return &video.Formats[index], true
		}
	}
	return nil, false
}

func isTransientYouTubeError(err error) bool {
	var networkError net.Error
	return errors.As(err, &networkError)
}

func FormatYouTubeError(err error, language string) string {
	var status youtube.ErrUnexpectedStatusCode
	if errors.As(err, &status) && status == http.StatusTooManyRequests {
		return localizedMessage(language,
			"YouTube limitou temporariamente este IP (HTTP 429). Aguarde antes de tentar novamente.",
			"YouTube temporarily limited this IP address (HTTP 429). Wait before trying again.",
		)
	}

	if errors.Is(err, youtube.ErrNotPlayableInEmbed) {
		return localizedMessage(language,
			"Este vídeo possui uma restrição de idade ou reprodução que impede o download sem login.",
			"This video has an age or playback restriction that prevents downloading without signing in.",
		)
	}

	if errors.Is(err, youtube.ErrVideoPrivate) {
		return localizedMessage(language,
			"Este vídeo é privado e não pode ser baixado.",
			"This video is private and cannot be downloaded.",
		)
	}

	var playbackError *youtube.ErrPlayabiltyStatus
	if errors.As(err, &playbackError) && isUnavailablePlaybackReason(playbackError.Reason) {
		return localizedMessage(language, "Vídeo indisponível.", "This video is unavailable.")
	}

	lowerError := strings.ToLower(err.Error())
	if strings.Contains(lowerError, "this video is unavailable") ||
		strings.Contains(lowerError, "vídeo indisponível") ||
		strings.Contains(lowerError, "video unavailable") {
		return localizedMessage(language, "Vídeo indisponível.", "This video is unavailable.")
	}

	return localizedPrefix(language, "Erro ao consultar o YouTube: ", "Error while querying YouTube: ") + err.Error()
}

func localizedMessage(language, portuguese, english string) string {
	if language == "en-US" {
		return english
	}
	return portuguese
}

func localizedPrefix(language, portuguese, english string) string {
	return localizedMessage(language, portuguese, english)
}

func isUnavailablePlaybackReason(reason string) bool {
	lowerReason := strings.ToLower(strings.TrimSpace(reason))
	return lowerReason == "this video is unavailable" ||
		lowerReason == "vídeo indisponível" ||
		lowerReason == "video unavailable"
}

func TranslateStoredYouTubeError(message, language string) string {
	lowerMessage := strings.ToLower(message)
	switch {
	case strings.Contains(lowerMessage, "can't bypass age restriction"),
		strings.Contains(lowerMessage, "restrição de idade"),
		strings.Contains(lowerMessage, "age or playback restriction"):
		return localizedMessage(language,
			"Este vídeo possui uma restrição de idade ou reprodução que impede o download sem login.",
			"This video has an age or playback restriction that prevents downloading without signing in.",
		)
	case strings.Contains(lowerMessage, "this video is unavailable"),
		strings.Contains(lowerMessage, "vídeo está indisponível"),
		strings.Contains(lowerMessage, "video is unavailable"):
		return localizedMessage(language, "Vídeo indisponível.", "This video is unavailable.")
	default:
		return message
	}
}

func FormatOperationError(operation string, err error, language string) string {
	switch operation {
	case "conversion":
		return localizedPrefix(language, "Erro na conversão: ", "Conversion error: ") + err.Error()
	case "finalize":
		return localizedPrefix(language, "Erro ao finalizar o arquivo: ", "Error while finalizing the file: ") + err.Error()
	default:
		return localizedPrefix(language, "Erro no download: ", "Download error: ") + err.Error()
	}
}

func (s *YouTubeSession) DownloadAudio(ctx context.Context, video *youtube.Video, destPath string, onProgress func(percent float64, downloaded int64, total int64)) (string, error) {
	formats := video.Formats.Type("audio")
	if len(formats) == 0 {
		return "", fmt.Errorf("no audio formats found")
	}

	sort.SliceStable(formats, func(i, j int) bool {
		return formats[i].Bitrate > formats[j].Bitrate
	})

	return s.DownloadFormat(ctx, video, &formats[0], destPath, onProgress)
}

func (s *YouTubeSession) DownloadFormat(ctx context.Context, video *youtube.Video, format *youtube.Format, destPath string, onProgress func(percent float64, downloaded int64, total int64)) (string, error) {
	streamURL, err := s.client.GetStreamURLContext(ctx, video, format)
	if err != nil {
		if fallbackErr := downloadFormatWithYTDLP(ctx, video.ID, format.ItagNo, destPath, err); fallbackErr == nil {
			return destPath, nil
		}
		return "", err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, streamURL, nil)
	if err != nil {
		return "", err
	}
	clientInfo := configuredYouTubeClientInfo(youtube.DefaultClient)
	req.Header.Set("User-Agent", clientInfo.UserAgent)
	req.Header.Set("Origin", "https://www.youtube.com")
	req.Header.Set("Referer", "https://www.youtube.com/watch?v="+video.ID)
	req.Header.Set("Sec-Fetch-Mode", "navigate")

	resp, err := newStreamingHTTPClient().Do(req)
	if err != nil {
		if fallbackErr := downloadFormatWithYTDLP(ctx, video.ID, format.ItagNo, destPath, err); fallbackErr == nil {
			return destPath, nil
		}
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode < http.StatusOK || resp.StatusCode >= http.StatusMultipleChoices {
		err := fmt.Errorf("unexpected status code: %d", resp.StatusCode)
		if fallbackErr := downloadFormatWithYTDLP(ctx, video.ID, format.ItagNo, destPath, err); fallbackErr == nil {
			return destPath, nil
		}
		return "", err
	}

	totalSize := format.ContentLength
	if totalSize <= 0 && resp.ContentLength > 0 {
		totalSize = resp.ContentLength
	}

	file, err := os.Create(destPath)
	if err != nil {
		return "", err
	}
	closeWithError := func(operationErr error) error {
		if closeErr := file.Close(); operationErr == nil {
			return closeErr
		}
		return operationErr
	}

	var downloaded int64
	buffer := make([]byte, 64*1024)
	for {
		if err := ctx.Err(); err != nil {
			return "", closeWithError(err)
		}
		n, err := resp.Body.Read(buffer)
		if n > 0 {
			_, writeErr := file.Write(buffer[:n])
			if writeErr != nil {
				return "", closeWithError(writeErr)
			}
			downloaded += int64(n)
			if onProgress != nil && totalSize > 0 {
				percent := float64(downloaded) / float64(totalSize) * 100
				onProgress(percent, downloaded, totalSize)
			}
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			return "", closeWithError(err)
		}
	}

	if err := file.Sync(); err != nil {
		return "", closeWithError(err)
	}
	if err := file.Close(); err != nil {
		return "", err
	}
	return destPath, nil
}

func downloadFormatWithYTDLP(ctx context.Context, videoID string, itag int, destPath string, sourceErr error) error {
	if !shouldFallbackToYTDLP(sourceErr) {
		return sourceErr
	}
	ytDLPPath, err := exec.LookPath("yt-dlp")
	if err != nil {
		return sourceErr
	}
	url := "https://www.youtube.com/watch?v=" + videoID
	cmd := exec.CommandContext(ctx, ytDLPPath,
		"--no-part",
		"--force-overwrites",
		"-f", strconv.Itoa(itag),
		"-o", destPath,
		url,
	)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("yt-dlp fallback error: %v, detail: %s", err, strings.TrimSpace(stderr.String()))
	}
	if _, err := os.Stat(destPath); err != nil {
		return err
	}
	return nil
}

func shouldFallbackToYTDLP(err error) bool {
	if err == nil {
		return false
	}
	message := strings.ToLower(err.Error())
	return strings.Contains(message, "unexpected status code: 403") ||
		strings.Contains(message, "unexpected status code: 429") ||
		strings.Contains(message, "cipher not found")
}

func ConvertToMp3(ctx context.Context, inputPath string, outputPath string, quality string, metadata *MusicMetadata, coverPath string) error {
	bitrate := "192k"
	if quality != "" {
		bitrate = strings.TrimSuffix(quality, "k") + "k"
	}
	ffmpegPath, err := CheckAndDownloadFFmpeg()
	if err != nil {
		return err
	}

	var stderr bytes.Buffer
	cmd := exec.CommandContext(ctx, ffmpegPath, ffmpegMP3Args(inputPath, outputPath, bitrate, metadata, coverPath)...)
	cmd.Stderr = &stderr

	err = cmd.Run()
	if err != nil {
		return fmt.Errorf("ffmpeg error: %v, detail: %s", err, stderr.String())
	}
	return nil
}

func ffmpegMP3Args(inputPath, outputPath, bitrate string, metadata *MusicMetadata, coverPath string) []string {
	args := []string{"-y", "-i", inputPath}

	if coverPath != "" {
		args = append(args, "-i", coverPath)
	}
	args = append(args,
		"-c:a", "libmp3lame",
		"-b:a", bitrate,
		"-ar", "44100",
		"-ac", "2",
		"-joint_stereo", "1",
	)

	if metadata != nil {
		if metadata.Song != "" {
			args = append(args, "-metadata", "title="+metadata.Song)
		}
		if metadata.Artist != "" {
			args = append(args, "-metadata", "artist="+metadata.Artist)
		}
		if metadata.Album != "" {
			args = append(args, "-metadata", "album="+metadata.Album)
		}
	}

	args = append(args, "-map_metadata", "0")

	if coverPath != "" {
		args = append(args,
			"-map", "0:a:0",
			"-map", "1:v:0",
			"-c:v", "copy",
			"-disposition:v", "attached_pic",
		)
	} else {
		args = append(args, "-vn")
	}

	args = append(args, "-id3v2_version", "3", "-f", "mp3", outputPath)
	return args
}

func ConvertToVideo(ctx context.Context, videoPath, audioPath, outputPath, container string) error {
	ffmpegPath, err := CheckAndDownloadFFmpeg()
	if err != nil {
		return err
	}
	var stderr bytes.Buffer
	cmd := exec.CommandContext(ctx, ffmpegPath, ffmpegVideoArgs(videoPath, audioPath, outputPath, container)...)
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("ffmpeg error: %v, detail: %s", err, stderr.String())
	}
	return nil
}

func ffmpegVideoArgs(videoPath, audioPath, outputPath, container string) []string {
	args := []string{"-y", "-i", videoPath}
	if audioPath != "" {
		args = append(args, "-i", audioPath, "-map", "0:v:0", "-map", "1:a:0")
	} else {
		args = append(args, "-map", "0")
	}
	args = append(args, "-c", "copy")
	if container == "mp4" {
		args = append(args, "-movflags", "+faststart")
	}
	format := container
	if container == "mkv" {
		format = "matroska"
	}
	return append(args, "-f", format, outputPath)
}
