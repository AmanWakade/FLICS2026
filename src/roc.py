import pandas as pd
import matplotlib.pyplot as plt

# Load coordinates
roc_central = pd.read_csv("results/centralised/roc_points.csv")
roc_fedavg = pd.read_csv("results/fedavg/roc_points.csv")
roc_fedprox = pd.read_csv("results/fedprox_mu0.01/roc_points.csv")
roc_scaffold = pd.read_csv("results/scaffold/roc_points.csv")

plt.figure(figsize=(6,5))

plt.plot(roc_central["fpr"], roc_central["tpr"], label="Centralised")
plt.plot(roc_fedavg["fpr"], roc_fedavg["tpr"], label="FedAvg")
plt.plot(roc_fedprox["fpr"], roc_fedprox["tpr"], label="FedProx")
plt.plot(roc_scaffold["fpr"], roc_scaffold["tpr"], label="SCAFFOLD")

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.legend()
plt.grid()

plt.savefig("roc_curve.png", dpi=300, bbox_inches="tight")