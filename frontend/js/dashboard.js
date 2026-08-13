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
        
        // Update current queue status card
        const queueStatus = document.getElementById('intelQueueStatus');
        const crowd = document.getElementById('intelCrowd');
        const trend = document.getElementById('intelTrend');
        const festival = document.getElementById('intelFestival');
        const prediction = document.getElementById('intelPrediction');
        const recommendation = document.getElementById('intelRecommendation');
        const dataSource = document.getElementById('queueDataSource');
        
        if (queueStatus) {
            const adminData = data.ai_prediction?.admin_crowd_data;
            queueStatus.textContent = adminData?.queue_status || data.crowd_density || '—';
        }
        
        if (crowd) {
            const adminData = data.ai_prediction?.admin_crowd_data;
            const count = adminData?.estimated_crowd || data.people_count || 0;
            crowd.textContent = count.toLocaleString();
        }
        
        if (trend) {
            const adminData = data.ai_prediction?.admin_crowd_data;
            const net = adminData?.net_pilgrims || 0;
            if (net > 100) {
                trend.textContent = '↑ INCREASING';
                trend.style.color = '#EF4444';
            } else if (net < -100) {
                trend.textContent = '↓ DECREASING';
                trend.style.color = '#10B981';
            } else {
                trend.textContent = '→ STABLE';
                trend.style.color = '#34D399';
            }
        }
        
        if (festival) {
            const adminData = data.ai_prediction?.admin_crowd_data;
            festival.textContent = adminData?.festival ? 'YES' : 'NO';
        }
        
        if (prediction) {
            const adminData = data.ai_prediction?.admin_crowd_data;
            const crowdLevel = adminData?.queue_status || data.ai_prediction?.current_crowd_level || 'Moderate';
            prediction.textContent = `Current: ${crowdLevel}. Predicted wait: ${data.ai_prediction?.predicted_wait_minutes || 0} min.`;
        }
        
        if (recommendation) {
            const bestTimes = data.ai_prediction?.best_times_to_join || [];
            if (bestTimes.length > 0) {
                recommendation.textContent = `Best time: ${bestTimes[0].time} (${bestTimes[0].recommendation})`;
            }
        }
        
        if (dataSource) {
            const adminData = data.ai_prediction?.admin_crowd_data;
            dataSource.textContent = adminData ? 'Live admin data' : 'AI Historical Prediction';
        }
        
    } catch (error) {
        console.error('Failed to load dashboard queue intelligence:', error);
    }
}

// Pilgrims receive only the public, backend-generated queue analysis.
async function loadQueueIntelligence() {
    try {
        const data = await API.get('queue');
        const setText = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };
        
        const adminData = data.ai_prediction?.admin_crowd_data;
        const dataSource = adminData ? 'Live admin data' : 'AI prediction';
        
        setText('queueDataSource', dataSource);
        setText('intelQueueStatus', adminData?.queue_status || data.ai_prediction?.current_crowd_level || 'N/A');
        setText('intelCrowd', Number(adminData?.estimated_crowd || data.people_count || 0).toLocaleString());
        
        // Calculate trend from admin data
        const net = adminData?.net_pilgrims || 0;
        let trend = 'STABLE';
        if (net > 100) trend = 'INCREASING';
        else if (net < -100) trend = 'DECREASING';
        setText('intelTrend', trend);
        
        setText('intelFestival', adminData?.festival ? 'YES' : 'NO');
        setText('intelPrediction', data.ai_prediction?.predicted_wait_minutes ? `${data.ai_prediction.predicted_wait_minutes} min wait` : 'Queue prediction unavailable.');
        
        // Get best time recommendation
        const bestTimes = data.ai_prediction?.best_times_to_join || [];
        const recommendation = bestTimes.length > 0 ? `${bestTimes[0].time} (${bestTimes[0].recommendation})` : 'Please follow TTD instructions.';
        setText('intelRecommendation', recommendation);
        
    } catch (error) {
        console.error('Failed to load queue intelligence:', error);
        const prediction = document.getElementById('intelPrediction');
        if (prediction) prediction.textContent = 'Queue intelligence is temporarily unavailable.';
    }
}

// Update date and time display
function updateDateTime() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const dayOptions = { weekday: 'long' };
    
    const dateElement = document.getElementById('currentDate');
    const dayElement = document.getElementById('currentDay');
    
    if (dateElement) {
        dateElement.textContent = now.toLocaleDateString('en-IN', options);
    }
    
    if (dayElement) {
        dayElement.textContent = now.toLocaleDateString('en-IN', dayOptions);
    }
    
    // Tithi calculation (simplified)
    const tithiElement = document.getElementById('tithi');
    if (tithiElement) {
        const tithi = calculateTithi(now);
        tithiElement.textContent = tithi;
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
            queueWaitElement.textContent = waitMinutes ? `${waitMinutes} min` : 'N/A';
        }
        
        if (crowdLevelElement) {
            const crowdLevel = data.ai_prediction?.current_crowd_level || data.crowd_density;
            crowdLevelElement.textContent = crowdLevel || 'N/A';
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
