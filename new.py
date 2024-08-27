import subprocess
import logging
import os
import json
from datetime import datetime


def setup_logger(log_file):
    logger = logging.getLogger("FFmpegProcessor")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def run_ffmpeg(args, logger):
    cmd = ["ffmpeg"] + args
    logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
    )
    for line in process.stdout:
        logger.debug(line.strip())
    return_code = process.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, cmd)


def get_video_dimensions(input_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_packets",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        input_path,
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )
    if result.returncode != 0:
        raise ValueError(f"Failed to get video dimensions: {result.stderr}")
    data = json.loads(result.stdout)
    if "streams" not in data or not data["streams"]:
        raise ValueError("No video stream found in the file")
    width = int(data["streams"][0]["width"])
    height = int(data["streams"][0]["height"])
    return width, height


def calculate_new_dimensions(width, height):
    aspect_ratio = width / height
    if width > height and width >= 1440:
        new_width = 1440
        new_height = int(new_width / aspect_ratio)
    elif height > width and height >= 1440:
        new_height = 1440
        new_width = int(new_height * aspect_ratio)
    elif width == height and width > 1440:
        new_width = new_height = 1440
    else:
        new_width, new_height = width, height

    # Ensure both dimensions are even
    new_width = new_width if new_width % 2 == 0 else new_width - 1
    new_height = new_height if new_height % 2 == 0 else new_height - 1

    return new_width, new_height


def process_video(input_path, output_path, logger):
    original_width, original_height = get_video_dimensions(input_path)
    new_width, new_height = calculate_new_dimensions(original_width, original_height)
    logger.info(f"Original Dimension: {original_width} X {original_height}")
    logger.info(f"New Dimension: {new_width} X {new_height}")
    ffmpeg_args = [
        "-y",
        "-i",
        input_path,
        "-preset",
        "slow",
        "-crf",
        "17",
        "-maxrate",
        "15M",
        "-bufsize",
        "25M",
        "-vf",
        f"scale={new_width}:{new_height}:flags=lanczos",
        "-c:v",
        "libx264",
        "-x264-params",
        "ref=6:me=umh:subme=8:rc-lookahead=60",
        "-pix_fmt",
        "yuv420p",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-colorspace",
        "bt709",
        "-c:a",
        "aac",
        "-b:a",
        "256k",
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
        output_path,
    ]
    try:
        logger.info(f"Starting high-quality video processing for {input_path}")
        run_ffmpeg(ffmpeg_args, logger)
        logger.info(f"Video processing completed. Output saved to {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred during video processing: {e}")
        logger.error(f"FFmpeg returned non-zero exit status {e.returncode}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)


def process_directory(input_dir, output_dir, logger):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"processed_{filename}")
            process_video(input_path, output_path, logger)


if __name__ == "__main__":
    if not os.path.exists("logs"):
        os.makedirs("logs")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/ffmpeg_process_{timestamp}.log"

    logger = setup_logger(log_file)

    input_dir = "dataset"
    output_dir = "out_1itr_final"

    logger.info("FFmpeg high-quality batch processing script started")
    process_directory(input_dir, output_dir, logger)
    logger.info("FFmpeg high-quality batch processing script finished")
    print(f"Processing complete. Check the log file at {log_file} for details.")
