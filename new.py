import subprocess
import logging
import os
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


def process_video(input_path, output_path, logger):
    ffmpeg_args = [
        "-y",
        "-i",
        input_path,
        "-preset",
        "veryslow",
        "-crf",
        "18",
        "-maxrate",
        "6000k",
        "-bufsize",
        "9000k",
        "-vf",
        "unsharp=5:5:1.0,scale='min(1440,iw)':'-2'",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p10le",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
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
    output_dir = "out2"

    logger.info("FFmpeg high-quality batch processing script started")
    process_directory(input_dir, output_dir, logger)
    logger.info("FFmpeg high-quality batch processing script finished")
    print(f"Processing complete. Check the log file at {log_file} for details.")
