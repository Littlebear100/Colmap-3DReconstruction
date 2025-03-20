import subprocess
import os
import json
from multiprocessing import Queue, cpu_count
from concurrent.futures import ThreadPoolExecutor

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

    def check_paths(self):
        paths = [
            self.image_folder,
            self.workspace_folder,
            self.colmap_executable
        ]
        for path in paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path does not exist: {path}")

    def run_command(self, command, description):
        command_str = ' '.join(command)
        print(f"Running command: {command_str}")
        result = subprocess.run(command_str, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            error_message = f"Error executing: {command_str}\n{result.stderr}"
            print(error_message)
            if self.progress_queue:
                self.progress_queue.put(error_message)
            raise RuntimeError(f"Command failed: {command_str}\n{result.stderr}")
        if self.progress_queue:
            self.progress_queue.put(description + " completed")
        print(f"{description} completed")

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
                "--ImageReader.single_camera", "1",
                "--SiftExtraction.max_num_features", "30000",
                "--SiftExtraction.estimate_affine_shape", "true",
                "--SiftExtraction.domain_size_pooling", "true"
            ]),
            ("Exhaustive Matching", [
                self.colmap_executable, "exhaustive_matcher",
                "--database_path", os.path.join(self.workspace_folder, "database.db")
            ]),
            ("Sparse Reconstruction", [
                self.colmap_executable, "mapper",
                "--database_path", os.path.join(self.workspace_folder, "database.db"),
                "--image_path", self.image_folder,
                "--output_path", sparse_folder,
                "--Mapper.ba_refine_focal_length", "1",
                "--Mapper.ba_refine_principal_point", "1"
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
                "--PatchMatchStereo.geom_consistency", "true",
                "--PatchMatchStereo.window_radius", "9",
                "--PatchMatchStereo.num_iterations", "5"
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

        max_workers = min(4, cpu_count() - 1)  # 控制并发线程数
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for description, command in commands:
                futures.append(executor.submit(self.run_command, command, description))
            for future in futures:
                future.result()

if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)
    progress_queue = Queue()
    reconstructor = ColmapReconstructor(config, progress_queue)
    reconstructor.run_colmap()
