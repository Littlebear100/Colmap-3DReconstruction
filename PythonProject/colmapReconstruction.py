import os
import subprocess
from logging_config import get_logger

logger = get_logger(__name__)

def run_command(command, step_name):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', shell=True)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        logger.info(f"{step_name} step completed successfully.")
    else:
        logger.error(f"{step_name} step failed with error: {stderr}")

def feature_extraction(database_path, image_path):
    command = f'colmap feature_extractor --database_path {database_path} --image_path {image_path} --ImageReader.camera_model PINHOLE --SiftExtraction.max_num_features 10000'
    run_command(command, "Feature Extraction")

def exhaustive_matching(database_path):
    command = f'colmap exhaustive_matcher --database_path {database_path}'
    run_command(command, "Exhaustive Matching")

def sparse_reconstruction(database_path, image_path, sparse_path):
    command = f'colmap mapper --database_path {database_path} --image_path {image_path} --output_path {sparse_path} --Mapper.num_threads 8'
    run_command(command, "Sparse Reconstruction")

def image_undistortion(image_path, sparse_path, undistorted_path):
    command = f'colmap image_undistorter --image_path {image_path} --input_path {sparse_path} --output_path {undistorted_path} --output_type COLMAP'
    run_command(command, "Image Undistortion")

def dense_reconstruction(undistorted_path, dense_path):
    command = f'colmap patch_match_stereo --workspace_path {undistorted_path} --workspace_format COLMAP --PatchMatchStereo.geom_consistency true'
    run_command(command, "Dense Reconstruction")

def dense_fusion(undistorted_path, dense_path):
    command = f'colmap stereo_fusion --workspace_path {undistorted_path} --workspace_format COLMAP --input_type geometric --output_path {dense_path}/fused.ply'
    run_command(command, "Dense Fusion")

def mesh_generation(dense_path, output_mesh_path):
    command = f'colmap poisson_mesher --input_path {dense_path}/fused.ply --output_path {output_mesh_path} --PoissonMeshing.trim 10'
    run_command(command, "Mesh Generation")

if __name__ == "__main__":
    database_path = "path/to/database.db"
    image_path = "path/to/images"
    sparse_path = "path/to/sparse"
    undistorted_path = "path/to/undistorted"
    dense_path = "path/to/dense"
    output_mesh_path = "path/to/output_mesh.ply"

    feature_extraction(database_path, image_path)
    exhaustive_matching(database_path)
    sparse_reconstruction(database_path, image_path, sparse_path)
    image_undistortion(image_path, sparse_path, undistorted_path)
    dense_reconstruction(undistorted_path, dense_path)
    dense_fusion(undistorted_path, dense_path)
    mesh_generation(dense_path, output_mesh_path)
