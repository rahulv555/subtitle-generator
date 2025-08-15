import os
import subprocess
import shlex



def convert_to_ass(srt_path, font, font_size, primary_color, outline_color, outline, shadow, alignment):
    # Create a styled .ass file
    ass_path = os.path.splitext(srt_path)[0] + ".ass"
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


    # Convert .srt to .ass content
    with open(srt_path, "r", encoding="utf-8") as srt_file:
        lines = srt_file.read().strip().split("\n")

    ass_events = []
    import re
    time_pattern = re.compile(r"(\d+):(\d+):(\d+),(\d+)")
    
    def srt_time_to_ass(t):
        m = time_pattern.match(t)
        h, mi, s, ms = map(int, m.groups())
        return f"{h:01}:{mi:02}:{s:02}.{int(ms/10):02}"

    i = 0
    while i < len(lines):
        if lines[i].isdigit():
            # index line
            start_time, end_time = lines[i+1].split(" --> ")
            text = "\\N".join(lines[i+2:i+3])  # simple, 1-line text
            ass_events.append(
                f"Dialogue: 0,{srt_time_to_ass(start_time)},{srt_time_to_ass(end_time)},Default,,0,0,0,,{text}"
            )
            i += 4
        else:
            i += 1

    with open(ass_path, "w", encoding="utf-8") as ass_file:
        ass_file.write(style_header + "\n".join(ass_events))
    
    return ass_path


def add_styled_subtitles(video_path, srt_path, output_path,
                         font="Arial", font_size=28,
                         primary_color="&HFFFFFF&",  # white
                         outline_color="&H000000&",  # black
                         outline=2, shadow=0, alignment=2):
    """
    Burn styled subtitles into a video using ffmpeg and ASS styling.

    Args:
        video_path: Path to video file.
        srt_path: Path to .srt subtitle file.
        output_path: Path to save output video.
        font: Font name.
        font_size: Font size in points.
        primary_color: Text color in ASS format (&HAABBGGRR&).
        outline_color: Outline color in ASS format (&HAABBGGRR&).
        outline: Outline thickness.
        shadow: Drop shadow size.
        alignment: Subtitle position (1=bottom-left, 2=bottom-center, 3=bottom-right,
                   9=top-left, 8=top-center, 7=top-right).
    """

    video_path = os.path.abspath(video_path).replace("\\", "/")
    srt_path = os.path.abspath(srt_path).replace("\\", "/")
    output_path = os.path.abspath(output_path).replace("\\", "/")
    
    ass_path = convert_to_ass(srt_path, font, font_size, primary_color, outline_color, outline, shadow, alignment)
    
    

    # Burn styled subtitles into video\
    if(':' in ass_path):
        ass_path = ass_path[0]+"\\:" + ass_path[2:]
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"subtitles={shlex.quote(ass_path)}",
        output_path
    ]

    print(cmd)
    subprocess.run(cmd, check=True)




if __name__ == "__main__":
    video_path = "input.mp4"  # Change to your video file
    srt_path = "subtitles.srt"
    output_path = "output_with_modified_subs.mp4"
    add_styled_subtitles(video_path, srt_path, output_path)
   