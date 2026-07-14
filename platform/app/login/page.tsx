"use client";

import { useActionState, useState } from "react";
import { login } from "@/app/actions/auth";
import { SilkCanvas } from "@/app/components/SilkCanvas";

export default function LoginPage() {
  const [state, formAction, pending] = useActionState(login, undefined);
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="grain relative flex min-h-dvh flex-1 bg-canvas-deep text-ink">
      {/* Living silk backdrop */}
      <SilkCanvas className="absolute inset-0 h-full w-full" />

      {/* Darkening veil so the form side stays readable */}
      <div
        aria-hidden
        className="absolute inset-0 bg-gradient-to-r from-canvas-deep via-canvas-deep/80 to-transparent sm:via-canvas-deep/60"
      />

      <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 items-center justify-between gap-16 px-6 py-16 sm:px-10">
        <div className="w-full max-w-md">
          <p className="font-mono mb-6 text-xs tracking-widest text-accent">
            MADRID · {new Date().getFullYear()}
          </p>

          <h1 className="display-hero text-5xl text-ink sm:text-6xl">
            Look After
            <br />
            <em className="text-accent">You</em>
          </h1>

          <p className="font-display mt-5 max-w-sm text-lg italic leading-snug text-muted">
            Cuidamos a quienes brillan — the night watch for a roster of stars.
          </p>

          <form action={formAction} className="mt-10">
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-ink">
              Team password
            </label>
            <div className="flex flex-col gap-3 sm:flex-row sm:gap-2">
              <div className="relative flex-1">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoFocus
                  autoComplete="current-password"
                  aria-invalid={!!state?.error}
                  aria-describedby="password-error"
                  className="w-full rounded-md border border-border bg-canvas/70 pl-3.5 pr-10 py-2.5 text-ink backdrop-blur-sm transition-colors outline-none placeholder:text-faint focus:border-accent"
                  placeholder="••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted hover:text-ink transition-colors cursor-pointer"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-5 w-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-5 w-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.644C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  )}
                </button>
              </div>
              <button
                type="submit"
                disabled={pending}
                className="shrink-0 rounded-md bg-accent px-5 py-2.5 font-semibold text-canvas-deep transition hover:bg-accent-bright disabled:opacity-50 cursor-pointer"
              >
                {pending ? "Entering…" : "Enter"}
              </button>
            </div>

            <p id="password-error" role="alert" className="min-h-5 mt-3 text-sm text-negative">
              {state?.error}
            </p>

            <p className="mt-8 text-xs text-muted">
              Team access password — ask your manager if you don&apos;t have it.
            </p>
          </form>
        </div>

        {/* Gallery plate: AI-generated key art, drifting slowly. */}
        <figure className="hidden shrink-0 lg:block">
          <div className="overflow-hidden rounded-[0.625rem] border border-border-faint">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/silk.jpg"
              alt="Silk fabric suspended in darkness, lit in garnet and gold"
              width={347}
              height={520}
              className="silk-drift block h-[520px] w-auto object-cover"
            />
          </div>
          <figcaption className="font-mono mt-3 flex items-baseline justify-between text-xs text-faint">
            <span className="italic">Seda en la medianoche</span>
            <span>№ 001</span>
          </figcaption>
        </figure>
      </div>
    </div>
  );
}
