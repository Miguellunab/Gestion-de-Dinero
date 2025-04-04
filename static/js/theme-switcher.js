document.addEventListener('DOMContentLoaded', function() {
    // Obtener preferencia de tema guardada o usar el tema claro por defecto
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Aplicar tema al cargar la página
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Actualizar estado del botón
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const themeIcon = document.getElementById('theme-icon');
        
        if (currentTheme === 'dark') {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        } else {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        }
        
        // Manejar el cambio de tema al hacer clic en el botón
        themeToggle.addEventListener('click', function() {
            const theme = document.documentElement.getAttribute('data-theme');
            const newTheme = theme === 'light' ? 'dark' : 'light';
            
            // Cambiar el tema
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Disparar evento personalizado para notificar cambio de tema
            const event = new CustomEvent('themeChanged', { 
              detail: { theme: newTheme } 
            });
            document.dispatchEvent(event);
            
            // Actualizar el icono
            if (newTheme === 'dark') {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        });
    }
});