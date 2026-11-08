// FAQ matcher for the browser: the same method as faq_bot.py
// (TF-IDF on words + 3-4 letter chunks, cosine similarity, confidence threshold).
(function (root) {
  const STOP = new Set(("a about above after again against all am an and any are as at be because been before being below between both but by " +
    "can could did do does doing down during each few for from further had has have having he her here hers herself him himself his i if in into is it its " +
    "itself just me more most my myself nor of off on once only or other our ours ourselves out over own same she should so some such than that the their " +
    "theirs them themselves then there these they this those through to too under until up very was we were what which while whom why will with would you " +
    "your yours yourself yourselves also get got may might must shall us hai hy hain kya kia ka ki ke ko se mein main kab kaun kon kaise kitni kitne kitna " +
    "tell want know please pls").split(" "));
  const KEEP = new Set(["no", "not", "online", "where", "when", "how", "who"]);

  function clean(t) {
    const w = (t.toLowerCase().match(/[a-z0-9]+/g) || []).filter(x => !STOP.has(x) || KEEP.has(x));
    return w.length ? w.join(" ") : t.toLowerCase();
  }
  function wordGrams(t) {
    const w = t.match(/[a-z0-9]{2,}/g) || [], out = [...w];
    for (let i = 0; i + 1 < w.length; i++) out.push(w[i] + " " + w[i + 1]);
    return out;
  }
  function charGrams(t) {
    const out = [];
    for (const w of t.split(/\s+/).filter(Boolean)) {
      const p = " " + w + " ";
      for (const n of [3, 4]) for (let i = 0; i + n <= p.length; i++) out.push(p.slice(i, i + n));
    }
    return out;
  }
  function Tfidf(docs, grams) {
    const df = new Map(), n = docs.length, toks = docs.map(grams);
    toks.forEach(ts => new Set(ts).forEach(g => df.set(g, (df.get(g) || 0) + 1)));
    const idf = g => Math.log((1 + n) / (1 + (df.get(g) || 0))) + 1;
    const vec = ts => {
      const tf = new Map(); ts.forEach(g => { if (df.has(g)) tf.set(g, (tf.get(g) || 0) + 1); });
      const v = new Map(); let norm = 0;
      tf.forEach((c, g) => { const x = (1 + Math.log(c)) * idf(g); v.set(g, x); norm += x * x; });
      norm = Math.sqrt(norm) || 1; v.forEach((x, g) => v.set(g, x / norm)); return v;
    };
    const mat = toks.map(vec);
    return { mat, query: t => vec(grams(t)) };
  }
  const dot = (a, b) => { let s = 0; a.forEach((x, g) => { const y = b.get(g); if (y) s += x * y; }); return s; };

  function FAQBot(data, threshold = 0.35) {
    const texts = [], ans = [], qs = [];
    for (const it of data.faqs.concat(data.smalltalk || [])) for (const t of [it.q].concat(it.alt || [])) { texts.push(clean(t)); ans.push(it.a); qs.push(it.q); }
    const W = Tfidf(texts, wordGrams), C = Tfidf(texts, charGrams);
    this.ask = function (question) {
      if (!question.trim()) return { answer: data.greeting, matched: null, confidence: 1 };
      const q = clean(question), wq = W.query(q), cq = C.query(q);
      let best = -1, bs = -1;
      for (let i = 0; i < texts.length; i++) { const s = 0.5 * dot(wq, W.mat[i]) + 0.5 * dot(cq, C.mat[i]); if (s > bs) { bs = s; best = i; } }
      return bs < threshold ? { answer: data.fallback, matched: null, confidence: bs } : { answer: ans[best], matched: qs[best], confidence: bs };
    };
  }
  root.FAQBot = FAQBot;
  if (typeof module !== "undefined") module.exports = { FAQBot };
})(typeof window !== "undefined" ? window : globalThis);
