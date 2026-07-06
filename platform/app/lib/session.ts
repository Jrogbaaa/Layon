import "server-only";
import { createHmac, timingSafeEqual } from "crypto";

const SESSION_VALUE = "authenticated";

function sign(value: string): string {
  const secret = process.env.SESSION_SECRET ?? "";
  return createHmac("sha256", secret).update(value).digest("hex");
}

export function createSessionCookieValue(): string {
  return `${SESSION_VALUE}.${sign(SESSION_VALUE)}`;
}

export function isValidSessionCookieValue(cookieValue: string | undefined): boolean {
  if (!cookieValue) return false;
  const [value, signature] = cookieValue.split(".");
  if (!value || !signature) return false;

  const expected = sign(value);
  const expectedBuf = Buffer.from(expected, "hex");
  const actualBuf = Buffer.from(signature, "hex");
  if (expectedBuf.length !== actualBuf.length) return false;

  return value === SESSION_VALUE && timingSafeEqual(expectedBuf, actualBuf);
}

export const SESSION_COOKIE_NAME = "yfg_session";
