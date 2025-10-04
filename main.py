import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QLabel, QFileDialog, QMessageBox, QHBoxLayout
)
from pydub import AudioSegment


class BeatSwapper(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.file_path = ""

    def init_ui(self):
        self.setWindowTitle("节拍调换器 - 按拍交换（支持自定义BPM）")
        self.setGeometry(300, 300, 450, 300)

        layout = QVBoxLayout()

        # 文件选择
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.file_button = QPushButton("选择 MP3/MP4 文件")
        self.file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_button)
        layout.addLayout(file_layout)

        # BPM 输入
        layout.addWidget(QLabel("BPM（每分钟节拍数）:"))
        self.bpm_input = QLineEdit()
        self.bpm_input.setPlaceholderText("例如: 120")
        layout.addWidget(self.bpm_input)

        # 每小节拍数
        layout.addWidget(QLabel("每小节拍数:"))
        self.beats_per_bar_input = QLineEdit()
        self.beats_per_bar_input.setText("4")  # 默认4拍
        layout.addWidget(self.beats_per_bar_input)

        # 交换拍号（如 "2,4"）
        layout.addWidget(QLabel("要交换的拍号（用逗号分隔，如 2,4）:"))
        self.swap_beats_input = QLineEdit()
        self.swap_beats_input.setText("2,4")
        layout.addWidget(self.swap_beats_input)

        # 处理按钮
        self.process_button = QPushButton("处理并保存")
        self.process_button.clicked.connect(self.process_file)
        layout.addWidget(self.process_button)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音频文件",
            "",
            "音频文件 (*.mp3 *.mp4)"
        )
        if file_path:
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))

    def parse_beat_indices(self, input_str, total_beats):
        """解析用户输入的拍号，返回要交换的两个索引（0-based）"""
        try:
            parts = input_str.replace(" ", "").split(",")
            if len(parts) != 2:
                raise ValueError("必须输入两个拍号，用逗号分隔")
            beat1, beat2 = int(parts[0]), int(parts[1])
            if not (1 <= beat1 <= total_beats and 1 <= beat2 <= total_beats):
                raise ValueError(f"拍号必须在 1 到 {total_beats} 之间")
            if beat1 == beat2:
                raise ValueError("两个拍号不能相同")
            return beat1 - 1, beat2 - 1  # 转为0-based索引
        except ValueError as e:
            raise ValueError(f"拍号格式错误: {e}")

    def process_file(self):
        if not self.file_path:
            QMessageBox.warning(self, "错误", "请先选择一个文件！")
            return

        try:
            # 获取输入
            bpm_str = self.bpm_input.text().strip()
            beats_per_bar_str = self.beats_per_bar_input.text().strip()
            swap_str = self.swap_beats_input.text().strip()

            if not bpm_str or not beats_per_bar_str or not swap_str:
                QMessageBox.warning(self, "错误", "请填写所有字段！")
                return

            bpm = float(bpm_str)
            beats_per_bar = int(beats_per_bar_str)

            if bpm <= 0 or beats_per_bar <= 0:
                raise ValueError("BPM 和 每小节拍数必须大于0")

            # 计算时间
            seconds_per_beat = 60.0 / bpm
            bar_duration_sec = beats_per_bar * seconds_per_beat
            bar_duration_ms = int(bar_duration_sec * 1000)
            beat_duration_ms = int(seconds_per_beat * 1000)

            if beat_duration_ms <= 0:
                raise ValueError("BPM过高，每拍时长太短")

            # 解析要交换的拍
            idx1, idx2 = self.parse_beat_indices(swap_str, beats_per_bar)

            # 加载音频
            audio = AudioSegment.from_file(self.file_path)

            # 处理每个小节
            processed_segments = []
            bar_start = 0
            while bar_start < len(audio):
                bar_end = min(bar_start + bar_duration_ms, len(audio))
                bar = audio[bar_start:bar_end]

                # 如果当前小节不足一拍，直接保留
                if len(bar) < beat_duration_ms:
                    processed_segments.append(bar)
                    bar_start = bar_end
                    continue

                # 切分小节为拍
                beats = []
                for i in range(beats_per_bar):
                    beat_start = i * beat_duration_ms
                    beat_end = min(beat_start + beat_duration_ms, len(bar))
                    beat = bar[beat_start:beat_end]
                    beats.append(beat)

                # 交换指定拍
                beats[idx1], beats[idx2] = beats[idx2], beats[idx1]

                # 合并拍为新小节
                new_bar = sum(beats, AudioSegment.empty())
                processed_segments.append(new_bar)

                bar_start = bar_end

            final_audio = sum(processed_segments, AudioSegment.empty())

            # 保存
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            output_path = f"output_{base_name}.mp3"
            final_audio.export(output_path, format="mp3")

            QMessageBox.information(self, "成功", f"处理完成！\n已保存为: {output_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理失败:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    window = BeatSwapper()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()