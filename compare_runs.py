"""Experiment table and recall-precision chart for the loan-default runs."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow

out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
runs = mlflow.search_runs(experiment_names=["loan-default"], order_by=["metrics.recall DESC"])
table = runs[["tags.mlflow.runName", "params.model", "metrics.auc", "metrics.recall",
              "metrics.precision", "run_id"]].copy()
table.columns = ["run", "model", "auc", "recall", "precision", "run_id"]
table.to_csv(f"{out_dir}/experiment_table.csv", index=False)
print(table.round(3).to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 6))
for _, r in table.iterrows():
    marker = "o" if r.model == "logreg" else "s"
    size = 400 * (r.auc - 0.90) / 0.03 + 40
    ax.scatter(r.precision, r.recall, s=size, marker=marker, alpha=0.7,
               color="tab:blue" if r.model == "logreg" else "tab:green")
    offset = (8, -22) if r.run.startswith("logreg-C=1.0") else (8, 2)
    ax.annotate(f"{r.run}\nAUC {r.auc:.3f}", (r.precision, r.recall),
                textcoords="offset points", xytext=offset, fontsize=7)
ax.scatter([], [], marker="o", color="tab:blue", label="Logistic regression")
ax.scatter([], [], marker="s", color="tab:green", label="Random forest")
ax.set_xlabel("Precision (share of flagged loans that default)")
ax.set_ylabel("Recall (share of defaulters caught)")
ax.set_title("loan-default runs: recall vs precision (marker size = AUC)")
ax.set_xlim(0.58, 0.95)
ax.legend(loc="lower left")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(f"{out_dir}/comparison_chart.png", dpi=150)
