import sys

sys.path.append("./")
import torch
from src.dataset import MeshDataset, TriMesh
import src.network as network
from torch_geometric.loader import DataLoader
import argparse
import commentjson as json
import tinycudann as tcnn
from tqdm import tqdm
from src.assemble import (
    assemble_single_boundary_matrix,
    assemble_double_boundary_matrix,
)

with open("config/config.json") as f:
    config = json.load(f)

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=str, default="dataset/ABC_Dataset/surf_mesh")
parser.add_argument("--network", type=str, default="PointNet2")
parser.add_argument("--preprocess", action="store_true")
parser.add_argument("--hidden_dim", type=int, default=64)
parser.add_argument("--batch_size", type=int, default=8)
parser.add_argument("--epochs", type=int, default=100)
parser.add_argument("--scale_factor", type=float, default=0.0001)

args = parser.parse_args()
scale_factor = args.scale_factor
train_dataset = MeshDataset(args.dataset, "train")
test_dataset = MeshDataset(args.dataset, "val")
if args.preprocess:
    train_dataset.pre_process_meshes()
    test_dataset.pre_process_meshes()
train_dataset.load_pre_processed_mesh()
test_dataset.load_pre_processed_mesh()
train_loader = DataLoader(
    train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=8
)
test_loader = DataLoader(
    test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=8
)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


graph_net = getattr(network, args.network)(
    train_dataset[0].x.shape[1], args.hidden_dim
).to(device)
freq_encoder = tcnn.Encoding(1, config["encoding"])
decoder = tcnn.Network(
    freq_encoder.n_output_dims + args.hidden_dim, 1, config["network"]
)

parameters = (
    list(graph_net.parameters())
    + list(freq_encoder.parameters())
    + list(decoder.parameters())
)

optimizer = torch.optim.Adam(parameters, lr=0.001)


def epoch_step(train=True):
    if train:
        graph_net.train()
        data_loader = train_loader
    else:
        graph_net.eval()
        data_loader = test_loader

    losses = []
    for i, data in enumerate(tqdm(data_loader)):
        data = data.to(device)
        optimizer.zero_grad()
        x = graph_net(data)
        verts_off = data.vertices_offset
        verts_off_bound = torch.cumsum(verts_off, dim=0)
        loss = 0
        graph_num = data.batch[-1] + 1
        for graph_idx in range(graph_num):
            vertices = (
                data.vertices[
                    verts_off_bound[graph_idx]
                    - verts_off[graph_idx] : verts_off_bound[graph_idx]
                ]
                .contiguous()
                .type(torch.float32)
            )
            mask = data.batch == graph_idx
            triangles = data.triangles[mask].contiguous().type(torch.int32)
            # TriMesh(vertices, triangles).save_obj(f"test_{graph_idx}.obj")
            freq = torch.rand([1, 1], device="cuda")
            wave_number = 5  # + (freq * 40).item()
            single_matrix = assemble_single_boundary_matrix(
                vertices, triangles, wave_number
            )
            b = single_matrix @ data.neumann[mask] / scale_factor
            freq_encode = freq_encoder(freq)
            freq_encode = freq_encode.repeat(triangles.shape[0], 1)
            feats = torch.cat([freq_encode, x[mask]], axis=1)
            predict = decoder(feats).float()
            # print("b: ", torch.abs(b).mean())
            # print("predict: ", torch.abs(predict).mean())
            if i == 100 and graph_idx == 0:
                torch.save(b, "b.pt")
                torch.save(data.neumann[mask], "neumann.pt")
                torch.save(predict, "predict.pt")
            #     return
            residual = predict - b
            loss_currect = torch.abs(residual).mean()
            loss = loss + loss_currect
            # print(loss.item() / torch.abs(b).mean())
        loss = loss / graph_num
        losses.append(loss.item())
        # print(loss.item())
        if train:
            loss.backward()
            optimizer.step()
    print(f"{'train' if train else 'test'} loss: {sum(losses) / len(losses)}")
    return sum(losses) / len(losses)


def train():
    return epoch_step(True)


@torch.no_grad()
def test():
    return epoch_step(False)


for epoch in range(args.epochs):
    train()
    # if epoch % 10 == 0:
    #     test()