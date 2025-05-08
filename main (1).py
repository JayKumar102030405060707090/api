from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from yt_dlp import YoutubeDL
from youtube_search_python import VideosSearch
import os
import uvicorn

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# yt-dlp options
YDL_OPTIONS = {'format': 'best', 'noplaylist': True}

# Helper function: Get video details
def get_video_details(link: str):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(link, download=False)
            return {
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "video_id": info.get("id"),
                "formats": info.get("formats"),
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/youtube")
async def youtube(query: str, video: bool = True):
    try:
        videos_search = VideosSearch(query, limit=1)
        result = videos_search.result()["result"]
        if not result:
            raise HTTPException(status_code=404, detail="No results found")
        item = result[0]
        return {
            "title": item["title"],
            "link": item["link"],
            "duration": item["duration"],
            "thumbnail": item["thumbnails"][0]["url"],
            "video": video,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/details")
async def details(link: str):
    return get_video_details(link)

@app.get("/track")
async def track(link: str):
    details = get_video_details(link)
    return {
        "title": details["title"],
        "link": f"https://www.youtube.com/watch?v={details['video_id']}",
        "video_id": details["video_id"],
        "thumbnail": details["thumbnail"]
    }

@app.get("/formats")
async def formats(link: str):
    details = get_video_details(link)
    return {"formats": details["formats"]}

@app.get("/playlist")
async def playlist(link: str, limit: int = Query(default=10)):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(link, download=False)
            if "entries" not in info:
                raise HTTPException(status_code=400, detail="Invalid playlist link")
            playlist_items = info["entries"][:limit]
            return [
                {"title": item["title"], "video_id": item["id"]}
                for item in playlist_items
                if item
            ]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/download/audio")
async def download_audio(link: str):
    options = {'format': 'bestaudio', 'outtmpl': 'downloads/%(title)s.%(ext)s'}
    with YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(link, download=True)
            return {"title": info["title"], "filepath": ydl.prepare_filename(info)}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/download/video")
async def download_video(link: str):
    options = {'format': 'bestvideo', 'outtmpl': 'downloads/%(title)s.%(ext)s'}
    with YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(link, download=True)
            return {"title": info["title"], "filepath": ydl.prepare_filename(info)}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/download/custom")
async def download_custom(link: str, format_id: str, title: str):
    options = {'format': format_id, 'outtmpl': f'downloads/{title}.%(ext)s'}
    with YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(link, download=True)
            return {"title": info["title"], "filepath": ydl.prepare_filename(info)}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/search")
async def search(query: str):
    try:
        videos_search = VideosSearch(query, limit=10)
        results = videos_search.result()["result"]
        return [
            {
                "title": item["title"],
                "link": item["link"],
                "duration": item["duration"],
                "thumbnail": item["thumbnails"][0]["url"],
            }
            for item in results
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/slider")
async def slider(query: str, index: int):
    try:
        videos_search = VideosSearch(query, limit=index + 1)
        results = videos_search.result()["result"]
        if index >= len(results):
            raise HTTPException(status_code=404, detail="Index out of range")
        item = results[index]
        return {
            "title": item["title"],
            "link": item["link"],
            "duration": item["duration"],
            "thumbnail": item["thumbnails"][0]["url"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))