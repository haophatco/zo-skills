---
name: faceless-video
description: "Tạo video faceless viral từ link TikTok/YouTube. Pipeline tự động: lấy transcript → viết script viral → TTS tiếng Việt → tìm B-roll Pexels → render video qua Creatomate hoặc Shotstack. Use when user says \"tạo video faceless\", \"faceless video\", or provides a Facebook/TikTok/YouTube link and wants to create a faceless video."
compatibility: Created for Zo Computer
author: hana.zo.computer
---
# Faceless Video Generator

Tạo video faceless viral tự động từ link TikTok hoặc YouTube.

## Pipeline

1. **Transcript** — Lấy transcript từ TikTok (tokbackup API) hoặc YouTube (tactiq API)
2. **Clean** — Làm sạch transcript bằng Gemini 2.0 Flash
3. **Write Script** — Viết lại thành script viral bằng Gemini 2.5 Pro (2500-3000 ký tự, văn phong kể chuyện, hook mạnh)
4. **Keywords** — Tạo 20 keyword tiếng Anh cho B-roll (Gemini 2.0 Flash)
5. **TTS** — Chuyển script thành giọng nói tiếng Việt (Google Cloud TTS, voice: vi-VN-Chirp3-HD-Enceladus)
6. **B-roll** — Tìm + tải + upload 20 video portrait từ Pexels lên Supabase
7. **Render** — Ghép audio + video qua Creatomate template
8. **Output** — Video hoàn chỉnh sẵn sàng đăng

## Cách chạy

```bash
python3 Skills/faceless-video/scripts/faceless_video.py <URL> [--output Videos/output.mp4]
```

### Ví dụ:
```bash
# Từ YouTube
python3 Skills/faceless-video/scripts/faceless_video.py "https://www.youtube.com/watch?v=xxxxx"

# Từ TikTok, tải video về
python3 Skills/faceless-video/scripts/faceless_video.py "https://www.tiktok.com/@user/video/123" --output Videos/faceless.mp4
```

## Environment Variables (Secrets)

Cần cấu hình trong [Settings > Advanced](/?t=settings&s=advanced) > **Secrets**:

| Variable | Mô tả | Bắt buộc |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `GOOGLE_TTS_API_KEY` | Google Cloud Text-to-Speech API key | ✅ |
| `PEXELS_API_KEY` | Pexels API key cho B-roll search | ✅ |
| `SUPABASE_SERVICE_KEY` | Supabase service role JWT | ✅ |
| `SHOTSTACK_API_KEY` | Shotstack API key cho render (free tier OK) | ✅ |
| `SHOTSTACK_ENV` | `stage` (free tier) hoặc `v1` (production) | ❌ (default: `stage`) |
| `SUPABASE_URL` | Supabase project URL | ❌ (có default) |
| `SUPABASE_BUCKET` | Supabase storage bucket | ❌ (có default) |
| `BG_MUSIC_URL` | URL nhạc nền | ❌ (có default) |

## Output

- Video URL từ Shotstack (public, có thể share)
- File MP4 local nếu dùng `--output`
- Script text lưu tại `Documents/faceless-video-last-script.txt`
