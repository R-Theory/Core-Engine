import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000'

export async function POST(request: NextRequest) {
  try {
    const contentType = request.headers.get('content-type')
    let body: string | FormData

    if (contentType?.includes('application/x-www-form-urlencoded')) {
      // Handle form data
      const formData = await request.formData()
      const urlSearchParams = new URLSearchParams()
      formData.forEach((value, key) => {
        urlSearchParams.append(key, value.toString())
      })
      body = urlSearchParams.toString()
    } else {
      // Handle JSON data (convert to form data for backend)
      const json = await request.json()
      const urlSearchParams = new URLSearchParams()
      urlSearchParams.append('username', json.username || json.email)
      urlSearchParams.append('password', json.password)
      body = urlSearchParams.toString()
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Login proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}