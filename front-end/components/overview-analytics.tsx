"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { formatDuration } from "@/lib/data"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { Badge } from "@/components/ui/badge"
import { Zap, Leaf, Clock, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { useModelRuns } from "@/lib/use-model-runs"

export function OverviewAnalytics() {
  const { modelRuns, isLoading, error, refreshData } = useModelRuns()

  // If loading, show skeleton UI
  if (isLoading) {
    return <OverviewSkeleton />
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

  // Calculate total metrics
  const totalEnergy = modelRuns.reduce((sum, run) => sum + (run.metrics?.gpu_energy_kwh || 0), 0)
  const totalCarbon = modelRuns.reduce((sum, run) => sum + (run.metrics?.gpu_carbon_kg || 0), 0)
  const totalRuns = modelRuns.length
  const successfulRuns = modelRuns.filter((run) => run.status === "FINISHED").length

  // Prepare data for energy and carbon chart
  const chartData = modelRuns.map((run) => ({
    name: run.tags?.["mlflow.runName"] || "Unknown",
    energy: run.metrics?.gpu_energy_kwh || 0,
    carbon: run.metrics?.gpu_carbon_kg || 0,
    runId: run.run_id?.substring(0, 8) || "Unknown",
  }))

  return (
    <div className="space-y-8">
      <div className="flex justify-end mb-4">
        <Button variant="outline" size="sm" onClick={refreshData}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh Data
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
            <div className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalRuns}</div>
            <p className="text-xs text-muted-foreground">
              {successfulRuns} successful, {totalRuns - successfulRuns} failed
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Energy Used</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalEnergy.toExponential(2)} kWh</div>
            <p className="text-xs text-muted-foreground">Across all GPU training runs</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total CO₂ Emitted</CardTitle>
            <Leaf className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCarbon.toExponential(2)} kg</div>
            <p className="text-xs text-muted-foreground">Carbon footprint of all runs</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Training Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatDuration(
                0,
                modelRuns.reduce((sum, run) => sum + ((run.end_time || 0) - (run.start_time || 0)), 0) /
                  modelRuns.length,
              )}
            </div>
            <p className="text-xs text-muted-foreground">Per training run</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Energy & Carbon Metrics</CardTitle>
          <CardDescription>GPU energy usage and carbon emissions per model run</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{
                  top: 20,
                  right: 30,
                  left: 20,
                  bottom: 70,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="runId" angle={-45} textAnchor="end" height={70} tick={{ fontSize: 12 }} />
                <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                <Tooltip
                  formatter={(value, name) => {
                    return [value.toExponential(2), name === "energy" ? "Energy (kWh)" : "Carbon (kg)"]
                  }}
                  labelFormatter={(label) => `Run ID: ${label}`}
                />
                <Legend />
                <Bar yAxisId="left" dataKey="energy" name="Energy (kWh)" fill="#8884d8" />
                <Bar yAxisId="right" dataKey="carbon" name="Carbon (kg)" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Training Runs</CardTitle>
          <CardDescription>All ML model training runs with metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run ID</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Energy (kWh)</TableHead>
                <TableHead>CO₂ (kg)</TableHead>
                <TableHead>F1 Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {modelRuns.map((run) => (
                <TableRow key={run.run_id}>
                  <TableCell className="font-mono text-xs">{run.run_id?.substring(0, 8)}...</TableCell>
                  <TableCell>{run.tags?.["mlflow.runName"] || "Unknown"}</TableCell>
                  <TableCell>
                    <Badge variant={run.status === "FINISHED" ? "success" : "destructive"}>
                      {run.status || "Unknown"}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDuration(run.start_time || 0, run.end_time || 0)}</TableCell>
                  <TableCell>{(run.metrics?.gpu_energy_kwh || 0).toExponential(2)}</TableCell>
                  <TableCell>{(run.metrics?.gpu_carbon_kg || 0).toExponential(2)}</TableCell>
                  <TableCell>
                    {run.metrics?.test_f1_score ? ((run.metrics.test_f1_score || 0) * 100).toFixed(2) + "%" : "N/A"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

function OverviewSkeleton() {
  return (
    <div className="space-y-8">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-4 w-4 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-24 mb-2" />
              <Skeleton className="h-4 w-40" />
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48 mb-2" />
          <Skeleton className="h-4 w-72" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-36 mb-2" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-8 w-full" />
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
