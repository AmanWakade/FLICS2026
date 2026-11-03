from dataclasses import dataclass
from pathlib import Path

@dataclass
class CFG:
    data_path: Path = Path("data/kidney_fl_5centers_dataset.csv")
    out_root: Path = Path("runs")

    seed: int = 42
    test_size: float = 0.20
    val_size: float = 0.10  # of remaining train part

    rounds: int = 20
    local_epochs: int = 5
    batch_size: int = 1024
    lr: float = 1e-3
    weight_decay: float = 1e-4

    fedprox_mu: float = 0.01  # used only in FedProx