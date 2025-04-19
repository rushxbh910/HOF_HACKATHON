import { ChartBarIcon } from "@/components/icons"

export function Navbar() {
  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center px-4 md:px-6">
        <div className="flex items-center gap-2 mx-auto">
          <ChartBarIcon className="h-8 w-8 text-primary" />
          <h1 className="text-2xl font-bold tracking-tight">Chronos</h1>
        </div>
      </div>
    </header>
  )
}
