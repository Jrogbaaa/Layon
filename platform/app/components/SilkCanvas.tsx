"use client";

import { useEffect, useRef } from "react";

const VERT = `
attribute vec2 a_pos;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }
`;

// Domain-warped fbm "silk" — luminous garnet/gold ribbons in darkness.
const FRAG = `
precision highp float;
uniform vec2 u_res;
uniform float u_time;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
    mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
    u.y
  );
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  mat2 rot = mat2(0.8, 0.6, -0.6, 0.8);
  for (int i = 0; i < 5; i++) {
    v += a * noise(p);
    p = rot * p * 2.05;
    a *= 0.5;
  }
  return v;
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_res.xy;
  vec2 p = uv;
  p.x *= u_res.x / u_res.y;

  float t = u_time * 0.045;

  // Two rounds of domain warping — the folds.
  vec2 q = vec2(fbm(p * 1.6 + vec2(0.0, t)), fbm(p * 1.6 + vec2(5.2, t * 1.3)));
  vec2 r = vec2(
    fbm(p * 1.6 + 3.4 * q + vec2(1.7, 9.2) + t * 0.6),
    fbm(p * 1.6 + 3.4 * q + vec2(8.3, 2.8) - t * 0.4)
  );
  float f = fbm(p * 1.6 + 3.2 * r);

  // Sharpen ridges into silk-like sheens.
  float sheen = smoothstep(0.42, 0.78, f);
  float ridge = pow(smoothstep(0.55, 0.95, f), 3.0);

  vec3 black = vec3(0.039, 0.020, 0.024);
  vec3 garnet = vec3(0.373, 0.098, 0.145);
  vec3 ember = vec3(0.706, 0.278, 0.196);
  vec3 gold = vec3(0.941, 0.788, 0.416);

  vec3 col = black;
  col = mix(col, garnet, smoothstep(0.25, 0.75, f));
  col = mix(col, ember, sheen * 0.55);
  col += gold * ridge * 0.8;

  // Corner vignette keeps the frame anchored in darkness.
  float vig = smoothstep(1.25, 0.35, length(uv - 0.5) * 1.6);
  col *= vig;

  gl_FragColor = vec4(col, 1.0);
}
`;

export function SilkCanvas({ className }: { className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const gl = canvas.getContext("webgl", { antialias: false, alpha: false });
    if (!gl) return;

    const compile = (type: number, src: string) => {
      const s = gl.createShader(type)!;
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    };
    const program = gl.createProgram()!;
    gl.attachShader(program, compile(gl.VERTEX_SHADER, VERT));
    gl.attachShader(program, compile(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return;
    gl.useProgram(program);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(program, "a_pos");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    const uRes = gl.getUniformLocation(program, "u_res");
    const uTime = gl.getUniformLocation(program, "u_time");

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.75);
      const w = Math.round(canvas.clientWidth * dpr);
      const h = Math.round(canvas.clientHeight * dpr);
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
        gl.viewport(0, 0, w, h);
      }
    };

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    let raf = 0;
    let running = false;
    const start = performance.now();

    const draw = (now: number) => {
      resize();
      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform1f(uTime, (now - start) / 1000);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    };

    const loop = (now: number) => {
      draw(now);
      raf = requestAnimationFrame(loop);
    };

    const setRunning = (on: boolean) => {
      if (on && !running && !reduced.matches) {
        running = true;
        raf = requestAnimationFrame(loop);
      } else if (!on && running) {
        running = false;
        cancelAnimationFrame(raf);
      }
    };

    // Static frame first — reduced-motion users get a beautiful still.
    draw(performance.now());
    setRunning(true);

    const onVisibility = () => setRunning(document.visibilityState === "visible");
    const io = new IntersectionObserver(([e]) => setRunning(e.isIntersecting));
    io.observe(canvas);
    document.addEventListener("visibilitychange", onVisibility);
    const onReduced = () => {
      setRunning(!reduced.matches);
      if (reduced.matches) draw(performance.now());
    };
    reduced.addEventListener("change", onReduced);
    const onWindowResize = () => draw(performance.now());
    window.addEventListener("resize", onWindowResize);

    return () => {
      cancelAnimationFrame(raf);
      io.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      reduced.removeEventListener("change", onReduced);
      window.removeEventListener("resize", onWindowResize);
    };
  }, []);

  return (
    <canvas
      ref={ref}
      aria-hidden
      className={className}
      style={{
        // No-WebGL fallback: the canvas background itself carries the mood.
        background:
          "radial-gradient(120% 90% at 70% 20%, #4a141d 0%, #1d0d10 55%, #0a0506 100%)",
      }}
    />
  );
}
