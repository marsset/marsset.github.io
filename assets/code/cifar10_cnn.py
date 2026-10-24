"""
A small CNN on CIFAR-10 -- practice for the standard training workflow
Target: test accuracy > 60% (this configuration usually reaches about 75% in 10 epochs)

Usage:
    python cifar10_cnn.py            # normal training (downloads CIFAR-10, about 170 MB, on first run)
    python cifar10_cnn.py --fake     # run the pipeline on random fake data (no download; only checks the code)
"""
import argparse
import os
import sys
import time
import urllib.request

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
import torchvision
import torchvision.transforms as T
from torchvision.datasets.utils import check_integrity, extract_archive


# ---------------------------------------------------------------------------
# 0. Dataset download with a speed readout
#    torchvision's built-in download only shows a simple progress bar; this one shows
#    downloaded / total size, current speed, average speed and estimated time left
# ---------------------------------------------------------------------------
CIFAR10_URL = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
CIFAR10_MD5 = "c58f30108f718f92721af3b95e74349a"


def download_with_progress(url: str, dst: str, chunk_size: int = 64 * 1024, report_every: float = 0.5):
    """Stream url to dst, refreshing the speed every report_every seconds. Honours the HTTPS_PROXY environment variable."""
    tmp = dst + ".part"  # write to a temp file and rename once complete, so an interrupted download never leaves a half file that looks finished
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(tmp, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        t_start = t_last = time.time()
        bytes_last = 0

        def report(final=False):
            now = time.time()
            elapsed = max(now - t_start, 1e-6)
            inst = (done - bytes_last) / max(now - t_last, 1e-6)  # speed over the last refresh interval
            avg = done / elapsed                                   # average speed since the start
            msg = f"\r  {done / 1e6:7.1f}"
            if total:
                msg += f" / {total / 1e6:.1f} MB ({done / total:5.1%})"
            else:
                msg += " MB"
            if final:
                msg += f" | avg {avg / 1e6:.2f} MB/s | took {elapsed:.1f}s\n"
            else:
                msg += f" | now {inst / 1e6:6.2f} MB/s | avg {avg / 1e6:6.2f} MB/s"
                if total and avg > 0:
                    msg += f" | left {(total - done) / avg:5.0f}s"
            sys.stdout.write(msg.ljust(100) if not final else msg)
            sys.stdout.flush()

        while chunk := resp.read(chunk_size):
            f.write(chunk)
            done += len(chunk)
            if time.time() - t_last >= report_every:
                report()
                t_last, bytes_last = time.time(), done
        report(final=True)
    os.replace(tmp, dst)


def prepare_cifar10(root: str = "./data"):
    """Skip if the data is already there; otherwise download -> verify MD5 -> extract. CIFAR10(download=False) then reads the local files."""
    if os.path.isdir(os.path.join(root, "cifar-10-batches-py")):
        return
    os.makedirs(root, exist_ok=True)
    archive = os.path.join(root, "cifar-10-python.tar.gz")
    if not check_integrity(archive, CIFAR10_MD5):
        print(f"Downloading CIFAR-10: {CIFAR10_URL}")
        download_with_progress(CIFAR10_URL, archive)
        if not check_integrity(archive, CIFAR10_MD5):
            raise RuntimeError("MD5 check failed; the download may be incomplete. Delete the file and retry: " + archive)
    print("Extracting ...")
    extract_archive(archive, root)


# ---------------------------------------------------------------------------
# 1. Model: nn.Module
#    __init__ "declares" the layers that have parameters (registers the parameters)
#    forward  "describes" how data flows through those layers (builds the computation graph)
# ---------------------------------------------------------------------------
class SmallCNN(nn.Module):
    def __init__(self, num_classes: int = 10):
        super().__init__()  # required: sets up the parameter registry, hooks and other internal state
        # input 3x32x32
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)   # -> 32x32x32
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)  # -> 64x32x32 -> pool -> 64x16x16
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1) # -> 128x16x16 -> pool -> 128x8x8
        self.bn3 = nn.BatchNorm2d(128)
        self.dropout = nn.Dropout(0.3)
        self.fc1 = nn.Linear(128 * 8 * 8, 256)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.max_pool2d(F.relu(self.bn2(self.conv2(x))), 2)
        x = F.max_pool2d(F.relu(self.bn3(self.conv3(x))), 2)
        x = torch.flatten(x, 1)          # (B, 128, 8, 8) -> (B, 8192), keeping the batch dimension
        x = self.dropout(F.relu(self.fc1(x)))
        return self.fc2(x)               # return logits, no softmax (CrossEntropyLoss applies it)


# ---------------------------------------------------------------------------
# 2. A custom Dataset example (to show the interface; CIFAR-10 itself uses torchvision's)
#    Only two methods are needed: __len__ tells the DataLoader how many examples there are;
#    __getitem__ returns the example at a given index
# ---------------------------------------------------------------------------
class RandomImageDataset(Dataset):
    def __init__(self, n: int, transform=None):
        self.images = torch.rand(n, 3, 32, 32)
        self.labels = torch.randint(0, 10, (n,))
        self.transform = transform

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        img, label = self.images[idx], self.labels[idx]
        if self.transform:
            img = self.transform(img)
        return img, label  # the DataLoader stacks batch_size of these tuples with collate_fn into (B,3,32,32), (B,)


def get_loaders(batch_size: int, num_workers: int, fake: bool):
    mean, std = (0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)

    # augment the training set; validation/test sets are only normalized -- evaluation must be deterministic
    train_tf = T.Compose([
        T.RandomCrop(32, padding=4),
        T.RandomHorizontalFlip(),
        T.ToTensor(),
        T.Normalize(mean, std),
    ])
    test_tf = T.Compose([T.ToTensor(), T.Normalize(mean, std)])

    if fake:
        train_set = RandomImageDataset(512)
        test_set = RandomImageDataset(256)
    else:
        prepare_cifar10("./data")
        train_set = torchvision.datasets.CIFAR10("./data", train=True, download=False, transform=train_tf)
        test_set = torchvision.datasets.CIFAR10("./data", train=False, download=False, transform=test_tf)

    train_loader = DataLoader(
        train_set,
        batch_size=batch_size,
        shuffle=True,          # reshuffle the training set every epoch
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=True,        # drop the last incomplete batch so BN statistics stay stable
    )
    test_loader = DataLoader(
        test_set,
        batch_size=batch_size * 2,  # evaluation stores no gradients and uses less memory, so the batch can be larger
        shuffle=False,
        num_workers=num_workers,
    )
    return train_loader, test_loader


# ---------------------------------------------------------------------------
# 3. Training / evaluation
# ---------------------------------------------------------------------------
def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()  # enable Dropout; BN uses the current batch statistics and updates running mean/var
    total_loss, correct, n = 0.0, 0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()            # gradients accumulate by default, so clear them every step
        logits = model(x)                # forward pass, builds the computation graph
        loss = criterion(logits, y)
        loss.backward()                  # backward pass, computes .grad for every parameter
        optimizer.step()                 # update the parameters from .grad

        total_loss += loss.item() * y.size(0)   # .item() takes out a Python float so the computation graph is not kept alive
        correct += (logits.argmax(1) == y).sum().item()
        n += y.size(0)
    return total_loss / n, correct / n


@torch.no_grad()  # same as wrapping the whole function in `with torch.no_grad():` -- no graph, no stored activations
def evaluate(model, loader, criterion, device):
    model.eval()   # disable Dropout; BN switches to the running mean/var accumulated in training
    total_loss, correct, n = 0.0, 0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        total_loss += criterion(logits, y).item() * y.size(0)
        correct += (logits.argmax(1) == y).sum().item()
        n += y.size(0)
    return total_loss / n, correct / n


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--fake", action="store_true")
    args = p.parse_args()

    torch.manual_seed(0)
    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"device: {device}")

    train_loader, test_loader = get_loaders(args.batch_size, args.num_workers, args.fake)

    model = SmallCNN().to(device)  # call .to(device) before building the optimizer, so the optimizer gets the on-device parameters
    print(f"params: {sum(p.numel() for p in model.parameters()):,}")

    criterion = nn.CrossEntropyLoss()  # = log_softmax + NLLLoss; takes logits and integer labels
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=5e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_acc = 0.0
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        tr_loss, tr_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        te_loss, te_acc = evaluate(model, test_loader, criterion, device)
        scheduler.step()  # adjust the learning rate per epoch, after optimizer.step()

        if te_acc > best_acc:
            best_acc = te_acc
            torch.save(model.state_dict(), "best_cnn.pt")  # save the state_dict, not the whole object

        print(f"epoch {epoch:2d} | train loss {tr_loss:.3f} acc {tr_acc:.1%} | "
              f"test loss {te_loss:.3f} acc {te_acc:.1%} | {time.time() - t0:.1f}s")

    print(f"best test acc: {best_acc:.1%}")


if __name__ == "__main__":
    main()
