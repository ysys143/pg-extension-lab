from __future__ import annotations

import struct
from pathlib import Path

MatrixF = list[list[float]]
MatrixI = list[list[int]]


def write_fbin(path: str | Path, arr: MatrixF) -> None:
    rows = len(arr)
    dims = len(arr[0]) if rows else 0
    with Path(path).open("wb") as f:
        f.write(struct.pack("<II", rows, dims))
        for row in arr:
            f.write(struct.pack("<" + "f" * dims, *row))


def read_fbin(path: str | Path) -> MatrixF:
    with Path(path).open("rb") as f:
        rows, dims = struct.unpack("<II", f.read(8))
        data = []
        for _ in range(rows):
            data.append(list(struct.unpack("<" + "f" * dims, f.read(4 * dims))))
    return data


def write_ibin(path: str | Path, arr: MatrixI) -> None:
    rows = len(arr)
    cols = len(arr[0]) if rows else 0
    with Path(path).open("wb") as f:
        f.write(struct.pack("<II", rows, cols))
        for row in arr:
            f.write(struct.pack("<" + "i" * cols, *row))


def read_ibin(path: str | Path) -> MatrixI:
    with Path(path).open("rb") as f:
        rows, cols = struct.unpack("<II", f.read(8))
        data = []
        for _ in range(rows):
            data.append(list(struct.unpack("<" + "i" * cols, f.read(4 * cols))))
    return data


def exact_l2(data: MatrixF, queries: MatrixF, k: int) -> MatrixI:
    out = []
    for q in queries:
        scored = []
        for idx, row in enumerate(data):
            dist = sum((a - b) ** 2 for a, b in zip(row, q))
            scored.append((dist, idx))
        scored.sort()
        out.append([idx for _, idx in scored[:k]])
    return out


def recall_at_k(gt: MatrixI, results: MatrixI, k: int) -> float:
    scores = []
    for expected, actual in zip(gt, results):
        scores.append(len(set(expected[:k]) & set(actual[:k])) / k)
    return sum(scores) / len(scores) if scores else 0.0
