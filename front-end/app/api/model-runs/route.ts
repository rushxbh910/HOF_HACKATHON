import { NextResponse } from "next/server"
import clientPromise from "@/lib/mongodb"

export async function GET() {
  try {
    console.log("Connecting to MongoDB...")
    const client = await clientPromise

    // Get database and collection names from environment variables
    const dbName = process.env.MONGODB_DB || "mlflow"
    const collectionName = process.env.MONGODB_COLLECTION || "model_runs"

    console.log(`Using database: ${dbName}, collection: ${collectionName}`)

    const db = client.db(dbName)
    const collection = db.collection(collectionName)

    // Fetch model runs from MongoDB
    console.log("Fetching data from MongoDB...")
    const modelRuns = await collection.find({}).toArray()

    console.log(`Found ${modelRuns.length} model runs`)

    return NextResponse.json({ modelRuns })
  } catch (error) {
    console.error("Error fetching model runs from MongoDB:", error)
    return NextResponse.json(
      {
        error: "Failed to fetch model runs from MongoDB",
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 },
    )
  }
}
