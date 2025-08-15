import whisper
import os
import subprocess
import shlex
from pathlib import Path

class SubtitleGenerator:    
    
    def __init__(self, model_name="base", device="cuda"):
        self.model_name = model_name
        self.device = device
        self.model = whisper.load_model(model_name, device=device)
    def extract_audio(self, video_path, audio_path):
        # Extract audio from video using ffmpeg
        cmd = [
            'ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path
        ]
        subprocess.run(cmd, check=True)

    def split_subtitle_segments_by_duration(self, result, max_segment_duration):
        """
        Splits Whisper transcription segments into smaller ones while keeping
        the same format as Whisper's result["segments"].
        Requires result to have 'words' in each segment (word_timestamps=True).
        """
        new_segments = []
        seg_id = 0

        for segment in result["segments"]:
            current_start = None
            current_words = []

            for word in segment["words"]:
                if current_start is None:
                    current_start = word["start"]

                current_words.append(word)
                
                if word["end"] - current_start >= max_segment_duration:
                    seg_id += 1
                    new_segments.append({
                        "id": seg_id,
                        "start": current_start,
                        "end": word["end"],
                        "text": "".join([w["word"] for w in current_words]).strip(),
                        "words": current_words
                    })
                    current_start = None
                    current_words = []

            # Handle leftover words at the end of the segment
            if current_words:
                seg_id += 1
                new_segments.append({
                    "id": seg_id,
                    "start": current_start,
                    "end": current_words[-1]["end"],
                    "text": "".join([w["word"] for w in current_words]).strip(),
                    "words": current_words
                })

        # Replace segments in original result
        result["segments"] = new_segments
        return result
    def split_subtitle_segments_by_word_count(self, result, max_words_per_segment):
        """
        Splits Whisper transcription segments into smaller ones based on
        a maximum number of words per segment.
        Keeps the same format as Whisper's result["segments"].
        Requires result to have 'words' in each segment (word_timestamps=True).
        """
        new_segments = []
        seg_id = 0

        for segment in result["segments"]:
            current_words = []
            current_start = None

            for word in segment["words"]:
                if current_start is None:
                    current_start = word["start"]

                current_words.append(word)

                if len(current_words) >= max_words_per_segment:
                    seg_id += 1
                    new_segments.append({
                        "id": seg_id,
                        "start": current_start,
                        "end": current_words[-1]["end"],
                        "text": "".join([w["word"] for w in current_words]).strip(),
                        "words": current_words
                    })
                    current_words = []
                    current_start = None

            # Handle leftover words
            if current_words:
                seg_id += 1
                new_segments.append({
                    "id": seg_id,
                    "start": current_start,
                    "end": current_words[-1]["end"],
                    "text": "".join([w["word"] for w in current_words]).strip(),
                    "words": current_words
                })

        result["segments"] = new_segments
        return result

    def transcribe_audio(self, audio_path, srt_path, model_name="base", device="cuda", max_words_per_line=None, max_segment_duration=None, max_words_per_segment=None):
        def split_subtitle_text(text, max_words):
            """Split text into multiple lines with at most max_words words per line. (multiple lines withing the same segment)"""
            words = text.split()
            lines = []
            for i in range(0, len(words), max_words):
                lines.append(" ".join(words[i:i + max_words]))
            return "\n".join(lines)  # SRT uses actual line breaks


        model = whisper.load_model(model_name, device=device)
        
        if max_segment_duration or max_words_per_segment:
            result = model.transcribe(audio_path, task="transcribe", fp16=True, verbose=True, word_timestamps=True)

            if max_segment_duration:
                result = self.split_subtitle_segments_by_duration(result, max_segment_duration)

            if max_words_per_segment:
                result = self.split_subtitle_segments_by_word_count(result, max_words_per_segment)
        else:
            result = model.transcribe(audio_path, task="transcribe", fp16=True, verbose=True)
        # Save SRT
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"]):
                start = segment["start"]
                end = segment["end"]

                
                if max_words_per_line:
                    text = split_subtitle_text(segment["text"].strip(), max_words_per_line)
                else:
                    text = segment["text"].strip()
                
                f.write(f"{i+1}\n")
                f.write(f"{self.format_timestamp(start)} --> {self.format_timestamp(end)}\n")
                f.write(f"{text}\n\n")

    def format_timestamp(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    def add_subtitles_to_video(self, video_path, srt_path, output_path, burn_in=False):
        # Add subtitles to video using ffmpeg
        print(video_path, srt_path, output_path, burn_in)
        if burn_in:
            srt_path = Path(srt_path).as_posix()
            if os.name == "nt": #windows
                srt_path = srt_path.replace(":", r"\:")
            vf_filter = f"subtitles='{srt_path}'"

            # Burn subtitles into video permanently
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-vf", vf_filter,
                output_path
            ]
        else:
            # Embed as soft subtitles (toggle-able in player)
            cmd = [
                "ffmpeg", "-y", "-i", video_path, "-i", srt_path,
                "-c", "copy",
                "-c:s", "mov_text",  # Format for mp4
                output_path
            ]
        print(cmd)
        # cmd = [
        #     'ffmpeg', '-y', '-i', video_path, '-vf', f"subtitles={srt_path}", output_path
        # ]
        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    video_path = "input.mp4"  # Change to your video file
    audio_path = "audio.wav"
    srt_path = "subtitles.srt"
    output_path = "output_with_subs.mp4"
    subtitleGenerator = SubtitleGenerator(model_name="base", device="cuda")
    print("Extracting audio...")
    subtitleGenerator.extract_audio(video_path, audio_path)
    print("Transcribing audio...")
    subtitleGenerator.transcribe_audio(audio_path, srt_path, max_words_per_line=15, max_segment_duration=5, max_words_per_segment=5)
    print("Adding subtitles to video...")
    subtitleGenerator.add_subtitles_to_video(video_path, srt_path, output_path)
    print(f"Done! Output video: {output_path}")