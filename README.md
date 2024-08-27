#One Iteration FFMPEG arguments detail:
-y: Overwrite output file without asking for confirmation.
-i [input]: Specifies the input file.
-preset slow: Sets the encoding preset to 'slow', which provides a good balance between encoding speed and compression efficiency.
-crf 17: Sets the Constant Rate Factor to 17, which provides very high quality. Lower values mean higher quality but larger file size (range: 0-51, where 0 is lossless).
-maxrate 15M: Sets the maximum bitrate to 15 Mbps.
-bufsize 25M: Sets the buffer size for rate control to 25 MB.
-vf scale=[width]:[height]:flags=lanczos: Video filter to resize the video using Lanczos algorithm, which generally provides high quality.
-c:v libx264: Sets the video codec to H.264.
-x264-params ref=6:me=umh:subme=8:rc-lookahead=60: Advanced x264 encoder parameters:

ref=6: Sets the number of reference frames to 6.
me=umh: Sets the motion estimation method to Uneven Multi-Hexagon Search.
subme=8: Sets the subpixel motion estimation and mode decision quality.
rc-lookahead=60: Sets the number of frames to look ahead for frametype and ratecontrol.


-pix_fmt yuv420p: Sets the pixel format to YUV 4:2:0, which is widely compatible.
-color_primaries bt709, -color_trc bt709, -colorspace bt709: Sets color space parameters to BT.709 standard (commonly used for HD video).
-c:a aac: Sets the audio codec to AAC.
-b:a 256k: Sets the audio bitrate to 256 kbps.
-ar 48000: Sets the audio sample rate to 48 kHz.
-movflags +faststart: Optimizes the output file for web streaming by moving the MOOV atom to the beginning of the file.

#######################################################################################################
#Two Iteration FFMPEG arguments detail:
First pass: Analyzes the video to gather data for optimal encoding
Second pass: Uses the data from the first pass to encode the video with optimal settings
@First Argument Pass:
-y: Overwrite output file without asking for confirmation.
-i [input]: Specifies the input file.
-preset veryslow: Uses the 'veryslow' preset, which provides the best compression efficiency but takes longer to encode.
-b:v 3500k: Sets the target video bitrate to 3500 kbps.
-maxrate 4000k: Sets the maximum allowed bitrate to 4000 kbps.
-bufsize 7000k: Sets the buffer size for rate control to 7000 kbps.
-vf: Applies video filters:

unsharp=5:5:1.0: Applies a slight sharpening effect.
scale='if(gt(iw,1440),if(gte(iw,ih),1440,-2),iw)':'if(gt(ih,1440),if(gt(ih,iw),1440,-2),ih)':flags=lanczos:
Scales the video to a maximum dimension of 1440 pixels while maintaining aspect ratio, using the high-quality Lanczos algorithm.


-pass 1: Indicates this is the first pass of a two-pass encoding process.
-f mp4: Forces the output format to MP4.
/dev/null: Discards the output as we only need the statistics from this pass.

@Second Argument Pass:
-pass 2: Indicates this is the second pass of the two-pass encoding process.
-b:a 192k: Sets the audio bitrate to 192 kbps.
-movflags +faststart: Optimizes the output file for web streaming by moving the MOOV atom to the beginning of the file.
[output]: Specifies the output file path instead of /dev/null
