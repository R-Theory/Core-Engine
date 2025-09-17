import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({})) // Empty body is fine for sync all
    
    const response = await fetch(`${BACKEND_URL}/api/v1/settings/integrations/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // TODO: Add authentication headers when auth is implemented
        // 'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to sync integrations:', error)
    return NextResponse.json(
      { error: 'Failed to sync integrations' },
      { status: 500 }
    )
  }
}