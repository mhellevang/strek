// NN handwriting in the browser: Graves RNN (Epoch_56, ONNX single-step graph)
// + programmatic æøå — a direct port of calligraphy/nn_text2svg.py.
// Runs on onnxruntime-web (vendor/ort.wasm.min.js); needs http(s), not file://.
//
//   const synth = await loadSynthesizer();
//   const svg = toSvg(await synth.synthesize("Blåbærsyltetøy på brød"), 15);

const NC = 20; // output mixture components

// original char -> [substitute, treatment, isUpper]
const SUBSTITUTIONS = {
  "æ": ["ae", "ligature", false], "Æ": ["Ae", "ligature", true],
  "ø": ["o", "slash", false], "Ø": ["O", "slash", true],
  "å": ["a", "ring", false], "Å": ["A", "ring", true],
};

export async function loadSynthesizer(opts = {}) {
  const ort = opts.ort ?? globalThis.ort;
  const base = opts.base ?? new URL(".", import.meta.url).href;
  if (!opts.ort) ort.env.wasm.wasmPaths = base + "vendor/";
  const meta = opts.meta ?? await (await fetch(base + "meta.json")).json();
  const session = await ort.InferenceSession.create(
    opts.model ?? base + "synthesis.onnx");
  return new Synthesizer(ort, session, meta);
}

class Synthesizer {
  constructor(ort, session, meta) {
    this.ort = ort;
    this.session = session;
    this.meta = meta;
    this.alphabet = meta.charset.length + 1; // index 0 = unknown
  }

  encode(text) { // one-hot (1, U, alphabet)
    const U = text.length;
    const c = new Float32Array(U * this.alphabet);
    for (let i = 0; i < U; i++) {
      c[i * this.alphabet + this.meta.charset.indexOf(text[i]) + 1] = 1;
    }
    return new this.ort.Tensor("float32", c, [1, U, this.alphabet]);
  }

  // One full sampling run. Returns {seq: [[dx,dy,eos],...], phi: [Float32Array(U),...]}
  async sample(c, U, { bias = 0.8, stochastic = true, maxSteps = 1500 } = {}) {
    const { ort, session } = this;
    // state inputs got renamed on export (w.3, k.1, ...) — map positionally:
    // x, c, w, k, h1, c1, h2, c2, h3, c3, bias
    const [X, C, W, K, H1, C1, H2, C2, H3, C3, B] = session.inputNames;
    const st = (n) => new ort.Tensor("float32", new Float32Array(n), [1, n]);
    const feed = {
      [X]: new ort.Tensor("float32", new Float32Array(3), [1, 1, 3]),
      [C]: c,
      [W]: new ort.Tensor("float32", new Float32Array(this.alphabet), [1, 1, this.alphabet]),
      [K]: st(10),
      [H1]: st(400), [C1]: st(400), [H2]: st(400), [C2]: st(400),
      [H3]: st(400), [C3]: st(400),
      [B]: new ort.Tensor("float32", Float32Array.of(bias), [1]),
    };
    const seq = [], phis = [];
    for (let t = 0; t < maxSteps; t++) {
      const o = await session.run(feed);
      const pi = o.pi.data, mu = o.mu.data, sd = o.sd.data, ro = o.ro.data;
      const eos = o.eos.data[0], phi = o.phi.data;

      const comp = stochastic ? multinomial(pi) : argmax(pi);
      let x = mu[comp], y = mu[comp + NC];
      if (stochastic) {
        // bivariate normal via Cholesky: y correlated with x by ro
        const z1 = gauss(), z2 = gauss(), r = ro[comp];
        x += sd[comp] * z1;
        y += sd[comp + NC] * (r * z1 + Math.sqrt(1 - r * r) * z2);
      }
      const eosFlag = eos > 0.5 ? 1 : 0;
      phis.push(Float32Array.from(phi));

      // stop when attention parks on the trailing sentinel (models.py _is_end_of_string)
      if (phi[U - 1] > 0.8 || (argmax(phi) === U - 1 && eosFlag)) {
        seq.push([x, y, 1]);
        break;
      }
      seq.push([x, y, eosFlag]);

      feed[X] = new ort.Tensor("float32", Float32Array.of(x, y, eosFlag), [1, 1, 3]);
      feed[W] = o.w; feed[K] = o.k;
      feed[H1] = o.h1; feed[C1] = o.c1; feed[H2] = o.h2; feed[C2] = o.c2;
      feed[H3] = o.h3; feed[C3] = o.c3;
    }
    return { seq, phi: phis };
  }

  // text (æøå ok) -> polylines [[x,y],...][] in model units, diacritics drawn in.
  async synthesize(text, opts = {}) {
    const { modelText, targets } = substitute(text, this.meta.charset);
    const c = this.encode(modelText + " "); // sentinel, as in visualize_attention
    const U = modelText.length + 1;

    let seq, phi;
    for (let attempt = 0; attempt < 5; attempt++) {
      ({ seq, phi } = await this.sample(c, U, opts));
      const skipped = skippedChars(modelText, phi);
      if (!skipped.length) break;
      console.warn(`attention skipped ${skipped}, resampling (${attempt + 1}/5)`);
    }

    const [muX, muY] = this.meta.mu, [sdX, sdY] = this.meta.std;
    const xs = [], ys = [], eos = [];
    let ax = 0, ay = 0;
    for (const [dx, dy, e] of seq) {
      ax += dx * sdX + muX;
      ay += dy * sdY + muY;
      xs.push(ax); ys.push(ay); eos.push(e);
    }

    // ligature squeezes mutate xs, so run them (in temporal order) before
    // measuring diacritic geometry or building stroke polylines
    for (const [ci, kind] of targets) {
      if (kind === "ligature") squeezeLigature(xs, ys, phi, ci);
    }
    const polylines = strokes(xs, ys, eos);
    for (const [ci, kind, upper] of targets) {
      if (kind === "ring") polylines.push(ringPoints(...centerRadius(xs, ys, phi, ci), upper));
      else if (kind === "slash") polylines.push(slashPoints(...centerRadius(xs, ys, phi, ci)));
    }
    return polylines;
  }
}

function substitute(text, charset) {
  let modelText = "";
  const targets = [];
  for (const ch of text) {
    const sub = SUBSTITUTIONS[ch];
    if (sub) {
      targets.push([modelText.length, sub[1], sub[2]]);
      modelText += sub[0];
    } else if (charset.includes(ch)) {
      modelText += ch;
    } else {
      console.warn(`'${ch}' not in model charset, dropped`);
    }
  }
  return { modelText, targets };
}

const argmax = (a) => a.reduce((m, v, i) => (v > a[m] ? i : m), 0);

function multinomial(pi) {
  let r = Math.random();
  for (let i = 0; i < pi.length; i++) if ((r -= pi[i]) <= 0) return i;
  return pi.length - 1;
}

function gauss() { // Box-Muller
  const u = 1 - Math.random(), v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function skippedChars(modelText, phi) {
  const peaks = new Set(phi.map(argmax));
  return [...modelText].filter((ch, i) => ch !== " " && !peaks.has(i));
}

// timesteps whose stroke points the model attributes to one character
function charIndices(phi, ci) {
  let idx = phi.flatMap((p, t) => (argmax(p) === ci ? [t] : []));
  if (idx.length < 2) { // attention never peaked there; fall back to soft weights
    const mx = Math.max(...phi.map((p) => p[ci]));
    idx = phi.flatMap((p, t) => (p[ci] > mx * 0.5 ? [t] : []));
  }
  return idx;
}

// median centre + MAD radius — robust to attention smearing onto tall neighbours
function centerRadius(xs, ys, phi, ci) {
  const idx = charIndices(phi, ci);
  const med = (v) => v.sort((a, b) => a - b)[v.length >> 1];
  const cx = med(idx.map((i) => xs[i])), cy = med(idx.map((i) => ys[i]));
  const dev = idx.map((i) => Math.abs(xs[i] - cx)).concat(idx.map((i) => Math.abs(ys[i] - cy)));
  return [cx, cy, 1.4 * med(dev)]; // median |offset| of a circle ≈ 0.7 r
}

// pull the letter after ci leftward so 'ae' fuses into an æ ligature.
// cursive strokes connect the letters, so there is no whitespace gap to
// close — aim for a target distance between the letter *centres* instead
function squeezeLigature(xs, ys, phi, ci) {
  const eIdx = charIndices(phi, ci + 1);
  if (!eIdx.length) return;
  const [aCx, , aR] = centerRadius(xs, ys, phi, ci);
  const [eCx, , eR] = centerRadius(xs, ys, phi, ci + 1);
  const delta = (eCx - aCx) - 0.6 * (aR + eR);
  if (delta <= 0) return;
  const t0 = Math.min(...eIdx), ramp = 6;
  for (let t = Math.max(0, t0 - ramp); t < xs.length; t++) {
    xs[t] -= delta * Math.min(1, (t - t0 + ramp) / ramp);
  }
}

const rnd = (a, b) => a + Math.random() * (b - a);

// hand-drawn-ish ring: wobbly radius, random start, slight overshoot.
// rc is the letter-body radius; the MAD estimate runs low on a capital's
// full height, so its gap ratio compensates.
function ringPoints(cx, cy, rc, upper = false, n = 24) {
  const r = (upper ? 0.4 : 0.55) * rc;
  cx += rnd(-0.08, 0.08) * rc;
  cy = cy - rc - (upper ? 1.0 : 0.6) * rc - r; // above the body (smaller y = up)
  const start = rnd(0, 2 * Math.PI), sweep = 2 * Math.PI * rnd(1.02, 1.12);
  const wPhase = rnd(0, 2 * Math.PI);
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const a = start + (sweep * i) / n;
    const ri = r * (1 + 0.07 * Math.sin(2 * a + wPhase) + rnd(-0.02, 0.02));
    pts.push([cx + ri * Math.cos(a), cy + ri * Math.sin(a)]);
  }
  return pts;
}

// hand-drawn-ish slash through the o: slightly bowed, jittered endpoints
function slashPoints(cx, cy, r) {
  const dx = 0.8 * r, dy = 1.35 * r, j = 0.12 * r; // lower-left to upper-right
  const p0 = [cx - dx + rnd(-j, j), cy + dy + rnd(-j, j)];
  const p1 = [cx + dx + rnd(-j, j), cy - dy + rnd(-j, j)];
  const bow = rnd(-0.06, 0.06) * Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
  const nx = -(p1[1] - p0[1]), ny = p1[0] - p0[0], nlen = Math.hypot(nx, ny);
  return [0, 0.35, 0.7, 1].map((t) => {
    const b = bow * Math.sin(Math.PI * t);
    return [p0[0] + (p1[0] - p0[0]) * t + (nx / nlen) * b,
            p0[1] + (p1[1] - p0[1]) * t + (ny / nlen) * b];
  });
}

function strokes(xs, ys, eos) {
  const out = [];
  let stroke = [];
  for (let i = 0; i < xs.length; i++) {
    stroke.push([xs[i], ys[i]]);
    if (eos[i] === 1) { out.push(stroke); stroke = []; }
  }
  if (stroke.length) out.push(stroke);
  return out;
}

// polylines (model units) -> SVG string, mm units — same format as text2svg.py
export function toSvg(polylines, heightMm = 15, marginMm = 2) {
  const all = polylines.flat();
  const x0 = Math.min(...all.map((p) => p[0]));
  const y0 = Math.min(...all.map((p) => p[1]));
  const y1 = Math.max(...all.map((p) => p[1]));
  const scale = heightMm / (y1 - y0);
  const fmt = (v) => +v.toFixed(2);
  const mm = polylines.map((line) =>
    line.map((p) => [fmt((p[0] - x0) * scale + marginMm), fmt((p[1] - y0) * scale + marginMm)]));
  const w = fmt(Math.max(...mm.flat().map((p) => p[0])) + marginMm);
  const h = fmt(heightMm + 2 * marginMm);
  const lines = mm.map((line) =>
    `<polyline points="${line.map((p) => p.join(",")).join(" ")}"/>`);
  return `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<svg xmlns="http://www.w3.org/2000/svg" width="${w}mm" height="${h}mm" viewBox="0 0 ${w} ${h}">\n` +
    `<g fill="none" stroke="black" stroke-width="0.3" stroke-linecap="round" stroke-linejoin="round">\n` +
    lines.join("\n") + "\n</g>\n</svg>";
}
