import os
import sys
import time
import subprocess

import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
from mlflow.tracking import MlflowClient

import GPUtil
from pymongo import MongoClient
from bson.json_util import dumps

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact
from networksecurity.entity.config_entity import ModelTrainerConfig
from networksecurity.utils.main_utils.utils import (
    load_numpy_array_data,
    save_object,
    load_object,
    evaluate_models
)
from networksecurity.utils.ml_utils.metric.classification_metric import get_classification_score
from networksecurity.utils.ml_utils.model.estimator import NetworkModel

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    AdaBoostClassifier,
    GradientBoostingClassifier
)

# ─── MLflow setup ─────────────────────────────────────────────
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("NetworkSecurity_Models")

# Path to dump full MongoDB collection to JSON
MONGO_JSON_EXPORT_PATH = os.getenv("MONGO_JSON_EXPORT_PATH", "./exported_gpu_runs.json")


class ModelTrainer:
    def __init__(
        self,
        model_trainer_config: ModelTrainerConfig,
        data_transformation_artifact: DataTransformationArtifact
    ):
        try:
            self.model_trainer_config         = model_trainer_config
            self.data_transformation_artifact = data_transformation_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # ── existing helpers ─────────────────────────────────────────
    def _log_metrics(self, stage: str, metrics_obj) -> None:
        if hasattr(metrics_obj, "_asdict"):
            items = metrics_obj._asdict().items()
        elif hasattr(metrics_obj, "metrics"):
            items = metrics_obj.metrics.items()
        else:
            items = vars(metrics_obj).items()

        for name, val in items:
            try:
                mlflow.log_metric(f"{stage}_{name}", float(val))
            except Exception:
                logging.warning(f"Could not log metric {stage}_{name}: {val}")

    @staticmethod
    def get_gpu_power_draw():
        try:
            result = subprocess.check_output(
                ['nvidia-smi', '--query-gpu=power.draw', '--format=csv,noheader,nounits']
            )
            return [float(p) for p in result.decode('utf-8').strip().split('\n')]
        except Exception as e:
            logging.warning(f"Could not fetch GPU power draw: {e}")
            return []

    def _log_gpu_metrics(self, stage: str) -> None:
        try:
            for i, gpu in enumerate(GPUtil.getGPUs()):
                mlflow.log_metric(f"{stage}_gpu_{i}_util",   gpu.load)
                mlflow.log_metric(f"{stage}_gpu_{i}_memutil", gpu.memoryUtil)
                mlflow.log_metric(f"{stage}_gpu_{i}_memused", gpu.memoryUsed)
                mlflow.log_metric(f"{stage}_gpu_{i}_memfree", gpu.memoryFree)
        except Exception as e:
            logging.warning(f"Could not log GPU metrics at {stage}: {e}")

    # ── export a completed MLflow run into MongoDB Atlas ───────────
    def _export_run_to_mongo(self, run_id: str):
        """Fetch one run from MLflow and upsert it into MongoDB Atlas, then dump collection to JSON."""
        # read env‑var for URL
        mongo_url = "mongodb+srv://rb5726:Rpb7675910!@cluster0.sb9vbdu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        if not mongo_url:
            raise NetworkSecurityException("Missing MONGO_DB_URL environment variable", sys)

        # hard‑coded database & collection
        db_name   = "RUSHXBH910"
        coll_name = "GPU_Carbon_Footprints"

        # connect to Atlas
        client     = MongoClient(mongo_url)
        collection = client[db_name][coll_name]

        # fetch run from MLflow
        mlc = MlflowClient()
        run = mlc.get_run(run_id)
        data, info = run.data, run.info

        # build document
        doc = {
            "run_id":       run_id,
            "start_time":   info.start_time,
            "end_time":     info.end_time,
            "status":       info.status,
            "artifact_uri": info.artifact_uri,
            "params":       data.params,
            "metrics":      data.metrics,
            "tags":         data.tags,
        }

        # upsert by run_id
        collection.replace_one({"run_id": run_id}, doc, upsert=True)
        logging.info(f"Exported run {run_id} → MongoDB {db_name}.{coll_name}")

        # dump the entire collection to JSON
        try:
            docs = list(collection.find())
            os.makedirs(os.path.dirname(MONGO_JSON_EXPORT_PATH) or '.', exist_ok=True)
            with open(MONGO_JSON_EXPORT_PATH, "w", encoding="utf-8") as f:
                f.write(dumps(docs, indent=2))
            logging.info(f"Dumped MongoDB collection {db_name}.{coll_name} to {MONGO_JSON_EXPORT_PATH}")
        except Exception as e:
            logging.warning(f"Could not dump MongoDB collection to JSON: {e}")

    # ── train + log + export ─────────────────────────────────────
    def train_model(self, x_train, y_train, x_test, y_test) -> ModelTrainerArtifact:
        models = {
            "Random Forest":       RandomForestClassifier(verbose=1),
            "Decision Tree":       DecisionTreeClassifier(),
            "Gradient Boosting":   GradientBoostingClassifier(verbose=1),
            "Logistic Regression": LogisticRegression(verbose=1),
            "AdaBoost":            AdaBoostClassifier()
        }

        params = {
            "Decision Tree":      {'criterion': ['gini','entropy','log_loss']},
            "Random Forest":      {'n_estimators': [8,16,32,128,256]},
            "Gradient Boosting":  {
                'learning_rate': [0.1,0.01,0.05,0.001],
                'subsample':     [0.6,0.7,0.75,0.85,0.9],
                'n_estimators':  [8,16,32,64,128,256]
            },
            "Logistic Regression": {},
            "AdaBoost":            {'learning_rate': [0.1,0.01,0.001],
                                     'n_estimators':  [8,16,32,64,128,256]}
        }

        report    = evaluate_models(
            X_train=x_train, y_train=y_train,
            X_test=x_test,   y_test=y_test,
            models=models,   params=params
        )
        best_name  = max(report, key=report.get)
        best_model = models[best_name]

        # infer signature/example
        try:
            signature     = infer_signature(x_train, best_model.predict(x_train))
            input_example = x_train[:5]
        except:
            signature, input_example = None, None

        # START MLflow run
        with mlflow.start_run(run_name=best_name) as run:
            mlflow.log_param("model_name", best_name)
            for p, v in best_model.get_params().items():
                mlflow.log_param(p, v)

            self._log_gpu_metrics("pre_train")

            t0     = time.time()
            before = self.get_gpu_power_draw()

            best_model.fit(x_train, y_train)

            t1     = time.time()
            self._log_gpu_metrics("post_train")
            after  = self.get_gpu_power_draw()

            avg_watts   = sum(before + after) / (len(before + after) or 1)
            duration_hr = (t1 - t0) / 3600
            energy_kwh  = avg_watts/1000 * duration_hr
            carbon      = energy_kwh * 0.475

            mlflow.log_metric("gpu_energy_kwh", energy_kwh)
            mlflow.log_metric("gpu_carbon_kg", carbon)

            ytr_pred = best_model.predict(x_train)
            yte_pred = best_model.predict(x_test)
            train_m  = get_classification_score(y_train, ytr_pred)
            test_m   = get_classification_score(y_test,  yte_pred)

            self._log_metrics("train", train_m)
            self._log_metrics("test",  test_m)

            preprocessor = load_object(
                self.data_transformation_artifact.transformed_object_file_path
            )
            pipeline = NetworkModel(preprocessor=preprocessor, model=best_model)

            mlflow.sklearn.log_model(
                sk_model=pipeline.model,
                artifact_path="sk_model",
                registered_model_name="NetworkSecurityModel",
                signature=signature,
                input_example=input_example
            )

        # AFTER run completes, export to MongoDB + dump JSON
        run_id = run.info.run_id
        self._export_run_to_mongo(run_id)

        # save locally & return
        model_dir = os.path.dirname(self.model_trainer_config.trained_model_file_path)
        os.makedirs(model_dir, exist_ok=True)
        save_object(self.model_trainer_config.trained_model_file_path, obj=pipeline)
        logging.info(f"Model saved to {self.model_trainer_config.trained_model_file_path}")

        return ModelTrainerArtifact(
            trained_model_file_path=self.model_trainer_config.trained_model_file_path,
            train_metric_artifact=train_m,
            test_metric_artifact=test_m
        )

    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        try:
            train_arr = load_numpy_array_data(
                self.data_transformation_artifact.transformed_train_file_path
            )
            test_arr  = load_numpy_array_data(
                self.data_transformation_artifact.transformed_test_file_path
            )

            x_train, y_train = train_arr[:, :-1], train_arr[:, -1]
            x_test,  y_test  = test_arr[:, :-1],  test_arr[:, -1]

            return self.train_model(x_train, y_train, x_test, y_test)
        except Exception as e:
            raise NetworkSecurityException(e, sys)