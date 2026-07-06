import { NextRequest, NextResponse } from "next/server";
import { isValidSessionCookieValue, SESSION_COOKIE_NAME } from "@/app/lib/session";

export default function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname;
  if (path === "/login") {
    return NextResponse.next();
  }

  const cookie = req.cookies.get(SESSION_COOKIE_NAME)?.value;
  if (!isValidSessionCookieValue(cookie)) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
