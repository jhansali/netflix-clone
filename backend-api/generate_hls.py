import os
import subprocess
import uuid

def generate_hls(input_path: str, output_dir: str):
    video_id = str(uuid.uuid4())
    output_path = os.path.join(output_dir, video_id)
    os.makedirs(output_path, exist_ok=True)

    ffmpeg_command = [
        "ffmpeg", "-i", input_path,
        "-preset", "veryfast", "-g", "48", "-sc_threshold", "0",

        "-filter_complex",
        "[0:v]split=3[v1][v2][v3];" +
        "[0:a]asplit=3[a1][a2][a3];" +
        "[v1]scale=w=1920:h=1080[v1out];" +
        "[v2]scale=w=1280:h=720[v2out];" +
        "[v3]scale=w=854:h=480[v3out]",

        "-map", "[v1out]", "-map", "[a1]",
        "-b:v:0", "5000k",

        "-map", "[v2out]", "-map", "[a2]",
        "-b:v:1", "2800k",

        "-map", "[v3out]", "-map", "[a3]",
        "-b:v:2", "1400k",

        "-var_stream_map", "v:0,a:0 v:1,a:1 v:2,a:2",
        "-master_pl_name", "master.m3u8",
        "-f", "hls",
        "-hls_time", "6",
        "-hls_list_size", "0",
        "-hls_segment_filename", f"{output_path}/v%v/segment_%03d.ts",
        f"{output_path}/v%v/prog.m3u8"
    ]

    print("Running ffmpeg...")
    subprocess.run(ffmpeg_command, check=True)
    print(f"HLS files generated in: {output_path}")

    return output_path, video_id


# Example usage
if __name__ == "__main__":
    input_video = "Tron_Ares.mp4"
    output_base_dir = "./hls_outputs"
    generate_hls(input_video, output_base_dir)
