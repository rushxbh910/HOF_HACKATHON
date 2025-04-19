import subprocess
import json
import os

# ---- Run Ollama LLM ----
def call_local_llm(prompt, model="gemma:2b-instruct"):
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode("utf-8"),
        capture_output=True,
        check=True
    )
    return result.stdout.decode("utf-8").strip()

# ---- Strip markdown from LLM output ----
def clean_output(text):
    return text.replace("```", "").replace("**", "").strip()

# ---- Load latest metrics from JSON file ----
def load_latest_metrics(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found at: {json_path}")

    with open(json_path, "r") as f:
        runs = json.load(f)

    if not runs:
        raise ValueError("❌ No run data found in the JSON file.")

    latest = sorted(runs, key=lambda x: x.get("end_time", 0), reverse=True)[0]
    metrics = latest.get("metrics", {})
    params  = latest.get("params", {})

    return {
        "gpu_before": metrics.get("pre_train_gpu_0_util", 0.0),
        "gpu_after" : metrics.get("post_train_gpu_0_util", 0.0),
        "mem_used"  : metrics.get("pre_train_gpu_0_memused", 0.0),
        "gpu_energy": metrics.get("gpu_energy_kwh", 0.0),
        "gpu_carbon": metrics.get("gpu_carbon_kg", 0.0),
        "hyperparams": {
            "lr"     : float(params.get("learning_rate", 0.001)),
            "batch"  : int(params.get("batch_size", 64)),
            "dropout": float(params.get("dropout", 0.1))
        },
        "train_f1": metrics.get("train_f1_score", 0.0),
        "test_f1" : metrics.get("test_f1_score", 0.0)
    }

# ---- Build prompt and evaluate with LLM ----
def evaluate_and_optimize_model(metrics):
    prompt = f"""Respond ONLY with the exact lines described below—no additional text.

FORMAT:
If optimal:
STATUS: OPTIMAL
REASON: <brief justification>

If retraining is needed:
STATUS: RETRAIN
SUGGESTED_HYPERPARAMS:
<one-line JSON>

### BEGIN ANALYSIS ###
You are an ML Model Efficiency Evaluator and Optimizer.

Current Model Metrics:
- GPU Utilization Before Training: {metrics['gpu_before']}%
- GPU Utilization After Training: {metrics['gpu_after']}%
- GPU Memory Used: {metrics['mem_used']} MB
- GPU Energy Consumed: {metrics['gpu_energy']} kWh
- Carbon Footprint: {metrics['gpu_carbon']} kg
- Current Hyperparameters: {json.dumps(metrics['hyperparams'])}
- Train F1 Score: {metrics['train_f1']}
- Test F1 Score: {metrics['test_f1']}

### END ANALYSIS ###

Provide your answer now.
"""
    return call_local_llm(prompt)

# ---- Main Execution ----
if __name__ == '__main__':
    try:
        json_file_path = r'C:\Projects\HOF_HACKATHON\exported_gpu_runs.json'
        metrics = load_latest_metrics(json_file_path)

        # debug
        print("DEBUG: loaded metrics →", json.dumps(metrics, indent=2))

        raw = evaluate_and_optimize_model(metrics)
        clean = clean_output(raw)

        print("🔎 Raw LLM Output:\n", clean)

        # ---- Parse Output ----
        status = "UNKNOWN"
        reason = ""
        suggested_params = None

        for line in clean.splitlines():
            if line.startswith("STATUS:"):
                status = line.split(":", 1)[1].strip().upper()
            elif line.startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()
            elif line.startswith("{") and line.endswith("}"):
                try:
                    suggested_params = json.loads(line)
                except json.JSONDecodeError as e:
                    suggested_params = f"⚠️ Failed to parse JSON: {e}"

        # ---- Final Output ----
        print(f"\n🧠 Model Status: {status}")
        if reason:
            print(f"📌 Reason: {reason}")
        if suggested_params:
            print("🔧 Suggested Hyperparameters:")
            print(json.dumps(suggested_params, indent=2))

    except Exception as e:
        print(f"Error: {e}")
