import sys

sys.path.append("./")
from dataset_test import (
    AcousticDatasetFar,
    acoustic_collation_fn,
    AcousticDataset,
)
from acoustic.trainer_template import *
from acoustic.acousticnet import AcousticNet
from torch.nn.functional import mse_loss
import argparse
import os
import torch
from PIL import Image
import numpy as np
from torch import optim
import matplotlib.pyplot as plt
from time import time


def to_img(data1, data2, filename):
    data1 = data1.T / data1.max()
    data2 = data2.T / data2.max()
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(211)
    ax.matshow(data1.detach().cpu().numpy())
    ax = fig.add_subplot(212)
    ax.matshow(data2.detach().cpu().numpy())
    plt.savefig(filename)
    plt.clf()
    plt.close()


def forward_fun(items):
    bcoords, feats_in, feats_out, feats_out_norm, filename = items
    # t = time()
    ffat_map, ffat_norm = Config.net(bcoords, feats_in)
    # check_shape(bcoords, feats_in, freq_norm, feats_out, feats_out_norm,ffat_map, ffat_norm)
    # print('time cost:', time() - t)
    print(filename)
    with torch.set_grad_enabled(False):
        log_dir = f"./output/{Config.tag}"
        os.makedirs(log_dir, exist_ok=True)
        gt, predict = feats_out[0, 0], ffat_map[0, 0]
        to_img(gt, predict, f"{log_dir}/{Config.idx_in_epoch}.png")

    return ffat_map, ffat_norm, feats_out, feats_out_norm


def loss_fun(ffat_map, ffat_norm, feats_out, feats_out_norm):
    loss1 = mse_loss(ffat_map, feats_out)
    loss2 = mse_loss(ffat_norm, feats_out_norm)
    # print(ffat_norm, feats_out_norm)
    # print(loss1.item(), loss2.item())
    return {
        "ffatmap": loss1,
        "norm": loss2,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", type=str, default="default")
    parser.add_argument("--suffix", type=str, default="")
    parser.add_argument("--dataset", type=str, default="dataset/acousticData")
    parser.add_argument("--linear", dest="linear", action="store_true")
    parser.set_defaults(linear=False)
    parser.add_argument("--far", dest="far", action="store_true")
    parser.set_defaults(far=False)
    parser.add_argument("--wdir", type=str, default="./")
    args = parser.parse_args()
    Config.dataset_root_dir = args.dataset
    Config.tag = args.tag
    if args.far:
        Config.CustomDataset = AcousticDatasetFar
    else:
        Config.CustomDataset = AcousticDataset
    Config.custom_collation_fn = acoustic_collation_fn
    Config.forward_fun = forward_fun
    Config.loss_fun = loss_fun

    Config.net = AcousticNet(23, linear=args.linear)
    Config.optimizer = optim.Adam(Config.net.parameters(), lr=1e-3)
    Config.scheduler = optim.lr_scheduler.StepLR(
        Config.optimizer, step_size=8, gamma=0.8
    )
    Config.BATCH_SIZE = 1
    Config.dataset_worker_num = 8
    Config.weights_dir = args.wdir
    Config.load_weights = True
    Config.only_test = True
    start_train(2)
