document.addEventListener('DOMContentLoaded', async () => {
  const inputBox = document.querySelector('.terminal-input');
  const terminalBoot = document.getElementById('terminal-screen');
  const terminalOutput = document.querySelector('.terminal1');
  const loaderContainer = document.querySelector('.container');

  // === Persistencia de conversación ===
  let usuario = 'invitado';
  try {
    const sessionInfo = await fetch('/session-info').then(res => res.json());
    usuario = typeof sessionInfo.usuario === 'string' ? sessionInfo.usuario : 'invitado';
  } catch (err) {
    console.warn('No se pudo obtener usuario:', err);
  }
  
  const CONVERSATION_KEY = `conversacion_eidolon_${usuario}`;
  
  function guardarConversacion() {
    const mensajes = Array.from(terminalOutput.querySelectorAll('.user-msg, .bot-msg')).map(el => {
      let contenido = '';
      
      if (el.classList.contains('user-msg')) {
        contenido = el.textContent.trim();
      } else if (el.classList.contains('bot-msg')) {
        // Buscar el texto en la estructura anidada si existe
        const nestedText = el.querySelector('span, div');
        if (nestedText) {
          contenido = nestedText.textContent.trim();
        } else {
          contenido = el.textContent.trim();
        }
      }
      
      return {
        tipo: el.classList.contains('user-msg') ? 'usuario' : 'bot',
        contenido: contenido
      };
    });
    
    localStorage.setItem(CONVERSATION_KEY, JSON.stringify(mensajes));
  }
  
  function cargarConversacion() {
    const guardado = localStorage.getItem(CONVERSATION_KEY);
    if (guardado) {
      try {
        const mensajes = JSON.parse(guardado);
        mensajes.forEach(msg => {
          const div = document.createElement("div");
          div.classList.add(msg.tipo === 'usuario' ? 'user-msg' : 'bot-msg');
          div.textContent = msg.contenido;
          terminalOutput.appendChild(div);
        });
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
      } catch (e) {
        console.warn("Error cargando conversación:", e);
      }
    }
  }
  
  function limpiarConversacion() {
    localStorage.removeItem(CONVERSATION_KEY);
    terminalOutput.innerHTML = '';
  }

  const lines = [
    { main: '> Estableciendo enlace neuronal...', extra: null },
    { main: '> Verificando autorización sanctum...', extra: ' [AUTORIZADO]' },
    { main: '> Iniciando sincronización cognitiva...', extra: ' [ESTABLECIDA]' },
    { main: '> Conectado a: EIDOLON', extra: ' [NUCLEO SOLAR ACTIVO]' },
    { main: '> Acceso concedido al Archivo Invictus', extra: ' [NIVEL: GLADIUS]' },
    { main: '> Que el sol guíe tus pasos, ', extra: 'USUARIO_API' }
  ];

  let currentLine = 0;

  function removeCursor(container) {
    const existing = container.querySelector('.cursor');
    if (existing) existing.remove();
  }

  function waitForUserInput(lineElement) {
    inputBox.classList.add('visible');
    setTimeout(() => inputBox.focus(), 0);

    const observer = new MutationObserver(() => {
      const cursor = lineElement.querySelector('.cursor');
      if (cursor) cursor.remove();
      observer.disconnect();
    });

    observer.observe(terminalOutput, { childList: true, subtree: true });
  }

  async function getUsuario() {
    try {
      const res = await fetch('/session-info');
      const data = await res.json();
      return typeof data.usuario === 'string' ? data.usuario.toUpperCase() : 'DESCONOCIDO';
    } catch (err) {
      return 'DESCONOCIDO';
    }
  }

  function typeText(container, text, extra, callback, speed = 10, extraDelay = 300, showFinalCursor = false) {
    let i = 0;
    const lineContainer = document.createElement('div');
    container.appendChild(lineContainer);

    function typeChar() {
      const visible = text.slice(0, i);
      lineContainer.innerHTML = visible + '<span class="writing-cursor">▮</span>';
      container.scrollTop = container.scrollHeight;

      if (i < text.length) {
        i++;
        setTimeout(typeChar, speed);
      } else {
        if (extra) {
          setTimeout(() => {
            lineContainer.innerHTML = text + extra + (showFinalCursor ? '<span class="cursor">▮</span>' : '');
            if (showFinalCursor) waitForUserInput(lineContainer);
            callback();
          }, extraDelay);
        } else {
          lineContainer.innerHTML = text + (showFinalCursor ? '<span class="cursor">▮</span>' : '');
          if (showFinalCursor) waitForUserInput(lineContainer);
          callback();
        }
      }
    }

    typeChar();
  }

  async function typeLine() {
    if (currentLine >= lines.length) return;

    let { main, extra } = lines[currentLine];
    if (extra === 'USUARIO_API') {
      extra = ' ' + (await getUsuario());
    }

    const isLastLine = currentLine === lines.length - 1;

    typeText(
      terminalBoot,
      main,
      extra,
      () => {
        currentLine++;
        if (!isLastLine) {
          setTimeout(typeLine, Math.floor(Math.random() * 300) + 300);
        }
      },
      Math.floor(Math.random() * 15) + 5,
      Math.floor(Math.random() * 200) + 200,
      isLastLine
    );
  }

  function typeResponse(container, text, callback, speed = 10, showCursor = true) {
    let i = 0;
    const lineContainer = document.createElement('div');
    container.appendChild(lineContainer);

    function typeChar() {
      const visible = text.slice(0, i);
      lineContainer.innerHTML = visible + '<span class="writing-cursor">▮</span>';
      container.scrollTop = container.scrollHeight;

      if (i < text.length) {
        i++;
        setTimeout(typeChar, speed);
      } else {
        lineContainer.innerHTML = text + (showCursor ? '<span class="cursor">▮</span>' : '');
        if (callback) callback();
      }
    }

    typeChar();
  }

  function appendToTerminal(text, isUser = false) {
    removeCursor(terminalOutput);
    const div = document.createElement('div');
    div.classList.add(isUser ? 'user-msg' : 'bot-msg');
    terminalOutput.appendChild(div);
    
    typeResponse(
      div,
      text,
      () => {},
      Math.floor(Math.random() * 5) + 5,
      true
    );
  }

  function animateSpeedChange(targetElement, start, end, duration = 1000) {
    const startTime = performance.now();

    function step(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = progress < 0.5
        ? 2 * progress * progress
        : -1 + (4 - 2 * progress) * progress;

      const currentSpeed = start + (end - start) * eased;
      targetElement.style.setProperty('--speed', `${currentSpeed.toFixed(2)}s`);

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }

    requestAnimationFrame(step);
  }

  function startProcessingAnimation() {
    loaderContainer.classList.add('processing');
    animateSpeedChange(loaderContainer, 3, 1.2, 800);
  }

  function stopProcessingAnimation() {
    animateSpeedChange(loaderContainer, 1.2, 3, 800);
    setTimeout(() => loaderContainer.classList.remove('processing'), 800);
  }

  inputBox.addEventListener('keydown', async (event) => {
    if (event.key === 'Enter') {
      const mensaje = inputBox.value.trim();
      if (!mensaje) return;

      appendToTerminal(`> ${mensaje}`, true);
      inputBox.value = '';
      
      // Guardar conversación después de cada mensaje del usuario
      guardarConversacion();

      startProcessingAnimation();

      try {
        const sessionInfo = await fetch('/session-info').then(res => res.json());
        const usuario = typeof sessionInfo.usuario === 'string' ? sessionInfo.usuario : '';

        const res = await fetch('/eidolon/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mensaje, id: usuario })
        });

        const data = await res.json();
        appendToTerminal(data.respuesta || '⚠️ Sin respuesta de la IA.');
        
        // Guardar conversación después de la respuesta
        guardarConversacion();
      } catch (err) {
        appendToTerminal('⚠️ Error al conectar con la IA.');
        console.error(err);
      } finally {
        stopProcessingAnimation();
      }
    }
  });

  // Cargar conversación al iniciar
  cargarConversacion();

  typeLine();
});
