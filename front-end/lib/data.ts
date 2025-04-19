// Type definitions and utility functions only - no static data

export interface ModelRun {
  _id: {
    $oid: string
  }
  run_id: string
  start_time: number
  end_time: number
  status: string
  artifact_uri: string
  params: Record<string, string>
  metrics: {
    gpu_energy_kwh: number
    gpu_carbon_kg: number
    test_f1_score?: number
    test_precision_score?: number
    test_recall_score?: number
    train_f1_score?: number
    train_precision_score?: number
    train_recall_score?: number
    [key: string]: number | undefined
  }
  tags: {
    "mlflow.runName": string
    "mlflow.user": string
    "mlflow.source.name": string
    "mlflow.source.type": string
    "mlflow.source.git.commit": string
    "mlflow.log-model.history"?: string
    [key: string]: string | undefined
  }
  lambda_response?: {
    message: string
    gpu_energy: number
    carbon: number
  }
  lambda_status?: string
  sent_at?: {
    $date: string
  }
}

export function formatDuration(startTime: number, endTime: number): string {
  const durationMs = endTime - startTime
  const seconds = Math.floor(durationMs / 1000)

  if (seconds < 60) {
    return `${seconds}s`
  }

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60

  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  return `${hours}h ${remainingMinutes}m ${remainingSeconds}s`
}

export function formatTimestamp(timestamp: number): string {
  return new Date(timestamp).toLocaleString()
}
