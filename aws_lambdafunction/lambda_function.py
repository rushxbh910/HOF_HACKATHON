
import json
import requests
import os

HUGGINGFACE_TOKEN = os.environ.get('HF_API_TOKEN')
MODEL_ENDPOINT = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"

def call_llm(prompt):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    payload = {"inputs": prompt}
    response = requests.post(MODEL_ENDPOINT, headers=headers, json=payload)
    return response.json()[0]['generated_text']

def lambda_handler(event, context):
    metrics = event['metrics']
    gpu_before = metrics.get("gpu_before")
    gpu_after = metrics.get("gpu_after")
    mem_used = metrics.get("mem_used")
    gpu_energy = metrics.get("gpu_energy")
    gpu_carbon = metrics.get("gpu_carbon")
    hyperparams = metrics.get("hyperparams")
    train_f1 = metrics.get("train_f1")
    test_f1 = metrics.get("test_f1")

    prompt = f"""
You are an ML Efficiency Evaluator. Given the following model training metrics:

- GPU Utilization before training: {gpu_before}
- GPU Utilization after training: {gpu_after}
- GPU memory used: {mem_used} MB
- GPU energy (kWh): {gpu_energy}
- Carbon footprint (kg): {gpu_carbon}
- Hyperparameters: {hyperparams}
- Train F1: {train_f1}, Test F1: {test_f1}

Evaluate:
1. Is the GPU underutilized or overutilized?
2. Are the carbon and energy costs justified?
3. Are the hyperparameters likely to be optimal?
4. Should the model be retrained with adjusted params?

Reply with "RETRAIN" if yes, otherwise say "OPTIMAL".
"""

    result = call_llm(prompt)

    if "RETRAIN" in result.upper():
        return {
            'statusCode': 200,
            'message': "Model retraining triggered based on LLM feedback.",
            'llm_response': result
        }
    else:
        return {
            'statusCode': 200,
            'message': "Model utilization is optimal.",
            'llm_response': result
        }
