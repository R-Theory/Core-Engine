import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function POST(request: NextRequest) {
  try {
    const authorization = request.headers.get('authorization')

    const response = await fetch(`${BACKEND_URL}/api/v1/auth/logout`, {
      method: 'POST',
      headers: {
        'Authorization': authorization || '',
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Logout proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}