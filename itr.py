import subprocess
import logging
import os
import json
from datetime import datetime


def setup_logger(log_file):
    logger = logging.getLogger("FFmpegProcessor")
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs even debug messages
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Create formatter and add it to the handler
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)

    # Add the handler to the logger
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

    # First pass
    ffmpeg_args_first_pass = [
        "-y",
        "-i",
        input_path,
        "-preset",
        "veryslow",
        "-b:v",
        "3500k",
        "-maxrate",
        "4000k",
        "-bufsize",
        "7000k",
        "-vf",
        f"unsharp=5:5:1.0,scale='if(gt(iw,1440),if(gte(iw,ih),1440,-2),iw)':'if(gt(ih,1440),if(gt(ih,iw),1440,-2),ih)':flags=lanczos",
        "-pass",
        "1",
        "-f",
        "mp4",
        "/dev/null",
    ]
    try:
        logger.info("Starting first pass for video processing")
        run_ffmpeg(ffmpeg_args_first_pass, logger)
        logger.info("First pass completed")
    except subprocess.CalledProcessError as e:
        logger.error(f"First pass failed: {e}")
        return

    # Second pass
    ffmpeg_args_second_pass = [
        "-y",
        "-i",
        input_path,
        "-preset",
        "veryslow",
        "-b:v",
        "3500k",
        "-maxrate",
        "4000k",
        "-bufsize",
        "7000k",
        "-vf",
        f"unsharp=5:5:1.0,scale='if(gt(iw,1440),if(gte(iw,ih),1440,-2),iw)':'if(gt(ih,1440),if(gt(ih,iw),1440,-2),ih)':flags=lanczos",
        "-pass",
        "2",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        output_path,
    ]
    try:
        logger.info("Starting second pass for video processing")
        run_ffmpeg(ffmpeg_args_second_pass, logger)
        logger.info(f"Video processing completed. Output saved to {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Second pass failed: {e}")


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
    output_dir = "out_new_itr_final"

    logger.info("FFmpeg high-quality batch processing script started")
    process_directory(input_dir, output_dir, logger)
    logger.info("FFmpeg high-quality batch processing script finished")
    print(f"Processing complete. Check the log file at {log_file} for details.")
