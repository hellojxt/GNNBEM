from .resnet import ResNetBase, BasicBlock
import torch
import torch.nn as nn
import MinkowskiEngine as ME
import MinkowskiEngine.MinkowskiFunctional as F


class Generator(nn.Module):
    def __init__(self, in_channel, linear=False):
        super().__init__()
        in_channel = in_channel // (16 * 8)
        self.in_channel = in_channel
        cs = [in_channel, in_channel // 2, 1]
        self.layer1 = nn.Sequential(
            nn.ConvTranspose2d(cs[0], cs[1], 4, 2, 1), nn.BatchNorm2d(cs[1])
        )
        if linear:
            self.relu = nn.Identity()
            self.tanh = nn.Identity()
        else:
            self.relu = nn.ReLU()
            self.tanh = nn.Tanh()

        self.layer2 = nn.ConvTranspose2d(cs[1], cs[2], 4, 2, 1)

    def forward(self, input):
        x = self.layer1(input.reshape(-1, self.in_channel, 16, 8))
        x = self.relu(x)
        x = self.layer2(x)
        return x


class ResNet34(ResNetBase):
    BLOCK = BasicBlock
    LAYERS = (2, 2, 2, 2)
    INIT_DIM = 32
    PLANES = (64, 128, 256, 512)


class ResNet14(ResNetBase):
    BLOCK = BasicBlock
    LAYERS = (1, 1, 1, 1)
    INIT_DIM = 8
    PLANES = (8, 16, 32, 64)


class Encoder(nn.Module):
    RESNET = ResNet34

    def __init__(self, in_channel, linear):
        super().__init__()
        self.mid_channel = 1024
        self.resnet = ResNet34(in_channel, self.mid_channel, linear=linear)

    def forward(self, coords, feats):
        sparse_input = ME.SparseTensor(feats, coords)
        out = self.resnet(sparse_input).F
        return out


class EncoderSmall(Encoder):
    RESNET = ResNet14


class AcousticNet(nn.Module):
    def __init__(self, in_channel, linear=False):
        super().__init__()
        self.encoder1 = Encoder(in_channel, linear=linear)
        self.encoder2 = EncoderSmall(in_channel, linear=linear)
        self.decoder1 = Generator(self.encoder1.mid_channel, linear=linear)
        self.decoder2 = nn.Sequential(
            nn.Linear(self.encoder2.mid_channel, self.encoder2.mid_channel),
            nn.ReLU(),
            nn.Linear(self.encoder2.mid_channel, 1),
        )

    def forward(self, coords, feats):
        mid1 = self.encoder1(coords, feats)
        mid2 = self.encoder2(coords, feats)
        out1 = self.decoder1(mid1)
        out2 = self.decoder2(mid2)
        return out1, out2
