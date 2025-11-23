import React, { useEffect, useRef, useState } from "react";
import "./App.css";

// Get API URL - when in Docker, use backend service, otherwise localhost
const API_URL = import.meta.env.VITE_API_BASE || "http://localhost:5000";

console.log("[App] API_URL:", API_URL);

export default function FlappyBird() {
  const canvasRef = useRef(null);
  const [playerName, setPlayerName] = useState("");
  const [gameStarted, setGameStarted] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [score, setScore] = useState(0);
  const [leaderboard, setLeaderboard] = useState([]);

  // Fetch leaderboard on mount and set auto-refresh every 3 seconds
  useEffect(() => {
    fetchLeaderboard();
    const interval = setInterval(fetchLeaderboard, 3000);
    return () => clearInterval(interval);
  }, []);

  function fetchLeaderboard() {
    const url = `${API_URL}/leaderboard?limit=5`;
    console.log("[fetchLeaderboard] Fetching from:", url);
    
    fetch(url)
      .then((r) => {
        console.log("[fetchLeaderboard] Response status:", r.status);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        console.log("[fetchLeaderboard] Received data:", data);
        if (Array.isArray(data)) {
          setLeaderboard(data);
        } else {
          console.error("[fetchLeaderboard] Data is not array:", typeof data);
          setLeaderboard([]);
        }
      })
      .catch((err) => {
        console.error("[fetchLeaderboard] Error:", err.message);
      });
  }

  function submitScore(finalScore) {
    if (!playerName) return;
    
    const payload = { name: playerName, score: finalScore };
    console.log("[submitScore] Submitting:", payload);
    
    fetch(`${API_URL}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        console.log("[submitScore] Response:", data);
        setTimeout(fetchLeaderboard, 500);
      })
      .catch((err) => console.error("[submitScore] Error:", err));
  }

  function startGame() {
    if (!playerName.trim()) {
      alert("Please enter your name!");
      return;
    }
    setGameOver(false);
    setScore(0);
    setGameStarted(true);
  }

  function resetGame() {
    setGameStarted(false);
    setGameOver(false);
    setScore(0);
    setPlayerName("");
  }

  // Game logic
  useEffect(() => {
    if (!gameStarted) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const W = canvas.width;
    const H = canvas.height;

    // Bird
    const bird = {
      x: W * 0.2,
      y: H * 0.5,
      vy: 0,
      radius: 12,
    };

    let pipes = [];
    let gameScore = 0;
    let frameCount = 0;
    let isGameOver = false;

    function drawBird() {
      ctx.fillStyle = "#FFD700";
      ctx.beginPath();
      ctx.arc(bird.x, bird.y, bird.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#FFA500";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    function drawPipes() {
      pipes.forEach((pipe) => {
        ctx.fillStyle = "#228B22";
        ctx.fillRect(pipe.x, 0, pipe.w, pipe.gap);
        ctx.fillRect(pipe.x, pipe.gap + pipe.gapSize, pipe.w, H - pipe.gap - pipe.gapSize);
      });
    }

    function drawBackground() {
      const gradient = ctx.createLinearGradient(0, 0, 0, H);
      gradient.addColorStop(0, "#87CEEB");
      gradient.addColorStop(1, "#E0F6FF");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, W, H);
    }

    function drawScore() {
      ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
      ctx.font = "bold 32px Arial";
      ctx.fillText(`Score: ${gameScore}`, 20, 50);
    }

    function update() {
      if (isGameOver) return;

      // Physics
      bird.vy += 0.6; // Gravity
      bird.y += bird.vy;

      // Boundaries
      if (bird.y - bird.radius < 0 || bird.y + bird.radius > H) {
        isGameOver = true;
        setGameOver(true);
        submitScore(gameScore);
        return;
      }

      // Spawn pipes
      if (frameCount % 80 === 0) {
        const minGap = 100;
        const maxGap = 150;
        const gapSize = Math.random() * (maxGap - minGap) + minGap;
        const gapY = Math.random() * (H - gapSize - 100) + 50;
        pipes.push({
          x: W,
          gap: gapY,
          gapSize: gapSize,
          w: 60,
          passed: false,
        });
      }

      // Update pipes
      pipes = pipes.filter((pipe) => pipe.x > -100);
      pipes.forEach((pipe) => {
        pipe.x -= 5;

        // Score
        if (!pipe.passed && pipe.x + pipe.w < bird.x) {
          pipe.passed = true;
          gameScore++;
          setScore(gameScore);
        }

        // Collision
        if (
          bird.x + bird.radius > pipe.x &&
          bird.x - bird.radius < pipe.x + pipe.w
        ) {
          if (
            bird.y - bird.radius < pipe.gap ||
            bird.y + bird.radius > pipe.gap + pipe.gapSize
          ) {
            isGameOver = true;
            setGameOver(true);
            submitScore(gameScore);
          }
        }
      });

      frameCount++;
    }

    function draw() {
      drawBackground();
      drawPipes();
      drawBird();
      drawScore();
    }

    function loop() {
      update();
      draw();
      if (!isGameOver) {
        requestAnimationFrame(loop);
      }
    }

    const handleKeyPress = (e) => {
      if (e.key === " " || e.code === "Space") {
        e.preventDefault();
        bird.vy = -12;
      }
    };

    const handleClick = () => {
      bird.vy = -12;
    };

    window.addEventListener("keydown", handleKeyPress);
    canvas.addEventListener("click", handleClick);

    loop();

    return () => {
      window.removeEventListener("keydown", handleKeyPress);
      canvas.removeEventListener("click", handleClick);
    };
  }, [gameStarted]);

  return (
    <div className="container">
      <canvas ref={canvasRef} className="game-canvas" />

      <div className="ui-panel">
        {/* Top Left - Input */}
        <div className="top-left">
          <input
            type="text"
            name="playerName"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && !gameStarted && startGame()}
            placeholder="Enter name..."
            className="input-field"
            disabled={gameStarted}
          />
          {!gameStarted ? (
            <button onClick={startGame} className="btn">
              Start
            </button>
          ) : (
            <>
              <button onClick={() => setGameStarted(false)} className="btn btn-danger">
                Stop
              </button>
              <span className="player-display">Playing: {playerName}</span>
            </>
          )}
        </div>

        {/* Top Right - Leaderboard */}
        <div className="top-right">
          <h3>🏆 Leaderboard</h3>
          <div className="leaderboard-list">
            {leaderboard && leaderboard.length > 0 ? (
              leaderboard.map((entry, i) => (
                <div key={i} className="leaderboard-item">
                  <span className="rank">#{i + 1}</span>
                  <span className="name">{entry.player_name || "Unknown"}</span>
                  <span className="points">{entry.score || 0}</span>
                </div>
              ))
            ) : (
              <p className="no-scores">No scores yet</p>
            )}
          </div>
          <button onClick={fetchLeaderboard} className="btn-small">
            Refresh
          </button>
        </div>
      </div>

      {/* Game Over Modal */}
      {gameOver && (
        <div className="modal">
          <div className="modal-content">
            <h2>Game Over!</h2>
            <p className="final-score">Your Score: {score}</p>
            <button onClick={resetGame} className="btn btn-large">
              Play Again
            </button>
          </div>
        </div>
      )}

      {/* Start Modal */}
      {!gameStarted && !gameOver && (
        <div className="modal">
          <div className="modal-content">
            <h1>🐦 Flappy Micro</h1>
            <p>Click the canvas or press SPACE to flap!</p>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && startGame()}
              placeholder="Enter your name..."
              className="input-field"
              autoFocus
            />
            <button onClick={startGame} className="btn btn-large">
              Start Game
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
