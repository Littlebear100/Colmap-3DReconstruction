import sys
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QFileDialog, QLabel, QLineEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPalette, QBrush, QLinearGradient, QColor
from multiprocessing import Manager
from logging_config import get_logger

class Worker(QThread):
    finished = Signal(str)
    progress_message = Signal(str)

    def __init__(self, command, progress_queue=None):
        super().__init__()
        self.command = command
        self.progress_queue = progress_queue
        self.error_message = None
        self.logger = get_logger(__name__)

    def run(self):
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.progress_message.emit(output.strip())
                self.logger.info(output.strip())
        stderr_output = process.stderr.read()
        if stderr_output:
            self.progress_message.emit(stderr_output.strip())
            self.logger.error(stderr_output.strip())
        exit_code = process.poll()
        if exit_code != 0:
            self.error_message = stderr_output.strip()
        self.finished.emit(self.error_message or "成功")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("三维重建软件")
        self.setGeometry(100, 100, 580, 520)

        self.setAutoFillBackground(True)
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QLinearGradient.StretchToDeviceMode)
        gradient.setColorAt(0.0, QColor("#f0f4f8"))
        gradient.setColorAt(1.0, QColor("#d9e2ec"))
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        font = QFont("Microsoft YaHei UI", 12)

        self.setStyleSheet("""
            QMainWindow {
                background-color: transparent;
            }
            QLabel#TitleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
                qproperty-alignment: AlignCenter;
                font-family: "Microsoft YaHei UI", Arial, sans-serif;
            }
            QLabel#DescriptionLabel {
                font-size: 14px;
                color: #666666;
                qproperty-alignment: AlignCenter;
                font-family: "Microsoft YaHei UI", Arial, sans-serif;
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: #ffffff;
                color: #000000;
                font-size: 12px;
                font-family: "Microsoft YaHei UI", Arial, sans-serif;
            }
            QPushButton {
                border: none;
                border-radius: 5px;
                padding: 6px;
                font-family: "Microsoft YaHei UI", Arial, sans-serif;
            }
            QPushButton#PrimaryButton {
                background-color: #007BFF;
                color: #ffffff;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton#PrimaryButton:hover {
                background-color: #0056b3;
            }
            QPushButton#PrimaryButton:pressed {
                background-color: #003d80;
            }
            QPushButton#SecondaryButton {
                background-color: #66BB6A;
                color: #ffffff;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton#SecondaryButton:hover {
                background-color: #5DAE59;
            }
            QPushButton#SecondaryButton:pressed {
                background-color: #4C8C4A;
            }
            QFrame {
                border-radius: 10px;
                padding: 10px;
            }
            QFrame#ImageProcessFrame {
                background-color: #e6f7ff;
            }
            QFrame#ReconstructionFrame {
                background-color: #fff2e6;
            }
            QFrame#VisualizationFrame {
                background-color: #e6ffe6;
            }
            QMessageBox {
                background-color: #ffffff;
                color: black;
                border-radius: 10px;
            }
            QLabel {
                color: black;
                font-size: 14px;
                font-family: "Microsoft YaHei UI", Arial, sans-serif;
            }
        """)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(12)

        # 图像处理部分
        self.image_process_frame = QFrame()
        self.image_process_frame.setObjectName("ImageProcessFrame")
        self.image_process_layout = QVBoxLayout()
        self.image_process_layout.setSpacing(8)

        self.image_process_label = QLabel("步骤1：图像处理", self)
        self.image_process_label.setObjectName("TitleLabel")
        self.image_process_label.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        self.image_process_layout.addWidget(self.image_process_label, alignment=Qt.AlignCenter)

        self.image_folder_layout = QHBoxLayout()
        self.image_folder_button = QPushButton("选择图像文件夹", self)
        self.image_folder_button.setObjectName("SecondaryButton")
        self.image_folder_button.setFixedWidth(150)
        self.image_folder_button.clicked.connect(self.select_image_folder)
        self.image_folder_layout.addWidget(self.image_folder_button)

        self.image_folder_path = QLineEdit(self)
        self.image_folder_path.setFixedWidth(250)
        self.image_folder_layout.addWidget(self.image_folder_path)

        self.image_process_layout.addLayout(self.image_folder_layout)
        self.image_process_layout.setAlignment(self.image_folder_layout, Qt.AlignCenter)

        self.process_images_button = QPushButton("图像录入", self)
        self.process_images_button.setObjectName("PrimaryButton")
        self.process_images_button.setFont(QFont("Microsoft YaHei UI", 14))
        self.process_images_button.setFixedSize(160, 40)
        self.process_images_button.clicked.connect(self.process_images)
        self.image_process_layout.addWidget(self.process_images_button, alignment=Qt.AlignCenter)

        self.image_process_description = QLabel("选择包含要处理的图像的文件夹", self)
        self.image_process_description.setObjectName("DescriptionLabel")
        self.image_process_description.setFont(QFont("Microsoft YaHei UI", 14))
        self.image_process_layout.addWidget(self.image_process_description, alignment=Qt.AlignCenter)

        self.image_process_frame.setLayout(self.image_process_layout)
        self.layout.addWidget(self.image_process_frame)

        # 三维重建部分
        self.reconstruction_frame = QFrame()
        self.reconstruction_frame.setObjectName("ReconstructionFrame")
        self.reconstruction_layout = QVBoxLayout()
        self.reconstruction_layout.setSpacing(8)

        self.reconstruction_label = QLabel("步骤2：三维重建", self)
        self.reconstruction_label.setObjectName("TitleLabel")
        self.reconstruction_label.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        self.reconstruction_layout.addWidget(self.reconstruction_label, alignment=Qt.AlignCenter)

        self.workspace_folder_layout = QHBoxLayout()
        self.workspace_folder_button = QPushButton("选择输出文件夹", self)
        self.workspace_folder_button.setObjectName("SecondaryButton")
        self.workspace_folder_button.setFixedWidth(150)
        self.workspace_folder_button.clicked.connect(self.select_workspace_folder)
        self.workspace_folder_layout.addWidget(self.workspace_folder_button)

        self.workspace_folder_path = QLineEdit(self)
        self.workspace_folder_path.setFixedWidth(250)
        self.workspace_folder_layout.addWidget(self.workspace_folder_path)

        self.workspace_folder_container = QWidget()
        self.workspace_folder_container.setLayout(self.workspace_folder_layout)
        self.reconstruction_layout.addWidget(self.workspace_folder_container, alignment=Qt.AlignCenter)

        self.reconstruct_button = QPushButton("进行三维重建", self)
        self.reconstruct_button.setObjectName("PrimaryButton")
        self.reconstruct_button.setFont(QFont("Microsoft YaHei UI", 16))
        self.reconstruct_button.setFixedSize(200, 50)
        self.reconstruct_button.clicked.connect(self.run_reconstruction)
        self.reconstruction_layout.addWidget(self.reconstruct_button, alignment=Qt.AlignCenter)

        self.reconstruction_description = QLabel("选择要输出三维重建结果的文件夹", self)
        self.reconstruction_description.setObjectName("DescriptionLabel")
        self.reconstruction_description.setFont(QFont("Microsoft YaHei UI", 14))
        self.reconstruction_layout.addWidget(self.reconstruction_description, alignment=Qt.AlignCenter)

        self.reconstruction_frame.setLayout(self.reconstruction_layout)
        self.layout.addWidget(self.reconstruction_frame)

        # 可视化部分
        self.visualization_frame = QFrame()
        self.visualization_frame.setObjectName("VisualizationFrame")
        self.visualization_layout = QVBoxLayout()
        self.visualization_layout.setSpacing(8)

        self.visualization_label = QLabel("步骤3：结果可视化", self)
        self.visualization_label.setObjectName("TitleLabel")
        self.visualization_label.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        self.visualization_layout.addWidget(self.visualization_label, alignment=Qt.AlignCenter)

        self.visualize_button = QPushButton("查看结果", self)
        self.visualize_button.setObjectName("PrimaryButton")
        self.visualize_button.setFont(QFont("Microsoft YaHei UI", 14))
        self.visualize_button.setFixedSize(160, 40)
        self.visualize_button.clicked.connect(self.visualize_results)
        self.visualization_layout.addWidget(self.visualize_button, alignment=Qt.AlignCenter)

        self.visualization_description = QLabel("可视化三维重建结果", self)
        self.visualization_description.setObjectName("DescriptionLabel")
        self.visualization_description.setFont(QFont("Microsoft YaHei UI", 14))
        self.visualization_layout.addWidget(self.visualization_description, alignment=Qt.AlignCenter)

        self.visualization_frame.setLayout(self.visualization_layout)
        self.layout.addWidget(self.visualization_frame)

        # 设置中央部件
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def select_image_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择图像文件夹")
        if folder:
            self.image_folder_path.setText(folder)

    def select_workspace_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.workspace_folder_path.setText(folder)

    def process_images(self):
        image_folder = self.image_folder_path.text()
        if image_folder:
            manager = Manager()
            progress_queue = manager.Queue()
            self.worker = Worker(["python", "ImageProcessor.py"], progress_queue)
            self.worker.progress_message.connect(self.update_log)
            self.worker.finished.connect(lambda message: self.on_command_finished(message, "图像录入成功"))
            self.worker.start()
        else:
            self.show_error("请选择图像文件夹")

    def run_reconstruction(self):
        workspace_folder = self.workspace_folder_path.text()
        if workspace_folder:
            manager = Manager()
            progress_queue = manager.Queue()
            self.worker = Worker(["python", "colmapReconstruction.py"], progress_queue)
            self.worker.progress_message.connect(self.update_log)
            self.worker.finished.connect(lambda message: self.on_command_finished(message, "三维重建成功"))
            self.worker.start()
        else:
            self.show_error("请选择输出文件夹")

    def visualize_results(self):
        self.run_command(["python", "visualization.py"], "欢迎您再次使用！")

    def run_command(self, command, success_message, progress_queue=None, progress_bar=False):
        if progress_bar:
            if not hasattr(self, 'worker') or self.worker is None:
                self.worker = Worker(command, progress_queue)
                self.worker.progress_message.connect(self.update_log)
                self.worker.finished.connect(lambda message: self.on_command_finished(message, success_message))
                self.worker.start()
            else:
                self.worker.command = command
                self.worker.progress_queue = progress_queue
                self.worker.finished.disconnect()
                self.worker.finished.connect(lambda message: self.on_command_finished(message, success_message))
                self.worker.start()
        else:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            while process.poll() is None:
                if progress_queue and not progress_queue.empty():
                    message = progress_queue.get()
                    self.update_log(message)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                self.show_error(f"错误: {stderr}")
            else:
                self.show_message(success_message)

    def update_log(self, message):
        print(message)

    def on_command_finished(self, message, success_message):
        if "成功" in message:
            self.show_message(success_message)
        else:
            self.show_error(f"操作失败，请查看日志文件了解详细信息：{message}")
        self.worker = None

    def show_error(self, message):
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("错误")
        error_dialog.setText(message)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.setDefaultButton(QMessageBox.Ok)
        error_dialog.exec()

    def show_message(self, message):
        message_dialog = QMessageBox(self)
        message_dialog.setIcon(QMessageBox.Information)
        message_dialog.setWindowTitle("信息")
        message_dialog.setText(message)
        message_dialog.setStandardButtons(QMessageBox.Ok)
        message_dialog.setDefaultButton(QMessageBox.Ok)
        message_dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
