#!/usr/bin/env python3
"""
Faceless Video Generator — Zo Native Skill
Replicates the n8n pipeline: Transcript → Script → TTS → B-roll → Render

Usage:
  python3 faceless_video.py <tiktok_or_youtube_url> [--output /path/to/output.mp4]
  python3 faceless_video.py --help
"""

import argparse, json, os, sys, time, base64, re, subprocess, tempfile
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ── Config from environment ──────────────────────────────────────────────────
GOOGLE_TTS_API_KEY = os.environ.get("GOOGLE_TTS_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("Gemini_API_Key", "")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "haophatco")
SHOTSTACK_API_KEY = os.environ.get("SHOTSTACK_API_KEY", "")
SHOTSTACK_ENV = os.environ.get("SHOTSTACK_ENV", "stage")  # "stage" (free tier) or "v1" (production)
TOKBACKUP_API_KEY = os.environ.get("TOKBACKUP_API_KEY", "Toktools2024@!NowMust")
BG_MUSIC_URL = os.environ.get("BG_MUSIC_URL", "")

SHOTSTACK_BASE = f"https://api.shotstack.io/edit/{SHOTSTACK_ENV}"

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def check_env():
    missing = []
    checks = {
        "GOOGLE_TTS_API_KEY": GOOGLE_TTS_API_KEY,
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "PEXELS_API_KEY": PEXELS_API_KEY,
        "SUPABASE_SERVICE_KEY": SUPABASE_KEY,
        "SHOTSTACK_API_KEY": SHOTSTACK_API_KEY,
    }
    for name, val in checks.items():
        if not val:
            missing.append(name)
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Set them in Zo Settings > Advanced > Secrets")
        sys.exit(1)


# ── Step 1: Extract Transcript ───────────────────────────────────────────────

def get_transcript(url: str) -> tuple[str, str]:
    """Returns (raw_transcript, source_type)"""
    if "tiktok.com" in url:
        return _get_tiktok_transcript(url), "tiktok"
    else:
        return _get_youtube_transcript(url), "youtube"


def _get_tiktok_transcript(url: str) -> str:
    print("📥 Extracting TikTok transcript...")
    resp = requests.post(
        "https://scriptadmin.tokbackup.com/v1/tiktok/fetchMultipleTikTokData",
        params={"get_transcript": "true", "ip": "116.96.46.78"},
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "x-api-key": TOKBACKUP_API_KEY,
        },
        json={"videoUrls": [url]},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    subtitles = data.get("data", [{}])[0].get("subtitles", "")
    if not subtitles:
        raise ValueError("No subtitles found in TikTok response")
    return subtitles


def _get_youtube_transcript(url: str) -> str:
    print("📥 Extracting YouTube transcript...")
    from youtube_transcript_api import YouTubeTranscriptApi
    video_id = re.search(r'(?:v=|youtu\.be/|shorts/)([\w-]{11})', url)
    if not video_id:
        raise ValueError(f"Cannot extract video ID from URL: {url}")
    vid = video_id.group(1)
    ytt = YouTubeTranscriptApi()
    try:
        snippets = ytt.fetch(vid, languages=["vi", "en"])
    except Exception:
        snippets = ytt.fetch(vid)
    return " ".join(s.text for s in snippets)


# ── Step 2: Clean Transcript (Gemini 2.0 Flash) ─────────────────────────────

def clean_transcript(raw: str, source: str) -> str:
    print("🧹 Cleaning transcript...")
    if source == "tiktok":
        prompt = (
            "Viết lại bản transcript dưới đây thành file transcript văn bản hoàn chỉnh thuần text. "
            "Viết y hệt nội dung gốc, chỉ bỏ các phần thừa của json. "
            "Yêu cầu viết thành 1 đoạn duy nhất không xuống dòng, không markdown\n\n"
            f"{raw}"
        )
    else:
        prompt = (
            "Viết lại bản transcript dưới đây thành văn bản hoàn chỉnh thuần text. "
            "Viết y hệt nội dung gốc, chỉ bỏ các phần thừa của json. "
            "Yêu cầu viết thành 1 đoạn duy nhất không xuống dòng, không markdown\n\n"
            f"Transcript: {raw}"
        )
    return _call_gemini("gemini-2.5-flash", prompt)


# ── Step 3: Write Viral Script (Gemini 2.5 Pro) ─────────────────────────────

WRITE_SCRIPT_PROMPT = r"""Transcript: {transcript}

Từ Transcript trên, hãy viết thành nội dung video viral trên TikTok tuân thủ chặt chẽ các yêu cầu sau:

# Yêu cầu quan trọng bắt buộc phải tuân thủ
1. Tuyệt đối không sử dụng ký tự (*) hay (**) trong nội dung. Và tuyệt đối không được xuống dòng
2. Bỏ toàn bộ những đoạn chú thích như "Nội dung video Tiktok về Marketing", "Nhạc nền sôi động", "Hình ảnh: nhân viên buồn bã" hay "Mở đầu - 3 giây" đi. Chỉ tạo ra văn bản là nội dung của video luôn để chỉ việc nói theo hoặc chuyển thành giọng nói ghép vào video
3. Viết liền mạch thành 1 đoạn văn duy nhất, không xuống dòng
4. Bắt buộc bỏ ký tự đóng mở ngoặc ("") trong nội dung đi để tránh json lỗi
5. Vào câu chuyện hoặc nội dung luôn. Không được mở đầu dài dòng. Sao cho khiến người nghe cảm thấy hấp dẫn tò mò ngay từ câu đầu. Bắt buộc bỏ các câu mở đầu thừa thãi như: "Bạn biết không" hay "bạn có biết" ở đầu nội dung đi. Thay vào đó cho câu mở đầu hấp dẫn trực diện và ấn tượng hơn.
6. Nội dung nên ở dạng kể chuyện vô cùng ý nghĩa, thực tế, sâu cay, ẩn chứa nhiều đạo lý sâu sắc. Nhưng phải vô cùng thực chiến
7. Hãy viết dấu câu chuẩn để sao cho chuyển thể sang giọng nói (TTS) có ngắt nghỉ và biểu cảm rõ ràng. Nội dung tạo ra nên có độ dài tương thích với video 2,5-3 phút khi chuyển thể sang giọng nói text to speech. Đầy đủ các dấu chấm than, hỏi chấm, hai chấm, chấm phẩy (!,?,:,;)
8. Nếu nội dung Transcript có bán sách và giới thiệu sách hay sản phẩm gì. Hãy lược bỏ các đoạn giới thiệu sản phẩm hay bán hàng trong nội dung bạn tạo ra
9. Hãy học toàn bộ văn phong, ngôn ngữ và cách dẫn dắt của những nội dung mẫu dưới đây. Từ đó tạo ra nội dung với văn phong, ngôn ngữ tương tự.

**Yêu cầu bắt buộc**:
- Text output must be a maximum of 3000 characters long and minimum of 2500 characters long. This is a mandatory requirement."""


def write_script(transcript: str) -> str:
    print("✍️  Writing viral script (Gemini 2.5 Flash)...")
    prompt = WRITE_SCRIPT_PROMPT.format(transcript=transcript)
    script = _call_gemini("gemini-2.5-flash", prompt)
    script = script.replace("*", "").replace('"', '').replace("\n", " ").strip()
    return script


# ── Step 4: Generate 20 Keywords (Gemini 2.0 Flash) ─────────────────────────

KEYWORD_PROMPT = """Nội dung Video: {script}

Tóm gọn nội dung video trên thành 1 đoạn 20 keyword chính mô tả cảnh quay bằng tiếng anh để pexels dễ dàng tìm kiếm video minh hoạ. (ví dụ: với từ khoá "Khổng từ" => hãy tạo "an old wise Asian man")

# Yêu cầu
1. Tuyệt đối không sử dụng ký tự (*) hay (**) trong nội dung. Bỏ toàn bộ markdown
2. Viết liền mạch, không xuống dòng
3. Tạo ra đúng 20 keyword, không hơn không kém
4. Các keyword mô tả phải đúng thứ tự thời gian theo dòng nội dung của Video gốc
5. Ngăn cách các keyword bởi dấu phẩy
6. Dùng các từ khóa thông dụng, dễ hiểu, đơn giản và cô đọng nhất để dễ dàng tìm ra video trên pexels. Không dùng từ khóa quá phức tạp chuyên môn
7. Không dùng các từ khoá: Customer Journey, ungratefulnes => Thay bằng các từ khoá khác"""


def generate_keywords(script: str) -> list[str]:
    print("🔑 Generating 20 B-roll keywords...")
    raw = _call_gemini("gemini-2.5-flash", KEYWORD_PROMPT.format(script=script))
    keywords = [k.strip() for k in raw.split(",") if k.strip()]
    if len(keywords) > 20:
        keywords = keywords[:20]
    print(f"   Keywords: {keywords}")
    return keywords


# ── Step 5: Text-to-Speech (Google Cloud TTS) ────────────────────────────────

def _tts_chunk(text: str) -> bytes:
    resp = requests.post(
        f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "input": {"text": text},
            "voice": {
                "languageCode": "vi-VN",
                "name": "vi-VN-Chirp3-HD-Enceladus",
                "ssmlGender": "MALE",
            },
            "audioConfig": {"audioEncoding": "MP3"},
        },
        timeout=60,
    )
    resp.raise_for_status()
    return base64.b64decode(resp.json()["audioContent"])

def text_to_speech(script: str) -> bytes:
    print("🔊 Converting script to speech...")
    max_bytes = 3000
    chunks = []
    current = ""
    for sentence in re.split(r'(?<=[.!?;:,])\s+', script):
        if len((current + " " + sentence).encode('utf-8')) > max_bytes and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip()
    if current:
        chunks.append(current.strip())
    print(f"   📝 Split into {len(chunks)} TTS chunks")
    audio_parts = []
    for i, chunk in enumerate(chunks):
        print(f"   🔊 TTS chunk {i+1}/{len(chunks)} ({len(chunk.encode('utf-8'))} bytes)")
        audio_parts.append(_tts_chunk(chunk))
        if i < len(chunks) - 1:
            time.sleep(1)
    return b"".join(audio_parts)


# ── Step 6: Upload to Supabase Storage ────────────────────────────────────────

def upload_to_supabase(data: bytes, filename: str, content_type: str) -> str:
    ts = int(time.time() * 1000)
    key = f"{SUPABASE_BUCKET}/{ts}-{filename}"
    resp = requests.put(
        f"{SUPABASE_URL}/storage/v1/object/{key}",
        headers={
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": content_type,
        },
        data=data,
        timeout=120,
    )
    resp.raise_for_status()
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{key}"
    return public_url


# ── Step 7: Search Pexels for B-roll ─────────────────────────────────────────

def search_pexels(keyword: str) -> list[dict]:
    resp = requests.get(
        "https://api.pexels.com/videos/search",
        params={
            "query": keyword,
            "per_page": 25,
            "orientation": "portrait",
            "min_duration": 10,
            "max_duration": 20,
        },
        headers={"Authorization": PEXELS_API_KEY},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("videos", [])


# ── Step 8: Filter, Download, Upload videos ──────────────────────────────────

def _pick_best_video_file(video: dict) -> dict | None:
    files = video.get("video_files", [])
    for f in files:
        if (f.get("link", "").startswith("https://")
                and f.get("width", 0) >= 1280
                and f.get("quality") in ("hd", "uhd")):
            return f
    for f in files:
        if f.get("link", "").startswith("https://"):
            return f
    return None


def process_keyword(keyword: str, index: int, used_ids: set) -> str | None:
    """Search, filter, download, upload one keyword's video. Returns Supabase URL or None."""
    try:
        videos = search_pexels(keyword)
    except Exception as e:
        print(f"   ⚠️  Pexels search failed for '{keyword}': {e}")
        return None

    for video in videos:
        vid = video["id"]
        dur = video.get("duration", 0)
        if vid in used_ids:
            continue
        if not (10 <= dur <= 20):
            continue
        vf = _pick_best_video_file(video)
        if not vf:
            continue

        used_ids.add(vid)
        try:
            dl = requests.get(vf["link"], timeout=60)
            dl.raise_for_status()
            url = upload_to_supabase(dl.content, f"video-{index}.mp4", "video/mp4")
            print(f"   ✅ Video-{index}: '{keyword}' → uploaded")
            return url
        except Exception as e:
            print(f"   ⚠️  Download/upload failed for '{keyword}': {e}")
            continue

    print(f"   ⚠️  No valid video found for '{keyword}'")
    return None


# ── Step 9: Subtitle & Overlay helpers ────────────────────────────────────────

def generate_subtitle_clips(script: str, audio_duration: float) -> list[dict]:
    """Split script into short phrases and return Shotstack html clips with proportional timing."""
    sentences = re.split(r'(?<=[.!?,;:])\s+', script.strip())
    chunks = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        words = s.split()
        if len(words) <= 9:
            chunks.append(s)
        else:
            for i in range(0, len(words), 8):
                part = ' '.join(words[i:i+8]).strip()
                if part:
                    chunks.append(part)

    total_chars = sum(len(c) for c in chunks)
    if total_chars == 0:
        return []

    clips = []
    pos_chars = 0
    for chunk in chunks:
        start = (pos_chars / total_chars) * audio_duration
        length = max(1.2, (len(chunk) / total_chars) * audio_duration)
        escaped = chunk.replace("'", "&#39;").replace('"', '&quot;').replace('<', '&lt;')
        clips.append({
            "asset": {
                "type": "html",
                "html": f"<p>{escaped}</p>",
                "css": (
                    "p { font-family: 'Noto Sans', Arial, sans-serif; "
                    "font-size: 52px; font-weight: 700; color: #FFFFFF; "
                    "text-align: center; line-height: 1.35; margin: 0; padding: 12px 24px; "
                    "text-shadow: 2px 2px 6px rgba(0,0,0,0.9); }"
                ),
                "width": 1000,
                "height": 180,
            },
            "start": round(start, 2),
            "length": round(length, 2),
            "position": "bottom",
            "offset": {"x": 0, "y": 0.06},
            "transition": {"in": "fade", "out": "fade"},
        })
        pos_chars += len(chunk)
    print(f"   📝 {len(clips)} subtitle clips generated")
    return clips


def build_overlay_clips(overlays: list[tuple]) -> list[dict]:
    """
    overlays: list of (start_sec, duration_sec, text, size)
    size: 'large' | 'medium' | 'small'
    Returns Shotstack html clips for key text moments.
    """
    size_map = {"large": "80px", "medium": "64px", "small": "48px"}
    clips = []
    for start, duration, text, size in overlays:
        px = size_map.get(size, "64px")
        escaped = text.replace("'", "&#39;").replace('"', '&quot;').replace('<', '&lt;')
        clips.append({
            "asset": {
                "type": "html",
                "html": f"<p>{escaped}</p>",
                "css": (
                    f"p {{ font-family: 'Noto Sans', Arial, sans-serif; "
                    f"font-size: {px}; font-weight: 900; color: #FFD700; "
                    f"text-align: center; line-height: 1.2; margin: 0; padding: 10px 20px; "
                    f"text-shadow: 3px 3px 8px rgba(0,0,0,1); }}"
                ),
                "width": 1000,
                "height": 200,
            },
            "start": round(start, 2),
            "length": round(duration, 2),
            "position": "center",
            "transition": {"in": "zoom", "out": "fade"},
        })
    return clips


OVERLAY_PROMPT = """Bạn là video editor chuyên nghiệp. Phân tích script TikTok bên dưới và xác định 5–8 khoảnh khắc quan trọng nhất cần hiển thị text overlay nổi bật (màu vàng, to, ở giữa màn hình).

Script (tổng thời lượng audio: {duration:.1f} giây):
{script}

Quy tắc tính thời gian:
- Script dài {total_chars} ký tự, tổng {duration:.1f}s
- Tốc độ đọc ≈ {chars_per_sec:.1f} ký tự/giây
- Để tính start_sec cho đoạn text X: đếm số ký tự từ đầu script đến đoạn X, rồi chia cho tốc độ đọc

Chọn các khoảnh khắc:
- Hook đầu video (0–5s): câu gây shock/tò mò
- Twist/insight chính: câu lật nhận thức quan trọng nhất
- Key phrase: 2–3 cụm từ đáng nhớ, viral nhất
- CTA cuối: lời kêu gọi hành động

Trả về JSON array (KHÔNG có markdown, KHÔNG có giải thích, chỉ JSON thuần):
[
  {{"start": 0.5, "duration": 2.0, "text": "SAI RỒI!", "size": "large"}},
  {{"start": 8.0, "duration": 2.5, "text": "Đây là sự thật", "size": "large"}},
  ...
]

size options: "large" (hook/twist), "medium" (key phrases), "small" (supporting)
text: ngắn gọn, tối đa 5 từ, ALL CAPS cho hook/twist"""


def generate_overlay_timestamps(script: str, audio_duration: float) -> list[tuple]:
    """Use Gemini to auto-generate key text overlay moments from the script.
    Returns list of (start_sec, duration_sec, text, size) tuples."""
    print("✨ Generating overlay timestamps (Gemini)...")
    total_chars = len(script)
    chars_per_sec = total_chars / audio_duration if audio_duration > 0 else 30
    prompt = OVERLAY_PROMPT.format(
        duration=audio_duration,
        script=script[:4000],  # cap to avoid prompt overflow
        total_chars=total_chars,
        chars_per_sec=chars_per_sec,
    )
    try:
        raw = _call_gemini("gemini-2.5-flash", prompt)
        # Extract JSON array from response
        raw = raw.strip()
        # Strip markdown fences if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        data = json.loads(raw)
        overlays = []
        for item in data:
            start = float(item.get("start", 0))
            duration = float(item.get("duration", 2.0))
            text = str(item.get("text", "")).strip()
            size = item.get("size", "large")
            # Clamp to audio duration
            if start >= audio_duration:
                continue
            if start + duration > audio_duration:
                duration = audio_duration - start
            if text and duration > 0:
                overlays.append((round(start, 2), round(duration, 2), text, size))
        print(f"   ✅ {len(overlays)} overlays generated")
        for o in overlays:
            print(f"      {o[0]:.1f}s +{o[1]:.1f}s → [{o[3]}] {o[2]}")
        return overlays
    except Exception as e:
        print(f"   ⚠️  Overlay generation failed ({e}), skipping overlays")
        return []


# ── Step 9: Render via Shotstack ──────────────────────────────────────────────

def _get_audio_duration_seconds(audio_bytes: bytes) -> float:
    """Use ffprobe on the raw audio bytes to get duration in seconds."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", tmp_path],
            text=True,
        )
        return float(out.strip())
    finally:
        os.unlink(tmp_path)


def render_video(
    audio_url: str,
    audio_duration: float,
    video_urls: list[str | None],
    subtitle_clips: list[dict] | None = None,
    overlay_clips: list[dict] | None = None,
) -> str:
    """Submit render job to Shotstack. Returns render ID."""
    print(f"🎬 Submitting render to Shotstack ({SHOTSTACK_ENV})...")
    valid_videos = [u for u in video_urls if u]
    if not valid_videos:
        raise RuntimeError("No valid video URLs to render")

    # Distribute B-roll clips evenly across the audio duration
    per_clip = audio_duration / len(valid_videos)
    print(f"   Audio: {audio_duration:.1f}s / {len(valid_videos)} clips → {per_clip:.2f}s per clip")

    broll_clips = []
    for i, url in enumerate(valid_videos):
        broll_clips.append({
            "asset": {
                "type": "video",
                "src": url,
                "volume": 0,
            },
            "start": round(i * per_clip, 2),
            "length": round(per_clip, 2),
            "fit": "cover",
        })

    voiceover_clip = {
        "asset": {"type": "audio", "src": audio_url},
        "start": 0,
        "length": round(audio_duration, 2),
    }

    tracks = []
    if overlay_clips:
        tracks.append({"clips": overlay_clips})   # track 1: key text overlays (top)
    if subtitle_clips:
        tracks.append({"clips": subtitle_clips})  # track 2: subtitles
    tracks.append({"clips": [voiceover_clip]})    # track: voiceover audio
    tracks.append({"clips": broll_clips})         # track: B-roll video (bottom)

    timeline: dict = {
        "background": "#000000",
        "tracks": tracks,
    }

    if BG_MUSIC_URL:
        timeline["soundtrack"] = {
            "src": BG_MUSIC_URL,
            "effect": "fadeOut",
            "volume": 0.2,
        }

    payload = {
        "timeline": timeline,
        "output": {
            "format": "mp4",
            "size": {"width": 1080, "height": 1920},
            "fps": 30,
        },
    }

    resp = requests.post(
        f"{SHOTSTACK_BASE}/render",
        headers={
            "x-api-key": SHOTSTACK_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if not resp.ok:
        print(f"   ❌ Shotstack error: {resp.status_code} {resp.text[:500]}")
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Shotstack rejected payload: {data}")
    render_id = data.get("response", {}).get("id")
    print(f"   Render ID: {render_id}")
    return render_id


def wait_for_render(render_id: str, max_wait: int = 600) -> str:
    """Poll Shotstack until render is done. Returns download URL."""
    print("⏳ Waiting for Shotstack render to complete...")
    start = time.time()
    while time.time() - start < max_wait:
        resp = requests.get(
            f"{SHOTSTACK_BASE}/render/{render_id}",
            headers={"x-api-key": SHOTSTACK_API_KEY},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("response", {})
        status = data.get("status", "")
        if status == "done":
            url = data.get("url", "")
            print(f"   ✅ Render complete!")
            return url
        elif status == "failed":
            err = data.get("error", "Unknown error")
            raise RuntimeError(f"Render failed: {err}")
        else:
            elapsed = int(time.time() - start)
            print(f"   ⏳ Status: {status} ({elapsed}s elapsed)")
            time.sleep(10)
    raise TimeoutError(f"Render did not complete within {max_wait}s")


# ── Gemini API Helper ────────────────────────────────────────────────────────

def _call_gemini(model: str, prompt: str, max_retries: int = 5) -> str:
    url = f"{GEMINI_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"
    for attempt in range(max_retries):
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7},
            },
            timeout=120,
        )
        if resp.status_code in (429, 503):
            wait = 2 ** (attempt + 1)
            reason = "rate limited" if resp.status_code == 429 else "service unavailable"
            print(f"   ⏳ Gemini {reason}, retrying in {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError(f"No candidates in Gemini response: {data}")
        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return text.strip()
    resp.raise_for_status()
    return ""


# ── Main Pipeline ────────────────────────────────────────────────────────────

def run_pipeline(video_url: str | None = None, output_path: str | None = None, script_text: str | None = None):
    check_env()
    print(f"\n{'='*60}")
    print(f"🎥 FACELESS VIDEO GENERATOR")
    print(f"{'='*60}")

    if script_text:
        print(f"Input: custom script ({len(script_text)} chars)\n")
        script = script_text
    else:
        if not video_url:
            raise ValueError("Must provide either video_url or script_text")
        print(f"Input: {video_url}\n")

        # 1. Get transcript
        raw_transcript, source = get_transcript(video_url)
        print(f"   ✅ Transcript extracted ({source}, {len(raw_transcript)} chars)\n")

        # 2. Clean transcript
        transcript = clean_transcript(raw_transcript, source)
        print(f"   ✅ Cleaned ({len(transcript)} chars)\n")

        # 3. Write script
        script = write_script(transcript)
        print(f"   ✅ Script written ({len(script)} chars)\n")

    # 4. Generate keywords + 5. TTS (parallel)
    with ThreadPoolExecutor(max_workers=2) as pool:
        kw_future = pool.submit(generate_keywords, script)
        tts_future = pool.submit(text_to_speech, script)
        keywords = kw_future.result()
        audio_bytes = tts_future.result()
    print(f"   ✅ TTS generated ({len(audio_bytes)} bytes)\n")

    # 6. Upload TTS to Supabase + measure duration
    audio_duration = _get_audio_duration_seconds(audio_bytes)
    audio_url = upload_to_supabase(audio_bytes, "tts-audio.mp3", "audio/mpeg")
    print(f"   ✅ Audio uploaded ({audio_duration:.1f}s): {audio_url}\n")

    # Generate subtitle clips from script
    print("📝 Generating subtitles...")
    subtitle_clips = generate_subtitle_clips(script, audio_duration)
    print()

    # Generate overlay timestamps via Gemini
    print("✨ Generating overlay timestamps...")
    overlays = generate_overlay_timestamps(script, audio_duration)
    overlay_clips = build_overlay_clips(overlays) if overlays else None
    print()

    # 7-8. Search + download + upload B-roll videos (sequential per keyword to avoid duplicates)
    print("🎞️  Searching & uploading B-roll videos...")
    used_ids = set()
    video_urls = []
    for i, kw in enumerate(keywords, 1):
        url = process_keyword(kw, i, used_ids)
        video_urls.append(url)
    print()

    uploaded_count = sum(1 for v in video_urls if v)
    print(f"   ✅ {uploaded_count}/{len(keywords)} videos ready\n")

    # 9. Render via Shotstack
    render_id = render_video(audio_url, audio_duration, video_urls, subtitle_clips=subtitle_clips, overlay_clips=overlay_clips)

    # 10. Wait for render + download
    final_url = wait_for_render(render_id)
    print(f"   📹 Final video URL: {final_url}\n")

    # Download if output path specified
    if output_path:
        print(f"📥 Downloading to {output_path}...")
        dl = requests.get(final_url, timeout=300)
        dl.raise_for_status()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(dl.content)
        print(f"   ✅ Saved ({len(dl.content) / 1024 / 1024:.1f} MB)")

    # Save script to workspace
    script_path = "/home/workspace/Documents/faceless-video-last-script.txt"
    Path(script_path).parent.mkdir(parents=True, exist_ok=True)
    Path(script_path).write_text(script, encoding="utf-8")
    print(f"   📝 Script saved to {script_path}")

    print(f"\n{'='*60}")
    print(f"✅ DONE!")
    print(f"   Final video: {final_url}")
    if output_path:
        print(f"   Local file:  {output_path}")
    print(f"{'='*60}\n")

    return final_url


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Faceless Video Generator — Create viral TikTok videos from any video URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 faceless_video.py https://www.youtube.com/watch?v=xxxxx
  python3 faceless_video.py https://www.tiktok.com/@user/video/123 --output Videos/output.mp4
  python3 faceless_video.py --script "Your Vietnamese script here..." --output Videos/output.mp4
  python3 faceless_video.py --script-file my_script.txt

Environment variables (set in Zo Settings > Advanced > Secrets):
  GEMINI_API_KEY          Google Gemini API key
  GOOGLE_TTS_API_KEY      Google Cloud TTS API key
  PEXELS_API_KEY          Pexels API key
  SUPABASE_SERVICE_KEY    Supabase service role key
  SHOTSTACK_API_KEY       Shotstack API key (free tier = stage)
  SHOTSTACK_ENV           "stage" (free) or "v1" (production), default: stage
  SUPABASE_URL            Supabase project URL (optional, has default)
  SUPABASE_BUCKET         Supabase storage bucket (optional, has default)
  BG_MUSIC_URL            Background music URL (optional, has default)
        """,
    )
    parser.add_argument("url", nargs="?", help="TikTok or YouTube video URL (omit when using --script / --script-file)")
    parser.add_argument("--output", "-o", help="Download final video to this path")
    parser.add_argument("--script", help="Use this text as the script directly (skips transcript extraction + rewriting)")
    parser.add_argument("--script-file", help="Read script text from a file (skips transcript extraction + rewriting)")
    args = parser.parse_args()

    script_text = args.script
    if args.script_file:
        script_text = Path(args.script_file).read_text(encoding="utf-8").strip()

    if not args.url and not script_text:
        parser.error("Must provide either a URL, --script, or --script-file")

    run_pipeline(args.url, args.output, script_text=script_text)


if __name__ == "__main__":
    main()
