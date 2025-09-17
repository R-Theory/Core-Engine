import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/settings/integrations/available`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to fetch available integrations:', error)
    return NextResponse.json(
      { error: 'Failed to fetch available integrations' },
      { status: 500 }
    )
  }
}