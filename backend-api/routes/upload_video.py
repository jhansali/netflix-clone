import os
import uuid
import subprocess
from fastapi import APIRouter, UploadFile, Form
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor
import boto3
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["Catalog0"]
collection = db["Movie"]

s3 = boto3.client("s3")
BUCKET = os.getenv("S3_BUCKET_NAME")
PART_SIZE = 8 * 1024 * 1024  # 8MB chunks for better throughput


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


def upload_part(part_number, data, upload_id, key):
    response = s3.upload_part(
        Bucket=BUCKET,
        Key=key,
        PartNumber=part_number,
        UploadId=upload_id,
        Body=data
    )
    return {"PartNumber": part_number, "ETag": response["ETag"]}


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

    key = f"uploads/{uuid.uuid4()}_{file.filename}"
    multipart_upload = s3.create_multipart_upload(Bucket=BUCKET, Key=key)
    upload_id = multipart_upload["UploadId"]

    try:
        chunks = []
        with open(temp_path, "rb") as f:
            part_number = 1
            while True:
                data = f.read(PART_SIZE)
                if not data:
                    break
                chunks.append((part_number, data))
                part_number += 1

        # Parallel upload
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(upload_part, part_num, data, upload_id, key)
                for part_num, data in chunks
            ]
            parts = [future.result() for future in futures]

        s3.complete_multipart_upload(
            Bucket=BUCKET,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts}
        )

    except Exception as e:
        s3.abort_multipart_upload(Bucket=BUCKET, Key=key, UploadId=upload_id)
        os.remove(temp_path)
        return JSONResponse(status_code=500, content={"error": str(e)})

    duration = get_video_duration(temp_path)
    thumbnail_filename = f"thumbnails/{uuid.uuid4()}.jpg"
    thumbnail_local = f"/tmp/{uuid.uuid4()}.jpg"
    thumbnail_url = ""

    if generate_thumbnail(temp_path, thumbnail_local):
        s3.upload_file(thumbnail_local, BUCKET, thumbnail_filename)
        thumbnail_url = f"https://{BUCKET}.s3.amazonaws.com/{thumbnail_filename}"
        os.remove(thumbnail_local)

    os.remove(temp_path)

    video_url = f"https://{BUCKET}.s3.amazonaws.com/{key}"
    record = {
        "title": title,
        "description": description,
        "genre": genre,
        "duration": duration,
        "videoUrl": video_url,
        "thumbnailUrl": thumbnail_url
    }
    collection.insert_one(record)

    return {"status": "ok", "videoUrl": video_url, "thumbnailUrl": thumbnail_url, "duration": duration}