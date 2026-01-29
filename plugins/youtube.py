from utils import YoutubeDL, re, lru_cache, hashlib, InputMediaPhotoExternal, db
from utils import os, InputMediaUploadedDocument, DocumentAttributeVideo, fast_upload
from utils import DocumentAttributeAudio, DownloadError, WebpageMediaEmptyError
from run import Button, Buttons
import asyncio

class YoutubeDownloader:

    @classmethod
    def initialize(cls):
        cls.MAXIMUM_DOWNLOAD_SIZE_MB = 100
        cls.DOWNLOAD_DIR = 'repository/Youtube'
        cls.COOKIE_FILE = 'cookies.txt' 

        # --- Sanity Check: View this in Koyeb Logs ---
        if os.path.exists(cls.COOKIE_FILE):
            print(f"✅ Found {cls.COOKIE_FILE} - Size: {os.path.getsize(cls.COOKIE_FILE)} bytes")
        else:
            print(f"❌ WARNING: {cls.COOKIE_FILE} NOT FOUND. YouTube will likely block you.")

        if not os.path.isdir(cls.DOWNLOAD_DIR):
            os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)

    @lru_cache(maxsize=128)
    def get_file_path(url, format_id, extension):
        url = url + format_id + extension
        url_hash = hashlib.blake2b(url.encode()).hexdigest()
        filename = f"{url_hash}.{extension}"
        return os.path.join(YoutubeDownloader.DOWNLOAD_DIR, filename)

    @staticmethod
    def is_youtube_link(url):
        youtube_patterns = [
            r'(https?\:\/\/)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11}).*',
            r'(https?\:\/\/)?www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/embed\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/v\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/[^\/]+\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
        ]
        for pattern in youtube_patterns:
            if re.match(pattern, url): return True
        return False

    @staticmethod
    def extract_youtube_url(text):
        youtube_patterns = [
            r'(https?\:\/\/)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11}).*',
            r'(https?\:\/\/)?www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/embed\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/v\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/[^\/]+\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
        ]
        for pattern in youtube_patterns:
            match = re.search(pattern, text)
            if match:
                video_id = match.group(2)
                if 'youtube.com/shorts/' in match.group(0):
                    return f'https://www.youtube.com/shorts/{video_id}'
                return f'https://www.youtube.com/watch?v={video_id}'
        return None

    @staticmethod
    async def send_youtube_info(client, event, youtube_link):
        url = youtube_link
        video_id = (youtube_link.split("&")[0].split("?si=")[0]
                    .replace("https://www.youtube.com/watch?v=", "")
                    .replace("https://www.youtube.com/shorts/", "")
                    .replace("https://youtu.be/", ""))
        
        try:
            ydl_opts = {
                'quiet': True, 'no_warnings': True,
                'cookiefile': YoutubeDownloader.COOKIE_FILE
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                formats = info.get('formats', [])
                thumbnail_url = info.get('thumbnail')

            all_buttons = []
            # We filter for the top 6 combined formats to increase stability
            v_count = 0
            for f in reversed(formats):
                if v_count >= 6: break
                
                ext = f.get('ext', 'mp4')
                res = f.get('resolution') or f.get('format_note') or "Video"
                if "storyboard" in res.lower(): continue
                
                size = f.get('filesize') or f.get('filesize_approx') or 0
                size_mb = f"{size / 1024 / 1024:.1f}" if size > 0 else "?"
                
                # We pass the format_id AND the resolution as a fallback
                data = f"yt/dl/{video_id}/{ext}/{f['format_id']}/{size_mb}"
                all_buttons.append([Button.inline(f"🎬 {ext} {res} ({size_mb}MB)", data=data)])
                v_count += 1

            all_buttons.append(Buttons.cancel_button)

            await client.send_file(
                event.chat_id,
                file=InputMediaPhotoExternal(thumbnail_url) if thumbnail_url else None,
                caption="**Select a format to download:**",
                buttons=all_buttons
            )

        except Exception as e:
            err = str(e)
            if "Sign in to confirm" in err:
                await event.respond("⚠️ YouTube blocked the session. Admin needs to refresh `cookies.txt`.")
            else:
                await event.respond(f"❌ Error fetching info: {err[:100]}")

    @staticmethod
    async def download_and_send_yt_file(client, event):
        user_id = event.sender_id
        if await db.get_file_processing_flag(user_id):
            return await event.respond("⚠️ Already processing a file.")

        try:
            data = event.data.decode('utf-8')
            parts = data.split('/')
            video_id, extension, format_id, size_mb = parts[2], parts[3], parts[4], parts[5]

            await db.set_file_processing_flag(user_id, is_processing=True)
            url = f"https://www.youtube.com/watch?v={video_id}"
            path = YoutubeDownloader.get_file_path(url, format_id, extension)

            if not os.path.isfile(path):
                prog_msg = await event.respond("📥 Downloading...")
                
                # --- FIXED FALLBACK LOGIC ---
                # We tell yt-dlp: Try the specific ID, if not, find the best audio+video
                ydl_opts = {
                    'format': f'{format_id}/bestvideo+bestaudio/best',
                    'outtmpl': path,
                    'quiet': True,
                    'cookiefile': YoutubeDownloader.COOKIE_FILE,
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                    'nocheckcertificate': True,
                }
                
                with YoutubeDL(ydl_opts) as ydl:
                    info = await asyncio.to_thread(ydl.extract_info, url, download=True)
                    duration, width, height = info.get('duration', 0), info.get('width', 0), info.get('height', 0)
                await prog_msg.delete()
            else:
                await event.respond("📂 Found in local cache...")
                with YoutubeDL({'quiet': True, 'cookiefile': YoutubeDownloader.COOKIE_FILE}) as ydl:
                    info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                    duration, width, height = info.get('duration', 0), info.get('width', 0), info.get('height', 0)

            upload_msg = await event.respond("📤 Uploading...")
            async with client.action(event.chat_id, 'document'):
                media_file = await fast_upload(client=client, file_location=path, reply=None, name=path, progress_bar_function=None)
                uploaded_file = await client.upload_file(media_file)

                if extension == "mp4":
                    attr = [DocumentAttributeVideo(duration=int(duration), w=int(width), h=int(height), supports_streaming=True)]
                    media = InputMediaUploadedDocument(file=uploaded_file, mime_type='video/mp4', attributes=attr)
                else:
                    attr = [DocumentAttributeAudio(duration=int(duration), title="YouTube Download", performer="@YourBot")]
                    media = InputMediaUploadedDocument(file=uploaded_file, mime_type='audio/mpeg', attributes=attr)

                await client.send_file(event.chat_id, file=media, caption="Done! 🎧", supports_streaming=True)
            await upload_msg.delete()

        except Exception as Err:
            await event.respond(f"❌ Error: {str(Err)[:100]}")
        finally:
            await db.set_file_processing_flag(user_id, is_processing=False)
