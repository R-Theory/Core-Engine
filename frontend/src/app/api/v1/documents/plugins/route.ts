import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/documents/plugins`, {
      headers: { authorization: request.headers.get('authorization') || '' },
    })
    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to fetch document plugins:', error)
    return NextResponse.json({ error: 'Failed to fetch plugins' }, { status: 500 })
  }
}
