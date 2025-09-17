import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/credentials/notion`, {
      headers: {
        authorization: request.headers.get('authorization') || '',
      },
    })
    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to get Notion credentials:', error)
    return NextResponse.json({ error: 'Failed to get Notion credentials' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const response = await fetch(`${BACKEND_URL}/api/v1/credentials/notion`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        authorization: request.headers.get('authorization') || '',
      },
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      const text = await response.text()
      throw new Error(`Backend responded with ${response.status}: ${text}`)
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to set Notion credentials:', error)
    return NextResponse.json({ error: 'Failed to set Notion credentials' }, { status: 500 })
  }
}

