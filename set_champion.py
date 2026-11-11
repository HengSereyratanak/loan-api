"""Move the champion alias to a version: python set_champion.py 2"""
import sys

from mlflow import MlflowClient

NAME, version = "loan-default", sys.argv[1]
client = MlflowClient()
before = client.get_model_version_by_alias(NAME, "champion").version
client.set_registered_model_alias(NAME, "champion", version)
print(f"champion: version {before} -> version {client.get_model_version_by_alias(NAME, 'champion').version}")
