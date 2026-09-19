// =====================================================
// OURS TTD – Dashboard JavaScript
// Handles dashboard page functionality
// =====================================================

// Load dashboard data when page is rendered
function loadDashboard() {
    console.log('Loading dashboard...');
    
    // Update current date and time
    updateDateTime();
    
    // Load queue status
    loadQueueStatus();
    
    // Load queue intelligence for dashboard cards
    loadDashboardQueueIntelligence();
    
    // Load weather information
    loadWeather();
    
    // Load announcements
    loadAnnouncements();
    
    // Load user profile
    loadUserProfile();
    
    // Set up refresh interval (clear existing to prevent duplicate timers)
    if (window._dashboardDateTimeInterval) {
        clearInterval(window._dashboardDateTimeInterval);
    }
    window._dashboardDateTimeInterval = setInterval(updateDateTime, 60000); // Update every minute
}

// Export functions for use in app.js
window.loadDashboard = loadDashboard;
window.loadDashboardQueueIntelligence = loadDashboardQueueIntelligence;
window.loadQueueStatus = loadQueueStatus;

// Load queue intelligence for dashboard cards
async function loadDashboardQueueIntelligence() {
    try {
        const data = await API.get('queue');
        const aiPred = data.ai_prediction || {};
        const adminData = aiPred.admin_crowd_data;
        
        // Update current queue status card
        const queueStatus = document.getElementById('intelQueueStatus');
        const crowd = document.getElementById('intelCrowd');
        const trend = document.getElementById('intelTrend');
        const festival = document.getElementById('intelFestival');
        const prediction = document.getElementById('intelPrediction');
        const recommendation = document.getElementById('intelRecommendation');
        const dataSource = document.getElementById('queueDataSource');
        
        if (queueStatus) {
            queueStatus.textContent = aiPred.queue_status_badge || (adminData?.queue_status ? `🔴 ${adminData.queue_status}` : 'No crowd data available');
        }
        
        if (crowd) {
            const count = aiPred.estimated_crowd ?? adminData?.estimated_crowd ?? data.people_count ?? 0;
            crowd.textContent = Number(count).toLocaleString();
        }
        
        if (trend) {
            const trendLabel = aiPred.crowd_trend || 'Stable';
            if (trendLabel === 'Increasing') {
                trend.textContent = '↗ INCREASING';
                trend.style.color = '#EF4444';
            } else if (trendLabel === 'Decreasing') {
                trend.textContent = '↘ DECREASING';
                trend.style.color = '#10B981';
            } else {
                trend.textContent = '→ STABLE';
                trend.style.color = '#34D399';
            }
        }
        
        if (festival) {
            const isFest = Boolean(aiPred.festival_impact_summary?.is_active || adminData?.festival);
            festival.textContent = isFest ? 'YES' : 'NO';
            festival.style.color = isFest ? '#FBBF24' : '#94A3B8';
        }
        
        if (prediction) {
            const predObj = aiPred.ai_prediction_summary || {};
            const expCrowd = predObj.expected_crowd || aiPred.current_crowd_level?.toUpperCase() || 'MODERATE';
            const waitMin = aiPred.predicted_wait_minutes || 60;
            const hrs = Math.floor(waitMin / 60);
            const mins = waitMin % 60;
            const waitStr = hrs > 0 ? (mins > 0 ? `${hrs}h ${mins}m` : `${hrs} hrs`) : `${waitMin} min`;
            const pts = predObj.points || [];
            prediction.innerHTML = `<strong>Expected Crowd: ${expCrowd}</strong> (Wait: ~${waitStr})<br>${pts[0] || 'Queue wait times remain normal.'}`;
        }
        
        if (recommendation) {
            const bestTimeObj = aiPred.best_time_to_join;
            if (bestTimeObj && bestTimeObj.has_data && bestTimeObj.time_window) {
                recommendation.textContent = `⭐ Best Time to Join: ${bestTimeObj.time_window}`;
                recommendation.style.color = '#34D399';
            } else {
                recommendation.textContent = '⭐ Best Time: Check Darshan Queue page for live guidance.';
            }
        }
        
        if (dataSource) {
            const isLive = Boolean(aiPred.admin_data_used);
            dataSource.textContent = isLive ? '🟢 Live Admin Data' : '🤖 AI Calculated';
            dataSource.style.color = isLive ? '#10B981' : 'var(--gold)';
        }
        
    } catch (error) {
        console.error('Failed to load dashboard queue intelligence:', error);
    }
}

// Update date and time display
function updateDateTime() {
    const now = new Date();
    const dateOptions = { day: 'numeric', month: 'short', year: 'numeric' };
    const dayOptions = { weekday: 'long' };
    
    const dateElement = document.getElementById('currentDate');
    const dayElement = document.getElementById('currentDay');
    
    if (dateElement) {
        dateElement.textContent = now.toLocaleDateString('en-IN', dateOptions);
    }
    
    if (dayElement) {
        dayElement.textContent = now.toLocaleDateString('en-IN', dayOptions);
    }
    
    // Tithi calculation (simplified)
    const tithiElement = document.getElementById('tithi');
    if (tithiElement) {
        const tithi = calculateTithi(now);
        tithiElement.textContent = `Tithi: ${tithi}`;
    }
}

// Calculate Tithi (simplified version)
function calculateTithi(date) {
    const lunarMonth = 29.53; // Average lunar month in days
    const epoch = new Date('2000-01-06').getTime(); // Known new moon date
    const diff = date.getTime() - epoch;
    const daysSinceEpoch = diff / (1000 * 60 * 60 * 24);
    const tithiNumber = Math.floor((daysSinceEpoch % lunarMonth) / lunarMonth * 30) + 1;
    
    const tithiNames = [
        'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
        'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
        'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima',
        'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
        'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
        'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Amavasya'
    ];
    
    return tithiNames[tithiNumber - 1] || 'Unknown';
}

// Load queue status from API
async function loadQueueStatus() {
    try {
        const data = await API.get('queue');
        
        const queueWaitElement = document.getElementById('queueWaitTime');
        const crowdLevelElement = document.getElementById('crowdLevel');
        
        if (queueWaitElement) {
            const waitMinutes = data.ai_prediction?.predicted_wait_minutes || data.wait_minutes;
            if (waitMinutes) {
                const hrs = Math.floor(waitMinutes / 60);
                const mins = waitMinutes % 60;
                queueWaitElement.textContent = hrs > 0 ? (mins > 0 ? `${hrs}h ${mins}m` : `${hrs} hrs`) : `${waitMinutes} min`;
            } else {
                queueWaitElement.textContent = 'Normal';
            }
        }
        
        if (crowdLevelElement) {
            const crowdLevel = data.ai_prediction?.current_crowd_level || (data.crowd_density && data.crowd_density !== 'Not published by TTD' ? data.crowd_density : 'Moderate');
            crowdLevelElement.textContent = crowdLevel || 'Moderate';
        }
        
        // Update alert message
        const alertMessage = document.getElementById('alertMessage');
        if (alertMessage && data.message) {
            alertMessage.textContent = data.message;
        }
    } catch (error) {
        console.error('Failed to load queue status:', error);
    }
}

// Load weather information
function loadWeather() {
    // Simulated weather data (in production, use real weather API)
    const weatherData = {
        temp: 28,
        humidity: 65,
        windSpeed: 12,
        condition: 'Partly Cloudy',
        icon: '⛅'
    };
    
    const tempElement = document.getElementById('temperature');
    const weatherTempElement = document.getElementById('weatherTemp');
    const humidityElement = document.getElementById('humidity');
    const windSpeedElement = document.getElementById('windSpeed');
    const weatherConditionElement = document.getElementById('weatherCondition');
    const weatherIconElement = document.getElementById('weatherIcon');
    
    if (tempElement) {
        tempElement.textContent = `${weatherData.temp}°C`;
    }
    
    if (weatherTempElement) {
        weatherTempElement.textContent = `${weatherData.temp}°C`;
    }
    
    if (humidityElement) {
        humidityElement.textContent = `${weatherData.humidity}%`;
    }
    
    if (windSpeedElement) {
        windSpeedElement.textContent = `${weatherData.windSpeed} km/h`;
    }
    
    if (weatherConditionElement) {
        weatherConditionElement.textContent = weatherData.condition;
    }
    
    if (weatherIconElement) {
        weatherIconElement.textContent = weatherData.icon;
    }
}

// Load TTD announcements
function loadAnnouncements() {
    // In production, load from API
    const announcements = [
        {
            time: '10:30 AM',
            message: 'Special darshan arrangements for Srivari Brahmotsavams'
        },
        {
            time: '9:00 AM',
            message: 'Free laddu distribution at VQC exit'
        },
        {
            time: '8:00 AM',
            message: 'Additional compartments opened for Sarva Darshan'
        }
    ];
    
    const announcementsList = document.getElementById('announcementsList');
    if (announcementsList) {
        announcementsList.innerHTML = announcements.map(ann => `
            <div class="announcement-item">
                <span class="announcement-time">${ann.time}</span>
                <p>${ann.message}</p>
            </div>
        `).join('');
    }
}

// Load user profile
function loadUserProfile() {
    const profileName = document.getElementById('profileName');
    const profileEmail = document.getElementById('profileEmail');
    const profileRole = document.getElementById('profileRole');
    
    // Check if user is logged in using the same token key as app.js
    const token = localStorage.getItem('authToken');
    
    // Get user info from the global authUser state set by app.js
    // Use a try-catch to safely access the global variable
    let user = {};
    try {
        user = typeof authUser !== 'undefined' ? authUser : {};
    } catch (e) {
        user = {};
    }
    
    const loginBtn = document.getElementById('loginBtn');
    
    if (token && user.name) {
        if (profileName) profileName.textContent = user.name;
        if (profileEmail) profileEmail.textContent = user.email || 'N/A';
        if (profileRole) profileRole.textContent = user.role || 'Pilgrim';
        
        if (loginBtn) {
            loginBtn.textContent = 'Logout';
            // Use the global logout function from app.js
            loginBtn.onclick = function() {
                const authBtn = document.getElementById('authBtn');
                if (authBtn) authBtn.click();
            };
        }
    } else {
        // User is logged out - reset UI to show login option
        if (profileName) profileName.textContent = 'Guest';
        if (profileEmail) profileEmail.textContent = 'N/A';
        if (profileRole) profileRole.textContent = 'Guest';
        
        if (loginBtn) {
            loginBtn.textContent = 'Login';
            loginBtn.onclick = function() {
                // Trigger the main auth dialog from app.js
                const authBtn = document.getElementById('authBtn');
                if (authBtn) authBtn.click();
            };
        }
    }
}



// Export functions for external use
window.loadDashboard = loadDashboard;
window.loadDashboardQueueIntelligence = loadDashboardQueueIntelligence;
window.loadQueueStatus = loadQueueStatus;
window.updateDateTime = updateDateTime;

// Handle sidebar toggle
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.querySelector('.sidebar-overlay');

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('open');
        if (sidebarOverlay) {
            sidebarOverlay.classList.toggle('active');
        }
    });
}

if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', function() {
        sidebar.classList.remove('open');
        sidebarOverlay.classList.remove('active');
    });
}

// Auto-load if dashboard DOM is already mounted
if (document.getElementById('queueWaitTime') || document.querySelector('.dashboard-page') || document.getElementById('currentDate')) {
    updateDateTime();
    loadDashboard();
}
