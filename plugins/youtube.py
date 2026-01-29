from utils import YoutubeDL, re, lru_cache, hashlib, InputMediaPhotoExternal, db
from utils import os, InputMediaUploadedDocument, DocumentAttributeVideo, fast_upload
from utils import DocumentAttributeAudio, DownloadError, WebpageMediaEmptyError
from run import Button, Buttons

class YoutubeDownloader:

    @classmethod
    def initialize(cls):
        cls.MAXIMUM_DOWNLOAD_SIZE_MB = 100
        cls.DOWNLOAD_DIR = 'repository/Youtube'
        # Ensure the cookie file is recognized from the root directory
        cls.COOKIE_FILE = 'cookies.txt' 

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
            match = re.match(pattern, url)
            if match:
                return True
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
                else:
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
                'quiet': True, 
                'no_warnings': True,
                'cookiefile': YoutubeDownloader.COOKIE_FILE
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                thumbnail_url = info.get('thumbnail')

            video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']

            all_buttons = []
            v_count = 0
            for f in reversed(video_formats):
                if v_count >= 4: break
                ext = f['ext']
                res = f.get('resolution') or f.get('format_note') or "Video"
                size = f.get('filesize') or f.get('filesize_approx') or 0
                size_mb = f"{size / 1024 / 1024:.1f}" if size > 0 else "?"
                data = f"yt/dl/{video_id}/{ext}/{f['format_id']}/{size_mb}"
                all_buttons.append([Button.inline(f"🎬 {ext} {res} ({size_mb}MB)", data=data)])
                v_count += 1

            a_count = 0
            for f in reversed(audio_formats):
                if a_count >= 3: break
                ext = f['ext']
                size = f.get('filesize') or f.get('filesize_approx') or 0
                size_mb = f"{size / 1024 / 1024:.1f}" if size > 0 else "?"
                data = f"yt/dl/{video_id}/{ext}/{f['format_id']}/{size_mb}"
                all_buttons.append([Button.inline(f"🎵 {ext} Audio ({size_mb}MB)", data=data)])
                a_count += 1

            all_buttons.append(Buttons.cancel_button)

            if thumbnail_url:
                try:
                    await client.send_file(
                        event.chat_id,
                        file=InputMediaPhotoExternal(thumbnail_url),
                        caption="**Select a format to download:**",
                        buttons=all_buttons
                    )
                except:
                    await event.respond("**Select a format to download:**", buttons=all_buttons)
            else:
                await event.respond("**Select a format to download:**", buttons=all_buttons)

        except Exception as e:
            err = str(e)
            if "Sign in to confirm" in err:
                await event.respond("⚠️ YouTube is blocking this request. Admin needs to refresh `cookies.txt`.")
            else:
                await event.respond(f"❌ Error fetching video info: {err[:100]}")

    @staticmethod
    async def download_and_send_yt_file(client, event):
        user_id = event.sender_id
        if await db.get_file_processing_flag(user_id):
            return await event.respond("⚠️ You already have a file being processed.")

        try:
            data = event.data.decode('utf-8')
            parts = data.split('/')
            video_id = parts[2]
            extension = parts[3]
            format_id = parts[4]
            size_mb = float(parts[5]) if parts[5] != "?" else 0

            if size_mb > YoutubeDownloader.MAXIMUM_DOWNLOAD_SIZE_MB:
                return await event.answer(f"⚠️ Size limit {YoutubeDownloader.MAXIMUM_DOWNLOAD_SIZE_MB}MB exceeded.", alert=True)

            await db.set_file_processing_flag(user_id, is_processing=True)
            url = f"https://www.youtube.com/watch?v={video_id}"
            path = YoutubeDownloader.get_file_path(url, format_id, extension)

            if not os.path.isfile(path):
                prog_msg = await event.respond("📥 Downloading...")
                # FIX: Correct Indentation (16 spaces)
                ydl_opts = {
                    'format': format_id,
                    'outtmpl': path,
                    'quiet': True,
                    'cookiefile': YoutubeDownloader.COOKIE_FILE,
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                    'nocheckcertificate': True,
                    'allow_unplayable_formats': True,
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    duration = info.get('duration', 0)
                    width = info.get('width', 0)
                    height = info.get('height', 0)
                await prog_msg.delete()
            else:
                await event.respond("📂 Found in local cache. Preparing...")
                ydl_opts = {'quiet': True, 'cookiefile': YoutubeDownloader.COOKIE_FILE}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    duration = info.get('duration', 0)
                    width = info.get('width', 0)
                    height = info.get('height', 0)

            upload_msg = await event.respond("📤 Uploading to Telegram...")
            async with client.action(event.chat_id, 'document'):
                media_file = await fast_upload(client=client, file_location=path, reply=None, name=path, progress_bar_function=None)
                uploaded_file = await client.upload_file(media_file)

                if extension == "mp4":
                    attr = DocumentAttributeVideo(duration=int(duration), w=int(width), h=int(height), supports_streaming=True)
                    media = InputMediaUploadedDocument(file=uploaded_file, mime_type='video/mp4', attributes=[attr])
                else:
                    attr = DocumentAttributeAudio(duration=int(duration), title="YouTube Download", performer="@YourBot")
                    mime = 'audio/m4a' if extension == "m4a" else 'audio/mpeg'
                    media = InputMediaUploadedDocument(file=uploaded_file, mime_type=mime, attributes=[attr])

                await client.send_file(event.chat_id, file=media, caption="Done! Enjoy your music/video. 🎧", supports_streaming=True)
            await upload_msg.delete()

        except Exception as Err:
            await event.respond(f"❌ Failed to process: {str(Err)[:100]}")
        finally:
            await db.set_file_processing_flag(user_id, is_processing=False)
