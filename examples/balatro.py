"""
This is meant to be an example of a Drafter site that has a procedural background, with a warped checker field, glowing suit particles, chromatic offsets, film grain, scanlines, and pointer parallax. It is meant to be a demonstration of how to use Drafter's features to create a visually appealing site.
It kind of works, but also kind of doesn't.

We need to invest more time into integrating it properly, instead of just bolting on the code.
"""

from drafter import *

add_website_css("""
                :root {
      color-scheme: dark;
      --ink: #f8f2d8;
      --panel: rgba(10, 8, 24, 0.68);
      --border: rgba(255, 255, 255, 0.16);
      --glow: rgba(255, 80, 170, 0.35);
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 100%;
      min-height: 100%;
      margin: 0;
      overflow: hidden;
      background: #07040f;
      color: var(--ink);
      font-family:
        Inter, ui-rounded, "SF Pro Rounded", system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    body::before,
    body::after {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 2;
    }

    /* CRT scanlines */
    body::before {
      background:
        repeating-linear-gradient(
          to bottom,
          rgba(255, 255, 255, 0.025) 0,
          rgba(255, 255, 255, 0.025) 1px,
          transparent 1px,
          transparent 4px
        );
      mix-blend-mode: overlay;
      opacity: 0.75;
    }

    /* Vignette and subtle glass tint */
    body::after {
      background:
        radial-gradient(circle at center, transparent 25%, rgba(0, 0, 0, 0.24) 68%, rgba(0, 0, 0, 0.76) 100%),
        linear-gradient(120deg, rgba(255, 0, 110, 0.05), transparent 42%, rgba(0, 225, 255, 0.045));
    }

    canvas {
      position: fixed;
      inset: 0;
      width: 100%;
      height: 100%;
      display: block;
      z-index: 0;
      filter: saturate(1.18) contrast(1.07);
    }

    .shell {
      position: relative;
      z-index: 3;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
    }

    .card {
      width: min(720px, 94vw);
      padding: clamp(24px, 5vw, 56px);
      border: 1px solid var(--border);
      border-radius: 28px;
      background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.09), transparent 35%),
        var(--panel);
      box-shadow:
        0 28px 90px rgba(0, 0, 0, 0.52),
        inset 0 1px 0 rgba(255, 255, 255, 0.12),
        0 0 80px var(--glow);
      backdrop-filter: blur(16px) saturate(1.1);
      -webkit-backdrop-filter: blur(16px) saturate(1.1);
      transform: perspective(1000px) rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
      transition: transform 140ms ease-out;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 11px;
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.055);
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }

    .pip {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #ff4d9d;
      box-shadow:
        0 0 14px #ff4d9d,
        0 0 26px rgba(255, 77, 157, 0.65);
      animation: pulse 1.8s ease-in-out infinite;
    }

    h1 {
      max-width: 12ch;
      margin: 24px 0 14px;
      font-size: clamp(3rem, 9vw, 7.5rem);
      line-height: 0.82;
      letter-spacing: -0.075em;
      text-transform: uppercase;
      text-wrap: balance;
      text-shadow:
        2px 2px 0 #d12372,
        -2px -1px 0 #18b8d6,
        0 12px 28px rgba(0, 0, 0, 0.42);
    }

    p {
      max-width: 58ch;
      margin: 0;
      color: rgba(248, 242, 216, 0.76);
      font-size: clamp(1rem, 2vw, 1.16rem);
      line-height: 1.65;
    }

    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 26px;
    }

    button {
      appearance: none;
      border: 1px solid rgba(255, 255, 255, 0.17);
      border-radius: 14px;
      padding: 11px 15px;
      background: rgba(255, 255, 255, 0.07);
      color: var(--ink);
      font: inherit;
      font-weight: 750;
      cursor: pointer;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
      transition:
        transform 120ms ease,
        background 120ms ease,
        border-color 120ms ease;
    }

    button:hover {
      transform: translateY(-1px);
      background: rgba(255, 255, 255, 0.11);
      border-color: rgba(255, 255, 255, 0.28);
    }

    button:active {
      transform: translateY(1px) scale(0.99);
    }

    button:focus-visible {
      outline: 3px solid rgba(56, 213, 255, 0.55);
      outline-offset: 3px;
    }

    .suits {
      display: flex;
      gap: 14px;
      margin-top: 24px;
      font-size: 1.5rem;
      opacity: 0.78;
      user-select: none;
    }

    .suits span {
      animation: bob 3.2s ease-in-out infinite;
      filter: drop-shadow(0 0 12px currentColor);
    }

    .suits span:nth-child(2) { animation-delay: -0.8s; }
    .suits span:nth-child(3) { animation-delay: -1.6s; }
    .suits span:nth-child(4) { animation-delay: -2.4s; }

    .red { color: #ff5c97; }
    .blue { color: #56ddff; }
    .gold { color: #ffd86a; }
    .violet { color: #ae7cff; }

    @keyframes pulse {
      50% { transform: scale(1.35); opacity: 0.65; }
    }

    @keyframes bob {
      50% { transform: translateY(-7px) rotate(4deg); }
    }

    @media (prefers-reduced-motion: reduce) {
      .pip,
      .suits span {
        animation: none;
      }

      .card {
        transition: none;
      }
    }""")

JS = """
               (() => {
      const canvas = document.getElementById("background");
      const ctx = canvas.getContext("2d", { alpha: false });
      const card = document.getElementById("card");
      const motionButton = document.getElementById("motionButton");
      const paletteButton = document.getElementById("paletteButton");
      const prefersReducedMotion = matchMedia("(prefers-reduced-motion: reduce)");

      const palettes = [
        {
          dark: "#090312",
          a: "#f52f8d",
          b: "#13b9d6",
          c: "#7f48ff",
          hot: "#ffcc66"
        },
        {
          dark: "#04110f",
          a: "#35e58c",
          b: "#21a8ff",
          c: "#f448b8",
          hot: "#f8f070"
        },
        {
          dark: "#100603",
          a: "#ff6f2c",
          b: "#f7cb3f",
          c: "#cb3cff",
          hot: "#63ecff"
        }
      ];

      let paletteIndex = 0;
      let paused = prefersReducedMotion.matches;
      let dpr = Math.min(devicePixelRatio || 1, 2);
      let width = 0;
      let height = 0;
      let time = 0;
      let last = performance.now();
      let pointerX = 0;
      let pointerY = 0;
      let targetX = 0;
      let targetY = 0;

      const particles = Array.from({ length: 44 }, (_, i) => ({
        angle: Math.random() * Math.PI * 2,
        radius: 0.16 + Math.random() * 0.52,
        speed: 0.08 + Math.random() * 0.22,
        size: 14 + Math.random() * 34,
        wobble: Math.random() * Math.PI * 2,
        suit: ["♥", "♠", "♦", "♣"][i % 4],
        alpha: 0.14 + Math.random() * 0.34
      }));

      function hexToRgb(hex) {
        const value = hex.replace("#", "");
        const bigint = parseInt(value, 16);
        return {
          r: (bigint >> 16) & 255,
          g: (bigint >> 8) & 255,
          b: bigint & 255
        };
      }

      function rgba(hex, alpha) {
        const { r, g, b } = hexToRgb(hex);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
      }

      function resize() {
        dpr = Math.min(devicePixelRatio || 1, 2);
        width = innerWidth;
        height = innerHeight;
        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      }

      function squircleWave(x, y, t) {
        const r = Math.hypot(x, y);
        const angle = Math.atan2(y, x);
        return (
          Math.sin(r * 0.031 - t * 1.2) * 20 +
          Math.sin(angle * 5 + t * 0.7) * 13 +
          Math.cos((x - y) * 0.012 + t * 0.45) * 8
        );
      }

      function drawChecker(palette, t) {
        const cx = width * 0.5 + pointerX * 42;
        const cy = height * 0.5 + pointerY * 34;
        const tile = Math.max(42, Math.min(width, height) * 0.075);
        const cols = Math.ceil(width / tile) + 8;
        const rows = Math.ceil(height / tile) + 8;

        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(Math.sin(t * 0.18) * 0.08 + pointerX * 0.045);
        ctx.translate(-cx, -cy);

        for (let row = -4; row < rows; row++) {
          for (let col = -4; col < cols; col++) {
            const baseX = col * tile - tile * 2;
            const baseY = row * tile - tile * 2;
            const localX = baseX + tile * 0.5 - cx;
            const localY = baseY + tile * 0.5 - cy;
            const warp = squircleWave(localX, localY, t);
            const bendX = Math.sin(localY * 0.012 + t * 0.5) * 24;
            const bendY = Math.cos(localX * 0.01 - t * 0.4) * 18;
            const depth = 1 + Math.sin(Math.hypot(localX, localY) * 0.009 - t) * 0.12;

            const x = baseX + bendX + (localX / Math.max(width, 1)) * warp;
            const y = baseY + bendY + (localY / Math.max(height, 1)) * warp;
            const checker = (row + col) & 1;

            ctx.fillStyle = checker
              ? rgba(palette.a, 0.15 + depth * 0.06)
              : rgba(palette.b, 0.11 + depth * 0.05);

            ctx.beginPath();
            ctx.roundRect(x, y, tile * 0.94 * depth, tile * 0.94 * depth, tile * 0.14);
            ctx.fill();
          }
        }

        ctx.restore();
      }

      function drawGlowOrbits(palette, t) {
        const cx = width * 0.5 + pointerX * 75;
        const cy = height * 0.5 + pointerY * 60;
        const maxRadius = Math.max(width, height) * 0.68;

        ctx.save();
        ctx.globalCompositeOperation = "screen";

        for (let i = 0; i < 5; i++) {
          const radius = maxRadius * (0.18 + i * 0.13);
          ctx.lineWidth = 2 + i * 0.7;
          ctx.strokeStyle = rgba(
            [palette.a, palette.b, palette.c, palette.hot][i % 4],
            0.13 - i * 0.013
          );
          ctx.beginPath();
          ctx.ellipse(
            cx,
            cy,
            radius * (1 + Math.sin(t * 0.3 + i) * 0.08),
            radius * 0.52,
            t * 0.08 + i * 0.48,
            0,
            Math.PI * 2
          );
          ctx.stroke();
        }

        const bloom = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxRadius * 0.72);
        bloom.addColorStop(0, rgba(palette.c, 0.19));
        bloom.addColorStop(0.36, rgba(palette.a, 0.1));
        bloom.addColorStop(1, rgba(palette.b, 0));
        ctx.fillStyle = bloom;
        ctx.fillRect(0, 0, width, height);
        ctx.restore();
      }

      function drawSuitParticles(palette, t) {
        const cx = width * 0.5;
        const cy = height * 0.5;
        const scale = Math.min(width, height);
        const colors = [palette.a, palette.b, palette.hot, palette.c];

        ctx.save();
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.globalCompositeOperation = "screen";

        particles.forEach((particle, index) => {
          const orbit = particle.angle + t * particle.speed;
          const wobble = Math.sin(t * 0.9 + particle.wobble) * 0.055;
          const rx = scale * particle.radius * (1.22 + wobble);
          const ry = scale * particle.radius * (0.48 - wobble * 0.3);
          const x = cx + Math.cos(orbit) * rx + pointerX * 100 * particle.radius;
          const y = cy + Math.sin(orbit) * ry + pointerY * 78 * particle.radius;
          const color = colors[index % colors.length];

          ctx.font = `800 ${particle.size}px Georgia, serif`;
          ctx.shadowBlur = 20;
          ctx.shadowColor = rgba(color, 0.8);
          ctx.fillStyle = rgba(color, particle.alpha);
          ctx.save();
          ctx.translate(x, y);
          ctx.rotate(orbit + Math.sin(t + index) * 0.25);
          ctx.fillText(particle.suit, 0, 0);
          ctx.restore();
        });

        ctx.restore();
      }

      function drawChromaticBands(palette, t) {
        ctx.save();
        ctx.globalCompositeOperation = "screen";

        const bandCount = 6;
        for (let i = 0; i < bandCount; i++) {
          const y = ((i / bandCount) * height + t * (14 + i * 2)) % (height + 140) - 70;
          const gradient = ctx.createLinearGradient(0, y - 50, width, y + 50);
          gradient.addColorStop(0, rgba(palette.a, 0));
          gradient.addColorStop(0.45, rgba(i % 2 ? palette.b : palette.a, 0.025));
          gradient.addColorStop(0.55, rgba(i % 2 ? palette.c : palette.hot, 0.038));
          gradient.addColorStop(1, rgba(palette.b, 0));
          ctx.fillStyle = gradient;
          ctx.fillRect(0, y - 70, width, 140);
        }

        ctx.restore();
      }

      function drawNoise() {
        const amount = Math.max(100, Math.floor((width * height) / 9000));
        ctx.save();
        for (let i = 0; i < amount; i++) {
          const alpha = Math.random() * 0.095;
          ctx.fillStyle = `rgba(255,255,255,${alpha})`;
          ctx.fillRect(Math.random() * width, Math.random() * height, 1, 1);
        }
        ctx.restore();
      }

      function draw(now) {
        const delta = Math.min((now - last) / 1000, 0.05);
        last = now;

        pointerX += (targetX - pointerX) * 0.055;
        pointerY += (targetY - pointerY) * 0.055;

        if (!paused) time += delta;

        const palette = palettes[paletteIndex];

        ctx.fillStyle = palette.dark;
        ctx.fillRect(0, 0, width, height);

        const wash = ctx.createLinearGradient(0, 0, width, height);
        wash.addColorStop(0, rgba(palette.a, 0.12));
        wash.addColorStop(0.48, rgba(palette.dark, 0));
        wash.addColorStop(1, rgba(palette.b, 0.12));
        ctx.fillStyle = wash;
        ctx.fillRect(0, 0, width, height);

        drawGlowOrbits(palette, time);
        drawChecker(palette, time);
        drawChromaticBands(palette, time);
        drawSuitParticles(palette, time);
        drawNoise();

        requestAnimationFrame(draw);
      }

      addEventListener("resize", resize, { passive: true });

      addEventListener("pointermove", (event) => {
        targetX = (event.clientX / Math.max(width, 1) - 0.5) * 2;
        targetY = (event.clientY / Math.max(height, 1) - 0.5) * 2;

        card.style.setProperty("--ry", `${targetX * 3.8}deg`);
        card.style.setProperty("--rx", `${targetY * -3.2}deg`);
      }, { passive: true });

      addEventListener("pointerleave", () => {
        targetX = 0;
        targetY = 0;
        card.style.setProperty("--ry", "0deg");
        card.style.setProperty("--rx", "0deg");
      });

      motionButton.addEventListener("click", () => {
        paused = !paused;
        motionButton.textContent = paused ? "Resume motion" : "Pause motion";
      });

      paletteButton.addEventListener("click", () => {
        paletteIndex = (paletteIndex + 1) % palettes.length;
      });

      prefersReducedMotion.addEventListener?.("change", (event) => {
        paused = event.matches;
        motionButton.textContent = paused ? "Resume motion" : "Pause motion";
      });

      resize();
      motionButton.textContent = paused ? "Resume motion" : "Pause motion";
      requestAnimationFrame(draw);
    })();"""


@route
def index():
    return Page(
        [
            Canvas("background", aria_hidden=True),
            Main(
                [
                    Section(
                        [
                            Div(
                                Span(classes="pip"),
                                "Procedural background",
                                classes="eyebrow",
                            ),
                            Header("Lucky\nShift", level=1),
                            Paragraph(
                                "A dependency-free canvas animation with a warped checker field, glowing "
                                "suit particles, chromatic offsets, film grain, scanlines, and pointer parallax.",
                                Div(
                                    Button(
                                        "Pause motion",
                                        "/",
                                        id="motionButton",
                                    ),
                                    Button(
                                        "Change palette",
                                        "/",
                                        id="paletteButton",
                                    ),
                                    classes="controls",
                                ),
                                Div(
                                    Span("♥", classes="red"),
                                    Span("♠", classes="blue"),
                                    Span("♦", classes="gold"),
                                    Span("♣", classes="violet"),
                                    classes="suits",
                                    aria_hidden=True,
                                ),
                            ),
                        ],
                        classes="card",
                        id="card",
                    ),
                ],
                classes="shell",
            ),
        ],
        js=JS,
    )


start_server()
