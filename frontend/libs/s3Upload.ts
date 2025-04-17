const MIN_PART_SIZE = 5 * 1024 * 1024; // 5MB

interface UploadPart {
  PartNumber: number;
  ETag: string;
}

export async function uploadVideoInChunks(
  file: File,
  setProgress: (p: number) => void
): Promise<{ location: string }> {
  const totalParts = Math.ceil(file.size / MIN_PART_SIZE);

  // Step 1: Initiate upload session
  const initRes = await fetch("http://localhost:8000/create-upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: file.name, parts: totalParts }),
  });
  const { uploadId, urls } = await initRes.json();

  const etags: UploadPart[] = [];

  // Step 2: Upload each chunk
  for (let i = 0; i < totalParts; i++) {
    const start = i * MIN_PART_SIZE;
    const end = Math.min(start + MIN_PART_SIZE, file.size);
    const chunk = file.slice(start, end);

    const uploadRes = await fetch(urls[i].url, {
      method: "PUT",
      body: chunk,
    });

    const etag = uploadRes.headers.get("ETag");
    if (etag) {
      etags.push({ PartNumber: i + 1, ETag: etag });
    }

    setProgress(Math.round(((i + 1) / totalParts) * 100));
  }

  // Step 3: Finalize upload
  const completeRes = await fetch("http://localhost:8000/complete-upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: file.name, uploadId, parts: etags }),
  });

  return await completeRes.json();
}
