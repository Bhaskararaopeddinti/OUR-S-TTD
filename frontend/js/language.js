const translatableElements = document.querySelectorAll('[data-translate]');
async function translatePage(targetLanguage) {
  if (targetLanguage === 'English') {
    translatableElements.forEach(el => {
      el.textContent = el.dataset.original || el.textContent;
    });
    return;
  }
  
  try {
    const texts = Array.from(translatableElements).map(el => el.textContent);
    const response = await API.post('translate', { text: texts.join('\n'), target_language: targetLanguage });
    const translatedTexts = response.translated.split('\n');
    
    translatableElements.forEach((el, index) => {
      if (!el.dataset.original) el.dataset.original = el.textContent;
      el.textContent = translatedTexts[index] || el.textContent;
    });
  } catch (error) {
    console.error('Translation error:', error);
  }
}

language.onchange=async()=>{
  localStorage.language=language.value;
  document.documentElement.lang=language.value==='English'?'en':'hi';
  await translatePage(language.value);
};
language.value=localStorage.language||'English';
if(localStorage.language!=='English')translatePage(localStorage.language);
