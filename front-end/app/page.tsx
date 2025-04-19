import { Navbar } from "@/components/navbar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { OverviewAnalytics } from "@/components/overview-analytics"
import { ModelMetrics } from "@/components/model-metrics"

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1 container mx-auto py-6 px-4 md:px-6">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2 mb-8">
            <TabsTrigger value="overview">📊 Overview & Analytics</TabsTrigger>
            <TabsTrigger value="metrics">📁 Model Metrics</TabsTrigger>
          </TabsList>
          <TabsContent value="overview">
            <OverviewAnalytics />
          </TabsContent>
          <TabsContent value="metrics">
            <ModelMetrics />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
