import { NextResponse, type NextRequest } from "next/server";

import { readAccessToken } from "@/lib/auth/cookies";
import { API_URL } from "@/lib/env";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string; versionId: string }> },
) {
  const { id, versionId } = await params;
  const token = await readAccessToken();
  if (!token) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const apiRes = await fetch(
    `${API_URL}/api/v1/submissions/${id}/versions/${versionId}/file`,
    {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    },
  );

  if (!apiRes.ok || !apiRes.body) {
    return NextResponse.json(
      { error: "download failed", status: apiRes.status },
      { status: apiRes.status },
    );
  }

  const headers = new Headers();
  const contentType = apiRes.headers.get("content-type");
  const disposition = apiRes.headers.get("content-disposition");
  if (contentType) headers.set("content-type", contentType);
  if (disposition) headers.set("content-disposition", disposition);

  return new NextResponse(apiRes.body, { status: 200, headers });
}
