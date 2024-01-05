import sys

sys.path.append("./")

from src.modalsound.model import SNR, complex_ssim
import numpy as np

import matplotlib.pyplot as plt
from glob import glob
import configparser

root_dir = sys.argv[1]

obj_dir = glob(f"{root_dir}/*")

for obj_path in obj_dir:
    bem_data = np.load(obj_path + "/bem.npz")
    NeuralSound_data = np.load(obj_path + "/NeuralSound.npz")
    ours_data = np.load(obj_path + "/ours.npz")
    points = bem_data["points"]

    bem_ffat = bem_data["ffat_map"].reshape(-1, 64, 32)
    r = (points**2).sum(-1) ** 0.5
    NeuralSound_ffat = NeuralSound_data["ffat_map"].reshape(*bem_ffat.shape) / r[0]
    ours_ffat = ours_data["ffat_map"].reshape(*bem_ffat.shape)

    bem_time = bem_data["cost_time"]
    ours_time = ours_data["cost_time"]
    NeuralSound_time = (
        NeuralSound_data["cost_time"] + np.load(obj_path + "/voxel.npz")["cost_time"]
    )
    mode_num = len(bem_ffat)

    for i in range(mode_num):
        print(
            f"{obj_path.split('/')[-1]}_{i}: bem SNR: {SNR(bem_ffat[i], bem_ffat[i])},  SSIM: {complex_ssim(bem_ffat[i], bem_ffat[i])}, time: {bem_time}"
        )
        print(
            f"{obj_path.split('/')[-1]}_{i}: ours SNR: {SNR(bem_ffat[i], ours_ffat[i])}, SSIM: {complex_ssim(bem_ffat[i], ours_ffat[i])}, time: {ours_time}"
        )
        print(
            f"{obj_path.split('/')[-1]}_{i}: NeuralSound SNR: {SNR(bem_ffat[i], NeuralSound_ffat[i])}, SSIM: {complex_ssim(bem_ffat[i], NeuralSound_ffat[i])}, time: {NeuralSound_time}"
        )

    for i in range(mode_num):
        plt.subplot(1, 3, 1)
        plt.imshow(np.abs(bem_ffat[i]), label=f"bem")
        plt.title(f"{obj_path.split('/')[-1]}_{i}")
        plt.colorbar()
        plt.subplot(1, 3, 2)
        plt.imshow(NeuralSound_ffat[i], label="NeuralSound")
        plt.colorbar()
        plt.subplot(1, 3, 3)
        plt.imshow(np.abs(ours_ffat[i]), label="ours")
        plt.colorbar()
        plt.show()
        plt.close()
