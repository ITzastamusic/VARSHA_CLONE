import asyncio

import os

import re

import json

import urllib.parse

from typing import Union



import requests

import yt_dlp

from pyrogram.enums import MessageEntityType

from pyrogram.types import Message

from youtubesearchpython.__future__ import VideosSearch

from Clonify.utils.database import is_on_off

from Clonify.utils.formatters import time_to_seconds

import glob

import random

import logging

import aiohttp

import config

from os import getenv



# Your deployed API first (search + resolve + download/cached)

API_BASE = os.getenv("DOWNLOADER_API_BASE", "https://youtubeapi-f071b339ce5d.herokuapp.com")



# Legacy quickearn config (fallback)

API_URL = getenv("API_URL", "https://api.thequickearn.xyz")

API_KEY = getenv("API_KEY", "NxGBNexGenBotsa02f5a")

VIDEO_API_URL = getenv("VIDEO_API_URL", "https://api.video.thequickearn.xyz")



# === SAAVN API CONFIGURATION ===

SAVN_API_BASE = "https://apikeyy-zeta.vercel.app/api/search"

SAVN_SONGS_API = "https://apikeyy-zeta.vercel.app/api/songs"



def cookie_txt_file():

    cookie_dir = f"{os.getcwd()}/cookies"

    if not os.path.exists(cookie_dir):

        print("⚠️ Cookies directory not found")

        return None

    try:

        cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]

        if not cookies_files:

            print("⚠️ No cookie files found")

            return None

        cookie_file = os.path.join(cookie_dir, random.choice(cookies_files))

        if not os.path.exists(cookie_file):

            print(f"⚠️ Cookie file not found: {cookie_file}")

            return None

        return cookie_file

    except Exception as e:

        print(f"⚠️ Error accessing cookies directory: {e}")

        return None



# ===== Helper: use your API first (works with name/link/id) =====



def _extract_video_id(text: str) -> str | None:

    if not text:

        return None

    t = text.strip()

    if len(t) in (11, 12) and "/" not in t and " " not in t:

        return t

    low = t.lower()

    if "youtu.be/" in low:

        try:

            return t.split("youtu.be/")[1].split("?")[0].split("/")[0]

        except Exception:

            return None

    if "watch?v=" in low:

        try:

            return t.split("watch?v=")[1].split("&")[0]

        except Exception:

            return None

    return None



async def _api_fetch_song(query_or_link: str):

    vid = _extract_video_id(query_or_link)

    if vid:

        endpoint = f"{API_BASE}/song/{vid}"

    else:

        qs = urllib.parse.urlencode({"q": query_or_link})

        endpoint = f"{API_BASE}/song-by-query?{qs}"



    async with aiohttp.ClientSession() as session:

        async with session.get(endpoint, timeout=300) as resp:

            if resp.status != 200:

                txt = await resp.text()

                print(f"[API_BASE FAIL] {resp.status} {txt}")

                return None

            data = await resp.json()



    link = data.get("link")

    if not link:

        return None

    if link.startswith("/"):

        link = f"{API_BASE}{link}"



    return {

        "link": link,

        "video_id": data.get("video_id") or vid,

        "title": data.get("title"),

        "format": data.get("format", "mp3"),

    }



async def _download_from_url_to_file(url: str, out_path: str) -> str | None:

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    async with aiohttp.ClientSession() as session:

        async with session.get(url, timeout=600) as resp:

            if resp.status != 200:

                print(f"[Download URL FAIL] {resp.status}")

                return None

            with open(out_path, "wb") as f:

                async for chunk in resp.content.iter_chunked(8192):

                    if chunk:

                        f.write(chunk)

    return out_path if os.path.exists(out_path) and os.path.getsize(out_path) > 0 else None



# === SAAVN API FUNCTIONS ===

def clean_query(query: str):

    """Clean and optimize search query"""

    stop_words = ["song", "music", "video", "official", "lyrics", "hd", "4k", "full"]

    query = query.lower().strip()

    words = query.split()

    cleaned_words = [word for word in words if word not in stop_words]

    cleaned_query = " ".join(cleaned_words)

    cleaned_query = re.sub(r"[^\w\s]", "", cleaned_query)

    cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()

    return cleaned_query



def find_best_match(songs: list, original_query: str):

    """Find the best matching song from search results with improved matching"""

    if not songs:

        return None

    original_query = original_query.lower().strip()

    cleaned_query = clean_query(original_query)

    query_words = cleaned_query.split()[:3]



    scored_songs = []

    for song in songs:

        title = song.get("title", "").lower()

        artist = song.get("primaryArtists", "").lower()

        score = 0

        if cleaned_query in title:

            score += 100

        title_words = title.split()

        matching_words = sum(1 for word in query_words if word in title_words)

        if matching_words >= len(query_words) * 0.7:

            score += 80

        score += matching_words * 15

        if len(query_words) >= 2:

            if query_words[0] in title and query_words[1] in title:

                if title.find(query_words[0]) < title.find(query_words[1]):

                    score += 30

        if any(word in artist for word in query_words):

            score += 10

        length_diff = abs(len(cleaned_query) - len(title))

        if length_diff < 15:

            score += 10

        elif length_diff > 30:

            score -= 20

        if len(title_words) > len(query_words) * 2:

            score -= 15

        scored_songs.append((score, song))



    scored_songs.sort(key=lambda x: x[0], reverse=True)

    if scored_songs and scored_songs[0][0] > 20:

        return scored_songs[0][1]

    return None



async def search_saavn_song(query: str):

    """Search for songs using Saavn API with multiple strategies"""

    try:

        print(f"🔍 Searching Saavn with original query: {query}")

        response = requests.get(SAVN_API_BASE, params={"query": query})

        if response.status_code == 200:

            data = response.json()

            if data.get("success") and "data" in data:

                songs = []

                if "songs" in data["data"] and "results" in data["data"]["songs"]:

                    songs = data["data"]["songs"]["results"]

                elif "topQuery" in data["data"] and "results" in data["data"]["topQuery"]:

                    songs = data["data"]["topQuery"]["results"]

                elif isinstance(data["data"], list):

                    songs = data["data"]

                if songs:

                    best_match = find_best_match(songs, query)

                    if best_match:

                        print(f"✅ Found match with original query: {best_match.get('title')}")

                        return [best_match]



        cleaned_query = clean_query(query)

        if cleaned_query != query.lower():

            print(f"🔍 Trying cleaned query: {cleaned_query}")

            response = requests.get(SAVN_API_BASE, params={"query": cleaned_query})

            if response.status_code == 200:

                data = response.json()

                if data.get("success") and "data" in data:

                    songs = []

                    if "songs" in data["data"] and "results" in data["data"]["songs"]:

                        songs = data["data"]["songs"]["results"]

                    elif "topQuery" in data["data"] and "results" in data["data"]["topQuery"]:

                        songs = data["data"]["topQuery"]["results"]

                    elif isinstance(data["data"], list):

                        songs = data["data"]

                    if songs:

                        best_match = find_best_match(songs, query)

                        if best_match:

                            print(f"✅ Found match with cleaned query: {best_match.get('title')}")

                            return [best_match]



        query_variations = [

            query.replace(" ", ""),

            query.split()[0] if len(query.split()) > 1 else query,

            query.split()[-1] if len(query.split()) > 1 else query,

        ]

        for variation in query_variations:

            if variation != query and variation != cleaned_query:

                print(f"🔍 Trying variation: {variation}")

                response = requests.get(SAVN_API_BASE, params={"query": variation})

                if response.status_code == 200:

                    data = response.json()

                    if data.get("success") and "data" in data:

                        songs = []

                        if "songs" in data["data"] and "results" in data["data"]["songs"]:

                            songs = data["data"]["songs"]["results"]

                        elif "topQuery" in data["data"] and "results" in data["data"]["topQuery"]:

                            songs = data["data"]["topQuery"]["results"]

                        elif isinstance(data["data"], list):

                            songs = data["data"]

                        if songs:

                            best_match = find_best_match(songs, query)

                            if best_match:

                                print(f"✅ Found match with variation '{variation}': {best_match.get('title')}")

                                return [best_match]



        print(f"❌ No matches found for query: {query}")

        return None

    except Exception as e:

        print(f"Saavn search error: {e}")

        return None



async def get_saavn_download_url(song_id: str, song_url: str):

    """Get download URL for Saavn song"""

    try:

        response = requests.get(SAVN_SONGS_API, params={"ids": song_id, "link": song_url})

        print(f"Saavn Songs API Response Status: {response.status_code}")

        if response.status_code != 200:

            return None

        data = response.json()

        print(f"Saavn Songs API Data: {data}")

        if data.get("success") and "data" in data and len(data["data"]) > 0:

            song_details = data["data"][0]

            download_urls = song_details.get("downloadUrl", [])

            if download_urls and isinstance(download_urls, list):

                for url_info in reversed(download_urls):

                    if isinstance(url_info, dict) and "url" in url_info:

                        return url_info["url"]

        return None

    except Exception as e:

        print(f"Saavn download URL error: {e}")

        return None



async def download_saavn_song(query: str):

    """Download song from Saavn API with enhanced matching"""

    try:

        print(f"🎵 Starting Saavn download for: {query}")

        songs = await search_saavn_song(query)

        if not songs:

            print(f"❌ No songs found for query: {query}")

            return None, None

        song = songs[0]

        title = song.get("title", "Unknown Title")

        artist = song.get("primaryArtists", "Unknown Artist")

        song_id = song.get("id")

        song_url = song.get("url")

        print(f"📀 Selected song: {title} by {artist}")

        print(f"🆔 Song ID: {song_id}")

        if not song_id:

            print("❌ No song ID found")

            return None, None

        print(f"🔗 Getting download URL for song ID: {song_id}")

        download_url = await get_saavn_download_url(song_id, song_url)

        if not download_url:

            print("❌ Failed to get download URL")

            return None, None

        print(f"✅ Successfully got download URL: {download_url[:50]}...")

        return download_url, {

            "title": title,

            "artist": artist,

            "source": "Saavn",

            "quality": "320kbps",

            "song_id": song_id

        }

    except Exception as e:

        print(f"❌ Saavn download error: {e}")

        return None, None



# ===== Modified: use your API first; fallback to legacy quickearn flow =====

async def download_song(link: str):

    """

    Use your deployed API first (handles name/link/id), download the returned link locally.

    On failure, fallback to the legacy quickearn API with YouTube video_id.

    """

    # 1) Try your API first

    try:

        info = await _api_fetch_song(link)

        if info:

            video_id = info.get("video_id") or (_extract_video_id(link) or "unknown")

            ext = (info.get("format") or "mp3").lower()

            if not ext or ext == "unknown":

                ext = "mp3"

            download_folder = "downloads"

            os.makedirs(download_folder, exist_ok=True)

            out_path = os.path.join(download_folder, f"{video_id}.{ext}")

            fetched = await _download_from_url_to_file(info["link"], out_path)

            if fetched:

                print(f"✅ Downloaded via API_BASE: {fetched}")

                return fetched

    except Exception as e:

        print(f"⚠️ API_BASE flow failed: {e}")



    # 2) Fallback to legacy quickearn by extracting YouTube video_id

    try:

        video_id = link.split("v=")[-1].split("&")[0]

    except Exception as e:

        print(f"⚠️ Error extracting video ID from link: {e}")

        return None



    download_folder = "downloads"

    try:

        os.makedirs(download_folder, exist_ok=True)

    except Exception as e:

        print(f"⚠️ Error creating download folder: {e}")

        return None



    for ext in ["mp3", "m4a", "webm"]:

        file_path = f"{download_folder}/{video_id}.{ext}"

        if os.path.exists(file_path):

            print(f"📁 File already exists: {file_path}")

            return file_path



    song_url = f"{API_URL}/song/{video_id}?api={API_KEY}"

    async with aiohttp.ClientSession() as session:

        for attempt in range(10):

            try:

                async with session.get(song_url) as response:

                    if response.status != 200:

                        raise Exception(f"API request failed with status code {response.status}")

                    data = await response.json()

                    status = data.get("status", "").lower()

                    if status == "done":

                        download_url = data.get("link")

                        if not download_url:

                            raise Exception("API response did not provide a download URL.")

                        break

                    elif status == "downloading":

                        await asyncio.sleep(4)

                    else:

                        error_msg = data.get("error") or data.get("message") or f"Unexpected status '{status}'"

                        raise Exception(f"API error: {error_msg}")

            except Exception as e:

                print(f"[FAIL] {e}")

                return None

        else:

            print("⏱️ Max retries reached. Still downloading...")

            return None



        try:

            file_format = data.get("format", "mp3")

            file_extension = file_format.lower()

            file_name = f"{video_id}.{file_extension}"

            file_path = os.path.join(download_folder, file_name)

            async with session.get(download_url) as file_response:

                if file_response.status != 200:

                    print(f"⚠️ Download failed with status: {file_response.status}")

                    return None

                with open(file_path, "wb") as f:

                    while True:

                        chunk = await file_response.content.read(8192)

                        if not chunk:

                            break

                        f.write(chunk)

            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:

                print(f"✅ Successfully downloaded: {file_path}")

                return file_path

            else:

                print(f"⚠️ Downloaded file is empty or doesn't exist")

                return None

        except aiohttp.ClientError as e:

            print(f"Network or client error occurred while downloading: {e}")

            return None

        except Exception as e:

            print(f"Error occurred while downloading song: {e}")

            return None



async def download_video(link: str):

    video_id = link.split("v=")[-1].split("&")[0]

    download_folder = "downloads"

    for ext in ["mp4", "webm", "mkv"]:

        file_path = f"{download_folder}/{video_id}.{ext}"

        if os.path.exists(file_path):

            return file_path



    video_url = f"{VIDEO_API_URL}/video/{video_id}?api={API_KEY}"

    async with aiohttp.ClientSession() as session:

        for attempt in range(10):

            try:

                async with session.get(video_url) as response:

                    if response.status != 200:

                        raise Exception(f"API request failed with status code {response.status}")

                    data = await response.json()

                    status = data.get("status", "").lower()

                    if status == "done":

                        download_url = data.get("link")

                        if not download_url:

                            raise Exception("API response did not provide a download URL.")

                        break

                    elif status == "downloading":

                        await asyncio.sleep(8)

                    else:

                        error_msg = data.get("error") or data.get("message") or f"Unexpected status '{status}'"

                        raise Exception(f"API error: {error_msg}")

            except Exception as e:

                print(f"[FAIL] {e}")

                return None

        else:

            print("⏱️ Max retries reached. Still downloading...")

            return None



        try:

            file_format = data.get("format", "mp4")

            file_extension = file_format.lower()

            file_name = f"{video_id}.{file_extension}"

            os.makedirs(download_folder, exist_ok=True)

            file_path = os.path.join(download_folder, file_name)

            async with session.get(download_url) as file_response:

                with open(file_path, "wb") as f:

                    while True:

                        chunk = await file_response.content.read(8192)

                        if not chunk:

                            break

                        f.write(chunk)

            return file_path

        except aiohttp.ClientError as e:

            print(f"Network or client error occurred while downloading: {e}")

            return None

        except Exception as e:

            print(f"Error occurred while downloading video: {e}")

            return None



async def check_file_size(link):

    async def get_format_info(link):

        cookie_file = cookie_txt_file()

        if not cookie_file:

            print("No cookies found. Cannot check file size.")

            return None

        proc = await asyncio.create_subprocess_exec(

            "yt-dlp",

            "--cookies", cookie_file,

            "-J",

            link,

            stdout=asyncio.subprocess.PIPE,

            stderr=asyncio.subprocess.PIPE,

        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:

            print(f"Error:\n{stderr.decode()}")

            return None

        return json.loads(stdout.decode())



    def parse_size(formats):

        total_size = 0

        for format in formats:

            if "filesize" in format:

                total_size += format["filesize"]

        return total_size



    info = await get_format_info(link)

    if info is None:

        return None

    formats = info.get("formats", [])

    if not formats:

        print("No formats found.")

        return None

    total_size = parse_size(formats)

    return total_size



async def shell_cmd(cmd):

    proc = await asyncio.create_subprocess_shell(

        cmd,

        stdout=asyncio.subprocess.PIPE,

        stderr=asyncio.subprocess.PIPE,

    )

    out, errorz = await proc.communicate()

    if errorz:

        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():

            return out.decode("utf-8")

        else:

            return errorz.decode("utf-8")

    return out.decode("utf-8")



class YouTubeAPI:

    def __init__(self):

        self.base = "https://www.youtube.com/watch?v="

        self.regex = r"(?:youtube\.com|youtu\.be)"

        self.status = "https://www.youtube.com/oembed?url="

        self.listbase = "https://youtube.com/playlist?list="

        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")



    async def exists(self, link: str, videoid: Union[bool, str] = None):

        if videoid:

            link = self.base + link

        if re.search(self.regex, link):

            return True

        else:

            return False



    async def url(self, message_1: Message) -> Union[str, None]:

        messages = [message_1]

        if message_1.reply_to_message:

            messages.append(message_1.reply_to_message)

        text = ""

        offset = None

        length = None

        for message in messages:

            if offset:

                break

            if message.entities:

                for entity in message.entities:

                    if entity.type == MessageEntityType.URL:

                        text = message.text or message.caption

                        offset, length = entity.offset, entity.length

                        break

            elif message.caption_entities:

                for entity in message.caption_entities:

                    if entity.type == MessageEntityType.TEXT_LINK:

                        return entity.url

        if offset in (None,):

            return None

        return text[offset : offset + length]



    async def details(self, link: str, videoid: Union[bool, str] = None):

        if videoid:

            link = self.base + link

        if "&" in link:

            link = link.split("&")[0]

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:

            title = result["title"]

            duration_min = result["duration"]

            thumbnail = result["thumbnails"][0]["url"].split("?")[0]

            vidid = result["id"]

            if str(duration_min) == "None":

                duration_sec = 0

            else:

                duration_sec = int(time_to_seconds(duration_min))

        return title, duration_min, duration_sec, thumbnail, vidid



    async def title(self, link: str, videoid: Union[bool, str] = None):

        if videoid:

            link = self.base + link

        if "&" in link:

            link = link.split("&")[0]

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:

            title = result["title"]

        return title



    async def duration(self, link: str, videoid: Union[bool, str] = None):

        if videoid:

            link = self.base + link

        if "&" in link:

            link = link.split("&")[0]

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:

            duration = result["duration"]

        return duration



    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):

        if videoid:

            link = self.base + link

        if "&" in link:

            link = link.split("&")[0]

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:

            thumbnail = result["thumbnails"][0]["url"].split("?")[0]

        return thumbnail



    async def video(self, link: str, videoid: Union[bool, str] = None):

        if videoid:

            link = self.base + link

        if "&" in link:

            link = link.split("&")[0]



        # Try video API first

        try:

            downloaded_file = await download_video(link)

            if downloaded_file:

                return 1, downloaded_file

        except Exception as e:

            print(f"Video API failed: {e}")



        # Fallback to cookies

        cookie_file = cookie_txt_file()

        if not cookie_file:

            return 0, "No cookies found. Cannot download video."



        proc = await asyncio.create_subprocess_exec(

            "yt-dlp",

            "--cookies", cookie_file,

            "-g",

            "-f",

            "best[height<=?720][width<=?1280]",

            f"{link}",

            stdout=asyncio.subprocess.PIPE,

            stderr=asyncio.subprocess.PIPE,

        )

        stdout, stderr = await proc.communicate()

        if stdout:

            return 1, stdout.decode().split("\n")[0]

        else:

            return 0, stderr.decode()



    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):

        if videoid:

            link = self.listbase + link

        if "&" in link:

            link = link.split("&")[0]



        cookie_file = cookie_txt_file()

        if not cookie_file:

            return []



        playlist = await shell_cmd(

            f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_file} --playlist-end {limit} --skip-download {link}"

        )

        try:

            result = playlist.split("\n")

            for key in result:

                if key == "":

                    result.remove(key)

        except:

            result = []

        return result



    async def track(self, link: str, videoid: Union[bool, str] = None):

        if videoid:

            link = self.base + link

        if "&" in link:

            link = link.split("&")[0]

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:

            title = result["title"]

            duration_min = result["duration"]

            vidid = result["id"]

            yturl = result["link"]

            thumbnail = result["thumbnails"][0]["url"].split("?")[0]

        track_details = {

            "title": title,

            "link": yturl,

            "vidid": vidid,

            "duration_min": duration_min,

            "thumb": thumbnail,

        }

        return track_details, vidid



    async def formats(self, link: str, videoid: Union[bool, str] = None):

        if videoid:

            link = self.base + link

        if "&" in link:

            link = link.split("&")[0]



        cookie_file = cookie_txt_file()

        if not cookie_file:

            return [], link



        ytdl_opts = {"quiet": True, "cookiefile": cookie_file}

        ydl = yt_dlp.YoutubeDL(ytdl_opts)

        with ydl:

            formats_available = []

            r = ydl.extract_info(link, download=False)

            for format in r["formats"]:

                try:

                    str(format["format"])

                except:

                    continue

                if not "dash" in str(format["format"]).lower():

                    try:

                        format["format"]

                        format["filesize"]

                        format["format_id"]

                        format["ext"]

                        format["format_note"]

                    except:

                        continue

                    formats_available.append(

                        {

                            "format": format["format"],

                            "filesize": format["filesize"],

                            "format_id": format["format_id"],

                            "ext": format["ext"],

                            "format_note": format["format_note"],

                            "yturl": link,

                        }

                    )

        return formats_available, link



    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):

        if videoid:

            link = self.base + link

        if "&" in link:

            link = link.split("&")[0]

        a = VideosSearch(link, limit=10)

        result = (await a.next()).get("result")

        title = result[query_type]["title"]

        duration_min = result[query_type]["duration"]

        vidid = result[query_type]["id"]

        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]

        return title, duration_min, thumbnail, vidid



    async def download(

        self,

        link: str,

        mystic,

        video: Union[bool, str] = None,

        videoid: Union[bool, str] = None,

        songaudio: Union[bool, str] = None,

        songvideo: Union[bool, str] = None,

        format_id: Union[bool, str] = None,

        title: Union[bool, str] = None,

    ) -> str:

        if videoid:

            link = self.base + link

        loop = asyncio.get_running_loop()



        def audio_dl():

            cookie_file = cookie_txt_file()

            if not cookie_file:

                raise Exception("No cookies found. Cannot download audio.")

            ydl_optssx = {

                "format": "bestaudio/best",

                "outtmpl": "downloads/%(id)s.%(ext)s",

                "geo_bypass": True,

                "nocheckcertificate": True,

                "quiet": True,

                "cookiefile": cookie_file,

                "no_warnings": True,

            }

            x = yt_dlp.YoutubeDL(ydl_optssx)

            info = x.extract_info(link, False)

            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")

            if os.path.exists(xyz):

                return xyz

            x.download([link])

            return xyz



        def video_dl():

            cookie_file = cookie_txt_file()

            if not cookie_file:

                raise Exception("No cookies found. Cannot download video.")

            ydl_optssx = {

                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",

                "outtmpl": "downloads/%(id)s.%(ext)s",

                "geo_bypass": True,

                "nocheckcertificate": True,

                "quiet": True,

                "cookiefile": cookie_file,

                "no_warnings": True,

            }

            x = yt_dlp.YoutubeDL(ydl_optssx)

            info = x.extract_info(link, False)

            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")

            if os.path.exists(xyz):

                return xyz

            x.download([link])

            return xyz



        def song_video_dl():

            cookie_file = cookie_txt_file()

            if not cookie_file:

                raise Exception("No cookies found. Cannot download song video.")

            formats = f"{format_id}+140"

            fpath = f"downloads/{title}"

            ydl_optssx = {

                "format": formats,

                "outtmpl": fpath,

                "geo_bypass": True,

                "nocheckcertificate": True,

                "quiet": True,

                "no_warnings": True,

                "cookiefile": cookie_file,

                "prefer_ffmpeg": True,

                "merge_output_format": "mp4",

            }

            x = yt_dlp.YoutubeDL(ydl_optssx)

            x.download([link])



        def song_audio_dl():

            cookie_file = cookie_txt_file()

            if not cookie_file:

                raise Exception("No cookies found. Cannot download song audio.")

            fpath = f"downloads/{title}.%(ext)s"

            ydl_optssx = {

                "format": format_id,

                "outtmpl": fpath,

                "geo_bypass": True,

                "nocheckcertificate": True,

                "quiet": True,

                "no_warnings": True,

                "cookiefile": cookie_file,

                "prefer_ffmpeg": True,

                "postprocessors": [

                    {

                        "key": "FFmpegExtractAudio",

                        "preferredcodec": "mp3",

                        "preferredquality": "192",

                    }

                ],

            }

            x = yt_dlp.YoutubeDL(ydl_optssx)

            x.download([link])



        # === MODIFIED DOWNLOAD LOGIC WITH SAAVN PRIORITY ===

        if songvideo:

            # Try Saavn first for song video

            query = title if title else link

            saavn_url, saavn_info = await download_saavn_song(query)

            if saavn_url:

                print(f"✅ Downloaded from Saavn: {saavn_info['title']}")

                return saavn_url, True

            # Fallback to YouTube

            try:

                downloaded_file = await download_song(link)

                if downloaded_file and os.path.exists(downloaded_file):

                    return downloaded_file, True

            except Exception as e:

                print(f"⚠️ YouTube download failed: {e}")

            return None, None



        elif songaudio:

            # Try Saavn first for song audio

            query = title if title else link

            saavn_url, saavn_info = await download_saavn_song(query)

            if saavn_url:

                print(f"✅ Downloaded from Saavn: {saavn_info['title']}")

                return saavn_url, True

            # Fallback to YouTube

            try:

                downloaded_file = await download_song(link)

                if downloaded_file and os.path.exists(downloaded_file):

                    return downloaded_file, True

            except Exception as e:

                print(f"⚠️ YouTube download failed: {e}")

            return None, None



        elif video:

            # Try video API first

            try:

                downloaded_file = await download_video(link)

                if downloaded_file:

                    direct = True

                    return downloaded_file, direct

            except Exception as e:

                print(f"Video API failed: {e}")



            # Fallback to cookies

            cookie_file = cookie_txt_file()

            if not cookie_file:

                print("No cookies found. Cannot download video.")

                return None, None



            if await is_on_off(1):

                direct = True

                downloaded_file = await download_song(link)

            else:

                proc = await asyncio.create_subprocess_exec(

                    "yt-dlp",

                    "--cookies", cookie_file,

                    "-g",

                    "-f",

                    "best[height<=?720][width<=?1280]",

                    f"{link}",

                    stdout=asyncio.subprocess.PIPE,

                    stderr=asyncio.subprocess.PIPE,

                )

                stdout, stderr = await proc.communicate()

                if stdout:

                    downloaded_file = stdout.decode().split("\n")[0]

                    direct = False

                else:

                    file_size = await check_file_size(link)

                    if not file_size:

                        print("None file Size")

                        return None, None

                    total_size_mb = file_size / (1024 * 1024)

                    if total_size_mb > 250:

                        print(f"File size {total_size_mb:.2f} MB exceeds the 100MB limit.")

                        return None, None

                    direct = True

                    downloaded_file = await loop.run_in_executor(None, video_dl)



        else:

            # === MAIN LOGIC: YOUTUBE SEARCH + SAAVN PLAY ===

            query = link

            if "youtube.com" in link or "youtu.be" in link:

                try:

                    print(f"🎬 Extracting title from YouTube URL: {link}")

                    title_result = await self.title(link)

                    query = title_result

                    print(f"📝 Extracted title: {title_result}")

                except Exception as e:

                    print(f"⚠️ Could not extract YouTube title: {e}")

                    query = link

            elif "watch?v=" in link:

                try:

                    video_id = link.split("v=")[-1].split("&")[0]

                    query = f"youtube video {video_id}"

                except:

                    query = link



            print(f"🔍 Using optimized top 1 search for: {query}")

            download_url, song_info, is_saavn = await optimized_top1_youtube_saavn_play(query)

            if download_url:

                if is_saavn:

                    print(f"✅ Downloaded from Saavn: {song_info['title']} by {song_info['artist']}")

                    return download_url, True

                else:

                    print(f"✅ Downloaded from YouTube: {song_info['title']}")

                    return download_url, True

            else:

                print(f"❌ All methods failed for: {query}")

                return None, None



        return None, None



# === OPTIMIZED TOP 1 SEARCH: YOUTUBE + JIO SAAVN ===

async def optimized_top1_youtube_saavn_play(query: str):

    print(f"🎵 Starting optimized top 1 search for: {query}")

    try:

        print(f"🔍 Getting top 1 YouTube result for: {query}")

        results = VideosSearch(query, limit=1)

        search_results = await results.next()

        if not search_results.get("result"):

            print("❌ No YouTube results found")

            return None, None, False

        top_result = search_results["result"][0]

        youtube_title = top_result["title"]

        youtube_artist = top_result.get("channel", {}).get("name", "Unknown")

        youtube_duration = top_result.get("duration", "Unknown")

        youtube_url = top_result["link"]

        print(f"📺 Top 1 YouTube result: {youtube_title}")

        print(f"🔍 Trying Jio Saavn API with: {youtube_title}")

        saavn_url, saavn_info = await download_saavn_song(youtube_title)

        if saavn_url:

            print(f"✅ SUCCESS! Playing from Jio Saavn: {saavn_info['title']} by {saavn_info['artist']}")

            return saavn_url, saavn_info, True

        print(f"🔍 Trying Jio Saavn with cleaned title...")

        cleaned_title = clean_youtube_title_for_saavn(youtube_title)

        saavn_url, saavn_info = await download_saavn_song(cleaned_title)

        if saavn_url:

            print(f"✅ SUCCESS! Playing from Jio Saavn: {saavn_info['title']} by {saavn_info['artist']}")

            return saavn_url, saavn_info, True

        print(f"🔄 Jio Saavn not available, using YouTube: {youtube_title}")

        downloaded_file = await download_song(youtube_url)

        if downloaded_file and os.path.exists(downloaded_file):

            youtube_info = {

                "title": youtube_title,

                "artist": youtube_artist,

                "source": "YouTube",

                "quality": "Variable",

                "duration": youtube_duration,

            }

            print(f"✅ Downloaded from YouTube: {youtube_title}")

            return downloaded_file, youtube_info, False

        else:

            print("❌ Failed to download from YouTube")

    except Exception as e:

        print(f"❌ Optimized search error: {e}")

    print(f"❌ All methods failed for: {query}")

    return None, None, False



# === ORIGINAL HYBRID SEARCH: YOUTUBE SEARCH + SAAVN PLAY ===

async def youtube_search_saavn_play(query: str):

    print(f"🎵 Starting hybrid search: YouTube → Saavn for: {query}")

    try:

        print(f"🔍 Searching YouTube for: {query}")

        results = VideosSearch(query, limit=5)

        search_results = await results.next()

        if not search_results.get("result"):

            print("❌ No YouTube results found")

            return None, None, False

        youtube_results = search_results["result"]

        print(f"📺 Found {len(youtube_results)} YouTube results")

        for i, result in enumerate(youtube_results, 1):

            youtube_title = result["title"]

            youtube_artist = result.get("channel", {}).get("name", "Unknown")

            youtube_duration = result.get("duration", "Unknown")

            print(f"\n🎯 Trying result {i}: {youtube_title}")

            saavn_query = clean_youtube_title_for_saavn(youtube_title)

            print(f"🧹 Cleaned title for Saavn: {saavn_query}")

            search_variations = generate_search_variations(saavn_query)

            print(f"🔍 Trying {len(search_variations)} search variations")

            for j, variation in enumerate(search_variations, 1):

                print(f"   Variation {j}: '{variation}'")

                saavn_url, saavn_info = await download_saavn_song(variation)

                if saavn_url:

                    found_title = saavn_info["title"].lower()

                    original_query = query.lower()

                    query_words = original_query.split()

                    title_words = found_title.split()

                    matching_words = sum(1 for word in query_words if word in title_words)

                    match_percentage = (matching_words / len(query_words)) * 100 if query_words else 0

                    print(f"   ✅ Found: {saavn_info['title']} (Match: {match_percentage:.0f}%)")

                    if match_percentage >= 60:

                        print(f"✅ SUCCESS! Found on Saavn: {saavn_info['title']} by {saavn_info['artist']}")

                        return saavn_url, saavn_info, True

                    else:

                        print(f"   ⚠️  Poor match, trying next variation...")

                        continue

                else:

                    print(f"   ❌ Not found with variation: '{variation}'")

            print(f"❌ No good matches found for: {youtube_title}")

        print(f"🔄 No Saavn matches found, falling back to YouTube")

        best_result = youtube_results[0]

        video_url = best_result["link"]

        print(f"⬇️ Downloading from YouTube: {best_result['title']}")

        downloaded_file = await download_song(video_url)

        if downloaded_file:

            youtube_info = {

                "title": best_result["title"],

                "artist": best_result.get("channel", {}).get("name", "YouTube"),

                "source": "YouTube",

                "quality": "Variable",

                "duration": best_result.get("duration", "Unknown"),

            }

            print(f"✅ Downloaded from YouTube: {best_result['title']}")

            return downloaded_file, youtube_info, False

        else:

            print("❌ Failed to download from YouTube")

    except Exception as e:

        print(f"❌ Hybrid search error: {e}")

    print(f"❌ All methods failed for: {query}")

    return None, None, False



def clean_youtube_title_for_saavn(youtube_title: str):

    """Clean YouTube title to make it suitable for Saavn search"""

    suffixes_to_remove = [

        "official video", "official music video", "official", "music video",

        "lyrics", "lyric video", "lyrics video", "hd", "4k", "full song",

        "song", "video", "audio", "cover", "remix", "version", "mix",

        "official audio", "official lyric video", "official hd", "official 4k",

        "full 4k video", "full hd", "full song hd", "full song 4k",

    ]

    actor_names = [

        "amitabh bachchan", "jaya prada", "kishore kumar", "lata mangeshkar",

        "mohammed rafi", "asha bhosle", "kumar sanu", "udit narayan",

        "alisha chinai", "anuradha paudwal", "sonu nigam", "shreya ghoshal",

    ]

    title = youtube_title.lower().strip()

    for suffix in suffixes_to_remove:

        if title.endswith(suffix):

            title = title[:-len(suffix)].strip()

    title = re.sub(r"\([^)]*\)", "", title)

    title = re.sub(r"\[[^\]]*\]", "", title)

    if "|" in title:

        title = title.split("|")[0].strip()

    prefixes_to_remove = ["watch:", "listen:", "play:", "song:"]

    for prefix in prefixes_to_remove:

        if title.startswith(prefix):

            title = title[len(prefix):].strip()

    for actor in actor_names:

        title = title.replace(actor, "").strip()

    title = re.sub(r"[^\w\s]", "", title)

    title = re.sub(r"\s+", " ", title).strip()

    words = title.split()

    if len(words) > 4:

        title = " ".join(words[:4])

    return title



def generate_search_variations(query: str):

    """Generate multiple search variations for better matching"""

    variations = []

    variations.append(query)

    words = query.split()

    if len(words) > 2:

        variations.append(" ".join(words[:-1]))

        if len(words) >= 2:

            variations.append(" ".join(words[:2]))

    variations.append(f'"{query}"')

    hindi_suffixes = ["song", "geet", "gaan"]

    for suffix in hindi_suffixes:

        variations.append(f"{query} {suffix}")

    return variations



# === NEW FUNCTION FOR HYBRID DOWNLOAD ===

async def download_with_saavn_priority(query: str):

    print(f"🎵 Starting hybrid download process for: {query}")

    return await youtube_search_saavn_play(query)



# === TEST FUNCTION FOR OPTIMIZED TOP 1 SEARCH ===

async def test_optimized_search(query: str):

    print(f"🧪 Testing optimized top 1 search for: {query}")

    try:

        download_url, song_info, is_saavn = await optimized_top1_youtube_saavn_play(query)

        if download_url:

            if is_saavn:

                print(f"✅ SUCCESS! Found on Jio Saavn: {song_info['title']} by {song_info['artist']}")

                print(f"🔗 Download URL: {download_url[:50]}...")

                print(f"📊 Quality: {song_info['quality']}")

            else:

                print(f"✅ SUCCESS! Downloaded from YouTube: {song_info['title']}")

                print(f"📁 File path: {download_url}")

        else:

            print("❌ No results found")

    except Exception as e:

        print(f"❌ Test failed with error: {e}")



# === LEGACY TEST FUNCTION ===

async def test_improved_search(query: str):

    return await test_optimized_search(query)
