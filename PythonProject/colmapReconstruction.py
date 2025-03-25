import subprocess
import os
import json
import logging
from multiprocessing import Queue
from PySide6.QtWidgets import QMessageBox

class ColmapReconstructor:
    def __init__(self, config, progress_queue=None):
        try:
            self.image_folder = config["output_folder"]
            self.workspace_folder = config["workspace_folder"]
            self.colmap_executable = config["colmap_executable"]
        except KeyError as e:
            raise KeyError(f"Missing configuration key: {e}")
        self.progress_queue = progress_queue

        self.check_paths()
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def check_paths(self):
        paths = [
            self.image_folder,
            self.workspace_folder,
            self.colmap_executable
        ]
        for path in paths:
            logging.debug(f"Checking path: {path}")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path does not exist: {path}")

    def run_command(self, command, description):
        command_str = ' '.join(command)
        logging.debug(f"Running command: {command_str}")
        if self.progress_queue:
            self.progress_queue.put(f"Running command: {command_str}")
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        logging.debug(f"Command stdout: {result.stdout}")
        logging.debug(f"Command stderr: {result.stderr}")
        if self.progress_queue:
            self.progress_queue.put(f"Command stdout: {result.stdout}")
            self.progress_queue.put(f"Command stderr: {result.stderr}")
        if result.returncode != 0:
            error_message = f"Error executing: {command_str}\n{result.stderr}"
            logging.error(f"{error_message}")
            if self.progress_queue:
                self.progress_queue.put(error_message)
            raise RuntimeError(f"Command failed: {command_str}\n{result.stderr}")
        if self.progress_queue:
            self.progress_queue.put(description + " completed")
        logging.debug(f"{description} completed")

    def run_colmap(self):
        if not os.path.exists(self.workspace_folder):
            os.makedirs(self.workspace_folder)

        sparse_folder = os.path.join(self.workspace_folder, "sparse")
        if not os.path.exists(sparse_folder):
            os.makedirs(sparse_folder)

        dense_folder = os.path.join(self.workspace_folder, "dense")
        if not os.path.exists(dense_folder):
            os.makedirs(dense_folder)

        fused_output_path = os.path.join(dense_folder, "fused.ply")
        meshed_output_path = os.path.join(dense_folder, "meshed.ply")

        commands = [
            ("Feature Extraction", [
                self.colmap_executable, "feature_extractor",
                "--database_path", os.path.join(self.workspace_folder, "database.db"),
                "--image_path", self.image_folder,
                "--ImageReader.single_camera", "1"
            ]),
            ("Exhaustive Matching", [
                self.colmap_executable, "exhaustive_matcher",
                "--database_path", os.path.join(self.workspace_folder, "database.db")
            ]),
            ("Sparse Reconstruction", [
                self.colmap_executable, "mapper",
                "--database_path", os.path.join(self.workspace_folder, "database.db"),
                "--image_path", self.image_folder,
                "--output_path", sparse_folder
            ]),
            ("Image Undistortion", [
                self.colmap_executable, "image_undistorter",
                "--image_path", self.image_folder,
                "--input_path", os.path.join(sparse_folder, "0"),
                "--output_path", dense_folder,
                "--output_type", "COLMAP"
            ]),
            ("Dense Reconstruction", [
                self.colmap_executable, "patch_match_stereo",
                "--workspace_path", dense_folder,
                "--workspace_format", "COLMAP",
                "--PatchMatchStereo.geom_consistency", "true"
            ]),
            ("Dense Fusion", [
                self.colmap_executable, "stereo_fusion",
                "--workspace_path", dense_folder,
                "--workspace_format", "COLMAP",
                "--input_type", "geometric",
                "--output_path", fused_output_path
            ]),
            ("Mesh Generation", [
                self.colmap_executable, "poisson_mesher",
                "--input_path", fused_output_path,
                "--output_path", meshed_output_path
            ])
        ]

        for description, command in commands:
            try:
                self.run_command(command, description)
                print(f"{description} step completed successfully.")
            except RuntimeError as e:
                logging.error(f"{description} failed with error: {e}")
                if self.progress_queue:
                    self.progress_queue.put(f"[ERROR] {description} failed with error: {e}")
                break

        # 三维重建完成后弹出消息框
        self.show_message("三维重建完成")

    def show_message(self, message):
        message_dialog = QMessageBox()
        message_dialog.setIcon(QMessageBox.Information)
        message_dialog.setWindowTitle("信息")
        message_dialog.setText(message)
        message_dialog.setStandardButtons(QMessageBox.Ok)
        message_dialog.setDefaultButton(QMessageBox.Ok)
        message_dialog.exec()

if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)
    progress_queue = Queue()
    reconstructor = ColmapReconstructor(config, progress_queue)
    reconstructor.run_colmap()
    print("3D reconstruction process completed.")
