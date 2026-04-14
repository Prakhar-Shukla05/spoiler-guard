/**
 * Spoiler Guard — content script for SonyLiv.
 *
 * Strips the poster attribute from video elements to prevent match
 * thumbnails (which often reveal the winner) from being visible.
 *
 * Only activates on pages with ?watch=true in the URL, which is how
 * the CLI tool opens videos.
 */

(() => {
  if (!window.location.search.includes("watch=true")) return;

  const stripPoster = () => {
    document.querySelectorAll("video[poster]").forEach((video) => {
      video.removeAttribute("poster");
    });
  };

  const observer = new MutationObserver(() => stripPoster());

  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      observer.observe(document.body, { childList: true, subtree: true });
    });
  }

  stripPoster();
})();
