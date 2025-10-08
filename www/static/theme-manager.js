/* ============================
   GESTOR DE TEMAS DE COLORES
============================ */

class ThemeManager {
  constructor() {
    this.currentTheme = this.getStoredTheme() || 'default';
    this.init();
  }

  init() {
    // Aplicar tema guardado al cargar
    this.applyTheme(this.currentTheme);
    
    // Configurar event listeners para el selector de colores
    this.setupColorSelector();
    
    // Aplicar tema a todas las páginas
    this.applyThemeGlobally();
  }

  getStoredTheme() {
    return localStorage.getItem('chatbotuvo-theme');
  }

  storeTheme(theme) {
    localStorage.setItem('chatbotuvo-theme', theme);
  }

  applyTheme(theme) {
    // Remover tema anterior
    document.documentElement.removeAttribute('data-theme');
    
    // Aplicar nuevo tema
    if (theme !== 'default') {
      document.documentElement.setAttribute('data-theme', theme);
    }
    
    this.currentTheme = theme;
    this.storeTheme(theme);
    
    // Actualizar indicador visual
    this.updateColorSelector();
  }

  setupColorSelector() {
    const colorOptions = document.querySelectorAll('.color-option');
    
    colorOptions.forEach(option => {
      option.addEventListener('click', () => {
        const theme = option.getAttribute('data-theme');
        this.applyTheme(theme);
        
        // Efecto visual de selección
        option.style.transform = 'scale(0.9)';
        setTimeout(() => {
          option.style.transform = 'scale(1)';
        }, 150);
      });
    });
  }

  updateColorSelector() {
    const colorOptions = document.querySelectorAll('.color-option');
    
    colorOptions.forEach(option => {
      const theme = option.getAttribute('data-theme');
      
      if (theme === this.currentTheme) {
        option.classList.add('active');
      } else {
        option.classList.remove('active');
      }
    });
  }

  applyThemeGlobally() {
    // Aplicar tema a todas las páginas que carguen este script
    const theme = this.getStoredTheme();
    if (theme && theme !== 'default') {
      document.documentElement.setAttribute('data-theme', theme);
    }
  }

  // Método público para cambiar tema programáticamente
  setTheme(theme) {
    this.applyTheme(theme);
  }

  // Método público para obtener tema actual
  getCurrentTheme() {
    return this.currentTheme;
  }
}

// Inicializar el gestor de temas cuando se carga el DOM
document.addEventListener('DOMContentLoaded', () => {
  window.themeManager = new ThemeManager();
});

// También aplicar tema si el script se carga después del DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (!window.themeManager) {
      window.themeManager = new ThemeManager();
    }
  });
} else {
  // DOM ya cargado
  if (!window.themeManager) {
    window.themeManager = new ThemeManager();
  }
}
