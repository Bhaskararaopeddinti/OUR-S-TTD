/**
 * queue.js – AI Queue Intelligence page implementation
 * Loads and displays predictive queue analysis with crowd trends.
 * Bulletproof null safety & automatic DOM retry guard.
 */
'use strict';

// Load queue intelligence data
async function loadQueueIntelligence(retryCount = 0) {
  const statusContainer     = document.getElementById('queueStatus');
  const predictionContainer = document.getElementById('aiPrediction');
  const trendContainer      = document.getElementById('crowdTrend');
  const bestTimesContainer  = document.getElementById('bestTimes');
  const adviceContainer     = document.getElementById('aiAdvice');
  const festivalContainer   = document.getElementById('festivalImpact');

  // Retry up to 5 times if DOM containers are not rendered yet
  if (!statusContainer && retryCount < 5) {
    console.log(`[queue.js] DOM elements not ready, retrying... (${retryCount + 1}/5)`);
    setTimeout(() => loadQueueIntelligence(retryCount + 1), 100);
    return;
  }

  try {
    console.log('[queue.js] Fetching queue data from API...');
    const data = await API.get('queue');
    console.log('[queue.js] Queue API response:', data);

    const aiPred    = data.ai_prediction || {};
    const adminData = aiPred.admin_crowd_data;

    // 1. DISPLAY CURRENT QUEUE STATUS
    if (statusContainer) {
      const locationName = data.location || 'Sarva Darshan';
      const waitMinutes  = aiPred.predicted_wait_minutes || data.wait_minutes || '—';
      const crowdDensity = adminData?.queue_status || aiPred.current_crowd_level || data.crowd_density || '—';
      const peopleCount  = adminData?.estimated_crowd || data.people_count || 0;
      const lastUpdated  = aiPred.prediction_timestamp || new Date().toISOString();
      const updatedTime  = new Date(lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      statusContainer.innerHTML = `
        <div class="stat-item" style="display:flex; justify-content:space-between; margin-bottom:0.5rem; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.06);">
          <span class="stat-label" style="color:var(--muted); font-size:0.9rem;">Location</span>
          <span class="stat-value" style="font-weight:700;">${locationName}</span>
        </div>
        <div class="stat-item" style="display:flex; justify-content:space-between; margin-bottom:0.5rem; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.06);">
          <span class="stat-label" style="color:var(--muted); font-size:0.9rem;">Current Wait</span>
          <span class="stat-value" style="font-weight:700; color:var(--gold);">${waitMinutes} min</span>
        </div>
        <div class="stat-item" style="display:flex; justify-content:space-between; margin-bottom:0.5rem; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.06);">
          <span class="stat-label" style="color:var(--muted); font-size:0.9rem;">Crowd Density</span>
          <span class="stat-value" style="font-weight:700;">${crowdDensity}</span>
        </div>
        <div class="stat-item" style="display:flex; justify-content:space-between; margin-bottom:0.5rem; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.06);">
          <span class="stat-label" style="color:var(--muted); font-size:0.9rem;">People in Queue</span>
          <span class="stat-value" style="font-weight:700;">${Number(peopleCount).toLocaleString()} devotees</span>
        </div>
        <div class="stat-item" style="display:flex; justify-content:space-between; margin-bottom:0.5rem; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.06);">
          <span class="stat-label" style="color:var(--muted); font-size:0.9rem;">Data Source</span>
          <span class="stat-value" style="font-size:0.85rem; color:${adminData ? '#10B981' : 'var(--gold)'};">${adminData ? '📊 Admin Data' : '🤖 AI Prediction'}</span>
        </div>
        <div class="stat-item" style="display:flex; justify-content:space-between; padding:0.4rem 0;">
          <span class="stat-label" style="color:var(--muted); font-size:0.9rem;">Last Updated</span>
          <span class="stat-value" style="font-size:0.85rem; color:var(--muted);">${updatedTime}</span>
        </div>
      `;

      // Update pill badge
      const sourceTag = document.getElementById('queueSourceTag');
      if (sourceTag) {
        sourceTag.textContent = adminData ? 'Live Admin Data' : 'AI Prediction';
        sourceTag.style.background = adminData ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)';
        sourceTag.style.color = adminData ? '#10B981' : 'var(--gold)';
      }
    }

    // 2. DISPLAY AI PREDICTION
    if (predictionContainer) {
      const crowdLevel    = (adminData?.queue_status || aiPred.current_crowd_level || 'Moderate').toString();
      const currentCrowd  = adminData?.estimated_crowd || data.people_count || 0;
      const normLevel     = crowdLevel.toLowerCase();

      let action      = 'JOIN NOW';
      let actionColor = '#10B981';
      let actionIcon  = '✅';

      if (normLevel.includes('moderate')) {
        action = 'CONSIDER JOINING';
        actionColor = '#F59E0B';
        actionIcon = '⚠️';
      } else if (normLevel.includes('high')) {
        action = 'WAIT';
        actionColor = '#EF4444';
        actionIcon = '⏳';
      } else if (normLevel.includes('critical') || normLevel.includes('very high')) {
        action = 'AVOID';
        actionColor = '#DC2626';
        actionIcon = '🚫';
      }

      let recommendationMessage = '';
      if (normLevel.includes('low')) {
        recommendationMessage = 'Good time to join. Queue is currently less crowded.';
      } else if (normLevel.includes('moderate')) {
        recommendationMessage = 'Moderate crowd. You can join now, or wait for lower evening rush.';
      } else if (normLevel.includes('high')) {
        recommendationMessage = 'High crowd detected. Consider waiting or choosing early morning hours.';
      } else {
        recommendationMessage = 'Heavy rush detected. Expected long waiting time.';
      }

      if (aiPred.best_times_to_join && aiPred.best_times_to_join.length > 0) {
        const bt = aiPred.best_times_to_join[0];
        recommendationMessage += ` Best time: ${bt.time} (${bt.recommendation}).`;
      }

      predictionContainer.innerHTML = `
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem;">
          <div style="background:rgba(255,255,255,0.04); padding:0.75rem; border-radius:8px;">
            <div style="font-size:0.75rem; color:var(--muted);">Queue Status</div>
            <div style="font-size:1.1rem; font-weight:700; color:var(--gold);">${crowdLevel}</div>
          </div>
          <div style="background:rgba(255,255,255,0.04); padding:0.75rem; border-radius:8px;">
            <div style="font-size:0.75rem; color:var(--muted);">Recommended Action</div>
            <div style="font-size:1rem; font-weight:700; color:${actionColor};">${actionIcon} ${action}</div>
          </div>
          <div style="background:rgba(255,255,255,0.04); padding:0.75rem; border-radius:8px;">
            <div style="font-size:0.75rem; color:var(--muted);">Predicted Wait</div>
            <div style="font-size:1.1rem; font-weight:700;">${aiPred.predicted_wait_minutes || '—'} min</div>
          </div>
          <div style="background:rgba(255,255,255,0.04); padding:0.75rem; border-radius:8px;">
            <div style="font-size:0.75rem; color:var(--muted);">Reported Crowd</div>
            <div style="font-size:1.1rem; font-weight:700;">${Number(currentCrowd).toLocaleString()}</div>
          </div>
        </div>
        <div style="padding:0.75rem; background:rgba(124,58,237,0.08); border:1px solid rgba(124,58,237,0.2); border-radius:8px; font-size:0.88rem;">
          💡 <strong>AI Guidance:</strong> ${recommendationMessage}
        </div>
        ${data.prediction_disclaimer ? `<p style="font-size:0.72rem; color:var(--muted); margin-top:0.5rem;">${data.prediction_disclaimer}</p>` : ''}
      `;
    }

    // 3. DISPLAY CROWD TREND
    if (trendContainer && aiPred.crowd_trend_next_6_hours) {
      const trends = aiPred.crowd_trend_next_6_hours;
      trendContainer.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap:0.75rem; margin-top:0.5rem;">
          ${trends.map(t => {
            const lvl = (t.crowd_level || 'Low').toString();
            const color = lvl.toLowerCase().includes('high') ? '#EF4444' : lvl.toLowerCase().includes('moderate') ? '#F59E0B' : '#10B981';
            return `
              <div style="background:rgba(255,255,255,0.04); padding:0.75rem; border-radius:8px; text-align:center;">
                <div style="font-size:0.8rem; color:var(--muted);">${t.time}</div>
                <div style="font-weight:700; color:${color}; font-size:0.95rem; margin:0.2rem 0;">${lvl}</div>
                <div style="font-size:0.75rem; color:var(--muted);">${t.predicted_wait_minutes || '—'} min wait</div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    }

    // 4. DISPLAY BEST TIMES
    if (bestTimesContainer) {
      const bestTimes = aiPred.best_times_to_join || [];
      if (bestTimes.length === 0) {
        bestTimesContainer.innerHTML = '<p style="color:var(--muted);">No specific window recommended in next 24h.</p>';
      } else {
        bestTimesContainer.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:0.5rem; margin-top:0.5rem;">
            ${bestTimes.slice(0, 4).map((t, i) => `
              <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(255,255,255,0.04); padding:0.6rem 0.8rem; border-radius:8px;">
                <div style="display:flex; align-items:center; gap:0.6rem;">
                  <span style="background:var(--gold); color:#000; font-weight:800; font-size:0.75rem; width:20px; height:20px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;">${i + 1}</span>
                  <span style="font-weight:700;">${t.time}</span>
                </div>
                <span style="font-size:0.85rem; color:#10B981;">${t.recommendation}</span>
              </div>
            `).join('')}
          </div>
        `;
      }
    }

    // 5. DISPLAY AI ADVICE
    if (adviceContainer) {
      const adviceList = aiPred.ai_advice || [
        'Join Sarva Darshan queue early in the morning for shorter wait times.',
        'Carry drinking water and essential medicines inside the queue complex.'
      ];
      adviceContainer.innerHTML = `
        <ul style="list-style:none; padding:0; margin:0.5rem 0 0 0; display:flex; flex-direction:column; gap:0.5rem;">
          ${adviceList.map(a => `
            <li style="padding:0.6rem 0.8rem; background:rgba(255,255,255,0.04); border-left:3px solid var(--gold); border-radius:0 6px 6px 0; font-size:0.88rem;">
              💡 ${a}
            </li>
          `).join('')}
        </ul>
      `;
    }

    // 6. DISPLAY FESTIVAL IMPACT
    if (festivalContainer) {
      const festivals = aiPred.festival_impacts || [];
      if (adminData && adminData.festival) {
        festivalContainer.innerHTML = `
          <div style="padding:0.75rem; background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3); border-radius:8px; font-size:0.88rem;">
            🎉 <strong>Festival Impact (Admin Reported):</strong> High rush expected due to ongoing festival activities. Please follow TTD ground control.
          </div>
        `;
      } else if (festivals.length > 0) {
        festivalContainer.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:0.5rem; margin-top:0.5rem;">
            ${festivals.map(f => `
              <div style="padding:0.75rem; background:rgba(245,158,11,0.1); border-radius:8px; font-size:0.88rem;">
                🎉 <strong>${f.festival}:</strong> ${f.description} (Multiplier: ×${f.multiplier})
              </div>
            `).join('')}
          </div>
        `;
      } else {
        festivalContainer.innerHTML = '<p style="color:var(--muted); font-size:0.85rem;">No active festival impact reported for today.</p>';
      }
    }

  } catch (error) {
    console.error('[queue.js] Failed to load queue intelligence:', error);
    const containers = [statusContainer, predictionContainer, trendContainer, bestTimesContainer, adviceContainer, festivalContainer];
    containers.forEach(c => {
      if (c) c.innerHTML = '<p style="color:#EF4444; font-size:0.85rem;">⚠ Unable to load live queue data. Please check connection.</p>';
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
    const wait = data.ai_prediction?.predicted_wait_minutes || data.wait_minutes || '—';
    const crowd = data.ai_prediction?.admin_crowd_data?.queue_status || data.ai_prediction?.current_crowd_level || data.crowd_density || '—';
    heroQueue.textContent = `${wait} min`;
    heroCrowd.textContent = crowd;
  } catch (error) {
    console.error('[queue.js] Failed to load hero stats:', error);
  }
}

// Export functions for app.js
window.loadQueueIntelligence = loadQueueIntelligence;
window.loadHeroStats = loadHeroStats;
