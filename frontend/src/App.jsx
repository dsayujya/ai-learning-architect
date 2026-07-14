import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import GraphMap from './GraphMap';

export default function App() {
  const navigate = useNavigate();
  const [goal, setGoal] = useState('');
  const [skills, setSkills] = useState('');
  const [roadmap, setRoadmap] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateRoadmap = async () => {
    setLoading(true);
    setError('');

    // AbortController with 120-second timeout for the ML pipeline
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    try {
      const skillsArray = skills.split(',').map(s => s.trim()).filter(s => s);
      const res = await fetch('http://localhost:8000/generate_roadmap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          goal: goal || 'I want to learn high frequency trading',
          current_skills: skillsArray
        })
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        const detail = await res.text().catch(() => '');
        throw new Error(
          `Server error (${res.status})${detail ? ': ' + detail : ''}`
        );
      }

      const data = await res.json();
      if (!data.roadmap || data.roadmap.length === 0) {
        throw new Error('No learning path found for this goal. Try a different query.');
      }
      setRoadmap(data.roadmap);
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request timed out — the server may be busy. Please try again.');
      } else if (err.message === 'Failed to fetch') {
        setError(
          'Cannot connect to the backend server. Make sure the server is running on port 8000.'
        );
      } else {
        setError(err.message);
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* ── Back to Landing nav ── */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        height: '2.75rem',
        background: 'rgba(10,10,15,0.85)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        display: 'flex', alignItems: 'center', padding: '0 1.5rem', gap: '1rem'
      }}>
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#d2bbff', fontSize: '0.8rem', fontFamily: 'Inter, sans-serif',
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.25rem 0.6rem', borderRadius: '0.4rem',
            transition: 'background 0.2s ease',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'rgba(124,58,237,0.15)'}
          onMouseLeave={e => e.currentTarget.style.background = 'none'}
        >
          ← Back to Home
        </button>
        <span style={{ color: '#4a4455', fontSize: '0.75rem' }}>|</span>
        <span style={{ color: '#958da1', fontSize: '0.8rem', fontFamily: 'Geist, monospace' }}>AI Learning Architect · v2.0</span>
      </div>
      <div className="sidebar">
        <div className="header">
          <h1>Learning Architect 101</h1>
        </div>

        <div className="input-group">
          <label>Career Goal:</label>
          <input
            type="text"
            placeholder="e.g. I want to learn web development"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
          />
        </div>

        <div className="input-group">
          <label>Current Skills (comma separated):</label>
          <input
            type="text"
            placeholder="e.g. HTML, CSS"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
          />
        </div>

        <button onClick={generateRoadmap} disabled={loading}>
          {loading ? 'Generating...' : 'Generate Roadmap'}
        </button>

        {loading && (
          <div style={{
            color: '#94a3b8',
            fontSize: '0.85rem',
            marginTop: '0.5rem',
            fontStyle: 'italic'
          }}>
            Running ML pipeline — this may take 30-60 seconds...
          </div>
        )}

        {error && (
          <div style={{
            color: '#ef4444',
            fontSize: '0.9rem',
            marginTop: '0.5rem',
            padding: '0.5rem 0.75rem',
            background: 'rgba(239, 68, 68, 0.1)',
            borderRadius: '6px',
            border: '1px solid rgba(239, 68, 68, 0.2)'
          }}>
            {error}
          </div>
        )}
      </div>

      <div className="canvas-area">
        {roadmap.length > 0 ? (
          <GraphMap roadmap={roadmap} />
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', opacity: 0.5, marginTop: '20%' }}>
            Set your goals and generate your custom learning path to see it mapped here.
          </div>
        )}
      </div>
    </div>
  );
}
