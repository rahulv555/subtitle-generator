from PyQt6.QtCore import QThread, pyqtSignal


class SubtitleWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, video_path, ass_text, output_path):
        super().__init__()
        self.video_path = video_path
        self.ass_text = ass_text
        self.output_path = output_path

    def run(self):
        # Call your blocking function
        from scripts.add_subtitles_to_video import add_styled_subtitles
        add_styled_subtitles(self.video_path, self.ass_text, self.output_path)
        self.finished.emit()