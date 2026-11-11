"""Register the two best runs under loan-default and give them roles."""
import mlflow
from mlflow import MlflowClient

NAME = "loan-default"
client = MlflowClient()
exp = client.get_experiment_by_name("loan-default")


def run_id(run_name):
    return client.search_runs([exp.experiment_id], f"attributes.run_name = '{run_name}'")[0].info.run_id


roles = [
    ("logreg-C=0.1-class_weight=balanced", "champion",
     "Balanced logistic regression: highest recall (0.865), AUC 0.923. Champion."),
    ("forest-max_depth=6-class_weight=balanced", "challenger",
     "Balanced random forest, depth 6: best AUC (0.927), higher precision (0.694). Challenger."),
]
for run_name, alias, description in roles:
    mv = mlflow.register_model(f"runs:/{run_id(run_name)}/model", NAME)
    client.update_model_version(NAME, mv.version, description=description)
    client.set_registered_model_alias(NAME, alias, mv.version)
    print(f"{NAME} v{mv.version} @{alias}: {run_name}")

client.update_registered_model(NAME, description="Probability that a loan applicant defaults.")
