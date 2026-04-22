/**
 * Spoiler Guard — content script for SonyLiv and Hotstar.
 *
 * SonyLiv: Strips video poster attributes to prevent match thumbnails
 * (which reveal the winner) from being visible. Only activates on pages
 * with ?watch=true in the URL (how the CLI opens videos).
 *
 * Hotstar: Hides elements whose text matches a match score pattern
 * (e.g. "Crystal Palace 0-0 West Ham"). Avoids touching player controls.
 * Activates on all /sports/ pages.
 */

(() => {
  const host = window.location.hostname;
  const isSonyLiv = host.includes("sonyliv.com");
  const isHotstar = host.includes("hotstar.com");

  // SonyLiv: only activate on CLI-opened URLs
  if (isSonyLiv && !window.location.search.includes("watch=true")) return;

  // Hotstar: activate on sports pages
  const isHotstarSports = isHotstar && window.location.pathname.includes("/sports/");
  if (isHotstar && !isHotstarSports) return;

  // Hotstar football: add marker class to hide seekbar/time via CSS
  // Only football — cricket highlights are short and don't spoil results
  const isHotstarFootball = isHotstarSports && window.location.pathname.includes("/football/");
  if (isHotstarFootball) {
    document.documentElement.classList.add("sg-hotstar-sports");
  }

  const stripPoster = () => {
    document.querySelectorAll("video[poster]").forEach((video) => {
      video.removeAttribute("poster");
    });
  };

  // Match score patterns: "Team 0-0 Team", "Team 2-1 Team"
  const SCORE_PATTERN = /\b\d+\s*[-–]\s*\d+\b/;

  // Selectors for player controls that must never be hidden
  const PLAYER_CONTROLS = "video, button, [class*='control' i], [class*='seekbar' i], [class*='slider' i], [class*='progress' i], [class*='volume' i], [class*='setting' i], [class*='quality' i], [class*='menu' i], [class*='icon' i], [class*='btn' i], svg, path";

  // Time pattern: "01:24", "1:02:30"
  const TIME_PATTERN = /^\d{1,2}:\d{2}(:\d{2})?$/;

  const hideScoreElements = () => {
    if (!isHotstar) return;

    // Check heading and text elements for score patterns
    const candidates = document.querySelectorAll("h1, h2, h3, h4, h5, h6, p, span");

    for (const el of candidates) {
      // Skip anything inside player controls
      if (el.closest(PLAYER_CONTROLS)) continue;

      const text = el.textContent.trim();
      if (text.length > 0 && text.length < 120 && SCORE_PATTERN.test(text)) {
        el.style.visibility = "hidden";
      }
    }
  };

  const hideTimeDisplay = () => {
    if (!isHotstarFootball) return;

    // Hide spans showing elapsed/remaining time (e.g. "01:24", "2:55:00")
    const spans = document.querySelectorAll("span");
    for (const el of spans) {
      const text = el.textContent.trim();
      if (TIME_PATTERN.test(text)) {
        el.style.visibility = "hidden";
      }
    }
  };

  const observer = new MutationObserver(() => {
    stripPoster();
    hideScoreElements();
    hideTimeDisplay();
  });

  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      observer.observe(document.body, { childList: true, subtree: true });
    });
  }

  stripPoster();
  hideScoreElements();
  hideTimeDisplay();
})();
