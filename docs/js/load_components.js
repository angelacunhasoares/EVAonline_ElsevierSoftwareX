document.addEventListener('DOMContentLoaded', function() {
    console.log('load_components.js: Script iniciado');

    // Determinar a base do caminho para GitHub Pages ou servidor local
    const basePath = window.location.pathname.includes('evaonline') ? '/evaonline/' : './';

    // Carregar Navbar
    fetch(basePath + 'navbar.html')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro ao carregar navbar.html: ${response.status} ${response.statusText}`);
            }
            console.log('load_components.js: navbar.html encontrado');
            return response.text();
        })
        .then(data => {
            console.log('load_components.js: navbar.html carregado com sucesso');
            document.getElementById('navbar-placeholder').innerHTML = data;
            // Atualizar classe ativa na navbar
            const currentPage = window.location.pathname.split('/').pop() || 'index.html';
            const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
            navLinks.forEach(link => {
                if (link.getAttribute('href') === currentPage) {
                    link.classList.add('active');
                }
            });
        })
        .catch(error => {
            console.error('load_components.js: Erro ao carregar navbar:', error);
            document.getElementById('navbar-placeholder').innerHTML = '<p>Erro ao carregar a navbar. Verifique o console para detalhes.</p>';
        });

    // Carregar Footer
    fetch(basePath + 'footer.html')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro ao carregar footer.html: ${response.status} ${response.statusText}`);
            }
            console.log('load_components.js: footer.html encontrado');
            return response.text();
        })
        .then(data => {
            console.log('load_components.js: footer.html carregado com sucesso');
            document.getElementById('footer-placeholder').innerHTML = data;
        })
        .catch(error => {
            console.error('load_components.js: Erro ao carregar footer:', error);
            document.getElementById('footer-placeholder').innerHTML = '<p>Erro ao carregar o footer. Verifique o console para detalhes.</p>';
        });
});