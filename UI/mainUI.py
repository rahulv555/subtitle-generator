import sys
import os
from time import sleep
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QPlainTextEdit, QLabel, QTabWidget, QComboBox, QHBoxLayout, QSpinBox, QCheckBox
)
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QImage, QPixmap
from UI.Progress import SubtitleWorker
from PyQt6.QtWidgets import QProgressBar

import cv2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.create_subtitles import SubtitleGenerator
from scripts.add_subtitles_to_video import convert_to_ass, add_styled_subtitles
from UI.ASSPreview import ASSPreview
from UI.LoadingOverlay import LoadingOverlay


class SubtitleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Generator")
        self.resize(900, 600)
        self.video_path = None

        # Tabs
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab1, "Generate Subtitles")
        self.tabs.addTab(self.tab2, "Edit & Finalize")

        self.init_tab1()
        self.init_tab2()
        self.loading_overlay = LoadingOverlay(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

    def init_tab1(self):
        layout = QVBoxLayout()

        # Video preview and file name
        self.video_label = QLabel("No video selected")
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self.video_label.setFixedSize(300, 150)

        # Select video button
        btn_select_video = QPushButton("Select Video")
        btn_select_video.clicked.connect(self.select_video)

        # Put label and button in horizontal layout
        video_row = QHBoxLayout()
        video_row.addWidget(self.video_label)
        video_row.addWidget(btn_select_video)
        layout.addLayout(video_row)

        

        # Number inputs for options
        
        max_words_per_line_layout = QHBoxLayout()
        self.spin_max_words_per_line = QSpinBox()
        self.spin_max_words_per_line.setRange(0, 100)
        self.spin_max_words_per_line.setValue(5)
        max_words_per_line_layout.addWidget(QLabel("Max words per line:"))
        max_words_per_line_layout.addWidget(self.spin_max_words_per_line)

        max_segment_duration_layout = QHBoxLayout()
        self.spin_max_segment_duration = QSpinBox()
        self.spin_max_segment_duration.setRange(0, 100)
        self.spin_max_segment_duration.setValue(2)
        max_segment_duration_layout.addWidget(QLabel("Max segment duration (s):"))
        max_segment_duration_layout.addWidget(self.spin_max_segment_duration)

        max_words_per_segment_layout = QHBoxLayout()
        self.spin_max_words_per_segment = QSpinBox()
        self.spin_max_words_per_segment.setRange(0, 100)
        self.spin_max_words_per_segment.setValue(0)
        max_words_per_segment_layout.addWidget(QLabel("Max words per segment:"))
        max_words_per_segment_layout.addWidget(self.spin_max_words_per_segment)

        layout.addLayout(max_words_per_line_layout)
        layout.addLayout(max_segment_duration_layout)
        layout.addLayout(max_words_per_segment_layout)

        # Whisper device dropdown
        self.device_dropdown = QComboBox()
        self.device_dropdown.addItems(["cpu", "cuda", "mps"])
        layout.addWidget(QLabel("Processing Device:"))
        layout.addWidget(self.device_dropdown)

        #Model size dropdown
        self.model_size_dropdown = QComboBox()
        self.model_size_dropdown.addItems(["tiny", "base", "small", "medium", "large","turbo"])
        layout.addWidget(QLabel("Whisper model size:"))
        layout.addWidget(self.model_size_dropdown)

        # Generate button
        self.btn_generate_srt = QPushButton("Generate Subtitles")
        self.btn_generate_srt.clicked.connect(self.generate_srt)
        layout.addWidget(self.btn_generate_srt)

        # SRT editor
        self.srt_editor = QPlainTextEdit()
        self.srt_editor.setPlaceholderText("SRT subtitles will appear here...")
        layout.addWidget(self.srt_editor)

        self.checkbox_burn_subtitles = QCheckBox("Burn in subtitles (Otherwise soft subtitles that can be selected in player)")
        self.checkbox_burn_subtitles.setChecked(False)  # default unchecked
        layout.addWidget(self.checkbox_burn_subtitles)

        # Save & convert buttons
        row_buttons = QHBoxLayout()
        self.btn_save_srt_with_video = QPushButton("Save SRT and Convert to Video")
        self.btn_save_srt_with_video.clicked.connect(self.save_srt_with_video)
        self.btn_convert_ass = QPushButton("Convert to ASS")
        self.btn_convert_ass.clicked.connect(self.convert_to_ass)
        row_buttons.addWidget(self.btn_save_srt_with_video)
        row_buttons.addWidget(self.btn_convert_ass)
        layout.addLayout(row_buttons)

        status_layout_1 = QHBoxLayout()
        self.status_label_tab1 = QLabel("Status: Idle")
        status_layout_1.addWidget(self.status_label_tab1)
        layout.addLayout(status_layout_1)

        self.tab1.setLayout(layout)

    def init_tab2(self):
        layout = QVBoxLayout()

        # ASS editor
        self.ass_editor = ASSPreview()
        self.ass_editor.set_ass_text("ASS subtitles will appear here...")

        # Add to video button
        self.btn_add_video = QPushButton("Add Subtitles to Video")
        self.btn_add_video.clicked.connect(self.add_to_video)

        # Video preview
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        layout.addWidget(self.ass_editor)
        layout.addWidget(self.btn_add_video)
        layout.addWidget(self.video_widget)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)

        self.tab2.setLayout(layout)

    def select_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Videos (*.mp4 *.mkv *.avi)"
        )
        if file_path:
            self.video_path = file_path
            self.video_label.setText(os.path.basename(file_path))
            self.ass_editor.set_video_preview(file_path)

            # Show first frame preview
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                qimg = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
                pix = QPixmap.fromImage(qimg).scaled(
                    self.video_label.width(), self.video_label.height(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.video_label.setPixmap(pix)

    def generate_srt(self):
        if not self.video_path:
            self.srt_editor.setPlainText("Please select a video first.")
            return

        self.btn_generate_srt.setDisabled(True)
        self.status_label_tab1.setText("Status: Generating SRT subtitles...")
        sleep(1)

        max_words_per_line = self.spin_max_words_per_line.value()
        max_segment_duration = self.spin_max_segment_duration.value()
        max_words_per_segment = self.spin_max_words_per_segment.value()
        device = self.device_dropdown.currentText()
        model_size = self.model_size_dropdown.currentText()
        
        self.loading_overlay = LoadingOverlay(self)
        # Placeholder SRT content
        subtitleGenerator = SubtitleGenerator(model_name=model_size, device=device)
        print("Extracting audio...")
        audio_path = os.path.splitext(self.video_path)[0] + ".wav"
        subtitleGenerator.extract_audio(self.video_path, audio_path)
        print("Transcribing audio...")
        srt_path = os.path.splitext(self.video_path)[0] + ".srt"
        subtitleGenerator.transcribe_audio(audio_path, srt_path, max_words_per_line=max_words_per_line, max_segment_duration=max_segment_duration, max_words_per_segment=max_words_per_segment)
        print("SRT Created")
        with open(srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()
        self.srt_editor.setPlainText(srt_content)
        self.loading_overlay.hide_overlay
        self.btn_generate_srt.setDisabled(False)
        self.status_label_tab1.setText("Status: SRT Subtitles generated successfully.")

    def save_srt(self):
        pass

    def save_srt_with_video(self):
        if not self.srt_editor.toPlainText().strip():
            return
        
        

        burn_in = self.checkbox_burn_subtitles.isChecked()

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Video",
            "",  # You can provide a default name here if you want
            "MP4 Video (*.mp4)"
        )

        print(save_path, " save_path")
        if save_path:
            self.btn_save_srt_with_video.setDisabled(True)
            self.status_label_tab1.setText("Status: Saving SRT and adding to video...")
            sleep(1)
            
            #saving subitles to SRT file
            srt_path = os.path.splitext(self.video_path)[0] + ".srt"
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(self.srt_editor.toPlainText())
            print("Saved Subtitles to SRT")

            #need to check srt in correct format
            print("Adding subtitles to video...")
            device = self.device_dropdown.currentText()
            model_size = self.model_size_dropdown.currentText()
            subtitleGenerator = SubtitleGenerator(model_name=model_size, device=device)
            subtitleGenerator.add_subtitles_to_video(self.video_path, srt_path, save_path, burn_in)
            print(f"Done! Output video: {save_path}")

            self.btn_save_srt_with_video.setDisabled(False)
            self.status_label_tab1.setText(f"Status: SRT saved at {srt_path}, Video saved at {save_path}. Now Idle")

    def convert_to_ass(self):
        if not self.srt_editor.toPlainText().strip():
            self.ass_editor.set_ass_text("Please generate or paste SRT first.")
            return

        self.btn_convert_ass.setDisabled(True)
        srt_text = self.srt_editor.toPlainText().strip()
        #create temp srt file
        ass_content = convert_to_ass(srt_text)
        
        self.ass_editor.set_ass_text(ass_content)
        self.tabs.setCurrentIndex(1)
        self.btn_convert_ass.setDisabled(False)

    def add_to_video(self):
        if not self.video_path:
            print("Input video not selected")
            return

        # Ask user for output filename and folder
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Video As", 
            os.path.splitext(os.path.basename(self.video_path))[0] + "_subtitled.mp4", 
            "Videos (*.mp4 *.mkv *.avi)"
        )
        if not save_path:
            return  # User cancelled

        # Call your custom function to burn subtitles
        # Replace `self.ass_editor.ass_path` with the path to your ASS file
        # if hasattr(self.ass_editor, 'ass_path') and self.ass_editor.ass_path:
        #     ass_path = self.ass_editor.ass_path
        # else:
        #     ass_path = None  # or handle error

        # Example custom function call
        #my_burn_subtitles_to_video(input_path=self.video_path, output_path=save_path, ass_path=ass_path)
        
        self.btn_add_video.setDisabled(True)
        self.btn_add_video.setText("Adding subtitles to video...")
        sleep(1)
        #need to check ass in correct format
        ass_text = self.ass_editor.editor.toPlainText()
        # add_styled_subtitles(self.video_path, ass_text, ass_path)
        worker = SubtitleWorker(self.video_path, ass_text, save_path)
        worker.finished.connect(lambda: self.progress_bar.setRange(0, 100))
        worker.start()

        print('Done')
        self.btn_add_video.setDisabled(False)
        self.btn_add_video.setText("Add Subtitles to Video")
        # Optionally, play the new video
        self.media_player.setSource(QUrl.fromLocalFile(save_path))
        self.media_player.play()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubtitleApp()
    window.show()
    sys.exit(app.exec())
