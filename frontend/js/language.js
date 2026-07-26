language.onchange=()=>{localStorage.language=language.value;document.documentElement.lang=language.value==='English'?'en':'hi';};language.value=localStorage.language||'English';
