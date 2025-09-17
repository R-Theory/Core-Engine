import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/v1/documents/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        authorization: request.headers.get('authorization') || '',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to search documents:', error)
    return NextResponse.json(
      { error: 'Failed to search documents' },
      { status: 500 }
    )
  }
}
