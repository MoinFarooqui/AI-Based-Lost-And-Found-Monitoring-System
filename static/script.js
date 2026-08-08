/* ==========================================================================
   AI-Based Lost & Found Monitoring System — Dashboard Script
   Vanilla JS only. Live Clock, Sidebar Active State, Smooth Scroll, Fade-in,
   and Dynamic Video Source Switching.
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  initLiveClock();
  initActiveNavHighlight();
  initSmoothScroll();
  initFadeIn();
});

/* ---------- Live Clock ---------- */
function initLiveClock() {
  const clockEl = document.getElementById("liveClock");
  if (!clockEl) return;

  const tick = () => {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString("en-US", { hour12: false });
  };

  tick();
  setInterval(tick, 1000);
}

/* ---------- Sidebar Active State ---------- */
function initActiveNavHighlight() {
  const navLinks = document.querySelectorAll(".nav-link");
  const sections = Array.from(navLinks)
    .map((link) => document.getElementById(link.dataset.section))
    .filter(Boolean);

  if (!sections.length) return;

  const setActive = (id) => {
    navLinks.forEach((link) => {
      link.classList.toggle("active", link.dataset.section === id);
    });
  };

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) setActive(entry.target.id);
      });
    },
    { rootMargin: "-40% 0px -50% 0px", threshold: 0 }
  );

  sections.forEach((section) => observer.observe(section));
}

/* ---------- Smooth Scroll ---------- */
function initSmoothScroll() {
  document.querySelectorAll('.nav-link[href^="#"]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const target = document.querySelector(link.getAttribute("href"));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

/* ---------- Simple Fade Animation ---------- */
function initFadeIn() {
  const fadeEls = document.querySelectorAll(".fade-in");
  if (!fadeEls.length) return;

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  fadeEls.forEach((el) => observer.observe(el));
}

/* ---------- Dynamic Video Source Switching ---------- */
// Triggered by the HTML dropdown: onchange="changeVideoSource(this.value)"
window.changeVideoSource = function(selectedSource) {
  fetch('/set_source', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ source: selectedSource })
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      console.log("Source successfully updated to:", selectedSource);
      
      // Force reload the video feed image to trigger the new stream
      const videoFeed = document.getElementById('videoFeedImg');
      if (videoFeed) {
        // Appending a timestamp query prevents the browser from caching the old image.
        // We strip any existing timestamp first to keep the URL clean.
        let baseUrl = videoFeed.src.split('?')[0]; 
        videoFeed.src = baseUrl + "?t=" + new Date().getTime();
      }
      
      // Optional: If you have a span showing the current source name, update it
      const currentSourceLabel = document.getElementById('currentSourceLabel');
      if (currentSourceLabel) {
        if (selectedSource == "0") {
          currentSourceLabel.textContent = "Webcam";
        } else {
          // Extracts just the filename if it's a path like videos/test.mp4
          currentSourceLabel.textContent = selectedSource.split('/').pop(); 
        }
      }
    }
  })
  .catch(error => console.error('Error changing stream source:', error));
};

// ================= AUTO REFRESH EVENTS & SNAPSHOTS =================

function refreshDashboard() {

    fetch("/api/events")
        .then(response => response.json())
        .then(data => {

            // Update Events Count
            const count = document.querySelector(".stat-value");
            if (count) {
                count.textContent = data.events_count;
            }

            // Update Events
            const eventsContainer = document.getElementById("eventsContainer");

            if (eventsContainer) {

                eventsContainer.innerHTML = "";

                data.events.forEach(event => {

                    eventsContainer.innerHTML += `
                        <div class="card event-card">
                            <img src="${event.snapshot}" alt="Snapshot">

                            <div class="card-details">

                                <span class="badge alert-badge">
                                    ${event.status}
                                </span>

                                <p class="time">
                                    <i class="fa-regular fa-clock"></i>
                                    ${event.time}
                                </p>

                                <a href="${event.video}"
                                   target="_blank"
                                   class="play-btn">

                                   <i class="fa-solid fa-play"></i>
                                   Watch Video

                                </a>

                            </div>
                        </div>
                    `;
                });

            }

            // Update Snapshots
            const snapContainer = document.getElementById("snapshotsContainer");

            if (snapContainer) {

                snapContainer.innerHTML = "";

                data.snapshots.forEach(img => {

                    snapContainer.innerHTML += `
                        <div class="snapshot-card">
                            <img src="${img}" alt="Snapshot">
                        </div>
                    `;

                });

            }

        })
        .catch(err => console.log(err));

}

// Refresh every 3 seconds
setInterval(refreshDashboard, 3000);