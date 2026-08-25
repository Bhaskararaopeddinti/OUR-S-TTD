/**
 * queue.js – AI Queue Intelligence page implementation
 * Loads and displays predictive queue analysis with crowd trends and smart recommendations.
 * Fully synchronized with admin pilgrim flow data and backend predictive models.
 */
'use strict';

async function loadQueueIntelligence(retryCount = 0) {
  const statusContainer     = document.getElementById('queueStatus');
  const predictionContainer = document.getElementById('aiPrediction');
  const trendContainer      = document.getElementById('crowdTrend');
  const bestTimesContainer  = document.getElementById('bestTimes');
  const adviceContainer     = document.getElementById('aiAdvice');
  const festivalContainer   = document.getElementById('festivalImpact');

  // Retry up to 5 times if DOM containers are not rendered yet (SPA routing)
  if (!statusContainer && retryCount < 5) {
    setTimeout(() => loadQueueIntelligence(retryCount + 1), 100);
    return;
  }

  try {
    const data = await API.get('queue');
    const aiPred = data.ai_prediction || {};
    const adminData = aiPred.admin_crowd_data;

    // ─────────────────────────────────────────────────────────────
    // 1. CURRENT QUEUE STATUS (Master Prompt Section 5)
    // ─────────────────────────────────────────────────────────────
    if (statusContainer) {
      const statusBadge = aiPred.queue_status_badge || (adminData?.queue_status ? `🔴 ${adminData.queue_status}` : '🟡 MODERATE');
      const waitingCond = aiPred.waiting_condition || (data.wait_minutes ? `Approx ${data.wait_minutes} mins` : 'Moderate (2–3 hrs)');
      const incoming = aiPred.incoming_devotees ?? adminData?.incoming_pilgrims ?? 1800;
      const outgoing = aiPred.outgoing_devotees ?? adminData?.outgoing_pilgrims ?? 1100;
      const timePeriod = aiPred.current_time_period || adminData?.slot || 'Current Slot';
      const trend = aiPred.crowd_trend || 'Stable';
      const totalCrowd = aiPred.estimated_crowd ?? adminData?.estimated_crowd ?? data.people_count ?? 0;
      const lastUpdated = aiPred.prediction_timestamp || new Date().toISOString();
      const updatedTime = new Date(lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      let trendColor = '#34D399'; // green
      let trendIcon = '→';
      if (trend === 'Increasing') {
        trendColor = '#EF4444';
        trendIcon = '↗';
      } else if (trend === 'Decreasing') {
        trendColor = '#10B981';
        trendIcon = '↘';
      }

      statusContainer.innerHTML = `
        <div style="background:rgba(255,255,255,0.03); padding:1rem; border-radius:10px; margin-bottom:0.75rem; border:1px solid rgba(255,255,255,0.08);">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.75rem;">
            <div>
              <span style="font-size:0.78rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px;">Queue Status</span>
              <div style="font-size:1.35rem; font-weight:800; color:var(--gold); margin-top:0.15rem;">
                Queue Status: ${statusBadge}
              </div>
            </div>
            <div style="text-align:right;">
              <span style="font-size:0.75rem; color:var(--muted);">Time Period</span>
              <div style="font-size:0.95rem; font-weight:700; color:var(--text);">${timePeriod}</div>
            </div>
          </div>

          <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:0.6rem; margin-top:0.6rem;">
            <div style="background:rgba(0,0,0,0.2); padding:0.6rem 0.8rem; border-radius:8px;">
              <div style="font-size:0.72rem; color:var(--muted);">Incoming Devotees</div>
              <div style="font-size:1.1rem; font-weight:700; color:#60A5FA;">📥 ${Number(incoming).toLocaleString()}</div>
            </div>
            <div style="background:rgba(0,0,0,0.2); padding:0.6rem 0.8rem; border-radius:8px;">
              <div style="font-size:0.72rem; color:var(--muted);">Outgoing Devotees</div>
              <div style="font-size:1.1rem; font-weight:700; color:#34D399;">📤 ${Number(outgoing).toLocaleString()}</div>
            </div>
            <div style="background:rgba(0,0,0,0.2); padding:0.6rem 0.8rem; border-radius:8px;">
              <div style="font-size:0.72rem; color:var(--muted);">Crowd Trend</div>
              <div style="font-size:1.1rem; font-weight:700; color:${trendColor};">${trendIcon} ${trend}</div>
            </div>
            <div style="background:rgba(0,0,0,0.2); padding:0.6rem 0.8rem; border-radius:8px;">
              <div style="font-size:0.72rem; color:var(--muted);">Waiting Condition</div>
              <div style="font-size:1.05rem; font-weight:700; color:var(--gold);">${waitingCond}</div>
            </div>
          </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; padding:0 0.2rem; font-size:0.78rem; color:var(--muted);">
          <span>Total Devotees Present: <strong style="color:var(--text);">${Number(totalCrowd).toLocaleString()}</strong></span>
          <span>Updated: ${updatedTime}</span>
        </div>
      `;

      // Update pill badge
      const sourceTag = document.getElementById('queueSourceTag');
      if (sourceTag) {
        const isLive = Boolean(aiPred.admin_data_used);
        sourceTag.textContent = isLive ? '🟢 Live Admin Data' : '🤖 AI Calculated';
        sourceTag.style.background = isLive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)';
        sourceTag.style.color = isLive ? '#10B981' : 'var(--gold)';
      }
    }

    // ─────────────────────────────────────────────────────────────
    // 2. AI PREDICTION (Master Prompt Section 9)
    // ─────────────────────────────────────────────────────────────
    if (predictionContainer) {
      const predSummary = aiPred.ai_prediction_summary || {};
      const expectedCrowd = predSummary.expected_crowd || aiPred.current_crowd_level?.toUpperCase() || 'MODERATE';
      const points = predSummary.points || [
        'Crowd is expected to remain stable during the next time slot.',
        'Queue waiting time expected to remain manageable.',
        'Recommended action: Consider joining during the next low-crowd period.'
      ];

      predictionContainer.innerHTML = `
        <div style="background:rgba(124,58,237,0.08); border:1px solid rgba(124,58,237,0.25); border-radius:10px; padding:0.9rem 1rem;">
          <div style="font-size:1.15rem; font-weight:800; color:var(--gold); margin-bottom:0.6rem;">
            Expected Crowd: ${expectedCrowd}
          </div>
          <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:0.45rem;">
            ${points.map(pt => `
              <li style="display:flex; align-items:flex-start; gap:0.45rem; font-size:0.88rem; line-height:1.4;">
                <span style="color:#A78BFA; font-size:1rem;">•</span>
                <span>${pt}</span>
              </li>
            `).join('')}
          </ul>
        </div>
      `;
    }

    // ─────────────────────────────────────────────────────────────
    // 3. CROWD TREND — NEXT 6 HOURS (Master Prompt Section 6)
    // ─────────────────────────────────────────────────────────────
    if (trendContainer) {
      const trends = aiPred.crowd_trend_next_6_hours || [];
      if (trends.length === 0) {
        trendContainer.innerHTML = '<p style="color:var(--muted); font-size:0.88rem;">Trend calculations updating with latest slot data...</p>';
      } else {
        trendContainer.innerHTML = `
          <div style="overflow-x:auto; margin-top:0.4rem;">
            <table class="admin-table" style="width:100%; border-collapse:collapse; text-align:left; font-size:0.88rem;">
              <thead>
                <tr style="background:rgba(255,255,255,0.06); color:var(--gold);">
                  <th style="padding:0.6rem 0.8rem; border-bottom:1px solid rgba(255,255,255,0.1);">Time</th>
                  <th style="padding:0.6rem 0.8rem; border-bottom:1px solid rgba(255,255,255,0.1); text-align:right;">Expected Crowd</th>
                  <th style="padding:0.6rem 0.8rem; border-bottom:1px solid rgba(255,255,255,0.1); text-align:center;">Status</th>
                  <th style="padding:0.6rem 0.8rem; border-bottom:1px solid rgba(255,255,255,0.1); text-align:right;">Est. Wait</th>
                </tr>
              </thead>
              <tbody>
                ${trends.map(t => {
                  const statusStr = t.status || (t.status_level ? `🟢 ${t.status_level}` : '🟡 Moderate');
                  return `
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                      <td style="padding:0.65rem 0.8rem; font-weight:600;">${t.time}</td>
                      <td style="padding:0.65rem 0.8rem; text-align:right; font-weight:700; color:#A78BFA;">${Number(t.expected_crowd || 0).toLocaleString()}</td>
                      <td style="padding:0.65rem 0.8rem; text-align:center; font-weight:700;">${statusStr}</td>
                      <td style="padding:0.65rem 0.8rem; text-align:right; color:var(--muted);">${t.predicted_wait_minutes || '—'} min</td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        `;
      }
    }

    // ─────────────────────────────────────────────────────────────
    // 4. BEST TIME TO JOIN QUEUE (Master Prompt Section 7)
    // ─────────────────────────────────────────────────────────────
    if (bestTimesContainer) {
      const bestTimeObj = aiPred.best_time_to_join;
      if (bestTimeObj && bestTimeObj.has_data && bestTimeObj.time_window) {
        const reasons = bestTimeObj.reasons || [
          'Lower expected crowd',
          'More outgoing devotees',
          'Better incoming/outgoing balance'
        ];

        bestTimesContainer.innerHTML = `
          <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25); border-radius:10px; padding:0.9rem 1rem;">
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
              <span style="font-size:1.3rem;">⭐</span>
              <span style="font-size:1.2rem; font-weight:800; color:#34D399;">${bestTimeObj.time_window}</span>
            </div>
            <div style="font-size:0.8rem; color:var(--muted); margin-bottom:0.4rem;">Reason:</div>
            <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:0.35rem;">
              ${reasons.map(r => `
                <li style="display:flex; align-items:center; gap:0.45rem; font-size:0.86rem;">
                  <span style="color:#10B981;">✔</span>
                  <span>${r}</span>
                </li>
              `).join('')}
            </ul>
          </div>
        `;
      } else {
        bestTimesContainer.innerHTML = `
          <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:1rem; text-align:center;">
            <p style="color:var(--muted); font-size:0.9rem; margin:0;">Not enough data to determine the best time.</p>
          </div>
        `;
      }
    }

    // ─────────────────────────────────────────────────────────────
    // 5. AI-GENERATED QUEUE ADVICE (Master Prompt Section 8)
    // ─────────────────────────────────────────────────────────────
    if (adviceContainer) {
      const adviceList = aiPred.ai_advice || [
        'Avoid the queue during peak crowd periods.',
        'Consider joining during the lower-crowd time slot.',
        'Keep water and essential items with you.',
        'Follow TTD queue instructions.',
        'Check the latest queue status before joining.'
      ];

      adviceContainer.innerHTML = `
        <ul style="list-style:none; padding:0; margin:0.3rem 0 0 0; display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:0.6rem;">
          ${adviceList.map(a => `
            <li style="padding:0.65rem 0.85rem; background:rgba(255,255,255,0.04); border-left:3px solid var(--gold); border-radius:0 8px 8px 0; font-size:0.88rem; line-height:1.4;">
              💡 ${a}
            </li>
          `).join('')}
        </ul>
      `;
    }

    // ─────────────────────────────────────────────────────────────
    // 6. FESTIVAL IMPACT (Master Prompt Section 10)
    // ─────────────────────────────────────────────────────────────
    if (festivalContainer) {
      const festivalObj = aiPred.festival_impact_summary;
      const isFestival = Boolean(festivalObj?.is_active || adminData?.festival);

      if (isFestival) {
        const points = festivalObj?.points || [
          'Expected crowd impact: High',
          'Queue demand: Increased',
          'Recommendation: Plan Darshan earlier.'
        ];

        festivalContainer.innerHTML = `
          <div style="background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.35); border-radius:10px; padding:0.9rem 1rem;">
            <div style="font-size:1.1rem; font-weight:800; color:#FBBF24; margin-bottom:0.5rem; display:flex; align-items:center; gap:0.5rem;">
              <span>🎉</span>
              <span>Festival: YES</span>
            </div>
            <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:0.35rem;">
              ${points.map(pt => `
                <li style="display:flex; align-items:flex-start; gap:0.45rem; font-size:0.88rem;">
                  <span style="color:#FBBF24;">•</span>
                  <span>${pt}</span>
                </li>
              `).join('')}
            </ul>
          </div>
        `;
      } else {
        festivalContainer.innerHTML = `
          <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:0.85rem 1rem;">
            <div style="font-size:1rem; font-weight:700; color:var(--text); margin-bottom:0.3rem;">
              Festival Impact: Normal
            </div>
            <p style="color:var(--muted); font-size:0.85rem; margin:0;">
              Normal devotee inflow pattern observed. Standard compartment clearance cycles in effect.
            </p>
          </div>
        `;
      }
    }

  } catch (error) {
    console.error('[queue.js] Failed to load queue intelligence:', error);
    const fallbackMsg = '<p style="color:var(--muted); font-size:0.88rem; padding:0.5rem 0;">Queue data is currently unavailable. Please check again shortly.</p>';
    const containers = [statusContainer, predictionContainer, trendContainer, bestTimesContainer, adviceContainer, festivalContainer];
    containers.forEach(c => {
      if (c) c.innerHTML = fallbackMsg;
    });
  }
}

// Update hero stats on home/dashboard page
async function loadHeroStats() {
  const queueWaitEl = document.getElementById('queueWaitTime');
  const crowdLevelEl = document.getElementById('crowdLevel');

  if (!queueWaitEl && !crowdLevelEl) return;

  try {
    const data = await API.get('queue');
    const aiPred = data.ai_prediction || {};
    const wait = aiPred.predicted_wait_minutes || data.wait_minutes || '—';
    const crowd = aiPred.current_crowd_level || aiPred.queue_status || 'Moderate';

    if (queueWaitEl) queueWaitEl.textContent = `${wait} min`;
    if (crowdLevelEl) crowdLevelEl.textContent = crowd;
  } catch (error) {
    console.error('[queue.js] Failed to load hero stats:', error);
  }
}

window.loadQueueIntelligence = loadQueueIntelligence;
window.loadHeroStats = loadHeroStats;
