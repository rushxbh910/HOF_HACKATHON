from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.components.data_validation import DataValidation
from networksecurity.components.data_transformation import DataTransformation
from networksecurity.components.model_trainer import ModelTrainer
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.config_entity import (
    DataIngestionConfig, 
    DataValidationConfig,
    DataTransformationConfig, 
    ModelTrainerConfig,
    TrainingPipelineConfig
)
import subprocess
import sys
import os

if __name__ == '__main__':
    try:
        trainingpipelineconfig = TrainingPipelineConfig()

        logging.info("Initiate the data ingestion")
        dataingestionconfig = DataIngestionConfig(trainingpipelineconfig)
        data_ingestion = DataIngestion(dataingestionconfig)
        dataingestionartifact = data_ingestion.initiate_data_ingestion()
        logging.info("Data Ingestion Completed!")
        print(dataingestionartifact)

        logging.info("Initiate data validation")
        data_validation_config = DataValidationConfig(trainingpipelineconfig)
        data_validation = DataValidation(dataingestionartifact, data_validation_config)
        data_validation_artifact = data_validation.initiate_data_validation()
        logging.info("Data Validation Completed!")
        print(data_validation_artifact)

        logging.info("Initiate data transformation")
        data_transformation_config = DataTransformationConfig(trainingpipelineconfig)
        data_transformation = DataTransformation(data_validation_artifact, data_transformation_config)
        data_transformation_artifact = data_transformation.initiate_data_transformation()
        logging.info("Data Transformation Completed!")
        print(data_transformation_artifact)

        logging.info("Initiate model training")
        model_trainer_config = ModelTrainerConfig(trainingpipelineconfig)
        model_trainer = ModelTrainer(model_trainer_config, data_transformation_artifact)
        model_trainer_artifact = model_trainer.initiate_model_trainer()
        logging.info("Model Training Completed!")
        print(model_trainer_artifact)

        # ---- LLM Evaluation ----
        logging.info("Running LLM evaluation on latest model metrics...")
        llm_script_path = os.path.join("aws_lambdafunction", "llmprompt.py")
        if os.path.exists(llm_script_path):
            subprocess.run([sys.executable, llm_script_path], check=True)
            logging.info("LLM evaluation completed successfully.")
        else:
            logging.warning(f"❌ LLM evaluation skipped — file not found: {llm_script_path}")

    except Exception as e:
        raise NetworkSecurityException(e, sys)