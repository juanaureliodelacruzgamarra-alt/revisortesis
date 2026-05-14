import { NextResponse, type NextRequest } from "next/server";

const PROTECTED_PREFIXES = ["/student", "/advisor", "/coordinator", "/admin"];
const AUTH_PAGES = ["/login", "/register"];
const ACCESS_COOKIE = "kimy.access";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const token = req.cookies.get(ACCESS_COOKIE)?.value;

  if (PROTECTED_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    if (!token) {
      const url = req.nextUrl.clone();
      url.pathname = "/login";
      url.searchParams.set("from", pathname);
      return NextResponse.redirect(url);
    }
  }

  if (token && AUTH_PAGES.includes(pathname)) {
    const url = req.nextUrl.clone();
    url.pathname = "/";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/student/:path*",
    "/advisor/:path*",
    "/coordinator/:path*",
    "/admin/:path*",
    "/login",
    "/register",
  ],
};
