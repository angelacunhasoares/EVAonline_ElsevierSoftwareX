document.addEventListener('DOMContentLoaded', function() {
    console.log('translations.js: Script iniciado');

    // Carregar idioma padrão (inglês) ou do localStorage
    let currentLang = localStorage.getItem('language') || 'en';
    console.log('translations.js: Idioma inicial:', currentLang);

    // Função para carregar traduções
    function loadTranslations(lang) {
        const basePath = window.location.pathname.includes('EVAonline_SoftwareX') ? '/EVAonline_SoftwareX/translations/' : '/docs/translations/';
        const translationUrl = basePath + `${lang}.json`;
        console.log('translations.js: Tentando carregar:', translationUrl);

        fetch(translationUrl)
            .then(response => {
                if (!response.ok) throw new Error(`Erro ao carregar translations/${lang}.json: ${response.status} ${response.statusText}`);
                console.log(`translations.js: ${lang}.json encontrado`);
                return response.json();
            })
            .then(translations => {
                console.log('translations.js: Traduções carregadas com sucesso', translations);
                document.querySelectorAll('[data-translate]').forEach(element => {
                    const key = element.getAttribute('data-translate');
                    console.log('translations.js: Processando elemento com data-translate:', key);
                    if (translations[key]) {
                        if (element.tagName === 'A' || element.innerHTML.includes('<a')) {
                            element.innerHTML = translations[key];
                        } else {
                            element.textContent = translations[key];
                        }
                    } else {
                        console.warn('translations.js: Chave não encontrada:', key);
                    }
                });
                // Atualizar título da página
                const titleElement = document.querySelector('title');
                if (titleElement && translations[titleElement.getAttribute('data-translate')]) {
                    titleElement.textContent = translations[titleElement.getAttribute('data-translate')];
                    console.log('translations.js: Título atualizado:', titleElement.textContent);
                }
                // Atualizar botão de idioma
                const langToggle = document.getElementById('lang-toggle');
                if (langToggle) {
                    langToggle.textContent = translations['lang_toggle'];
                    console.log('translations.js: Botão lang-toggle atualizado com:', translations['lang_toggle']);
                } else {
                    console.error('translations.js: Botão lang-toggle não encontrado');
                }
                localStorage.setItem('language', lang);
            })
            .catch(error => console.error('translations.js: Erro ao carregar traduções:', error));
    }

    // Função para configurar o evento do botão de tradução
    function setupLangToggle() {
        const langToggle = document.getElementById('lang-toggle');
        if (langToggle) {
            console.log('translations.js: Botão lang-toggle encontrado, adicionando evento de clique');
            langToggle.addEventListener('click', () => {
                console.log('translations.js: Botão lang-toggle clicado');
                currentLang = currentLang === 'en' ? 'pt' : 'en';
                console.log('translations.js: Alterando idioma para:', currentLang);
                loadTranslations(currentLang);
            });
        } else {
            console.error('translations.js: Botão lang-toggle não encontrado, tentando novamente em 100ms');
            setTimeout(setupLangToggle, 100); // Tentar novamente após 100ms
        }
    }

    // Carregar traduções iniciais
    loadTranslations(currentLang);

    // Configurar evento do botão de tradução
    setupLangToggle();
});