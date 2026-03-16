import React, { useMemo, useRef, useState, useEffect } from "react";
import { Play, ArrowLeft, Search, Star, Sparkles } from "lucide-react";

const styles = `
  * { box-sizing: border-box; }

  html, body, #root {
    margin: 0;
    min-height: 100%;
    width: 100%;
    font-family: Inter, Arial, sans-serif;
    background: #071422;
    color: white;
    overflow-x: hidden;
  }

  button {
    font: inherit;
  }

  a {
    color: inherit;
  }

  .app-shell {
    min-height: 100vh;
    width: 100vw;
    background: linear-gradient(180deg, #0a1a2b 0%, #08192a 100%);
    color: white;
  }

  .top-header {
    height: 88px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    padding: 0 28px;
    width: 100%;
  }

  .brand-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
  }

  .brand-logo {
    width: 44px;
    height: 44px;
    border-radius: 999px;
    background: #d6e1f7;
    color: #6d8fb7;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    font-weight: 700;
    box-shadow: 0 8px 20px rgba(0,0,0,0.18);
    flex: 0 0 auto;
  }

  .brand {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 34px;
    line-height: 1;
    font-weight: 500;
    letter-spacing: -0.4px;
    color: #8cb3df;
    text-shadow: 0 2px 10px rgba(0,0,0,0.18);
    white-space: nowrap;
  }

  .profile-box {
    position: absolute;
    right: 28px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 19px;
    color: rgba(255,255,255,0.96);
  }

  .profile-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #f2c07a;
    color: #111;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
  }

  .main-layout {
    display: grid;
    grid-template-columns: 210px minmax(0, 1fr);
    min-height: calc(100vh - 88px);
    width: 100vw;
  }

  .sidebar {
    border-right: 1px solid rgba(255,255,255,0.12);
    padding: 18px 28px 28px 34px;
  }

  .search-label {
    display: flex;
    align-items: center;
    gap: 10px;
    color: rgba(255,255,255,0.95);
    font-size: 16px;
    margin-bottom: 92px;
  }

  .nav-list {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .nav-item {
    font-size: 22px;
    color: rgba(255,255,255,0.9);
    cursor: pointer;
    font-weight: 300;
  }

  .nav-item.active {
    font-weight: 700;
    color: white;
  }

  .content-area {
    min-width: 0;
    width: 100%;
    padding: 8px 8px 24px 12px;
    display: flex;
    align-items: flex-start;
    overflow: hidden;
  }

  .poster-row {
    width: 100%;
    display: flex;
    align-items: flex-end;
    justify-content: flex-start;
    gap: 28px;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 22px 8px 16px 8px;
    scrollbar-width: thin;
    scrollbar-color: rgba(163,178,199,0.8) rgba(255,255,255,0.08);
  }

  .poster-row::-webkit-scrollbar {
    height: 12px;
  }

  .poster-row::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.08);
    border-radius: 999px;
  }

  .poster-row::-webkit-scrollbar-thumb {
    background: rgba(163,178,199,0.8);
    border-radius: 999px;
  }

  .poster-button {
    border: none;
    background: transparent;
    padding: 0;
    cursor: pointer;
    flex: 0 0 auto;
    transition: transform 0.18s ease;
  }

  .poster-button:hover {
    transform: translateY(-5px) scale(1.02);
  }

  .poster-wrap {
    width: 200px;
  }

  .poster-title {
    font-size: 18px;
    font-weight: 300;
    color: rgba(255,255,255,0.98);
    margin-bottom: 10px;
    text-align: center;
    line-height: 1.3;
    min-height: 20px;
    letter-spacing: 0.3px;
    text-shadow: 0 20px 18px rgba(0, 0, 0, 0.9);
  }

  .poster-card {
    width: 200px;
    height: 500px;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 16px 34px rgba(0,0,0,0.4);
    background: #0f1822;
  }

  .level-0 { margin-bottom: 0px; }
  .level-1 { margin-bottom: 30px; }
  .level-2 { margin-bottom: 0px; }
  .level-3 { margin-bottom: 30px; }
  .level-4 { margin-bottom: 0px; }
  .level-5 { margin-bottom: 30px; }
  .level-6 { margin-bottom: 0px; }
  .level-7 { margin-bottom: 30px; }
  .level-8 { margin-bottom: 0px; }
  .level-9 { margin-bottom: 30px; }

  .poster-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .show-page {
    min-height: 100vh;
    background: linear-gradient(180deg, #0a1a2b 0%, #08192a 44%, #06111c 100%);
    color: white;
  }

  .hero {
    position: relative;
    min-height: 68vh;
    display: flex;
    align-items: flex-end;
    overflow: hidden;
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }

  .hero-image {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center top;
  }

  .hero-gradient {
    position: absolute;
    inset: 0;
    background: linear-gradient(
      180deg,
      rgba(8,25,42,0.1) 0%,
      rgba(8,25,42,0.35) 34%,
      rgba(8,25,42,0.78) 66%,
      #08192a 100%
    );
  }

  .hero-topbar {
    position: absolute;
    top: 26px;
    left: 32px;
    right: 32px;
    z-index: 10;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .back-btn {
    border: none;
    background: rgba(0,0,0,0.75);
    color: white;
    border-radius: 16px;
    padding: 16px 24px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    backdrop-filter: blur(8px);
    font-size: 16px;
    font-weight: 600;
    transform: translateY(-20px);
  }

  .back-btn:hover {
    background: rgba(0,0,0,0.85);
  }

  .hero-content {
    position: relative;
    z-index: 2;
    width: 100%;
    padding: 0 42px 34px 42px;
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 36px;
    align-items: end;
    background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 100%);
  }

  .hero-poster {
    width: 280px;
    height: 420px;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 24px 48px rgba(0,0,0,0.45);
    transform: translateY(30px);
  }

  .hero-poster img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .show-title {
    font-size: 54px;
    font-weight: 800;
    margin: 0 0 10px 0;
  }

  .show-meta {
    font-size: 18px;
    color: rgba(255,255,255,0.82);
    margin-bottom: 18px;
  }

  .about-text {
    max-width: 1200px;
    font-size: 18px;
    line-height: 1.7;
    color: rgba(255,255,255,0.86);
    margin-bottom: 22px;
  }

  .watch-btn {
    border: none;
    background: white;
    color: black;
    border-radius: 16px;
    padding: 14px 24px;
    font-weight: 700;
    font-size: 17px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 10px;
  }

  .video-section {
    padding: 24px 24px 40px 24px;
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .video-title {
    font-size: 28px;
    font-weight: 700;
    margin: 0 0 16px 0;
    width: min(100%, 1220px);
  }

  .video-stage {
    width: min(100%, 1220px);
    display: flex;
    justify-content: center;
  }

  .video-wrap {
    width: 100%;
    overflow: hidden;
    background: black;
    box-shadow: 0 18px 36px rgba(0,0,0,0.45);
    position: relative;
    border-radius: 12px;
  }

  .video-element {
    width: 100%;
    height: min(100vh, 760px);
    display: block;
    background: black;
    cursor: pointer;
    position: relative;
    z-index: 1;
    object-fit: contain;
  }

  .video-thumbnail-overlay {
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    z-index: 2;
    cursor: pointer;
  }

  .video-thumbnail-overlay::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.18) 0%, rgba(0,0,0,0.34) 100%);
  }

  .video-overlay-play {
    position: absolute;
    inset: 0;
    z-index: 3;
    border: none;
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }

  .video-overlay-circle {
    width: 88px;
    height: 88px;
    border-radius: 999px;
    background: rgba(0,0,0,0.62);
    border: 1px solid rgba(255,255,255,0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(6px);
  }

  .timeline-block {
    width: min(100%, 1220px);
    margin: 16px auto 0 auto;
  }

  .timeline-bar {
    position: relative;
    height: 10px;
    border-radius: 999px;
    background: rgba(255,255,255,0.16);
    overflow: hidden;
    cursor: pointer;
  }

  .timeline-highlight {
    position: absolute;
    top: 0;
    bottom: 0;
    background: rgba(255, 198, 92, 0.5);
    z-index: 1;
  }

  .timeline-progress {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    background: white;
    z-index: 2;
  }

  .player-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 18px;
    padding-top: 14px;
    flex-wrap: wrap;
  }

  .player-left {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }

  .play-btn {
    border: none;
    background: rgba(255,255,255,0.14);
    color: white;
    border-radius: 12px;
    padding: 10px 14px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
  }

  .nova-btn {
    border: none;
    background: linear-gradient(135deg, #ffb347 0%, #ff7a18 100%);
    color: white;
    border-radius: 12px;
    padding: 10px 14px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-weight: 700;
    box-shadow: 0 8px 18px rgba(255, 122, 24, 0.28);
  }

  .nova-btn:disabled {
    opacity: 0.7;
    cursor: wait;
  }

  .time-label,
  .frame-label {
    color: rgba(255,255,255,0.84);
    font-size: 14px;
  }

  .product-overlay {
    position: absolute;
    left: 24px;
    right: 24px;
    bottom: 12px;
    width: auto;
    max-width: 760px;
    z-index: 5;
    display: grid;
    grid-template-columns: 100px 1fr;
    gap: 12px;
    padding: 0px 12px;
    border-radius: 16px;
    background: rgba(7, 16, 28, 0.88);
    border: 1px solid rgba(255,255,255,0.12);
    backdrop-filter: blur(10px);
    box-shadow: 0 16px 34px rgba(0,0,0,0.4);
    cursor: pointer;
    transition: opacity 0.25s ease, transform 0.25s ease;
    transform: translateY(8px);
  }

  .product-overlay-out {
    opacity: 0;
    transform: translateY(12px);
  }

  .product-image {
    width: 100px;
    height: 100px;
    margin: 5px 0px 0px 0px;
    border-radius: 12px;
    object-fit: cover;
    display: block;
  }

  .product-body {
    min-width: 0;
  }

  .product-title {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 1px;
  }

  .product-desc {
    font-size: 14px;
    line-height: 1.45;
    color: rgba(255,255,255,0.82);
    margin-bottom: -10px;
  }

  .product-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
  }

  .product-price {
    font-size: 18px;
    font-weight: 700;
    color: #ffd27a;
  }

  .product-stars {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #ffd27a;
  }

  .product-countdown-track {
    width: 100%;
    height: 6px;
    border-radius: 999px;
    background: rgba(255,255,255,0.14);
    overflow: hidden;
  }

  .product-countdown-fill {
    height: 100%;
    background: linear-gradient(90deg, #ffd27a 0%, #ff8a5b 100%);
    transition: width 0.35s ease;
    will-change: width;
  }

  .product-note {
    margin-top: 8px;
    font-size: 12px;
    color: rgba(255,255,255,0.7);
  }

  .nova-toast {
    position: absolute;
    top: 16px;
    left: 50%;
    transform: translateX(-50%) translateY(-10px);
    z-index: 8;
    min-width: 320px;
    max-width: min(92%, 760px);
    padding: 14px 16px;
    border-radius: 16px;
    background: rgba(10, 22, 38, 0.96);
    border: 1px solid rgba(255,255,255,0.14);
    box-shadow: 0 20px 40px rgba(0,0,0,0.45);
    backdrop-filter: blur(10px);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.28s ease, transform 0.28s ease;
  }

  .nova-toast-show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
    pointer-events: auto;
  }

  .nova-toast-title {
    font-size: 14px;
    font-weight: 800;
    color: #ffbe66;
    margin-bottom: 6px;
  }

  .nova-toast-text {
    font-size: 14px;
    line-height: 1.45;
    color: rgba(255,255,255,0.9);
    margin-bottom: 8px;
  }

  .nova-toast-link {
    font-size: 14px;
    font-weight: 700;
    color: #8fc7ff;
    text-decoration: none;
    word-break: break-all;
  }

  .nova-toast-link:hover {
    text-decoration: underline;
  }

  .loading-box,
  .error-box,
  .config-box {
    width: min(100%, 900px);
    margin: 20px auto 0 auto;
    padding: 18px 20px;
    border-radius: 16px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
  }

  .error-box {
    color: #ffb4b4;
    background: rgba(255, 84, 84, 0.08);
    border-color: rgba(255, 84, 84, 0.25);
  }

  .config-box pre {
    white-space: pre-wrap;
    word-break: break-word;
    margin: 12px 0 0 0;
    padding: 14px;
    border-radius: 12px;
    background: rgba(0,0,0,0.28);
    overflow-x: auto;
  }

  @media (max-width: 900px) {
    .main-layout {
      grid-template-columns: 1fr;
    }

    .sidebar {
      display: none;
    }

    .hero-content {
      grid-template-columns: 1fr;
    }

    .hero-poster {
      width: 220px;
      height: 330px;
    }

    .show-title {
      font-size: 38px;
    }

    .product-overlay {
      grid-template-columns: 1fr;
    }

    .product-image {
      width: 100%;
      height: 180px;
    }
  }
`;

const CONFIG_EXAMPLE = `# id|videoPath|startFrame|endFrame|productImage|productTitle|productDescription|price|rating|url
suits|/videos/suits.mp4|150|320|/products/watch.jpg|Omega Seamaster|Luxury steel watch seen in the office scene.|$299.99|5|https://example.com/omega
theboys|/videos/theboys.mp4|90|240|/products/shoes.jpg|Black Sneakers|Streetwear sneakers featured in the episode.|$129.99|4|https://example.com/shoes`;

const baseShows = [
  {
    id: "theboys",
    title: "The BOYS",
    year: "2026",
    genre: "Drama",
    description: "A simple placeholder page for your TV show. Replace this text with the real summary.",
    poster:
      "https://resizing.flixster.com/mmvBo8CgJiLxvYSimsMguhNEv58=/ems.cHJkLWVtcy1hc3NldHMvdHZzZWFzb24vYWM4MWJjZjUtN2I0My00NmQwLThmZjEtOTA0NTU4OWNlOWE3LmpwZw==",
    level: 0,
  },
  {
    id: "suits",
    title: "Suits",
    year: "2011",
    genre: "Drama",
    description:
      "Before he was a lawyer, he was a fraud. Meet Mike Ross, a brilliant college dropout who accidentally lands a job at one of New York City's top law firms alongside Harvey Specter, the city's best closer. There's just one catch: Mike never went to law school.",
    poster:
      "https://resizing.flixster.com/u8-QdjD-tUZ_G9zrTr3-Z58PuYk=/ems.cHJkLWVtcy1hc3NldHMvdHZzZWFzb24vUlRUVjYyNDE5LndlYnA=",
    level: 1,
  },
  {
    id: "breaking-bad",
    title: "Breaking Bad",
    year: "2008",
    genre: "Crime",
    description:
      "Walter White, a struggling high school chemistry teacher, is diagnosed with advanced lung cancer. To secure his family's financial future, he turns to a life of crime.",
    poster: "https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p185846_b_v8_ad.jpg",
    level: 2,
  },
  {
    id: "desperate-housewives",
    title: "Desperate Housewives",
    year: "2004",
    genre: "Drama",
    description:
      "Welcome to Wisteria Lane, where the grass is green, the houses are perfect, and the secrets are deadly.",
    poster: "https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p7896059_b_v13_ab.jpg",
    level: 3,
  },
  {
    id: "fallout",
    title: "Fallout",
    year: "2024",
    genre: "Drama",
    description:
      "Based on one of the greatest video games of all time, Fallout is the story of haves and have-nots in a world in which there’s almost nothing left to have. 200 years after the apocalypse, the gentle denizens of luxury fallout shelters are forced to return to the incredibly complex, gleefully weird and highly violent universe waiting for them above.",
    poster:
      "https://resizing.flixster.com/_suBUkrhJoxiUqiRIuQncCEhJ-o=/ems.cHJkLWVtcy1hc3NldHMvdHZzZWFzb24vYWI1NDExNWMtZGJiYS00Mjg2LTk2NTYtOTJkODA0N2M2YzMxLmpwZw==",
    level: 4,
  },
  {
    id: "prison-break",
    title: "Prison Break",
    year: "2005",
    genre: "Drama",
    description:
      "A man framed for his brother's murder escapes prison and returns home to exact revenge.",
    poster: "https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p7894210_b_v8_al.jpg",
    level: 5,
  },
  {
    id: "the-walking-dead",
    title: "The Walking Dead",
    year: "2010",
    genre: "Drama",
    description:
      "A group of survivors are on a mission to find a safe and secure location after a zombie apocalypse.",
    poster:
      "https://resizing.flixster.com/Lzq-nUwBS4DCJDOoSpOVTsCdJ5E=/ems.cHJkLWVtcy1hc3NldHMvdHZzZWFzb24vUlRUVjIwMTY1MC53ZWJw",
    level: 6,
  },
  {
    id: "young-sherlock",
    title: "Young Sherlock",
    year: "2026",
    genre: "Adventure",
    description:
      "A young Sherlock Holmes and his friend Dr. Watson solve crimes in 19th-century London.",
    poster:
      "https://resizing.flixster.com/6KYdhwSCt5lyHfNgMA4RZX-vPTU=/ems.cHJkLWVtcy1hc3NldHMvdHZzZXJpZXMvZGI2YmU1M2QtYmIyNS00ZTJhLTk4NmItYTBiMDgyMTE1NTUzLmpwZw==",
    level: 7,
  },
  {
    id: "game-of-thrones",
    title: "Game of Thrones",
    year: "2026",
    genre: "Mystery",
    description:
      "Epic fantasy drama about noble families fighting for control of the Iron Throne.",
    poster: "https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p12502846_b_v8_aa.jpg",
    level: 8,
  },
  {
    id: "big-bang-theory",
    title: "The Big Bang Theory",
    year: "2026",
    genre: "Comedy",
    description:
      "A group of brilliant scientists navigate friendship, love, and awkward social situations.",
    poster:
      "https://resizing.flixster.com/P4WwV56xWD5lH558e8HSol0ZB-U=/fit-in/705x460/v2/https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p185554_b_v10_az.jpg",
    level: 9,
  },
];

function parseVideoConfig(text) {
  const map = {};
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  for (const line of lines) {
    if (line.startsWith("#")) continue;

    const parts = line.split("|").map((part) => part.trim());
    if (parts.length < 10) continue;

    const [
      id,
      videoSrc,
      startFrameRaw,
      endFrameRaw,
      productImage,
      productTitle,
      productDescription,
      price,
      ratingRaw,
      productUrl,
    ] = parts;

    map[id] = {
      videoSrc,
      highlightStartFrame: Number(startFrameRaw) || 0,
      highlightEndFrame: Number(endFrameRaw) || 0,
      productImage,
      productTitle,
      productDescription,
      price,
      rating: Math.max(0, Math.min(5, Number(ratingRaw) || 0)),
      productUrl,
    };
  }

  return map;
}

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${mins}:${secs}`;
}

function Sidebar() {
  const items = ["Home", "TV shows", "Movies", "Newest", "My list"];

  return (
    <aside className="sidebar">
      <div className="search-label">
        <Search size={16} />
        <span>Search</span>
      </div>

      <nav className="nav-list">
        {items.map((item, i) => (
          <div key={item} className={`nav-item ${i === 0 ? "active" : ""}`}>
            {item}
          </div>
        ))}
      </nav>
    </aside>
  );
}

function Header() {
  return (
    <div className="top-header">
      <div className="brand-wrap">
        <div className="brand-logo">B</div>
        <div className="brand">BackstageCommercials</div>
      </div>

      <div className="profile-box">
        <div className="profile-avatar">M</div>
        <span>Max</span>
      </div>
    </div>
  );
}

function HomePage({ shows, onOpenShow }) {
  return (
    <div className="app-shell">
      <Header />
      <div className="main-layout">
        <Sidebar />

        <main className="content-area">
          <div className="poster-row">
            {shows.map((show) => (
              <button
                key={show.id}
                onClick={() => onOpenShow(show.id)}
                className={`poster-button level-${show.level}`}
                type="button"
              >
                <div className="poster-wrap">
                  <div className="poster-title">{show.title}</div>
                  <div className="poster-card">
                    <img src={show.poster} alt={show.title} className="poster-image" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}

function Stars({ rating }) {
  return (
    <div className="product-stars">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star key={i} size={14} fill={i < rating ? "currentColor" : "none"} />
      ))}
    </div>
  );
}

function ProductOverlay({ show, remainingRatio, isLeaving }) {
  const openProduct = () => {
    if (!show.productUrl) return;
    window.open(show.productUrl, "_blank", "noopener,noreferrer");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openProduct();
    }
  };

  return (
    <div
      className={`product-overlay ${isLeaving ? "product-overlay-out" : ""}`}
      onClick={openProduct}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
    >
      <img src={show.productImage} alt={show.productTitle} className="product-image" />
      <div className="product-body">
        <div className="product-title">{show.productTitle}</div>
        <div className="product-desc">{show.productDescription}</div>

        <div className="product-meta">
          <div className="product-price">{show.price}</div>
          <Stars rating={show.rating} />
        </div>

        <div className="product-countdown-track">
          <div
            className="product-countdown-fill"
            style={{
              width: `${Math.max(0, Math.min(1, remainingRatio)) * 100}%`,
            }}
          />
        </div>

        <div className="product-note">Offer disappears when this scene ends</div>
      </div>
    </div>
  );
}

function EpisodePlayer({ show }) {
  const videoRef = useRef(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [showProductOverlay, setShowProductOverlay] = useState(false);
  const [isOverlayLeaving, setIsOverlayLeaving] = useState(false);
  const [isNovaLoading, setIsNovaLoading] = useState(false);
  const [showNovaToast, setShowNovaToast] = useState(false);

  const fps = 30;
  const src = show.videoSrc;
  const highlightStartFrame = show.highlightStartFrame ?? 0;
  const highlightEndFrame = show.highlightEndFrame ?? 0;
  const highlightStartTime = highlightStartFrame / fps;
  const highlightEndTime = highlightEndFrame / fps;

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    setCurrentTime(0);
    setDuration(0);
    setIsPlaying(false);
    setHasStarted(false);
    setIsNovaLoading(false);
    setShowNovaToast(false);

    const onLoaded = () => setDuration(video.duration || 0);
    const onTime = () => setCurrentTime(video.currentTime || 0);
    const onPlay = () => {
      setIsPlaying(true);
      setHasStarted(true);
    };
    const onPause = () => setIsPlaying(false);
    const onEnded = () => setIsPlaying(false);

    video.addEventListener("loadedmetadata", onLoaded);
    video.addEventListener("timeupdate", onTime);
    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);
    video.addEventListener("ended", onEnded);

    return () => {
      video.removeEventListener("loadedmetadata", onLoaded);
      video.removeEventListener("timeupdate", onTime);
      video.removeEventListener("play", onPlay);
      video.removeEventListener("pause", onPause);
      video.removeEventListener("ended", onEnded);
    };
  }, [src]);

  const progressPercent = duration ? (currentTime / duration) * 100 : 0;
  const highlightLeft = duration ? (highlightStartTime / duration) * 100 : 0;
  const highlightWidth = duration
    ? ((highlightEndTime - highlightStartTime) / duration) * 100
    : 0;

  const extendedEndTime = highlightEndTime + 1.25;
  const displayZoneActive =
    currentTime >= highlightStartTime &&
    currentTime <= extendedEndTime &&
    Boolean(show.productImage);

  const remainingRatio =
    extendedEndTime > highlightStartTime
      ? (extendedEndTime - currentTime) / (extendedEndTime - highlightStartTime)
      : 0;

  const togglePlay = async () => {
    const video = videoRef.current;
    if (!video || !src) return;

    try {
      if (video.paused) {
        await video.play();
      } else {
        video.pause();
      }
    } catch (err) {
      console.error("Video play error:", err);
    }
  };

  const handleSeek = (e) => {
    const video = videoRef.current;
    if (!video || !duration) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    video.currentTime = Math.max(0, Math.min(duration, ratio * duration));
  };

  const handleNovaSearch = () => {
    if (isNovaLoading) return;

    setIsNovaLoading(true);
    setShowNovaToast(false);

    setTimeout(() => {
      setIsNovaLoading(false);
      setShowNovaToast(true);

      setTimeout(() => {
        setShowNovaToast(false);
      }, 9000);
    }, 6000);
  };

  useEffect(() => {
    if (displayZoneActive) {
      setShowProductOverlay(true);
      setIsOverlayLeaving(false);
      return;
    }

    if (showProductOverlay) {
      setIsOverlayLeaving(true);
      const timeout = setTimeout(() => {
        setShowProductOverlay(false);
        setIsOverlayLeaving(false);
      }, 250);

      return () => clearTimeout(timeout);
    }
  }, [displayZoneActive, showProductOverlay]);

  return (
    <div>
      <div className="video-stage">
        <div className="video-wrap">
          {showNovaToast && (
            <div className={`nova-toast ${showNovaToast ? "nova-toast-show" : ""}`}>
              <div className="nova-toast-title">Amazon Nova Search</div>
              <div className="nova-toast-text">
                Prompt found product match: {show.productTitle || "Detected product"}.
              </div>
              {"https://www.amazon.com/exec/obidos/asin/B01C35MZVG/rdbests-20/?utm_source=nova.amazon.com" && (
                <a
                  href={"https://www.amazon.com/exec/obidos/asin/B01C35MZVG/rdbests-20/?utm_source=nova.amazon.com"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="nova-toast-link"
                >
                  {"https://www.amazon.com/exec/obidos/asin/B01C35MZVG/rdbests-20/?utm_source=nova.amazon.com"}
                </a>
              )}
            </div>
          )}

          <video
            ref={videoRef}
            src={src}
            className="video-element"
            controls={false}
            preload="metadata"
            poster={show.poster}
            onClick={togglePlay}
          />

          {!hasStarted && (
            <div
              className="video-thumbnail-overlay"
              onClick={togglePlay}
              style={{ backgroundImage: `url(${show.poster})` }}
            />
          )}

          {!isPlaying && (
            <button className="video-overlay-play" onClick={togglePlay} type="button">
              <div className="video-overlay-circle">
                <Play size={36} fill="white" />
              </div>
            </button>
          )}

          {showProductOverlay && (
            <ProductOverlay
              show={show}
              remainingRatio={remainingRatio}
              isLeaving={isOverlayLeaving}
            />
          )}
        </div>
      </div>

      <div className="timeline-block">
        <div className="timeline-bar" onClick={handleSeek}>
          <div
            className="timeline-highlight"
            style={{
              left: `${highlightLeft}%`,
              width: `${highlightWidth}%`,
            }}
          />
          <div
            className="timeline-progress"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        <div className="player-controls">
          <div className="player-left">
            <button onClick={togglePlay} className="play-btn" type="button">
              <Play size={16} />
              <span>{isPlaying ? "Pause" : "Play"}</span>
            </button>

            <button
              onClick={handleNovaSearch}
              className="nova-btn"
              type="button"
              disabled={isNovaLoading}
            >
              <Sparkles size={16} />
              <span>{isNovaLoading ? "Listening..." : "Ask Nova"}</span>
            </button>

            <span className="time-label">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>

          {/* <div className="frame-label">
            Highlight frames: {highlightStartFrame} - {highlightEndFrame}
          </div> */}
        </div>
      </div>
    </div>
  );
}

function ShowPage({ show, onBack }) {
  const videoSectionRef = useRef(null);

  const scrollToVideo = () => {
    videoSectionRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  return (
    <div className="show-page">
      <section className="hero">
        <img src={show.poster} alt={show.title} className="hero-image" />
        <div className="hero-gradient" />

        <div className="hero-topbar">
          <button onClick={onBack} className="back-btn" type="button">
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>

          <div className="profile-box" style={{ position: "static", transform: "none" }}>
            <div className="profile-avatar">M</div>
            <span>Max</span>
          </div>
        </div>

        <div className="hero-content">
          <div className="hero-poster">
            <img src={show.poster} alt={show.title} />
          </div>

          <div>
            <h1 className="show-title">{show.title}</h1>
            <div className="show-meta">
              {show.year} · {show.genre}
            </div>
            <div className="about-text">{show.description}</div>

            <button className="watch-btn" onClick={scrollToVideo} type="button">
              <Play size={18} />
              <span>Watch</span>
            </button>
          </div>
        </div>
      </section>

      <section className="video-section" ref={videoSectionRef}>
        <h2 className="video-title">Now watching</h2>
        <EpisodePlayer show={show} />
      </section>
    </div>
  );
}

export default function App() {
  const [videoConfig, setVideoConfig] = useState({});
  const [configLoading, setConfigLoading] = useState(true);
  const [configError, setConfigError] = useState("");
  const [selectedShowId, setSelectedShowId] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadConfig() {
      try {
        setConfigLoading(true);
        setConfigError("");

        const res = await fetch("/video_config.txt");
        if (!res.ok) {
          throw new Error(`Failed to load /video_config.txt (${res.status})`);
        }

        const text = await res.text();
        const parsed = parseVideoConfig(text);

        if (!cancelled) {
          setVideoConfig(parsed);
        }
      } catch (err) {
        if (!cancelled) {
          setConfigError(err.message || "Failed to load video config.");
        }
      } finally {
        if (!cancelled) {
          setConfigLoading(false);
        }
      }
    }

    loadConfig();

    return () => {
      cancelled = true;
    };
  }, []);

  const shows = useMemo(() => {
    return baseShows.map((show) => ({
      ...show,
      videoSrc: videoConfig[show.id]?.videoSrc || "",
      highlightStartFrame: videoConfig[show.id]?.highlightStartFrame ?? 0,
      highlightEndFrame: videoConfig[show.id]?.highlightEndFrame ?? 0,
      productImage: videoConfig[show.id]?.productImage || "",
      productTitle: videoConfig[show.id]?.productTitle || "",
      productDescription: videoConfig[show.id]?.productDescription || "",
      price: videoConfig[show.id]?.price || "",
      rating: videoConfig[show.id]?.rating ?? 0,
      productUrl: videoConfig[show.id]?.productUrl || "",
    }));
  }, [videoConfig]);

  const selectedShow = useMemo(
    () => shows.find((show) => show.id === selectedShowId) || null,
    [shows, selectedShowId]
  );

  return (
    <>
      <style>{styles}</style>

      {configLoading ? (
        <div className="app-shell">
          <Header />
          <div className="loading-box">Loading video config...</div>
          <div className="config-box">
            Create <strong>public/video_config.txt</strong> with this format:
            <br />
            <pre>{CONFIG_EXAMPLE}</pre>
          </div>
        </div>
      ) : configError ? (
        <div className="app-shell">
          <Header />
          <div className="error-box">{configError}</div>
          <div className="config-box">
            Expected format for <strong>public/video_config.txt</strong>:
            <br />
            <pre>{CONFIG_EXAMPLE}</pre>
          </div>
        </div>
      ) : selectedShow ? (
        <ShowPage show={selectedShow} onBack={() => setSelectedShowId(null)} />
      ) : (
        <HomePage shows={shows} onOpenShow={setSelectedShowId} />
      )}
    </>
  );
}