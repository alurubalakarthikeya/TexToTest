import { useState, useEffect } from "react";
import { Play, Pause } from "lucide-react";
import "./NavBar.css";

const Navbar = () => {
  const [time, setTime] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  // Stopwatch logic
  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(() => {
        setTime((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  const toggleStopwatch = () => {
    setIsRunning((prev) => !prev);
  };

  const formatTime = (t) => {
    const minutes = String(Math.floor(t / 60)).padStart(2, "0");
    const seconds = String(t % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  };

  return (
    <nav className="navbar">
      <div className="logo">TexToTest</div>

      <div className="nav-links">
        {/* Stopwatch */}
        <div
          className={`stopwatch-container ${isRunning ? "expanded" : ""}`}
          onClick={toggleStopwatch}
        >
          <div className="stopwatch-circle">
            {isRunning ? <Pause size={14} /> : <Play size={14} />}
          </div>
          {isRunning && (
            <span className="stopwatch-time">{formatTime(time)}</span>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
