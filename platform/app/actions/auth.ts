"use server";

import { timingSafeEqual, createHash } from "crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { createSessionCookieValue, SESSION_COOKIE_NAME } from "@/app/lib/session";

function safeCompare(a: string, b: string): boolean {
  const hashA = createHash("sha256").update(a).digest();
  const hashB = createHash("sha256").update(b).digest();
  return timingSafeEqual(hashA, hashB);
}

export type LoginState = { error?: string } | undefined;

export async function login(_prevState: LoginState, formData: FormData): Promise<LoginState> {
  const password = formData.get("password");
  const sitePassword = process.env.SITE_PASSWORD ?? "";

  if (typeof password !== "string" || !safeCompare(password, sitePassword)) {
    return { error: "Incorrect password." };
  }

  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE_NAME, createSessionCookieValue(), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });

  redirect("/");
}

export async function logout(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_COOKIE_NAME);
  redirect("/login");
}
