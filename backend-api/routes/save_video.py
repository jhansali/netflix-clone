import os
import uuid
import subprocess
from fastapi import APIRouter, Body
from pymongo import MongoClient
import boto3
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["Catalog0"]
collection = db["Movie"]

# S3 setup
s3 = boto3.client("s3")
BUCKET = os.getenv("S3_BUCKET_NAME")

def get_video_duration(file_path: str) -> str:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        seconds = float(result.stdout.strip())
        minutes = int(seconds // 60)
        remaining = int(seconds % 60)
        return f"{minutes}m {remaining}s"
    except Exception as e:
        print(f"Error getting duration: {e}")
        return "Unknown"

def generate_thumbnail(video_path: str, thumbnail_path: str) -> bool:
    try:
        subprocess.run([
            "ffmpeg",
            "-ss", "00:00:01",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            thumbnail_path
        ], check=True)
        return True
    except Exception as e:
        print("Thumbnail generation failed:", e)
        return False

@router.post("/save-video")
def save_video(data: dict = Body(...)):
    filename = str(uuid.uuid4()) + ".mp4"
    temp_path = f"/tmp/{filename}"

    # Extract S3 key from URL
    s3_key = data["videoUrl"].split("/")[-1]
    s3.download_file(BUCKET, s3_key, temp_path)

    # Get duration
    duration = get_video_duration(temp_path)

    # Handle thumbnail
    user_thumbnail = data.get("thumbnailUrl", "").strip()
    thumbnail_url = user_thumbnail

    if not thumbnail_url:
        thumbnail_filename = str(uuid.uuid4()) + ".jpg"
        thumbnail_local = f"/tmp/{thumbnail_filename}"

        if generate_thumbnail(temp_path, thumbnail_local):
            s3.upload_file(thumbnail_local, BUCKET, f"thumbnails/{thumbnail_filename}")
            thumbnail_url = f"https://{BUCKET}.s3.amazonaws.com/thumbnails/{thumbnail_filename}"
            os.remove(thumbnail_local)

    os.remove(temp_path)

    # Save metadata in MongoDB
    record = {
        "title": data["title"],
        "description": data.get("description", ""),
        "duration": duration,
        "genre": data["genre"],
        "videoUrl": data["videoUrl"],
        "thumbnailUrl": thumbnail_url
    }
    collection.insert_one(record)
    return {"status": "ok", "duration": duration, "thumbnailUrl": thumbnail_url}