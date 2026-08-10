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
    
    // Load weather information
    loadWeather();
    
    // Load announcements
    loadAnnouncements();
    
    // Load user profile
    loadUserProfile();
    
    // Set up refresh interval
    setInterval(updateDateTime, 60000); // Update every minute
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
    
    // Check if user is logged in
    const token = localStorage.getItem('auth_token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (token && user.name) {
        if (profileName) profileName.textContent = user.name;
        if (profileEmail) profileEmail.textContent = user.email || 'N/A';
        if (profileRole) profileRole.textContent = user.role || 'Pilgrim';
        
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.textContent = 'Logout';
            loginBtn.onclick = logout;
        }
    }
}

// Logout function
function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    showToast('Logged out successfully', 'success');
    loadUserProfile();
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the dashboard page
    if (document.querySelector('.dashboard-page')) {
        loadDashboard();
    }
});

// Handle sidebar navigation
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('nav-item')) {
        const page = e.target.dataset.page;
        if (page) {
            navigate(page);
        }
    }
});

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
