"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatDuration, formatTimestamp } from "@/lib/data"
import { Zap, Leaf, Clock, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { useModelRuns } from "@/lib/use-model-runs"

export function ModelMetrics() {
  const { modelRuns, isLoading, error, refreshData } = useModelRuns()

  // If loading, show skeleton UI
  if (isLoading) {
    return <ModelMetricsSkeleton />
  }

  // If error, show error message
  if (error) {
    return (
      <Alert variant="destructive" className="mb-6">
        <AlertTitle>Error loading data</AlertTitle>
        <AlertDescription>
          {error}
          <Button variant="outline" size="sm" className="mt-2" onClick={refreshData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Try Again
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  // If no data, show empty state
  if (!modelRuns || modelRuns.length === 0) {
    return (
      <Alert className="mb-6">
        <AlertTitle>No data available</AlertTitle>
        <AlertDescription>
          No model runs data found. Please check the MongoDB connection.
          <Button variant="outline" size="sm" className="mt-2" onClick={refreshData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh Data
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <>
      <div className="flex justify-end mb-4">
        <Button variant="outline" size="sm" onClick={refreshData}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh Data
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {modelRuns.map((run) => (
          <Card key={run.run_id} className="flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{run.tags?.["mlflow.runName"] || "Unknown"}</CardTitle>
                <Badge variant={run.status === "FINISHED" ? "success" : "destructive"}>{run.status || "Unknown"}</Badge>
              </div>
              <CardDescription className="font-mono text-xs">{run.run_id}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Duration:</span>
                  </div>
                  <div>{formatDuration(run.start_time || 0, run.end_time || 0)}</div>

                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Energy:</span>
                  </div>
                  <div>{(run.metrics?.gpu_energy_kwh || 0).toExponential(2)} kWh</div>

                  <div className="flex items-center gap-2">
                    <Leaf className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">CO₂:</span>
                  </div>
                  <div>{(run.metrics?.gpu_carbon_kg || 0).toExponential(2)} kg</div>
                </div>

                {run.metrics?.test_f1_score && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Test Metrics</div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">F1 Score:</div>
                      <div>{((run.metrics.test_f1_score || 0) * 100).toFixed(2)}%</div>

                      <div className="text-muted-foreground">Precision:</div>
                      <div>{((run.metrics.test_precision_score || 0) * 100).toFixed(2)}%</div>

                      <div className="text-muted-foreground">Recall:</div>
                      <div>{((run.metrics.test_recall_score || 0) * 100).toFixed(2)}%</div>
                    </div>
                  </div>
                )}

                <div className="text-xs text-muted-foreground">Created: {formatTimestamp(run.start_time || 0)}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  )
}

function ModelMetricsSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <Card key={i} className="flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-5 w-20" />
            </div>
            <Skeleton className="h-4 w-48 mt-2" />
          </CardHeader>
          <CardContent className="flex-1">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                {[1, 2, 3, 4, 5, 6].map((j) => (
                  <Skeleton key={j} className="h-5 w-full" />
                ))}
              </div>
              <Skeleton className="h-4 w-32 mt-4" />
              <div className="grid grid-cols-2 gap-2">
                {[1, 2, 3, 4, 5, 6].map((j) => (
                  <Skeleton key={j} className="h-5 w-full" />
                ))}
              </div>
              <Skeleton className="h-4 w-48 mt-2" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
