import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://backend:8000";

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/dashboard`, {
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    const body = await response.text();
    return new NextResponse(body, {
      status: response.status,
      headers: {
        "cache-control": "no-store",
        "content-type": response.headers.get("content-type") ?? "application/json; charset=utf-8",
      },
    });
  } catch {
    return NextResponse.json(
      { error: "Failed to reach backend dashboard service" },
      { status: 502 },
    );
  }
}
