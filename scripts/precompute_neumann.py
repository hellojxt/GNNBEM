import sys

sys.path.append("./")
from src.mesh_loader import tetra_surf_from_triangle_mesh
from src.fem.solver import FEMmodel, Material, MatSet, LOBPCG_solver, SoundObj
from src.mesh_loader import tetra_from_mesh
from glob import glob
from tqdm import tqdm
import pymesh
import numpy as np
import logging, sys
import os
from scipy.spatial import KDTree
import torch

# logging.disable(sys.maxsize)

mesh_dir = sys.argv[1]
if mesh_dir[-1] == "/":
    mesh_dir = mesh_dir[:-1]
neumann_dir = mesh_dir + "_neumann"
mode_num = 20
if not os.path.exists(neumann_dir):
    os.makedirs(neumann_dir, exist_ok=True)

for mesh_file in tqdm(glob(mesh_dir + "/*.obj")):
    basename = os.path.basename(mesh_file)
    obj = SoundObj(mesh_file)
    obj.tetrahedralize()
    obj.modal_analysis(k=mode_num, material=Material(MatSet.Plastic))
    tree = KDTree(obj.tet_vertices)
    origin_vertices = obj.origin_mesh.vertices
    # map origin vertices to tetrahedralized vertices
    _, idx = tree.query(origin_vertices)
    eigenvectors = obj.eigenvectors.reshape(-1, 3, mode_num)
    eigenvectors = eigenvectors[idx, :, :]
    obj.origin_mesh.add_attribute("vertex_normal")
    vertex_normal = obj.origin_mesh.get_vertex_attribute("vertex_normal")
    neumann = (eigenvectors * vertex_normal.reshape(-1, 3, 1)).sum(axis=1)
    neumann = torch.from_numpy(neumann).float()
    torch.save(neumann, neumann_dir + "/" + basename.replace(".sf.obj", ".pt"))