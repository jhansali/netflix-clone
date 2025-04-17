import React, { useState } from "react";
import { useSession } from "next-auth/react";
import { uploadVideoInChunks } from "@/libs/s3Upload";

export default function VideoUploader() {
  const { data: session } = useSession();
  const email = session?.user?.email;

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [genre, setGenre] = useState("Action");
  const [thumbnail, setThumbnail] = useState<File | null>(null);

  const handleThumbnailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setThumbnail(file);
  };

  const uploadThumbnailToS3 = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:8000/upload-thumbnail", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    return data.thumbnailUrl;
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage("");

    try {
      let thumbnailUrl = "";
      if (thumbnail) {
        thumbnailUrl = await uploadThumbnailToS3(thumbnail);
      }

      const result = await uploadVideoInChunks(file, setProgress);
      const videoUrl = result.location;

      await fetch("http://localhost:8000/save-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          description,
          genre,
          videoUrl,
          thumbnailUrl
        })
      });

      setMessage("Upload and save complete!");
    } catch (error) {
      console.error("Upload failed:", error);
      setMessage("Upload failed. Check console for details.");
    }

    setUploading(false);
  };

  if (email !== "test@gmail.com") {
    return (
      <div className="text-center text-red-500 mt-20">
        You do not have permission to upload videos.
      </div>
    );
  }

  return (
    <div className="p-6 bg-zinc-800 rounded-lg shadow-md w-full max-w-md mx-auto mt-20 text-white">
      <h2 className="text-xl font-bold mb-4">Upload a Video</h2>

      <label className="block mb-2">Title</label>
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="mb-4 w-full p-2 text-black rounded"
      />

      <label className="block mb-2">Description</label>
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="mb-4 w-full p-2 text-black rounded"
      />

      <label className="block mb-2">Genre</label>
      <select
        value={genre}
        onChange={(e) => setGenre(e.target.value)}
        className="mb-4 w-full p-2 text-black rounded"
      >
        <option>Action</option>
        <option>Drama</option>
        <option>Comedy</option>
        <option>Horror</option>
        <option>Sci-Fi</option>
      </select>

      <label className="block mb-2">Custom Thumbnail (optional)</label>
      <input
        type="file"
        accept="image/*"
        onChange={handleThumbnailChange}
        className="mb-4 w-full text-sm text-gray-300"
        disabled={uploading}
      />

      <input
        type="file"
        accept="video/*"
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4
                   file:rounded-md file:border-0
                   file:text-sm file:font-semibold
                   file:bg-red-500 file:text-white
                   hover:file:bg-red-600
                   cursor-pointer"
        disabled={uploading}
      />
      {uploading && <p className="mt-4">Uploading: {progress}%</p>}
      {message && <p className="mt-4 text-green-400">{message}</p>}
    </div>
  );
}