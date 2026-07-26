theme.onclick=()=>document.body.classList.toggle('dark');

// Authentication UI is created here to keep the single-page experience lightweight.
const loginButton=document.createElement('button');
loginButton.className='login-button'; loginButton.textContent='Login';
theme.before(loginButton);
const authDialog=document.createElement('dialog');
authDialog.innerHTML=`<form id="authForm"><button type="button" class="close" id="authClose">×</button><p class="eyebrow" id="authLabel">WELCOME BACK</p><h2 id="authTitle">Login to your journey</h2><input id="authName" placeholder="Full name" aria-label="Full name" hidden><input id="authEmail" type="email" placeholder="Email address" required aria-label="Email address"><input id="authPassword" type="password" placeholder="Password (minimum 8 characters)" required minlength="8" aria-label="Password"><button class="button primary" id="authSubmit">Login</button><p id="authStatus"></p><button type="button" class="text-button" id="authSwitch">New pilgrim? Create an account</button><p class="demo-login">Demo admin: <b>admin@oursttd.demo</b><br>Password: <b>DemoAdmin123</b></p></form>`;
document.body.append(authDialog);
const authStyle=document.createElement('style'); authStyle.textContent=`.login-button{background:var(--brown);color:#fff;padding:8px 14px;border-radius:6px;font-weight:700}#authForm{display:grid;gap:12px}#authForm input{padding:13px;border:1px solid var(--line);border-radius:7px;font:inherit}.text-button{background:none;color:var(--gold);text-decoration:underline}.demo-login{font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:12px;margin:0}`;document.head.append(authStyle);
let registering=false;
loginButton.onclick=()=>authDialog.showModal(); authClose.onclick=()=>authDialog.close();
authSwitch.onclick=()=>{registering=!registering;authName.hidden=!registering;authLabel.textContent=registering?'CREATE YOUR PROFILE':'WELCOME BACK';authTitle.textContent=registering?'Begin your pilgrimage':'Login to your journey';authSubmit.textContent=registering?'Create account':'Login';authSwitch.textContent=registering?'Already registered? Login':'New pilgrim? Create an account';authStatus.textContent=''};
authForm.onsubmit=async e=>{e.preventDefault();authStatus.textContent='Please wait…';try{const body={email:authEmail.value,password:authPassword.value};if(registering)body.name=authName.value;const r=await API.post(`auth/${registering?'register':'login'}`,body);localStorage.authToken=r.access_token;loginButton.textContent='✓ Signed in';authStatus.textContent='Signed in successfully. Welcome!';setTimeout(()=>authDialog.close(),900)}catch(err){authStatus.textContent=err.detail||'Unable to sign in. Check your details and try again.'}};

const locationButton=document.createElement('button');
locationButton.className='login-button'; locationButton.textContent='⌖ Enable location';
loginButton.before(locationButton);
locationButton.onclick=()=>{
  if(!navigator.geolocation){alert('Location is not supported by this browser.');return}
  locationButton.textContent='Finding you…';
  navigator.geolocation.getCurrentPosition(pos=>{
    localStorage.pilgrimLocation=JSON.stringify({latitude:pos.coords.latitude,longitude:pos.coords.longitude,accuracy:pos.coords.accuracy,recordedAt:new Date().toISOString(),source:'device-gps'});
    localStorage.removeItem('manualNearbyPlace'); locationButton.textContent='✓ Live location on';
    queueAdvice.textContent=`Live device location enabled (accuracy approximately ${Math.round(pos.coords.accuracy)} m). Nearby guidance and SOS alerts use this GPS location.`;
  },()=>{locationButton.textContent='⌖ Enable location';alert('Location permission was not granted. You can enable it from the browser address-bar settings.')},{enableHighAccuracy:true,timeout:10000,maximumAge:60000});
};
if(localStorage.pilgrimLocation)locationButton.textContent='✓ Live location on';

const nearbyButton=document.createElement('button');
nearbyButton.className='login-button'; nearbyButton.textContent='Set nearby place';
locationButton.after(nearbyButton);
const nearbyDialog=document.createElement('dialog');
nearbyDialog.innerHTML=`<form method="dialog" id="nearbyForm"><button class="close" value="cancel">×</button><p class="eyebrow">MANUAL REFERENCE</p><h2>Choose your nearby place</h2><p>This does not create a GPS location. It helps the assistant give directions from the landmark you select.</p><select id="nearbyPlace" required><option value="">Select a nearby place</option><option>Vaikuntam Queue Complex I</option><option>Vaikuntam Queue Complex II</option><option>PAC-3</option><option>PAC-5 (Venkatadri Nilayam)</option><option>Matrusri Tarigonda Vengamamba Annaprasada Complex</option><option>Aswini Hospital</option><option>Rambagicha Bus Stand</option><option>Alipiri Footpath</option><option>Srivari Mettu Footpath</option></select><button class="button primary" value="confirm">Use this place</button></form>`;
document.body.append(nearbyDialog);
nearbyButton.onclick=()=>nearbyDialog.showModal();
const nearbyForm=nearbyDialog.querySelector('#nearbyForm'), nearbyPlace=nearbyDialog.querySelector('#nearbyPlace');
nearbyForm.addEventListener('submit',e=>{if(e.submitter.value!=='confirm')return;if(!nearbyPlace.value){e.preventDefault();return}localStorage.manualNearbyPlace=nearbyPlace.value;queueAdvice.textContent=`Manual nearby-place reference set to: ${nearbyPlace.value}. Enable live location for GPS-based guidance.`;nearbyButton.textContent='✓ Nearby place set';});
