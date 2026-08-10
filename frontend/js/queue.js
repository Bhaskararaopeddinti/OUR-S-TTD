/**
 * queue.js – AI Queue Intelligence page implementation
 * Loads and displays predictive queue analysis with crowd trends.
 */
'use strict';

// Load queue intelligence data
async function loadQueueIntelligence() {
  const statusContainer = document.getElementById('queueStatus');
  const predictionContainer = document.getElementById('aiPrediction');
  const trendContainer = document.getElementById('crowdTrend');
  const bestTimesContainer = document.getElementById('bestTimes');
  const adviceContainer = document.getElementById('aiAdvice');
  const festivalContainer = document.getElementById('festivalImpact');

  try {
    const data = await API.get('queue');
    
    // Display current status
    if (statusContainer) {
      statusContainer.innerHTML = `
        <div class="stat-item">
          <span class="stat-label">Location</span>
          <span class="stat-value">${data.location || 'Sarva Darshan'}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Current Wait</span>
          <span class="stat-value">${data.wait_minutes || '—'} min</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Crowd Density</span>
          <span class="stat-value">${data.crowd_density || '—'}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">People in Queue</span>
          <span class="stat-value">${data.people_count?.toLocaleString() || '—'}</span>
        </div>
      `;
    }

    // Display AI prediction
    if (predictionContainer && data.ai_prediction) {
      const pred = data.ai_prediction;
      predictionContainer.innerHTML = `
        <div class="prediction-item">
          <span class="pred-label">Predicted Wait Time</span>
          <span class="pred-value">${pred.predicted_wait_minutes} min</span>
        </div>
        <div class="prediction-item">
          <span class="pred-label">Current Crowd Level</span>
          <span class="pred-value crowd-${pred.current_crowd_level?.toLowerCase()}">${pred.current_crowd_level}</span>
        </div>
        <div class="prediction-item">
          <span class="pred-label">Recommendation</span>
          <span class="pred-value">${pred.low_crowd_recommendation}</span>
        </div>
        <p class="disclaimer">${data.prediction_disclaimer}</p>
      `;
    }

    // Display crowd trend
    if (trendContainer && data.ai_prediction?.crowd_trend_next_6_hours) {
      const trends = data.ai_prediction.crowd_trend_next_6_hours;
      trendContainer.innerHTML = `
        <div class="trend-chart">
          ${trends.map(t => `
            <div class="trend-item">
              <span class="trend-time">${t.time}</span>
              <span class="trend-level crowd-${t.crowd_level?.toLowerCase()}">${t.crowd_level}</span>
              <span class="trend-factor">×${t.wait_factor}</span>
            </div>
          `).join('')}
        </div>
      `;
    }

    // Display best times
    if (bestTimesContainer && data.ai_prediction?.best_times_to_join) {
      const bestTimes = data.ai_prediction.best_times_to_join;
      if (bestTimes.length === 0) {
        bestTimesContainer.innerHTML = '<p class="hint">No optimal times found in the next 24 hours</p>';
      } else {
        bestTimesContainer.innerHTML = `
          <ul class="best-times-list">
            ${bestTimes.map((t, i) => `
              <li class="best-time-item">
                <span class="rank">${i + 1}</span>
                <span class="time">${t.time}</span>
                <span class="info">${t.recommendation}</span>
                <span class="wait-factor">×${t.wait_factor}</span>
              </li>
            `).join('')}
          </ul>
        `;
      }
    }

    // Display AI advice
    if (adviceContainer && data.ai_prediction?.ai_advice) {
      const advice = data.ai_prediction.ai_advice;
      adviceContainer.innerHTML = `
        <ul class="advice-list">
          ${advice.map(a => `<li class="advice-item">${a}</li>`).join('')}
        </ul>
      `;
    }

    // Display festival impact
    if (festivalContainer && data.ai_prediction?.festival_impacts) {
      const festivals = data.ai_prediction.festival_impacts;
      if (festivals.length === 0) {
        festivalContainer.innerHTML = '<p class="hint">No major festivals currently affecting crowd levels</p>';
      } else {
        festivalContainer.innerHTML = `
          <div class="festival-alerts">
            ${festivals.map(f => `
              <div class="festival-alert">
                <span class="festival-icon">🎉</span>
                <div>
                  <strong>${f.festival}</strong>
                  <p>${f.description}</p>
                  <span class="multiplier">Crowd multiplier: ×${f.multiplier}</span>
                </div>
              </div>
            `).join('')}
          </div>
        `;
      }
    }

  } catch (error) {
    console.error('Failed to load queue intelligence:', error);
    const containers = [statusContainer, predictionContainer, trendContainer, bestTimesContainer, adviceContainer];
    containers.forEach(c => {
      if (c) c.innerHTML = '<p class="error">Failed to load queue data. Please try again.</p>';
    });
  }
}

// Update hero stats on home page
async function loadHeroStats() {
  const heroQueue = document.getElementById('heroQueue');
  const heroCrowd = document.getElementById('heroCrowd');
  
  if (!heroQueue || !heroCrowd) return;

  try {
    const data = await API.get('queue');
    heroQueue.textContent = `${data.wait_minutes || '—'} min`;
    heroCrowd.textContent = data.crowd_density || '—';
  } catch (error) {
    console.error('Failed to load hero stats:', error);
  }
}

// WebSocket connection for live push updates
(function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}/ws/live`);
  ws.onmessage = e => {
    try {
      const data = JSON.parse(e.data);
      // Refresh queue data on the queue page if open
      if (document.querySelector('.queue-page')) {
        loadQueueIntelligence();
      }
      // Update hero stats
      loadHeroStats();
    } catch { /* ignore malformed messages */ }
  };
  ws.onerror = () => {}; // Silently reconnect
  ws.onclose = () => { setTimeout(connectWS, 5000); }; // Reconnect after 5s
})();

// Export functions for app.js
window.loadQueueIntelligence = loadQueueIntelligence;
window.loadHeroStats = loadHeroStats;
