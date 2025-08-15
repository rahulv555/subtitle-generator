import os
from pathlib import Path
import subprocess
import shlex
import re


def convert_to_ass(srt_text, font="Arial", font_size=28,
                             primary_color="&HFFFFFF&", outline_color="&H000000&",
                             outline=2, shadow=0, alignment=2):
    """
    Convert SRT text into ASS text with styling.
    """
    style_header = f"""[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},{primary_color},&H000000&,{outline_color},&H000000&,-1,0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},10,10,30,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = srt_text.strip().splitlines()
    ass_events = []
    time_pattern = re.compile(r"(\d+):(\d+):(\d+),(\d+)")

    def srt_time_to_ass(t):
        m = time_pattern.match(t)
        h, mi, s, ms = map(int, m.groups())
        return f"{h:01}:{mi:02}:{s:02}.{int(ms/10):02}"

    i = 0
    while i < len(lines):
        if lines[i].isdigit():
            start_time, end_time = lines[i + 1].split(" --> ")
            text = "\\N".join(lines[i + 2:i + 3])  # simple, 1-line text
            ass_events.append(
                f"Dialogue: 0,{srt_time_to_ass(start_time)},{srt_time_to_ass(end_time)},Default,,0,0,0,,{text}"
            )
            i += 4
        else:
            i += 1

    ass_text = style_header + "\n".join(ass_events)
    return ass_text


def add_styled_subtitles(video_path, ass_text, output_path):
    """
    Burn styled ASS subtitles into a video using ffmpeg.

    Args:
        video_path: Path to video file.
        ass_text: ASS subtitle text (already includes styles).
        output_path: Path to save output video.
    """
    video_path = os.path.abspath(video_path).replace("\\", "/")
    output_path = os.path.abspath(output_path).replace("\\", "/")

    # Write ASS text to a temporary file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_ass_path = os.path.join(script_dir, "temp.ass")
    with open(temp_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_text)
    
    temp_ass_path = Path(temp_ass_path).resolve().as_posix()
    if os.name == "nt": #windows
        temp_ass_path = temp_ass_path.replace(":", r"\:")
    vf_filter = f"subtitles='{temp_ass_path}'"

    # Burn subtitles using ffmpeg
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", vf_filter,
        output_path
    ]
    subprocess.run(cmd, check=True)

    # Optionally remove temp file
    os.remove(os.path.join(script_dir, "temp.ass"))


if __name__ == "__main__":
    video_path = "input.mp4"
    srt_text = """1
00:00:01,000 --> 00:00:04,000
Hello World!"""

    ass_text = convert_to_ass(srt_text)
    output_path = "output_with_subs.mp4"
    add_styled_subtitles(video_path, ass_text, output_path)
