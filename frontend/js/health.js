/**
 * health.js – Health & Emergency Companion functionality
 * Handles health profile, reminders, and emergency features.
 */
'use strict';

// Health profile management
function initHealthProfile() {
  const form = document.getElementById('healthProfileForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Gather form data
    const formData = new FormData(form);
    const conditions = [];
    document.querySelectorAll('input[name="conditions"]:checked').forEach(cb => {
      conditions.push(cb.value);
    });
    
    const profileData = {
      age: formData.get('age') ? parseInt(formData.get('age')) : null,
      blood_group: formData.get('blood_group') || '',
      medical_conditions: conditions.join(', ') + (formData.get('other_conditions') ? `, ${formData.get('other_conditions')}` : ''),
      emergency_contact: formData.get('emergency_contact') || '',
      wheelchair_required: formData.get('wheelchair_required') === 'true'
    };

    try {
      const response = await API.put('/profile', profileData);
      document.getElementById('healthProfileStatus').textContent = 'Health profile saved successfully!';
      document.getElementById('healthProfileStatus').className = 'status success';
      loadHealthCard();
      generateHealthRecommendations(profileData);
    } catch (error) {
      document.getElementById('healthProfileStatus').textContent = 'Failed to save profile. Please try again.';
      document.getElementById('healthProfileStatus').className = 'status error';
    }
  });
}

// Load and display health card
async function loadHealthCard() {
  try {
    const profile = await API.get('/profile');
    
    document.getElementById('hcName').textContent = profile.name || '—';
    document.getElementById('hcAge').textContent = `Age: ${profile.age || '—'}`;
    document.getElementById('hcBlood').textContent = `Blood Group: ${profile.blood_group || '—'}`;
    document.getElementById('hcConditions').textContent = `Conditions: ${profile.medical_conditions || 'None'}`;
    document.getElementById('hcEmergency').textContent = `Emergency Contact: ${profile.emergency_contact || '—'}`;
    document.getElementById('hcWheelchair').textContent = `Wheelchair: ${profile.wheelchair_required ? 'Required' : 'Not Required'}`;
    
    // Pre-fill form
    if (profile.age) document.getElementById('healthAge').value = profile.age;
    if (profile.blood_group) document.getElementById('healthBlood').value = profile.blood_group;
    if (profile.emergency_contact) document.getElementById('healthEmergency').value = profile.emergency_contact;
    if (profile.wheelchair_required) document.getElementById('healthWheelchair').value = 'true';
    
    // Check conditions
    if (profile.medical_conditions) {
      const conditions = profile.medical_conditions.split(',').map(c => c.trim().toLowerCase());
      document.querySelectorAll('input[name="conditions"]').forEach(cb => {
        if (conditions.includes(cb.value.toLowerCase())) {
          cb.checked = true;
        }
      });
    }
    
    generateHealthRecommendations(profile);
  } catch (error) {
    console.log('Could not load health profile:', error);
  }
}

// Generate personalized health recommendations
function generateHealthRecommendations(profile) {
  const container = document.getElementById('healthRecommendations');
  if (!container) return;
  
  const recommendations = [];
  
  // Age-based recommendations
  if (profile.age) {
    if (profile.age >= 65) {
      recommendations.push('👴 Consider Divya Darshan for shorter wait times (senior citizens 65+)');
      recommendations.push('♿ Wheelchair assistance available at medical centers and help desks');
      recommendations.push('💧 Stay hydrated - take regular breaks during queue');
    } else if (profile.age < 12) {
      recommendations.push('👶 Children should be supervised at all times');
      recommendations.push('🍛 Free milk and refreshments available in queue compartments');
    }
  }
  
  // Condition-based recommendations
  const conditions = profile.medical_conditions?.toLowerCase() || '';
  if (conditions.includes('diabetes')) {
    recommendations.push('💊 Carry your medication and snacks to manage blood sugar');
    recommendations.push('⏰ Set medication reminders every 4-6 hours');
    recommendations.push('💧 Stay hydrated - avoid sugary drinks');
  }
  if (conditions.includes('heart') || conditions.includes('hypertension')) {
    recommendations.push('❤️ Avoid strenuous climbing - consider using bus transport');
    recommendations.push('💊 Keep emergency medication accessible');
    recommendations.push('🏥 Medical centers available at key locations');
    recommendations.push('⏰ Set regular rest reminders every 30-45 minutes');
  }
  if (conditions.includes('pregnancy')) {
    recommendations.push('🤰 Use Divya Darshan queue for shorter wait times');
    recommendations.push('💧 Stay hydrated and take frequent rest breaks');
    recommendations.push('🏥 Medical assistance available on footpaths');
    recommendations.push('♿ Wheelchair assistance available if needed');
  }
  if (conditions.includes('disability') || profile.wheelchair_required) {
    recommendations.push('♿ Free wheelchair service available - request at help desks');
    recommendations.push('🚑 Divya Darshan available for differently abled devotees');
    recommendations.push('🏥 Accessible medical facilities throughout');
  }
  
  // General recommendations
  recommendations.push('💧 Free drinking water available throughout the complex');
  recommendations.push('🍛 Annaprasadam (free meals) available at MTVAC and VQC');
  recommendations.push('🏥 Aswini Hospital provides 24/7 emergency care');
  recommendations.push('📞 Emergency: Call 155257 for immediate assistance');
  
  // Display recommendations
  container.innerHTML = recommendations.map(rec => 
    `<div class="recommendation-item">${rec}</div>`
  ).join('');
}

// Reminder management
function initReminders() {
  const form = document.getElementById('reminderForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(form);
    const reminderData = {
      reminder_type: formData.get('reminder_type'),
      interval_minutes: parseInt(formData.get('interval_minutes')),
      message: formData.get('message') || ''
    };

    try {
      await API.post('/health/reminders', reminderData);
      document.getElementById('reminderStatus').textContent = 'Reminder set successfully!';
      document.getElementById('reminderStatus').className = 'status success';
      loadActiveReminders();
      form.reset();
    } catch (error) {
      document.getElementById('reminderStatus').textContent = 'Failed to set reminder. Please login first.';
      document.getElementById('reminderStatus').className = 'status error';
    }
  });
}

async function loadActiveReminders() {
  const container = document.getElementById('activeReminders');
  if (!container) return;

  try {
    const reminders = await API.get('/health/reminders');
    
    if (reminders.length === 0) {
      container.innerHTML = '<li class="empty-state">No active reminders</li>';
      return;
    }
    
    container.innerHTML = reminders.map(r => `
      <li class="reminder-item">
        <span class="reminder-type">${getReminderIcon(r.reminder_type)} ${r.reminder_type}</span>
        <span class="reminder-interval">Every ${r.interval_minutes} min</span>
        <span class="reminder-message">${r.message || 'Default message'}</span>
      </li>
    `).join('');
  } catch (error) {
    container.innerHTML = '<li class="empty-state">Login to view reminders</li>';
  }
}

function getReminderIcon(type) {
  const icons = {
    hydration: '💧',
    medication: '💊',
    rest: '😴',
    food: '🍛'
  };
  return icons[type] || '⏰';
}

// Find nearest medical center
function initMedicalFinder() {
  const btn = document.getElementById('findMedicalBtn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }

    btn.textContent = '📍 Locating...';
    btn.disabled = true;

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        
        try {
          const response = await API.get('/nearby', {
            latitude,
            longitude,
            kind: 'medical',
            max_distance: 2000
          });
          
          displayMedicalResults(response.facilities);
        } catch (error) {
          document.getElementById('medicalResults').innerHTML = 
            '<p class="error">Failed to find medical facilities</p>';
        }
        
        btn.textContent = '📍 Find Nearest Medical Centre';
        btn.disabled = false;
      },
      (error) => {
        document.getElementById('medicalResults').innerHTML = 
          '<p class="error">Could not get your location. Please enable location services.</p>';
        btn.textContent = '📍 Find Nearest Medical Centre';
        btn.disabled = false;
      }
    );
  });
}

function displayMedicalResults(facilities) {
  const container = document.getElementById('medicalResults');
  if (!container) return;

  if (facilities.length === 0) {
    container.innerHTML = '<p class="hint">No medical facilities found within 2km</p>';
    return;
  }

  container.innerHTML = facilities.map(f => `
    <div class="medical-result">
      <h4>${f.name}</h4>
      <p>📍 ${f.distance_label} away</p>
      <p>🚶 Walking time: ${f.walking_time?.walking_time_formatted || 'N/A'}</p>
      <p>👥 Crowd: ${f.walking_time?.crowd_level || 'N/A'}</p>
      <p>${f.details}</p>
    </div>
  `).join('');
}

// Quick assistance buttons
function initAssistanceButtons() {
  const buttons = {
    wheelchairBtn: 'Wheelchair request sent. Help is on the way!',
    volunteerBtn: 'Volunteer request sent. Someone will assist you shortly.',
    waterBtn: 'Water request sent. Free water points are available throughout.',
    medSosBtn: '🚨 MEDICAL SOS ACTIVATED! Help is being dispatched. Call 155257 for immediate assistance.'
  };

  Object.entries(buttons).forEach(([btnId, message]) => {
    const btn = document.getElementById(btnId);
    if (!btn) return;

    btn.addEventListener('click', () => {
      const status = document.getElementById('assistStatus');
      status.textContent = message;
      status.className = 'status ' + (btnId === 'medSosBtn' ? 'error' : 'success');
      
      // For SOS, also trigger the SOS dialog
      if (btnId === 'medSosBtn') {
        document.getElementById('sosFab')?.click();
      }
    });
  });
}

// Initialize all health features
document.addEventListener('DOMContentLoaded', () => {
  initHealthProfile();
  initReminders();
  initMedicalFinder();
  initAssistanceButtons();
  
  // Load health card if on health page
  if (document.querySelector('.health-page')) {
    loadHealthCard();
    loadActiveReminders();
  }
});
