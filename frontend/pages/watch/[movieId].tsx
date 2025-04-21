import React, { useEffect, useRef, useState } from "react";
import Hls from "hls.js";
import { useRouter } from "next/router";
import useMovie from "@/hooks/useMovie";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";

const Watch = () => {
  const router = useRouter();
  const { movieId } = router.query;
  const { data } = useMovie(movieId as string);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);

  const [resOptions, setResOptions] = useState<string[]>(["Auto"]);
  const [selectedRes, setSelectedRes] = useState("Auto");

  useEffect(() => {
    if (Hls.isSupported() && videoRef.current && data?.videoUrl) {
      const hls = new Hls();
      hls.loadSource(data.videoUrl);
      hls.attachMedia(videoRef.current);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setTimeout(() => {
          console.log("Parsed levels:", hls.levels);
          const levels = hls.levels.filter((lvl) => lvl.height > 0);
          const resolutions = Array.from(new Set(levels.map((lvl) => `${lvl.height}p`)));
          setResOptions(["Auto", ...resolutions]);
        }, 200);
      });

      hls.on(Hls.Events.LEVEL_SWITCHED, (_, data) => {
        const level = hls.levels[data.level];
        setSelectedRes(level ? `${level.height}p` : "Auto");
      });

      hlsRef.current = hls;
    }
  }, [data?.videoUrl]);

  const handleResolutionChange = (res: string) => {
    if (!hlsRef.current) return;
    if (res === "Auto") {
      hlsRef.current.currentLevel = -1;
    } else {
      const levelIndex = hlsRef.current.levels.findIndex(
        (lvl) => `${lvl.height}p` === res
      );
      hlsRef.current.currentLevel = levelIndex;
    }
    setSelectedRes(res);
  };

  return (
    <div className="relative h-screen w-screen bg-black">
      <nav className="fixed w-full p-4 z-10 flex flex-row items-center gap-8 bg-black bg-opacity-70">
        <ArrowLeftIcon
          onClick={() => router.push("/")}
          className="w-6 md:w-10 text-white cursor-pointer hover:opacity-80 transition"
        />
        <p className="text-white text-xl md:text-3xl font-bold">
          <span className="font-light">Watching: </span>
          {data?.title}
        </p>
      </nav>

      <video ref={videoRef} className="h-full w-full" controls autoPlay />

      <div className="absolute top-4 right-4 z-20">
        <div className="relative">
          <select
            value={selectedRes}
            onChange={(e) => handleResolutionChange(e.target.value)}
            className="bg-black bg-opacity-80 text-white px-3 py-1 rounded-md shadow-lg appearance-none"
          >
            {resOptions.map((res) => (
              <option key={res} value={res}>
                {res}
              </option>
            ))}
          </select>
        </div>
</div>
    </div>
  );
};

export default Watch;
