# Littlebear is coming!!!
import open3d as o3d

def visualize_ply(file_path):
    # 读取 PLY 文件
    mesh = o3d.io.read_triangle_mesh(file_path)
    # 计算法线
    mesh.compute_vertex_normals()
    # 可视化
    o3d.visualization.draw_geometries([mesh])

if __name__ == "__main__":
    ply_file_path = "D:/Littlebear/PythonProject/workspace/dense/meshed.ply"
    visualize_ply(ply_file_path)
