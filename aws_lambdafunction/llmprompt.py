import subprocess
import json

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

# ---- Build prompt and evaluate with LLM ----
def evaluate_and_optimize_model(metrics):
    prompt = f"""
You are an ML Model Efficiency Evaluator and Optimizer.

Your job is to:
1. Evaluate if the current model configuration is OPTIMAL or needs RETRAINING.
2. If RETRAIN is needed, suggest new hyperparameters that will:
   - Maximize test F1 score
   - Minimize GPU energy (kWh) and carbon (kg)
   - Avoid GPU under/overutilization
   - Stay within reasonable memory usage

### Current Model Metrics:
- GPU Utilization Before Training: {metrics['gpu_before']}%
- GPU Utilization After Training: {metrics['gpu_after']}%
- GPU Memory Used: {metrics['mem_used']} MB
- GPU Energy Consumed: {metrics['gpu_energy']} kWh
- Carbon Footprint: {metrics['gpu_carbon']} kg
- Current Hyperparameters: {json.dumps(metrics['hyperparams'])}
- Train F1 Score: {metrics['train_f1']}
- Test F1 Score: {metrics['test_f1']}

### Output Format (STRICT):

If model is optimal:
STATUS: OPTIMAL
REASON: <brief justification>

If model needs retraining:
STATUS: RETRAIN
SUGGESTED_HYPERPARAMS:
<one-line valid JSON only, no bullets, no explanation>
Example:
{{ "lr": 0.0007, "batch": 128, "dropout": 0.2 }}

IMPORTANT:
- Do NOT include markdown formatting, bullet points, or explanations.
- Only output lines in this exact format.
"""
    return call_local_llm(prompt)

# ---- Sample Metrics ----
metrics = {
    "gpu_before": 15,
    "gpu_after": 60,
    "mem_used": 7200,
    "gpu_energy": 0.0025,
    "gpu_carbon": 0.0011,
    "hyperparams": {"lr": 0.001, "batch": 64, "dropout": 0.1},
    "train_f1": 0.89,
    "test_f1": 0.65
}

# ---- Call LLM and Clean Output ----
output = evaluate_and_optimize_model(metrics)
output = clean_output(output)

print("🔎 Raw LLM Output:\n", output)

# ---- Parse Output ----
lines = output.splitlines()
status = "UNKNOWN"
suggested_params = None
reason = ""

for i, line in enumerate(lines):
    if line.strip().startswith("STATUS:"):
        status = line.split(":", 1)[1].strip().upper()

    elif line.strip().startswith("REASON:"):
        reason = line.split(":", 1)[1].strip()

    elif "SUGGESTED_HYPERPARAMS" in line.upper():
        for j in range(i + 1, len(lines)):
            candidate = lines[j].strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                try:
                    suggested_params = json.loads(candidate)
                    break
                except Exception as e:
                    suggested_params = f"⚠️ Failed to parse JSON: {e}"

# ---- Final Output ----
print(f"\n🧠 Model Status: {status}")
if reason:
    print(f"📌 Reason: {reason}")
if suggested_params:
    print(f"🔧 Suggested Hyperparameters:\n{json.dumps(suggested_params, indent=2)}")
