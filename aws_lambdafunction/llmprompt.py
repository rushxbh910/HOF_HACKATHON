import subprocess
import json

def call_local_llm(prompt, model="gemma:2b-instruct"):
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode(),
        capture_output=True,
        check=True
    )
    return result.stdout.decode().strip()

def evaluate_model(metrics):
    prompt = f"""
You are an ML Efficiency Evaluator. Given the following model training metrics:

- GPU Utilization before training: {metrics['gpu_before']}
- GPU Utilization after training: {metrics['gpu_after']}
- GPU memory used: {metrics['mem_used']} MB
- GPU energy (kWh): {metrics['gpu_energy']}
- Carbon footprint (kg): {metrics['gpu_carbon']}
- Hyperparameters: {json.dumps(metrics['hyperparams'])}
- Train F1: {metrics['train_f1']}, Test F1: {metrics['test_f1']}

Evaluation Criteria:
1. Is the GPU underutilized or overutilized?
2. Are the carbon and energy costs justified?
3. Are the hyperparameters likely to be optimal?
4. Should the model be retrained with adjusted params?

Respond with just one word:
- "RETRAIN" if retraining is needed.
- "OPTIMAL" if the model is well-utilized.
"""
    return call_local_llm(prompt)

# Example usage
metrics = {
    "gpu_before": 15,
    "gpu_after": 60,
    "mem_used": 7200,
    "gpu_energy": 0.0025,
    "gpu_carbon": 0.0011,
    "hyperparams": {"lr": 0.001, "batch": 64},
    "train_f1": 0.89,
    "test_f1": 0.65
}

result = evaluate_model(metrics)

print(f"LLM Decision: {result}")
