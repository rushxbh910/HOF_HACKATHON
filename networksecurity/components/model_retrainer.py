# model_retrainer.py

import os
import json
from llmprompt import load_latest_metrics, evaluate_and_optimize_model, clean_output
from networksecurity.entity.config_entity import ModelTrainerConfig
from networksecurity.entity.artifact_entity import DataTransformationArtifact
from networksecurity.components.model_trainer import ModelTrainer

# ── CONFIGURE YOUR PATHS HERE ───────────────────────────────────────────
JSON_PATH = r'C:\Projects\HOF_HACKATHON\exported_gpu_runs.json'
# These should match what you passed to your original ModelTrainer
TRAINED_MODEL_PATH   = r'C:\Projects\HOF_HACKATHON\artifacts\model.pkl'
TRANSFORMED_TRAIN_FP = r'C:\Projects\HOF_HACKATHON\artifacts\transformed_train.npz'
TRANSFORMED_TEST_FP  = r'C:\Projects\HOF_HACKATHON\artifacts\transformed_test.npz'

def main():
    # 1) load and evaluate
    metrics = load_latest_metrics(JSON_PATH)
    raw      = evaluate_and_optimize_model(metrics)
    clean    = clean_output(raw)
    print("🔎 Evaluation Output:\n", clean, "\n")

    # 2) parse status
    status = None
    for line in clean.splitlines():
        if line.upper().startswith("STATUS:"):
            status = line.split(":", 1)[1].strip().upper()
            break

    # 3) decide
    if status == "RETRAIN":
        print("🛠  Status=RETRAIN → kicking off a full retrain…")

        # Build the config & artifact objects exactly as your pipeline does
        trainer_config = ModelTrainerConfig(
            trained_model_file_path = TRAINED_MODEL_PATH
        )
        data_artifact = DataTransformationArtifact(
            transformed_train_file_path = TRANSFORMED_TRAIN_FP,
            transformed_test_file_path  = TRANSFORMED_TEST_FP,
            transformed_object_file_path = ""  # only needed if you log a preprocessing object
        )

        trainer = ModelTrainer(trainer_config, data_artifact)
        artifact = trainer.initiate_model_trainer()

        print("✅ Retraining complete.")
        print(f"  • Saved model to: {artifact.trained_model_file_path}")
        print(f"  • Train metrics:  {artifact.train_metric_artifact}")
        print(f"  • Test metrics:   {artifact.test_metric_artifact}")

    elif status == "OPTIMAL":
        print("✅ STATUS=OPTIMAL → no retraining needed.")
    else:
        print(f"⚠️ Unrecognized STATUS: {status!r}. No action taken.")


if __name__ == "__main__":
    main()
