import sys

sys.path.append("./")

import torch
from src.cuda_imp import FDTDSimulator, get_bound_info
from src.visualize import CombinedFig
from src.modalsound.model import MeshObj
from src.timer import Timer
import os
import time
import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm

res = 256
freq = 8000
obj = MeshObj("dataset/bunny.obj", 0.2)
vertices = torch.from_numpy(obj.vertices).cuda().float()
triangles = torch.from_numpy(obj.triangles).cuda().int()
min_bound, max_bound, bound_size = get_bound_info(obj.vertices, padding=2)

listen_pos = torch.tensor([0.0, 0.0, 0.1], device="cuda", dtype=torch.float32)
fdtd = FDTDSimulator(min_bound, max_bound, bound_size, res, listen_pos)

ts = torch.arange(200, device="cuda", dtype=torch.float32) * fdtd.dt
triangles_neumann = (
    torch.sin(2 * np.pi * freq * ts)
    .cuda()
    .unsqueeze(1)
    .repeat(1, triangles.shape[0])
    .T.float()
)
fdtd.update(vertices, triangles, triangles_neumann)
points = fdtd.grid_points()[:, :, res // 2]
values = fdtd.grids[0, :, :, res // 2]
print(values.min(), values.max())
print(points.shape, values.shape)
cmax = values.max().item() * 0.5
cmin = values.min().item() * 0.5
CombinedFig().add_points(points, values, cmax=cmax, cmin=cmin).show()
