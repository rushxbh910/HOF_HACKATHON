"use client"

import { useState, useEffect } from "react"
import type { ModelRun } from "./data"

export function useModelRuns() {
  const [modelRuns, setModelRuns] = useState<ModelRun[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch("/api/model-runs")

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || "Failed to fetch data")
      }

      const data = await response.json()
      setModelRuns(data.modelRuns)
    } catch (err) {
      console.error("Error fetching model runs:", err)
      setError(err instanceof Error ? err.message : "An unknown error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  // Initial data fetch
  useEffect(() => {
    fetchData()
  }, [])

  // Function to manually refresh data
  const refreshData = async () => {
    await fetchData()
  }

  return {
    modelRuns,
    isLoading,
    error,
    refreshData,
  }
}
