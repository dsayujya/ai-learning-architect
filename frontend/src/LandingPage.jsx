import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();

  // Scroll reveal via Intersection Observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('lp-active');
            obs.unobserve(entry.target);
          }
        });
      },
      { root: null, rootMargin: '0px', threshold: 0.1 }
    );
    document.querySelectorAll('.lp-reveal-up').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <>
      {/* ── Scoped styles ── */}
      <style>{`
        /* ── Reset / base ── */
        .lp-root {
          font-family: 'Inter', sans-serif;
          background-color: #0a0a0f;
          color: #e4e1e9;
          min-height: 100vh;
          overflow-x: hidden;
        }

        /* ── Glass card ── */
        .lp-glass {
          background: rgba(22, 22, 30, 0.7);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 1rem;
          transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
          will-change: transform, box-shadow, border-color;
        }
        .lp-glass:hover {
          transform: translateY(-6px);
          box-shadow: 0 20px 40px rgba(124, 58, 237, 0.4);
          border-color: rgba(124, 58, 237, 0.5);
        }

        /* ── Primary button ── */
        .lp-btn {
          background: linear-gradient(to right, #7c3aed, #a855f7);
          color: #fff;
          border: none;
          cursor: pointer;
          border-radius: 0.5rem;
          padding: 1rem 2rem;
          font-size: 1rem;
          font-weight: 600;
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          box-shadow: 0 0 30px rgba(124, 58, 237, 0.3);
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          will-change: transform, box-shadow;
          position: relative;
          overflow: hidden;
          text-decoration: none;
        }
        .lp-btn::after {
          content: '';
          position: absolute;
          inset: 0;
          border-radius: inherit;
          box-shadow: 0 0 20px rgba(124, 58, 237, 0.8);
          opacity: 0;
          transition: opacity 0.3s ease;
        }
        .lp-btn:hover { transform: scale(1.04); }
        .lp-btn:hover::after { animation: lp-pulse-glow 1.5s infinite; }

        /* ── Nav link underline ── */
        .lp-nav-link {
          position: relative;
          text-decoration: none;
          color: rgba(204,195,216,0.8);
          font-size: 0.95rem;
          transition: color 0.3s ease;
        }
        .lp-nav-link:hover { color: #d2bbff; }
        .lp-nav-link::after {
          content: '';
          position: absolute;
          width: 100%;
          transform: scaleX(0);
          height: 2px;
          bottom: -2px;
          left: 0;
          background-color: #d2bbff;
          transform-origin: bottom right;
          transition: transform 0.3s ease-out;
        }
        .lp-nav-link:hover::after {
          transform: scaleX(1);
          transform-origin: bottom left;
        }

        /* ── Badge / tag ── */
        .lp-badge {
          background: rgba(124, 58, 237, 0.1);
          border: 1px solid rgba(124, 58, 237, 0.3);
          border-radius: 9999px;
          padding: 0.35rem 0.9rem;
          font-size: 0.75rem;
          font-weight: 500;
          letter-spacing: 0.05em;
          text-transform: uppercase;
          color: #d2bbff;
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          transition: background 0.3s ease, transform 0.3s ease;
          will-change: transform, background-color;
        }
        .lp-badge:hover {
          background: rgba(124, 58, 237, 0.25);
          transform: scale(1.05);
        }

        /* ── Pipeline step card ── */
        .lp-pipe-card {
          background: rgba(22, 22, 30, 0.7);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 0.75rem;
          padding: 1.25rem 1.5rem;
          transition: border-color 0.3s ease, box-shadow 0.3s ease;
          will-change: border-color, box-shadow;
          text-align: center;
          min-width: 120px;
        }
        .lp-pipe-card:hover {
          border-color: rgba(124, 58, 237, 0.5);
          box-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
        }

        /* ── Scroll reveal ── */
        .lp-reveal-up {
          opacity: 0;
          transform: translateY(30px);
          transition: opacity 0.6s ease-out, transform 0.6s ease-out;
          will-change: opacity, transform;
        }
        .lp-reveal-up.lp-active {
          opacity: 1;
          transform: translateY(0);
        }

        /* ── Hero entrance ── */
        .lp-hero-reveal {
          opacity: 0;
          transform: translateY(20px);
          animation: lp-hero-in 0.8s ease-out forwards;
          will-change: opacity, transform;
        }
        @keyframes lp-hero-in {
          to { opacity: 1; transform: translateY(0); }
        }

        /* ── Hero radial pulse ── */
        .lp-hero-pulse {
          position: absolute;
          top: 50%; left: 50%;
          transform: translate(-50%, -50%);
          width: 120%; height: 120%;
          background: radial-gradient(circle, rgba(124,58,237,0.08) 0%, rgba(0,0,0,0) 70%);
          animation: lp-soft-pulse 4s ease-in-out infinite alternate;
          z-index: 0;
          pointer-events: none;
        }
        @keyframes lp-soft-pulse {
          from { opacity: 0.3; }
          to   { opacity: 1; }
        }

        /* ── Neural bg drift ── */
        .lp-bg-drift {
          animation: lp-drift 10s ease-in-out infinite alternate;
          will-change: transform;
        }
        @keyframes lp-drift {
          0%   { transform: translate(0, 0); }
          50%  { transform: translate(10px, -15px); }
          100% { transform: translate(-8px, 10px); }
        }

        /* ── Button pulse glow ── */
        @keyframes lp-pulse-glow {
          0%, 100% { opacity: 0.6; }
          50%       { opacity: 1; }
        }

        /* ── Icon circle ── */
        .lp-icon-circle {
          width: 3rem; height: 3rem;
          border-radius: 0.5rem;
          background: rgba(124, 58, 237, 0.15);
          display: flex; align-items: center; justify-content: center;
          color: #d2bbff;
          font-size: 1.4rem;
          transition: transform 0.3s ease;
          flex-shrink: 0;
        }
        .lp-glass:hover .lp-icon-circle { transform: scale(1.1); }

        /* ── Stack tag ── */
        .lp-stack-tag {
          background: rgba(124, 58, 237, 0.1);
          border: 1px solid rgba(124, 58, 237, 0.25);
          border-radius: 0.5rem;
          padding: 0.4rem 0.85rem;
          font-size: 0.8rem;
          font-family: 'Geist', monospace;
          color: #d2bbff;
          transition: background 0.3s ease, transform 0.3s ease;
          will-change: background, transform;
        }
        .lp-stack-tag:hover {
          background: rgba(124, 58, 237, 0.25);
          transform: scale(1.05);
        }

        /* ── Layout helpers ── */
        .lp-container { max-width: 1280px; margin: 0 auto; padding: 0 1.5rem; }
        .lp-section   { padding: 7rem 1.5rem; }

        /* ── Accessibility ── */
        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
          .lp-reveal-up, .lp-hero-reveal { opacity: 1 !important; transform: none !important; }
        }
      `}</style>

      <div className="lp-root">

        {/* ── Nav ── */}
        <nav style={{
          position: 'fixed', top: 0, width: '100%', zIndex: 50,
          background: 'rgba(19,19,24,0.7)', backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 0 30px rgba(124,58,237,0.08)'
        }}>
          <div className="lp-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '5rem' }}>
            <span style={{ fontSize: '1.5rem', fontWeight: 700, color: '#d2bbff', letterSpacing: '-0.04em', cursor: 'default' }}>
              Architect
            </span>
            <ul style={{ display: 'flex', gap: '2rem', listStyle: 'none', margin: 0, padding: 0 }}>
              <li><a className="lp-nav-link" href="#capabilities">Capabilities</a></li>
              <li><a className="lp-nav-link" href="#methodology">Methodology</a></li>
              <li><a className="lp-nav-link" href="#stack">Stack</a></li>
            </ul>
            <button className="lp-btn" style={{ padding: '0.6rem 1.4rem', fontSize: '0.8rem' }} onClick={() => navigate('/app')}>
              Launch the App →
            </button>
          </div>
        </nav>

        <main style={{ paddingTop: '5rem' }}>

          {/* ── Hero ── */}
          <section style={{
            position: 'relative', minHeight: '92vh', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            padding: '7rem 1.5rem', overflow: 'hidden',
            background: 'radial-gradient(circle at center, rgba(124,58,237,0.12) 0%, transparent 65%)'
          }}>
            {/* drifting neural-network bg image */}
            <div className="lp-bg-drift" style={{
              position: 'absolute', inset: 0, zIndex: 0, opacity: 0.35,
              backgroundImage: `url('https://lh3.googleusercontent.com/aida-public/AB6AXuCnM3lHgUZQ46B6uC0y6RmS3xsU9t9clxWwcYy_9IuERw7tjBaeDKBm_sWy6RfmXx2eF5SoGhmENv2gwjwZpTgdHjx0HHPPtzydFrMp6GOHa3Kt2fAKnGXUF9LhZlcsDLmPupl8IRVDxAvNQzfMWMOwgQF7kM8RVtM998DLlFrQ5NcKcVNuSogNQQ1VARCv6qxNRzP5Lm1FAtcolpshBifxtZEQDWCT6pAi4qo7WLTCrWaAQ_D6BThA46EN28_6xpMfHmK_eCIo0Y00')`,
              backgroundSize: 'cover', backgroundPosition: 'center',
              pointerEvents: 'none'
            }} />

            <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: '56rem', margin: '0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem' }}>
              <div className="lp-hero-pulse" />

              <div className="lp-hero-reveal lp-badge" style={{ animationDelay: '0.1s' }}>
                <span style={{ fontSize: '1rem' }}>✦</span>
                Powered by 5 ML Models · Running Locally
              </div>

              <h1 className="lp-hero-reveal" style={{
                animationDelay: '0.2s',
                fontSize: 'clamp(2.5rem, 6vw, 4rem)',
                fontWeight: 700,
                lineHeight: 1.1,
                letterSpacing: '-0.04em',
                marginBottom: '0.5rem'
              }}>
                Your{' '}
                <span style={{ background: 'linear-gradient(to right, #d2bbff, #a855f7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
                  AI-Powered
                </span>
                <br />Learning Roadmap Generator
              </h1>

              <p className="lp-hero-reveal" style={{
                animationDelay: '0.3s',
                fontSize: '1.125rem', lineHeight: 1.7,
                color: '#ccc3d8', maxWidth: '38rem', marginBottom: '1rem'
              }}>
                Type your vague goal. Get a personalized, AI-generated learning path with embedded YouTube tutorials — powered by 5 ML models running entirely on your machine.
              </p>

              <div className="lp-hero-reveal" style={{ animationDelay: '0.4s' }}>
                <button className="lp-btn" onClick={() => navigate('/app')}>
                  Launch the App <span style={{ fontSize: '1.2rem' }}>→</span>
                </button>
              </div>
            </div>
          </section>

          {/* ── Capabilities ── */}
          <section className="lp-section" id="capabilities" style={{ maxWidth: '1280px', margin: '0 auto' }}>
            <div className="lp-reveal-up" style={{ textAlign: 'center', marginBottom: '4rem' }}>
              <h2 style={{ fontSize: '2rem', fontWeight: 600, letterSpacing: '-0.02em', marginBottom: '0.75rem' }}>Core Capabilities</h2>
              <p style={{ color: '#ccc3d8', fontSize: '1rem' }}>The five-model ML stack driving your personalized curriculum.</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
              {[
                { icon: '🔍', delay: '0.1s', title: 'Semantic Intent Resolution', desc: 'FAISS vector search maps vague goals to curriculum topics via cosine similarity using all-MiniLM-L6-v2 embeddings — zero keyword matching.' },
                { icon: '🗺️', delay: '0.2s', title: 'Graph Pathfinding', desc: 'NetworkX Dijkstra finds the cheapest cognitive path through prerequisite chains using |Δcomplexity| + (1 − cosine_sim) edge weights.' },
                { icon: '🧠', delay: '0.3s', title: 'GNN Sequencing', desc: 'A self-supervised 2-layer Graph Attention Network in pure PyTorch predicts node readiness and priority classification.' },
                { icon: '📹', delay: '0.4s', title: 'Cross-Encoder Video Ranking', desc: 'ms-marco-MiniLM-L-6-v2 dynamically scrapes YouTube and semantically ranks tutorials — zero hardcoded URLs, ever.', wide: true },
                { icon: '⚡', delay: '0.5s', title: 'LangGraph Orchestration', desc: 'Deterministic 4-stage StateGraph coordinates all ML models in an inspectable, typed pipeline from intent to output.' },
              ].map(({ icon, delay, title, desc, wide }) => (
                <div key={title} className="lp-glass lp-reveal-up" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '0.85rem', transitionDelay: delay, gridColumn: wide ? 'span 2' : undefined }}>
                  <div className="lp-icon-circle">{icon}</div>
                  <h3 style={{ fontWeight: 600, fontSize: '1.05rem', color: '#e4e1e9' }}>{title}</h3>
                  <p style={{ fontSize: '0.9rem', color: '#ccc3d8', lineHeight: 1.65 }}>{desc}</p>
                </div>
              ))}
            </div>
          </section>

          {/* ── How It Works / Pipeline ── */}
          <section className="lp-section" id="methodology" style={{ background: 'rgba(14,14,19,0.6)', borderTop: '1px solid rgba(255,255,255,0.05)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <div className="lp-container">
              <div className="lp-reveal-up" style={{ textAlign: 'center', marginBottom: '4rem' }}>
                <h2 style={{ fontSize: '2rem', fontWeight: 600, letterSpacing: '-0.02em', marginBottom: '0.75rem' }}>How It Works</h2>
                <p style={{ color: '#ccc3d8', fontSize: '1rem' }}>A 4-stage ML pipeline — from vague input to interactive learning graph.</p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                {[
                  { label: 'User Goal', sub: 'free text input' },
                  { label: 'FAISS Resolver', sub: 'intent → vector' },
                  { label: 'Dijkstra Navigator', sub: 'optimal path' },
                  { label: 'GNN Sequencer', sub: 'readiness scores' },
                  { label: 'CrossEncoder Ranker', sub: 'YouTube ranking' },
                  { label: 'React Flow Graph', sub: 'interactive output' },
                ].map(({ label, sub }, i, arr) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div className="lp-pipe-card lp-reveal-up" style={{ transitionDelay: `${i * 0.12}s` }}>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#e4e1e9', whiteSpace: 'nowrap' }}>{label}</div>
                      <div style={{ fontSize: '0.72rem', color: '#958da1', marginTop: '0.25rem' }}>{sub}</div>
                    </div>
                    {i < arr.length - 1 && (
                      <span style={{ color: '#7c3aed', fontSize: '1.4rem', fontWeight: 700, flexShrink: 0 }}>→</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ── Tech Stack ── */}
          <section className="lp-section" id="stack">
            <div className="lp-container">
              <div className="lp-reveal-up" style={{ textAlign: 'center', marginBottom: '4rem' }}>
                <h2 style={{ fontSize: '2rem', fontWeight: 600, letterSpacing: '-0.02em', marginBottom: '0.75rem' }}>Technology Stack</h2>
                <p style={{ color: '#ccc3d8', fontSize: '1rem' }}>Best-in-class open-source tools, stitched together with zero compromise.</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                {[
                  {
                    label: 'Backend', icon: '⚙️',
                    tags: ['Python 3', 'FastAPI', 'LangGraph', 'PyTorch', 'NetworkX', 'FAISS', 'Sentence-Transformers', 'Pydantic v2', 'Uvicorn']
                  },
                  {
                    label: 'Frontend', icon: '🎨',
                    tags: ['React 19', 'Vite', 'React Flow', 'Tailwind CSS', 'Glassmorphism UI']
                  },
                ].map(({ label, icon, tags }) => (
                  <div key={label} className="lp-glass lp-reveal-up" style={{ padding: '2rem' }}>
                    <h3 style={{ fontWeight: 600, fontSize: '1.1rem', marginBottom: '1.25rem', color: '#e4e1e9', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span>{icon}</span> {label}
                    </h3>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem' }}>
                      {tags.map(t => <span key={t} className="lp-stack-tag">{t}</span>)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ── Footer CTA ── */}
          <section style={{ padding: '6rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
            <div className="lp-reveal-up" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
              <h2 style={{ fontSize: '2rem', fontWeight: 600, letterSpacing: '-0.02em' }}>Ready to build your learning path?</h2>
              <p style={{ color: '#ccc3d8', maxWidth: '28rem', lineHeight: 1.7 }}>
                Boot the app in one click with <code style={{ background: 'rgba(124,58,237,0.15)', padding: '0.1rem 0.4rem', borderRadius: '0.25rem', fontSize: '0.9em' }}>launch.bat</code> and generate your personalized roadmap.
              </p>
              <button className="lp-btn" onClick={() => navigate('/app')}>
                Launch AI Learning Architect <span style={{ fontSize: '1.2rem' }}>→</span>
              </button>
            </div>
          </section>

        </main>

        {/* ── Footer ── */}
        <footer style={{ background: '#0e0e13', borderTop: '1px solid rgba(255,255,255,0.06)', padding: '3rem 1.5rem' }}>
          <div className="lp-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 700, color: '#d2bbff', letterSpacing: '-0.04em' }}>Architect</span>
            <div style={{ fontSize: '0.75rem', color: '#958da1', fontFamily: 'Geist, monospace' }}>
              © 2026 AI Learning Architect · Engineered for the Spark.
            </div>
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              {['Documentation', 'GitHub', 'License'].map(link => (
                <a key={link} className="lp-nav-link" href="#" style={{ fontSize: '0.8rem', color: '#958da1' }}>{link}</a>
              ))}
            </div>
          </div>
        </footer>

      </div>
    </>
  );
}
