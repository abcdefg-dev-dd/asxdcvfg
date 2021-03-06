import torch
import numpy as np
import pickle
from utils.process import *


class StandardScaler():
    """
    Standard the input
    """
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std
    def transform(self, data):
        return (data - self.mean.to(data.device)) / self.std.to(data.device)
    def inverse_transform(self, data, dim):
        return (data * self.std[...,dim].item()) + self.mean[...,dim].item()

class DataLoader(object):
    def __init__(self, xs, ys, batch_size, pad_with_last_sample=True):
        """
        :param xs:
        :param ys:
        :param batch_size:
        :param pad_with_last_sample: pad with the last sample to make number of samples divisible to batch_size.
        """
        self.batch_size = batch_size
        self.current_ind = 0
        if pad_with_last_sample:
            num_padding = (batch_size - (len(xs) % batch_size)) % batch_size
            x_padding = np.repeat(xs[-1:], num_padding, axis=0)
            y_padding = np.repeat(ys[-1:], num_padding, axis=0)
            xs = np.concatenate([xs, x_padding], axis=0)
            ys = np.concatenate([ys, y_padding], axis=0)

        self.size = len(xs)
        self.num_batch = int(self.size // self.batch_size)
        self.xs = xs
        self.ys = ys

    def shuffle(self):
        permutation = np.random.permutation(self.size)
        xs, ys = self.xs[permutation], self.ys[permutation]
        self.xs = xs
        self.ys = ys

    def get_iterator(self):
        self.current_ind = 0
        def _wrapper():
            while self.current_ind < self.num_batch:
                start_ind = self.batch_size * self.current_ind
                end_ind = min(self.size, self.batch_size * (self.current_ind + 1))
                x_i = self.xs[start_ind: end_ind, ...]
                y_i = self.ys[start_ind: end_ind, ...]
                yield (x_i, y_i)
                self.current_ind += 1
        return _wrapper()

class pemsD:
    def __init__(self, num_nodes, path, adjpath, idpath=None):
        self.num_nodes = num_nodes
        self.path = path
        self.adjpath = adjpath
        self.idpath = idpath

    def load(self):
        data = np.load(self.path)
        return data['data']

    def load_graph(self):
        node2id = dict()
        if self.idpath is not None:
            file = open(self.idpath)
            id = 0
            for li in file:
                li = li.strip()
                node2id[int(li)] = id
                id += 1

        file = open(self.adjpath)
        nodes = [i for i in range(self.num_nodes)]
        dist = [0 for i in range(self.num_nodes)]

        srclist = []
        tgtlist = []
        dislist = []
        adj = torch.zeros(self.num_nodes,self.num_nodes)

        for li in file:
            li = li.strip().split(',')
            try:
                li = [float(t) for t in li]
            except Exception:
                continue
            if self.idpath is not None:
                src = int(node2id[li[0]])
                tgt = int(node2id[li[1]])
            else:
                src = int(li[0])
                tgt = int(li[1])
            adj[src,tgt] = li[2]
            srclist.append(src)
            tgtlist.append(tgt)
            dislist.append(li[2])


        return adj, nodes+srclist+tgtlist, nodes+tgtlist+srclist, dist+dislist+[t+1e9 for t in dislist]


    def load_graph1(self):
        node2id = dict()
        if self.idpath is not None:
            file = open(self.idpath)
            id = 0
            for li in file:
                li = li.strip()
                node2id[int(li)] = id
                id += 1

        file = open(self.adjpath)
        nodes = [i for i in range(self.num_nodes)]
        dist = [0 for i in range(self.num_nodes)]


        adj = torch.zeros(self.num_nodes,self.num_nodes)

        for li in file:
            li = li.strip().split(',')
            try:
                li = [float(t) for t in li]
            except Exception:
                continue
            if self.idpath is not None:
                src = int(node2id[li[0]])
                tgt = int(node2id[li[1]])
            else:
                src = int(li[0])
                tgt = int(li[1])
            if src!=tgt:
                adj[src,tgt] = li[2]
                #adj[tgt,src] = li[2]

        srclist = []
        tgtlist = []
        dislist = []
        # adj = torch.matmul(adj,adj)
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if adj[i, j] > 1e-9 and i!=j:
                    srclist.append(i)
                    tgtlist.append(j)
                    dislist.append(adj[i, j].item())

        # for i in range(self.num_nodes):
        #     for j in range(self.num_nodes):
        #         if adj[i, j] > 1e-9 and i!=j:
        #             srclist.append(j)
        #             tgtlist.append(i)
        #             dislist.append(1e9+adj[i, j].item())
        # print('# edges', len(srclist))
        return adj, nodes+srclist, nodes+tgtlist, dist+dislist

    def prcoess(self, savepath):
        data = {}
        x = self.load()
        x = x.transpose()
        x = torch.Tensor(x)
        length = x.shape[2]
        trainx = []
        trainy = []
        valx = []
        valy = []
        testx = []
        testy = []

        x = x.unsqueeze(dim=0)

        for i in range(int(length*0.6)-24):
            tx = x[...,i:i+12]
            ty = x[...,i+12:i+24]
            trainx.append(tx)
            trainy.append(ty)
        for i in range(int(length*0.6),int(length*0.8)-24):
            tx = x[...,i:i+12]
            ty = x[...,i+12:i+24]
            valx.append(tx)
            valy.append(ty)
        for i in range(int(length*0.8), length-24):
            tx = x[...,i:i+12]
            ty = x[...,i+12:i+24]
            testx.append(tx)
            testy.append(ty)

        trainx = torch.cat(trainx,dim=0)
        trainx = trainx.transpose(3,1)
        trainy = torch.cat(trainy,dim=0)
        trainy = trainy.transpose(3,1)

        valx = torch.cat(valx,dim=0)
        valx = valx.transpose(3,1)
        valy = torch.cat(valy,dim=0)
        valy = valy.transpose(3,1)

        testx = torch.cat(testx,dim=0)
        testx = testx.transpose(3,1)
        testy = torch.cat(testy,dim=0)
        testy = testy.transpose(3,1)

        data['x_train'] = trainx
        data['y_train'] = trainy
        data['x_val'] = valx
        data['y_val'] = valy
        data['x_test'] = testx
        data['y_test'] = testy

        data['adj'], srclist, tgtlist, distlist = self.load_graph1()
        file = open(savepath, "wb")
        pickle.dump(data, file)


def load_data(batch_size, path, device=None, normalize=True):
    file = open(path, "rb")
    data = pickle.load(file)
    mean = data['x_train'].mean(axis=(0, 1, 2), keepdims=True)
    std = data['x_train'].std(axis=(0, 1, 2), keepdims=True)
    if normalize:
        scaler = StandardScaler(mean=mean, std=std)
        for category in ['train', 'val', 'test']:
            data['x_' + category] = scaler.transform(data['x_' + category])
            data['y_' + category] = scaler.transform(data['y_' + category])
    else:
        scaler = StandardScaler(mean=0, std=1)

    data['train_loader'] = DataLoader(data['x_train'], data['y_train'], batch_size)
    data['val_loader'] = DataLoader(data['x_val'], data['y_val'], batch_size)
    data['test_loader'] = DataLoader(data['x_test'], data['y_test'], batch_size)
    data['scaler'] = scaler
    return data

