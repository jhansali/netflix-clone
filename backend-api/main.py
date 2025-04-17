from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routes.save_video import router as save_video_router
from s3_upload import create_multipart_upload, generate_presigned_urls, complete_upload
from routes.upload_video import router as upload_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/create-upload")
def create_upload(
    filename: str = Body(...),
    parts: int = Body(...)
):
    upload_id = create_multipart_upload(filename)
    urls = generate_presigned_urls(filename, upload_id, parts)
    return {
        "uploadId": upload_id,
        "urls": urls
    }

@app.post("/complete-upload")
def complete_s3_upload(
    filename: str = Body(...),
    uploadId: str = Body(...),
    parts: list[dict] = Body(...)
):
    result = complete_upload(filename, uploadId, parts)
    return {
        "message": "Upload completed",
        "location": result["Location"]
    }

app.include_router(save_video_router)

app.include_router(upload_router)