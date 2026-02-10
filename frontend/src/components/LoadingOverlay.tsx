import { useState } from 'react';

function BubblingBeaker() {
  return (
    <svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <style>{`
        @keyframes bubble {
          0% { opacity: 0.8; transform: translateY(0); }
          100% { opacity: 0; transform: translateY(-30px); }
        }
        .bubble1 { animation: bubble 1.4s ease-out infinite; }
        .bubble2 { animation: bubble 1.4s ease-out 0.3s infinite; }
        .bubble3 { animation: bubble 1.4s ease-out 0.7s infinite; }
        .bubble4 { animation: bubble 1.4s ease-out 1.0s infinite; }
      `}</style>
      {/* Beaker body */}
      <path d="M40 30 L40 85 Q40 95 50 95 L70 95 Q80 95 80 85 L80 30" fill="none" stroke="#6366f1" strokeWidth="3" strokeLinecap="round" />
      {/* Beaker rim */}
      <line x1="34" y1="30" x2="46" y2="30" stroke="#6366f1" strokeWidth="3" strokeLinecap="round" />
      <line x1="74" y1="30" x2="86" y2="30" stroke="#6366f1" strokeWidth="3" strokeLinecap="round" />
      {/* Liquid */}
      <path d="M42 65 Q60 58 78 65 L78 85 Q78 93 70 93 L50 93 Q42 93 42 85 Z" fill="#a5b4fc" opacity="0.5" />
      {/* Bubbles */}
      <circle className="bubble1" cx="55" cy="80" r="3" fill="#818cf8" />
      <circle className="bubble2" cx="65" cy="75" r="2.5" fill="#818cf8" />
      <circle className="bubble3" cx="52" cy="72" r="2" fill="#818cf8" />
      <circle className="bubble4" cx="68" cy="82" r="3.5" fill="#818cf8" />
    </svg>
  );
}

function SpinningDNA() {
  return (
    <svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <style>{`
        @keyframes spin-dna { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .dna-spin { animation: spin-dna 3s linear infinite; transform-origin: 60px 60px; }
      `}</style>
      <g className="dna-spin">
        {/* Left strand */}
        <path d="M35 15 Q60 35 35 55 Q60 75 35 95 Q60 115 35 135" fill="none" stroke="#6366f1" strokeWidth="3" />
        {/* Right strand */}
        <path d="M85 15 Q60 35 85 55 Q60 75 85 95 Q60 115 85 135" fill="none" stroke="#a78bfa" strokeWidth="3" />
        {/* Rungs */}
        <line x1="47" y1="25" x2="73" y2="25" stroke="#c4b5fd" strokeWidth="2" />
        <line x1="38" y1="40" x2="82" y2="40" stroke="#c4b5fd" strokeWidth="2" />
        <line x1="47" y1="55" x2="73" y2="55" stroke="#c4b5fd" strokeWidth="2" />
        <line x1="38" y1="70" x2="82" y2="70" stroke="#c4b5fd" strokeWidth="2" />
        <line x1="47" y1="85" x2="73" y2="85" stroke="#c4b5fd" strokeWidth="2" />
        <line x1="38" y1="100" x2="82" y2="100" stroke="#c4b5fd" strokeWidth="2" />
      </g>
    </svg>
  );
}

function BacteriaPetriDish() {
  return (
    <svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <style>{`
        @keyframes grow1 { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.3); } }
        @keyframes grow2 { 0%, 100% { transform: scale(1.2); } 50% { transform: scale(0.8); } }
        @keyframes grow3 { 0%, 100% { transform: scale(0.9); } 50% { transform: scale(1.25); } }
        .bact1 { animation: grow1 2s ease-in-out infinite; transform-origin: 50px 55px; }
        .bact2 { animation: grow2 2.3s ease-in-out infinite; transform-origin: 72px 48px; }
        .bact3 { animation: grow3 1.8s ease-in-out infinite; transform-origin: 58px 72px; }
        .bact4 { animation: grow1 2.5s ease-in-out 0.5s infinite; transform-origin: 42px 68px; }
        .bact5 { animation: grow2 2.1s ease-in-out 0.3s infinite; transform-origin: 68px 65px; }
      `}</style>
      {/* Dish */}
      <ellipse cx="60" cy="62" rx="42" ry="38" fill="#f0fdf4" stroke="#86efac" strokeWidth="2.5" />
      <ellipse cx="60" cy="62" rx="36" ry="32" fill="none" stroke="#bbf7d0" strokeWidth="1" />
      {/* Bacteria blobs */}
      <ellipse className="bact1" cx="50" cy="55" rx="6" ry="4" fill="#4ade80" opacity="0.7" />
      <ellipse className="bact2" cx="72" cy="48" rx="5" ry="3.5" fill="#22c55e" opacity="0.6" transform="rotate(30 72 48)" />
      <ellipse className="bact3" cx="58" cy="72" rx="7" ry="4" fill="#86efac" opacity="0.7" transform="rotate(-20 58 72)" />
      <ellipse className="bact4" cx="42" cy="68" rx="4" ry="3" fill="#4ade80" opacity="0.5" transform="rotate(45 42 68)" />
      <ellipse className="bact5" cx="68" cy="65" rx="5" ry="3" fill="#22c55e" opacity="0.6" transform="rotate(-40 68 65)" />
    </svg>
  );
}

function MassSpecLines() {
  return (
    <svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <style>{`
        @keyframes scroll-left {
          0% { transform: translateX(0); }
          100% { transform: translateX(-60px); }
        }
        .spec-scroll { animation: scroll-left 3s linear infinite; }
      `}</style>
      {/* Baseline */}
      <line x1="10" y1="95" x2="110" y2="95" stroke="#cbd5e1" strokeWidth="1.5" />
      {/* Scrolling peaks — duplicated for seamless loop */}
      <g clipPath="url(#spec-clip)">
        <g className="spec-scroll">
          <polyline points="0,95 8,95 10,60 12,95 25,95 27,35 29,95 40,95 42,75 44,95 55,95 57,20 59,95 60,95 68,95 70,60 72,95 85,95 87,35 89,95 100,95 102,75 104,95 115,95 117,20 119,95" fill="none" stroke="#6366f1" strokeWidth="2" />
        </g>
      </g>
      <defs>
        <clipPath id="spec-clip">
          <rect x="10" y="10" width="100" height="90" />
        </clipPath>
      </defs>
      {/* Axis labels */}
      <text x="60" y="112" textAnchor="middle" fontSize="8" fill="#94a3b8">m/z</text>
    </svg>
  );
}

function ChromatographyPeaks() {
  return (
    <svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <style>{`
        @keyframes pulse1 { 0%, 100% { transform: scaleY(1); } 50% { transform: scaleY(1.3); } }
        @keyframes pulse2 { 0%, 100% { transform: scaleY(1.2); } 50% { transform: scaleY(0.7); } }
        @keyframes pulse3 { 0%, 100% { transform: scaleY(0.8); } 50% { transform: scaleY(1.2); } }
        .peak1 { animation: pulse1 1.6s ease-in-out infinite; transform-origin: 30px 95px; }
        .peak2 { animation: pulse2 2.0s ease-in-out infinite; transform-origin: 55px 95px; }
        .peak3 { animation: pulse3 1.8s ease-in-out 0.4s infinite; transform-origin: 80px 95px; }
        .peak4 { animation: pulse1 2.2s ease-in-out 0.6s infinite; transform-origin: 100px 95px; }
      `}</style>
      {/* Baseline */}
      <line x1="10" y1="95" x2="115" y2="95" stroke="#cbd5e1" strokeWidth="1.5" />
      <line x1="15" y1="100" x2="15" y2="20" stroke="#cbd5e1" strokeWidth="1.5" />
      {/* Peaks as filled curves */}
      <path className="peak1" d="M18 95 Q24 90 27 50 Q30 25 33 50 Q36 90 42 95 Z" fill="#818cf8" opacity="0.6" />
      <path className="peak2" d="M43 95 Q48 85 52 40 Q55 15 58 40 Q62 85 67 95 Z" fill="#6366f1" opacity="0.5" />
      <path className="peak3" d="M68 95 Q73 80 77 55 Q80 35 83 55 Q87 80 92 95 Z" fill="#a78bfa" opacity="0.6" />
      <path className="peak4" d="M93 95 Q96 85 98 60 Q100 45 102 60 Q104 85 107 95 Z" fill="#818cf8" opacity="0.5" />
      {/* Axis label */}
      <text x="65" y="112" textAnchor="middle" fontSize="8" fill="#94a3b8">retention time</text>
    </svg>
  );
}

const animations = [BubblingBeaker, SpinningDNA, BacteriaPetriDish, MassSpecLines, ChromatographyPeaks];

export function LoadingOverlay() {
  const [Animation] = useState(() => animations[Math.floor(Math.random() * animations.length)]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-4 bg-white rounded-2xl p-8 shadow-xl">
        <Animation />
        <p className="text-sm font-medium text-slate-600 animate-pulse">Analyzing...</p>
      </div>
    </div>
  );
}
