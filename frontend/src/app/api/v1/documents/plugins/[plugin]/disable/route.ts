import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function POST(request: NextRequest, context: { params: { plugin: string } }) {
  try {
    const plugin = context.params.plugin
    const response = await fetch(`${BACKEND_URL}/api/v1/documents/plugins/${plugin}/disable`, {
      method: 'POST',
      headers: { authorization: request.headers.get('authorization') || '' },
    })
    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to disable document plugin:', error)
    return NextResponse.json({ error: 'Failed to disable plugin' }, { status: 500 })
  }
}
