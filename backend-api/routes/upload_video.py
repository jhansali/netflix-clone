import os
import uuid
import subprocess
import shutil
from fastapi import APIRouter, UploadFile, Form
from fastapi.responses import JSONResponse
from pymongo import MongoClient
import boto3
from dotenv import load_dotenv
from generate_hls import generate_hls

load_dotenv()

router = APIRouter()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["Catalog0"]
collection = db["Movie"]

s3 = boto3.client("s3")
BUCKET = os.getenv("S3_BUCKET_NAME")

def get_video_duration(file_path: str) -> str:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        seconds = float(result.stdout.strip())
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}m {seconds}s"
    except Exception as e:
        print("ffprobe error:", e)
        return "Unknown"

def generate_thumbnail(video_path: str, thumbnail_path: str):
    try:
        subprocess.run([
            "ffmpeg", "-ss", "00:00:01", "-i", video_path,
            "-vframes", "1", "-q:v", "2", thumbnail_path
        ], check=True)
        return True
    except Exception as e:
        print("Thumbnail error:", e)
        return False

def upload_directory_to_s3(local_dir, s3_prefix):
    for root, _, files in os.walk(local_dir):
        for file in files:
            full_path = os.path.join(root, file)
            s3_key = os.path.join(s3_prefix, os.path.relpath(full_path, local_dir)).replace("\\", "/")
            s3.upload_file(full_path, BUCKET, s3_key)

@router.post("/upload")
async def upload_video(
    file: UploadFile,
    title: str = Form(...),
    description: str = Form(""),
    genre: str = Form("Action")
):
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(temp_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    # Generate HLS from video
    output_base_dir = "./hls_outputs"
    try:
        hls_output_path, video_id = generate_hls(temp_path, output_base_dir)
        hls_s3_prefix = f"hls/{video_id}"
        upload_directory_to_s3(hls_output_path, hls_s3_prefix)
        master_url = f"https://{BUCKET}.s3.amazonaws.com/hls/{video_id}/master.m3u8"
    except Exception as e:
        os.remove(temp_path)
        return JSONResponse(status_code=500, content={"error": f"HLS generation failed: {str(e)}"})

    # Generate thumbnail
    thumbnail_filename = f"thumbnails/{uuid.uuid4()}.jpg"
    thumbnail_local = f"/tmp/{uuid.uuid4()}.jpg"
    thumbnail_url = ""
    if generate_thumbnail(temp_path, thumbnail_local):
        s3.upload_file(thumbnail_local, BUCKET, thumbnail_filename)
        thumbnail_url = f"https://{BUCKET}.s3.amazonaws.com/{thumbnail_filename}"
        os.remove(thumbnail_local)

    os.remove(temp_path)
    shutil.rmtree(hls_output_path, ignore_errors=True)

    duration = get_video_duration(temp_path)

    record = {
        "title": title,
        "description": description,
        "genre": genre,
        "duration": duration,
        "videoUrl": master_url,
        "thumbnailUrl": thumbnail_url
    }
    collection.insert_one(record)

    return {
        "status": "ok",
        "videoUrl": master_url,
        "thumbnailUrl": thumbnail_url,
        "duration": duration
    }