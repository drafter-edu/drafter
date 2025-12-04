// Cloudflare Worker: Simple Gemini Proxy with CORS Protection
// -----------------------------------------------------------
// This worker forwards requests from your GitHub Pages frontend to the Gemini API.
// It does **not** inspect or log request/response data.
// It uses a Cloudflare stored secret (GEMINI_API_KEY).
// CORS is restricted so only your GitHub Pages origin can call this proxy.


// Set this in Cloudflare Dashboard → Workers → Variables → Environment Variables
// Name: GEMINI_API_KEY
export default {
  async fetch(request, env) {
  const allowedOrigin = "https://ud-f25-cs1.github.io"; // <-- CHANGE THIS
  const model = "gemini-2.5-flash";


  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": allowedOrigin,
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": request.headers.get("Access-Control-Request-Headers") || "*",
        "Access-Control-Max-Age": "86400",
      },
    });
  }


  // Only allow your frontend
  const origin = request.headers.get("Origin");
  if (origin !== allowedOrigin) {
    return new Response("Forbidden", { status: 403 });
  }


  // Forward request to Gemini

  const geminiURL = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`; // adjust endpoint as needed


  const apiKey = env.GEMINI_API_KEY;
  const newURL = `${geminiURL}?key=${apiKey}`;


  const forwarded = await fetch(newURL, {
    method: request.method,
    headers: {
      "Content-Type": "application/json",
    },
    body: request.body,
  });


  // Return Gemini response with CORS
  const responseBody = await forwarded.arrayBuffer();
    return new Response(responseBody, {
      status: forwarded.status,
      headers: {
        "Content-Type": forwarded.headers.get("Content-Type") || "application/json",
        "Access-Control-Allow-Origin": allowedOrigin,
      },
    });
  },
};