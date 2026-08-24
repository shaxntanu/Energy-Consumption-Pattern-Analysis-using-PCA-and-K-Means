/**
 * API route to proxy requests to Streamlit service
 * Allows React frontend to interact with Streamlit backend
 */

export async function GET(request: Request) {
  try {
    const streamlitUrl = process.env.STREAMLIT_URL || 'http://localhost:8501';
    const response = await fetch(`${streamlitUrl}/api/health`, {
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      return Response.json(
        { error: 'Streamlit service unavailable' },
        { status: 503 }
      );
    }

    return Response.json({ status: 'ok', streamlit: streamlitUrl });
  } catch (error) {
    return Response.json(
      { error: 'Failed to connect to Streamlit', details: String(error) },
      { status: 503 }
    );
  }
}
