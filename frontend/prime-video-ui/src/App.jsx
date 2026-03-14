import React, { useMemo, useRef, useState, useEffect } from "react";
import { Play, ArrowLeft, Search } from "lucide-react";

const styles = `
  * { box-sizing: border-box; }
  html, body, #root {
    margin: 0;
    min-height: 100%;
    width: 100%;
    font-family: Arial, Helvetica, sans-serif;
    background: #071422;
    color: white;
    overflow-x: hidden;
  }

  button { font: inherit; }

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
    font-weight: 400;
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
    gap: 22px;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 22px 8px 16px 8px;
    scrollbar-width: thin;
    scrollbar-color: rgba(163,178,199,0.8) rgba(255,255,255,0.08);
  }

  .poster-row::-webkit-scrollbar { height: 12px; }
  .poster-row::-webkit-scrollbar-track { background: rgba(255,255,255,0.08); border-radius: 999px; }
  .poster-row::-webkit-scrollbar-thumb { background: rgba(163,178,199,0.8); border-radius: 999px; }

  .poster-button {
    border: none;
    background: transparent;
    padding: 0;
    cursor: pointer;
    flex: 0 0 auto;
    transition: transform 0.18s ease;
  }

  .poster-button:hover { transform: translateY(-5px) scale(1.02); }

  .poster-wrap { width: 145px; }

  .poster-title {
    font-size: 15px;
    font-weight: 700;
    color: rgba(255,255,255,0.98);
    margin-bottom: 10px;
    text-align: center;
    line-height: 1.3;
    min-height: 20px;
    letter-spacing: 0.3px;
    text-shadow: 0 2px 8px rgba(0,0,0,0.6);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  .poster-card {
    width: 145px;
    height: 400px;
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
    background: linear-gradient(180deg, rgba(8,25,42,0.1) 0%, rgba(8,25,42,0.35) 34%, rgba(8,25,42,0.78) 66%, #08192a 100%);
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
    z-index: 1000;
    font-size: 16px;
    font-weight: 600;
    transform: translateY(-20px);
  }

  .back-btn:hover { background: rgba(0,0,0,0.85); }

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
    max-width: 980px;
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
  }

  .video-title {
    font-size: 28px;
    font-weight: 700;
    margin: 0 0 16px 0;
  }

  .video-wrap {
    width: 100%;
    overflow: hidden;
    background: black;
    box-shadow: 0 18px 36px rgba(0,0,0,0.45);
  }

  .video-element {
    width: 100%;
    height: auto;
    aspect-ratio: 16 / 9;
    display: block;
    background: black;
    cursor: pointer;
  }

  .timeline-block { margin-top: 16px; }

  .timeline-bar {
    position: relative;
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: rgba(255,255,255,0.18);
    overflow: hidden;
    cursor: pointer;
  }

  .timeline-highlight { position: absolute; top: 0; height: 100%; background: #efd34f; }
  .timeline-progress { position: absolute; top: 0; left: 0; height: 100%; background: white; }

  .player-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-top: 14px;
    flex-wrap: wrap;
  }

  .player-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .play-btn {
    border: none;
    background: white;
    color: black;
    border-radius: 14px;
    padding: 10px 16px;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .time-label, .frame-label {
    color: rgba(255,255,255,0.72);
    font-size: 14px;
  }

  @media (max-width: 900px) {
    .main-layout { grid-template-columns: 1fr; }
    .sidebar { display: none; }
    .top-header { justify-content: flex-start; padding-left: 20px; }
    .brand { font-size: 28px; }
    .profile-box { right: 20px; font-size: 16px; }
    .content-area { padding: 0 8px 24px 8px; }
    .hero-content { grid-template-columns: 1fr; padding: 0 20px 26px 20px; }
    .hero-poster { width: 220px; height: 330px; }
    .show-title { font-size: 36px; }
    .video-section { padding: 20px 16px 30px 16px; }
  }
`;

const shows = [
  {
    id: "theboys",
    title: "The BOYS",
    year: "2026",
    genre: "Drama",
    description: "A simple placeholder page for your TV show. Replace this text with the real summary.",
    poster: "https://resizing.flixster.com/mmvBo8CgJiLxvYSimsMguhNEv58=/ems.cHJkLWVtcy1hc3NldHMvdHZzZWFzb24vYWM4MWJjZjUtN2I0My00NmQwLThmZjEtOTA0NTU4OWNlOWE3LmpwZw==",
    videoSrc: "https://www.w3schools.com/html/mov_bbb.mp4",
    level: 0,
  },
  {
    id: "suits",
    title: "Suits",
    year: "2011",
    genre: "Drama",
    description: "Before he was a lawyer, he was a fraud. Meet Mike Ross, a brilliant college dropout who accidentally lands a job at one of New York City's top law firms alongside Harvey Specter, the city's best closer. There's just one catch: Mike never went to law school. Together, this dynamic duo takes on high-stakes cases while keeping Mike's secret hidden from everyone—including the ruthless Jessica Pearson and the firm's managing partner. Sharp, stylish, and full of legal maneuvering, Suits is a thrilling ride through the cutthroat world of corporate law.",
    poster: "https://resizing.flixster.com/u8-QdjD-tUZ_G9zrTr3-Z58PuYk=/ems.cHJkLWVtcy1hc3NldHMvdHZzZWFzb24vUlRUVjYyNDE5LndlYnA=",
    videoSrc: "/suits.mp4",
    level: 1,
  },
  {
    id: "breaking-bad",
    title: "Breaking Bad",
    year: "2008",
    genre: "Crime",
    description: "Walter White, a struggling high school chemistry teacher, is diagnosed with advanced lung cancer. To secure his family's financial future, he turns to a life of crime, producing and selling methamphetamine.",
    poster: "https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p185846_b_v8_ad.jpg",
    videoSrc: "https://www.w3schools.com/html/mov_bbb.mp4",
    level: 2,
  },
  {
    id: "desperate-housewives",
    title: "Desperate Housewives",
    year: "2004",
    genre: "Drama",
    description: "Welcome to Wisteria Lane, where the grass is green, the houses are perfect, and the secrets are deadly. After the mysterious suicide of her friend Mary Alice Young, four suburban housewives—Susan, Lynette, Bree, and Gabrielle—find their seemingly idyllic lives unraveling. From illicit affairs and financial ruin to murder cover-ups and family scandals, Desperate Housewives peels back the manicured lawns of suburbia to reveal a dark, hilarious, and thrilling world where everyone has something to hide.",
    poster: "https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p7896057_b_v13_ab.jpg",
    videoSrc: "https://www.w3schools.com/html/movie.mp4",
    level: 3,
  },
  {
    id: "fallout",
    title: "Fallout",
    year: "2014",
    genre: "Drama",
    description: "A man is released from prison after 15 years and returns to his family, only to find that his wife has remarried and his son is now a teenager.",
    poster: "https://resizing.flixster.com/_suBUkrhJoxiUqiRIuQncCEhJ-o=/ems.cHJkLWVtcy1hc3NldHMvdHZzZWFzb24vYWI1NDExNWMtZGJiYS00Mjg2LTk2NTYtOTJkODA0N2M2YzMxLmpwZw==",
    videoSrc: "https://www.w3schools.com/html/mov_bbb.mp4",
    level: 4,
  },
  {
    id: "prison-break",
    title: "Prison Break",
    year: "2005",
    genre: "Drama",
    description: "A man framed for his brother's murder escapes prison and returns home to exact revenge.",
    poster: "https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p7894210_b_v8_al.jpg",
    videoSrc: "https://www.w3schools.com/html/movie.mp4",
    level: 5,
  },
  {
    id: "the-walking-dead",
    title: "The Walking Dead",
    year: "2010",
    genre: "Drama",
    description: "A group of survivors are on a mission to find a safe and secure location after a zombie apocalypse.",
    poster: "https://resizing.flixster.com/Lzq-nUwBS4DCJDOoSpOVTsCdJ5E=/ems.cHJkLWVtcy1hc3NldHMvdHZzZWFzb24vUlRUVjIwMTY1MC53ZWJw",
    videoSrc: "https://www.w3schools.com/html/movie.mp4",
    level: 6,
  },
  {
    id: "young-sherlock",
    title: "Young Sherlock",
    year: "2026",
    genre: "Adventure",
    description: "A young Sherlock Holmes and his friend Dr. Watson solve crimes in 19th-century London.",
    poster: "https://resizing.flixster.com/6KYdhwSCt5lyHfNgMA4RZX-vPTU=/ems.cHJkLWVtcy1hc3NldHMvdHZzZXJpZXMvZGI2YmU1M2QtYmIyNS00ZTJhLTk4NmItYTBiMDgyMTE1NTUzLmpwZw==",
    videoSrc: "https://www.w3schools.com/html/movie.mp4",
    level: 7,
  },
  {
    id: "game-of-thrones",
    title: "Game of Thrones",
    year: "2026",
    genre: "Mystery",
    description: "The progress bar supports a yellow highlighted frame interval.",
    poster: "https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p12502846_b_v8_aa.jpg",
    videoSrc: "https://www.w3schools.com/html/movie.mp4",
    level: 8,
  },
  {
    id: "big-bang-theory",
    title: "The Big Bang Theory",
    year: "2026",
    genre: "Mystery",
    description: "The progress bar supports a yellow highlighted frame interval.",
    poster: "https://resizing.flixster.com/P4WwV56xWD5lH558e8HSol0ZB-U=/fit-in/705x460/v2/https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p185554_b_v10_az.jpg",
    videoSrc: "https://www.w3schools.com/html/movie.mp4",
    level: 9,
  },
];

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
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

function HomePage({ onOpenShow }) {
  return (
    <div className="app-shell">
      <Header />
      <div className="main-layout">
        <Sidebar />
        <main className="content-area">
          <div className="poster-row">
            {shows.map((show) => (
              <button key={show.id} onClick={() => onOpenShow(show.id)} className={`poster-button level-${show.level}`}>
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

function EpisodePlayer({ src }) {
  const videoRef = useRef(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const fps = 30;
  const highlightStartFrame = 90;
  const highlightEndFrame = 240;
  const highlightStartTime = highlightStartFrame / fps;
  const highlightEndTime = highlightEndFrame / fps;

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onLoaded = () => setDuration(video.duration || 0);
    const onTime = () => setCurrentTime(video.currentTime || 0);
    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);

    video.addEventListener("loadedmetadata", onLoaded);
    video.addEventListener("timeupdate", onTime);
    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);

    return () => {
      video.removeEventListener("loadedmetadata", onLoaded);
      video.removeEventListener("timeupdate", onTime);
      video.removeEventListener("play", onPlay);
      video.removeEventListener("pause", onPause);
    };
  }, []);

  const progressPercent = duration ? (currentTime / duration) * 100 : 0;
  const highlightLeft = duration ? (highlightStartTime / duration) * 100 : 0;
  const highlightWidth = duration ? ((highlightEndTime - highlightStartTime) / duration) * 100 : 0;

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) video.play();
    else video.pause();
  };

  const handleSeek = (e) => {
    const video = videoRef.current;
    if (!video || !duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    video.currentTime = Math.max(0, Math.min(duration, ratio * duration));
  };

  return (
    <div>
      <div className="video-wrap">
        <video ref={videoRef} src={src} className="video-element" controls={false} onClick={togglePlay} />
      </div>

      <div className="timeline-block">
        <div className="timeline-bar" onClick={handleSeek}>
          <div className="timeline-highlight" style={{ left: `${highlightLeft}%`, width: `${highlightWidth}%` }} />
          <div className="timeline-progress" style={{ width: `${progressPercent}%` }} />
        </div>

        <div className="player-controls">
          <div className="player-left">
            <button onClick={togglePlay} className="play-btn">
              <Play size={16} />
              <span>{isPlaying ? "Pause" : "Play"}</span>
            </button>
            <span className="time-label">{formatTime(currentTime)} / {formatTime(duration)}</span>
          </div>
          <div className="frame-label">Highlight frames: {highlightStartFrame} - {highlightEndFrame}</div>
        </div>
      </div>
    </div>
  );
}

function ShowPage({ show, onBack }) {
  const videoSectionRef = useRef(null);

  const scrollToVideo = () => {
    videoSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="show-page">
      <section className="hero">
        <img src={show.poster} alt={show.title} className="hero-image" />
        <div className="hero-gradient" />

        <div className="hero-topbar">
          <button onClick={onBack} className="back-btn">
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
            <div className="show-meta">{show.year} · {show.genre}</div>
            <div className="about-text">{show.description}</div>
            <button className="watch-btn" onClick={scrollToVideo}>
              <Play size={18} />
              <span>Watch</span>
            </button>
          </div>
        </div>
      </section>

      <section className="video-section" ref={videoSectionRef}>
        <h2 className="video-title">Now watching</h2>
        <EpisodePlayer src={show.videoSrc} />
      </section>
    </div>
  );
}

export default function App() {
  const [selectedShowId, setSelectedShowId] = useState(null);

  const selectedShow = useMemo(
    () => shows.find((show) => show.id === selectedShowId) || null,
    [selectedShowId]
  );

  return (
    <>
      <style>{styles}</style>
      {selectedShow ? (
        <ShowPage show={selectedShow} onBack={() => setSelectedShowId(null)} />
      ) : (
        <HomePage onOpenShow={setSelectedShowId} />
      )}
    </>
  );
}
