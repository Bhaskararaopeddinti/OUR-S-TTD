/**
 * emergency.js – Emergency SOS functionality
 * Handles SOS button, location sharing, and emergency contacts
 */
'use strict';

let emergencyLocation = null;
let sosActivated = false;

// Initialize emergency page
function initEmergency() {
  // SOS button
  document.getElementById('sosButton')?.addEventListener('click', handleSOS);
  
  // Get location button
  document.getElementById('getEmergencyLocation')?.addEventListener('click', getEmergencyLocation);
}

// Handle SOS button press
function handleSOS() {
  if (sosActivated) {
    // Cancel SOS
    cancelSOS();
  } else {
    // Activate SOS
    activateSOS();
  }
}

// Activate SOS
function activateSOS() {
  sosActivated = true;
  const sosButton = document.getElementById('sosButton');
  const sosStatus = document.getElementById('sosStatus');
  
  if (sosButton) {
    sosButton.classList.add('active');
    sosButton.innerHTML = `
      <span class="sos-icon">🛑</span>
      <span class="sos-text">CANCEL</span>
    `;
  }
  
  if (sosStatus) {
    sosStatus.innerHTML = '<div class="sos-activating">Activating emergency response...</div>';
  }
  
  // Get current location
  getEmergencyLocation().then(() => {
    // Send emergency alert
    sendEmergencyAlert();
  });
  
  // Play alert sound (if available)
  playAlertSound();
  
  // Vibrate device
  if (navigator.vibrate) {
    navigator.vibrate([500, 200, 500, 200, 500]);
  }
}

// Cancel SOS
function cancelSOS() {
  sosActivated = false;
  const sosButton = document.getElementById('sosButton');
  const sosStatus = document.getElementById('sosStatus');
  
  if (sosButton) {
    sosButton.classList.remove('active');
    sosButton.innerHTML = `
      <span class="sos-icon">🚨</span>
      <span class="sos-text">SOS</span>
    `;
  }
  
  if (sosStatus) {
    sosStatus.innerHTML = '<div class="sos-cancelled">Emergency alert cancelled</div>';
  }
  
  showToast('Emergency alert cancelled', 'info');
}

// Get emergency location
function getEmergencyLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      const locationDisplay = document.getElementById('emergencyLocation');
      if (locationDisplay) {
        locationDisplay.innerHTML = '<p class="error">Geolocation not supported</p>';
      }
      reject('Geolocation not supported');
      return;
    }
    
    const locationDisplay = document.getElementById('emergencyLocation');
    if (locationDisplay) {
      locationDisplay.innerHTML = '<div class="loading">Getting location...</div>';
    }
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        emergencyLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy
        };
        
        if (locationDisplay) {
          locationDisplay.innerHTML = `
            <div class="location-coordinates">
              <div class="coord-item">
                <span class="coord-label">Latitude:</span>
                <span class="coord-value">${emergencyLocation.latitude.toFixed(6)}</span>
              </div>
              <div class="coord-item">
                <span class="coord-label">Longitude:</span>
                <span class="coord-value">${emergencyLocation.longitude.toFixed(6)}</span>
              </div>
              <div class="coord-item">
                <span class="coord-label">Accuracy:</span>
                <span class="coord-value">${emergencyLocation.accuracy.toFixed(0)} meters</span>
              </div>
            </div>
          `;
        }
        
        resolve(emergencyLocation);
      },
      (error) => {
        let errorMessage = 'Unable to get location';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location permission denied';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location unavailable';
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out';
            break;
        }
        
        if (locationDisplay) {
          locationDisplay.innerHTML = `<p class="error">${errorMessage}</p>`;
        }
        
        reject(errorMessage);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  });
}

// Send emergency alert
function sendEmergencyAlert() {
  const sosStatus = document.getElementById('sosStatus');
  
  if (!emergencyLocation) {
    if (sosStatus) {
      sosStatus.innerHTML = '<div class="sos-error">Location not available. Please enable location services.</div>';
    }
    return;
  }
  
  // In production, send to emergency API
  // For demo, show success message
  if (sosStatus) {
    sosStatus.innerHTML = `
      <div class="sos-success">
        <div class="success-icon">✓</div>
        <div class="success-message">Emergency alert sent!</div>
        <div class="success-details">
          Location shared with TTD emergency services
        </div>
      </div>
    `;
  }
  
  showToast('Emergency alert sent to authorities', 'success');
  
  // Log emergency alert
  console.log('Emergency alert sent:', {
    location: emergencyLocation,
    timestamp: new Date().toISOString()
  });
}

// Play alert sound
function playAlertSound() {
  // Create audio context for alert sound
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    gainNode.gain.value = 0.3;
    
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.5);
  } catch (error) {
    console.log('Audio not available:', error);
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  if (document.querySelector('.emergency-page')) {
    initEmergency();
  }
});
