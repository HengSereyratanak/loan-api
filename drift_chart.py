"""Chart the 14-day drift run with alert thresholds."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
from mlflow import MlflowClient

client = MlflowClient()
exp = client.get_experiment_by_name("loan-default-monitoring")
run = client.search_runs([exp.experiment_id], "attributes.run_name = 'daily-drift-check'",
                         order_by=["attributes.start_time DESC"])[0]
rid = run.info.run_id


def series(key):
    hist = sorted(client.get_metric_history(rid, key), key=lambda m: m.step)
    return [m.step for m in hist], [m.value for m in hist]


fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

for key, label, style in [("psi_monthly_income_usd", "Income PSI", "o-"),
                          ("psi_amount_usd", "Loan amount PSI", "s-"),
                          ("psi_late_payments", "Late payments PSI", "^-")]:
    ax1.plot(*series(key), style, label=label)
ax1.axhline(0.1, color="orange", ls="--", label="Watch: 0.1")
ax1.axhline(0.2, color="red", ls="--", label="Alert: 0.2")
ax1.axvline(7, color="orange", alpha=0.3, lw=8)
ax1.axvline(9, color="red", alpha=0.3, lw=8)
ax1.annotate("Watch fires\n(days 6-7 >= 0.1)", (7, 0.45), ha="center", fontsize=8)
ax1.annotate("Alert fires\n(days 8-9 > 0.2)", (9, 0.55), ha="center", fontsize=8)
ax1.set_ylabel("PSI vs training data")
ax1.set_title("Data drift: PSI per feature")
ax1.legend(fontsize=8, loc="upper left")

ax2.plot(*series("mean_predicted_default"), "o-", label="Mean predicted default")
ax2.plot(*series("actual_default_rate"), "x:", color="gray", label="Actual default rate (known months later)")
ax2.axhspan(0.346, 0.375, color="green", alpha=0.15, label="Days 1-5 range (normal)")
ax2.axhline(0.40, color="red", ls="--", label="Alert: 0.40")
ax2.axvline(10, color="red", alpha=0.3, lw=8)
ax2.annotate("Alert fires\n(days 9-10 > 0.40)", (8.2, 0.425), ha="center", fontsize=8)
ax2.set_ylabel("Probability")
ax2.set_xlabel("Day")
ax2.set_title("Prediction drift: mean predicted default")
ax2.set_xticks(range(1, 15))
ax2.legend(fontsize=8, loc="lower right")

fig.tight_layout()
out = sys.argv[1] if len(sys.argv) > 1 else "drift_chart.png"
fig.savefig(out, dpi=150)
with mlflow.start_run(run_id=rid):
    mlflow.log_figure(fig, "drift_chart.png")
print("saved", out, "and logged to run", rid)
