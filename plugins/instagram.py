from utils import bs4, wget
from utils import asyncio, re, requests

class Insta:

    @classmethod
    def initialize(cls):
        cls.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Length": "99",
            "Origin": "https://saveig.app",
            "Connection": "keep-alive",
            "Referer": "https://saveig.app/en",
        }

    @staticmethod
    def is_instagram_url(text) -> bool:
        if not text: return False
        pattern = r'(?:https?:\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am)(?:\/(?:p|reel|tv|stories)\/(?:[^\s\/]+)|\/([\w-]+)(?:\/(?:[^\s\/]+))?)'
        match = re.search(pattern, text)
        return bool(match)

    @staticmethod
    def extract_url(text) -> str | None:
        if not text: return None
        pattern = r'(https?:\/\/(?:www\.)?(?:ddinstagram\.com|instagram\.com|instagr\.am)\/(?:p|reel|tv|stories)\/[\w-]+\/?(?:\?[^\s]+)?(?:={1,2})?)'
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def determine_content_type(text) -> str:
        # --- FIX 1: Null Guard ---
        if not text: 
            return None

        content_types = {
            '/p/': 'post',
            '/reel/': 'reel',
            '/tv': 'igtv',
            '/stories/': 'story',
        }

        for pattern, content_type in content_types.items():
            if pattern in text:
                return content_type

        return None

    @staticmethod
    def is_publicly_available(url) -> bool:
        if not url: return False
        try:
            response = requests.get(url, headers=Insta.headers, timeout=10)
            return response.status_code == 200
        except:
            return False

    @staticmethod
    async def download_content(client, event, start_message, link) -> bool:
        # --- FIX 2: Ensure link exists before processing ---
        if not link:
            if start_message: await start_message.edit("❌ Invalid link detected.")
            return False

        content_type = Insta.determine_content_type(link)
        try:
            if content_type == 'reel':
                await Insta.download_reel(client, event, link)
            elif content_type == 'post':
                await Insta.download_post(client, event, link)
            elif content_type == 'story':
                await Insta.download_story(client, event, link)
            else:
                await event.reply("Sorry, unable to determine content type. Is it a public post?")
            
            if start_message: await start_message.delete()
            return True
        except Exception as e:
            print(f"Insta Download Error: {e}")
            await event.reply("Sorry, unable to find the requested content. Please ensure it's publicly available.")
            if start_message: await start_message.delete()
            return False

    @staticmethod
    async def download(client, event) -> bool:
        link = Insta.extract_url(event.message.text)
        
        # --- FIX 3: Prevent crash if no link is found ---
        if not link:
            return False # Silent return, or add a reply if preferred

        start_message = await event.respond("Processing Your insta link ....")
        
        try:
            # Check for ddinstagram only if link is valid
            if link and "ddinstagram.com" not in link:
                link = link.replace("instagram.com", "ddinstagram.com")
            
            return await Insta.download_content(client, event, start_message, link)
        except Exception:
            # Fallback to original link if replace fails
            return await Insta.download_content(client, event, start_message, link)

    @staticmethod
    async def download_reel(client, event, link):
        try:
            meta_tag = await Insta.get_meta_tag(link)
            if meta_tag and 'content' in meta_tag.attrs:
                content_value = f"https://ddinstagram.com{meta_tag['content']}"
            else:
                raise Exception
        except:
            meta_tag = await Insta.search_saveig(link)
            content_value = meta_tag[0] if meta_tag else None

        if content_value:
            await Insta.send_file(client, event, content_value)
        else:
            await event.reply("Oops, I couldn't extract the video from this Reel.")

    @staticmethod
    async def download_post(client, event, link):
        meta_tags = await Insta.search_saveig(link)
        if meta_tags:
            for meta in meta_tags:
                await asyncio.sleep(1)
                await Insta.send_file(client, event, meta)
        else:
            await event.reply("Oops, I couldn't find the media in this post.")

    @staticmethod
    async def download_story(client, event, link):
        meta_tag = await Insta.search_saveig(link)
        if meta_tag:
            await Insta.send_file(client, event, meta_tag[0])
        else:
            await event.reply("Oops, stories are hard! I couldn't get this one.")

    @staticmethod
    async def get_meta_tag(link):
        try:
            getdata = requests.get(link, timeout=10).text
            soup = bs4.BeautifulSoup(getdata, 'html.parser')
            return soup.find('meta', attrs={'property': 'og:video'})
        except:
            return None

    @staticmethod
    async def search_saveig(link):
        try:
            meta_tag = requests.post("https://saveig.app/api/ajaxSearch", 
                                     data={"q": link, "t": "media", "lang": "en"},
                                     headers=Insta.headers, timeout=15)
            if meta_tag.ok:
                res = meta_tag.json()
                return re.findall(r'href="(https?://[^"]+)"', res['data'])
        except:
            return None
        return None

    @staticmethod
    async def send_file(client, event, content_value):
        try:
            await client.send_file(event.chat_id, content_value, caption="Here's your Instagram content")
        except:
            try:
                # Fallback download using wget
                fileoutput = f"instadownload_{asyncio.get_event_loop().time()}.mp4"
                wget.download(content_value, out=fileoutput)
                await client.send_file(event.chat_id, fileoutput, caption="Here's your Instagram content")
                if os.path.exists(fileoutput): os.remove(fileoutput)
            except:
                await event.respond(f"I found the content, but Telegram blocked the upload. You can view it here: {content_value}")
