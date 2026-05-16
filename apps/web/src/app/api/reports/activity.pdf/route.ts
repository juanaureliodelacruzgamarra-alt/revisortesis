import { NextResponse, type NextRequest } from "next/server";

import { readAccessToken } from "@/lib/auth/cookies";
import { API_URL } from "@/lib/env";

export async function GET(req: NextRequest) {
  const token = await readAccessToken();
  if (!token) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const qs = req.nextUrl.searchParams.toString();
  const apiRes = await fetch(
    `${API_URL}/api/v1/reports/activity.pdf${qs ? `?${qs}` : ""}`,
    {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    },
  );

  if (!apiRes.ok || !apiRes.body) {
    return NextResponse.json(
      { error: "pdf generation failed", status: apiRes.status },
      { status: apiRes.status },
    );
  }

  const headers = new Headers();
  headers.set(
    "content-type",
    apiRes.headers.get("content-type") ?? "application/pdf",
  );
  const disposition = apiRes.headers.get("content-disposition");
  if (disposition) headers.set("content-disposition", disposition);

  return new NextResponse(apiRes.body, { status: 200, headers });
}
