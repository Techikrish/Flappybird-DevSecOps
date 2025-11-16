import React, { useState, useEffect, useRef } from "react";

const App = () => {
  const [playerName, setPlayerName] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const [bestScore, setBestScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [leaderboard, setLeaderboard] = useState([]);
  const canvasRef = useRef(null);

  const gravity = 0.5;
  const jump = -9;

  const fetchLeaderboard = async () => {
    try {
      const backendUrl = window.location.hostname === 'localhost' 
        ? 'http://localhost:5000'
        : 'http://backend:5000';
      const res = await fetch(`${backendUrl}/scores`);
      const data = await res.json();
      setLeaderboard(data);
    } catch (err) {
      console.error("Error fetching leaderboard:", err);
    }
  };

  useEffect(() => {
    if (!submitted) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let birdY = canvas.height / 2;
    let velocity = 0;
    let pipes = [];
    let frame = 0;
    let animation;
    let running = true;
    let points = 0;

    const gap = 120;

    const resetGame = () => {
      birdY = canvas.height / 2;
      velocity = 0;
      pipes = [];
      frame = 0;
      points = 0;
      running = true;
      setScore(0);
      setGameOver(false);
      draw();
    };

    const submitScore = async (finalScore) => {
      try {
        const backendUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:5000'
          : 'http://backend:5000';
        await fetch(`${backendUrl}/score`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ player_name: playerName, score: finalScore }),
        });
        await fetchLeaderboard();
      } catch (error) {
        console.error("Error submitting score:", error);
      }
    };

    const draw = () => {
      ctx.fillStyle = "#70c5ce";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw bird
      ctx.fillStyle = "#ff0";
      ctx.fillRect(50, birdY, 20, 20);

      // Pipes logic
      if (frame % 90 === 0) {
        const topHeight = Math.random() * (canvas.height - gap - 100) + 50;
        pipes.push({
          x: canvas.width,
          topHeight,
          passed: false,
        });
      }

      pipes.forEach((pipe, i) => {
        pipe.x -= 2;

        ctx.fillStyle = "#0f0";
        ctx.fillRect(pipe.x, 0, 50, pipe.topHeight);
        ctx.fillRect(
          pipe.x,
          pipe.topHeight + gap,
          50,
          canvas.height - pipe.topHeight - gap
        );

        // Check collision
        if (
          50 + 20 > pipe.x &&
          50 < pipe.x + 50 &&
          (birdY < pipe.topHeight || birdY + 20 > pipe.topHeight + gap)
        ) {
          running = false;
          cancelAnimationFrame(animation);
          setGameOver(true);
          submitScore(points);
        }

        // Scoring
        if (!pipe.passed && pipe.x + 50 < 50) {
          pipe.passed = true;
          points++;
          setScore(points);
        }
      });

      // Bird physics
      velocity += gravity;
      birdY += velocity;

      // Ground or ceiling collision
      if (birdY + 20 >= canvas.height || birdY <= 0) {
        running = false;
        cancelAnimationFrame(animation);
        setGameOver(true);
        submitScore(points);
      }

      frame++;
      if (running) animation = requestAnimationFrame(draw);
    };

    const jumpHandler = (e) => {
      if (e.code === "Space") velocity = jump;
    };

    window.addEventListener("keydown", jumpHandler);
    draw();

    return () => {
      window.removeEventListener("keydown", jumpHandler);
      cancelAnimationFrame(animation);
    };
  }, [submitted, playerName]);

  const handleStart = (e) => {
    e.preventDefault();
    if (playerName.trim()) {
      setSubmitted(true);
      fetchLeaderboard();
    }
  };

  const handleRestart = () => {
    window.location.reload();
  };

  return (
    <div className="game-container">
      {!submitted ? (
        <form onSubmit={handleStart} className="player-form">
          <h2>Enter Your Name</h2>
          <input
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            placeholder="Player name"
          />
          <button type="submit">Start Game</button>
        </form>
      ) : (
        <>
          <h2>Flappy Bird</h2>
          <canvas ref={canvasRef} width="400" height="500"></canvas>
          <p>Score: {score}</p>
          {gameOver && (
            <div className="overlay">
              <h3>Game Over!</h3>
              <p>Your Score: {score}</p>
              <button onClick={handleRestart}>Restart</button>
            </div>
          )}
          <h3>Leaderboard</h3>
          <ul>
            {leaderboard.map((item, index) => (
              <li key={index}>
                {item.player_name}: {item.score}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
};

export default App;
