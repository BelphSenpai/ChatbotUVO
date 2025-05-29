document.addEventListener("DOMContentLoaded", async () => {
  const path = window.location.pathname;
  const ia = path.split('/')[1]; // 'anima' por ejemplo
  const codeBlock = document.querySelector(".code");
  const input = document.querySelector(".runic-input");
  const glyphsLeft = document.getElementById("runes-left");
  const glyphsRight = document.getElementById("runes-right");
  const runes = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᛠᛡᛥᛦ".split("");

  let usuario = "invitado";

  // Carga de sesión y visibilidad de elementos condicionales
  try {
    const res = await fetch("/session-info");
    const data = await res.json();
    usuario = data.usuario || "invitado";

    if (data.rol === "admin") {
      document.getElementById("admin-link-container").style.display = "inline-block";
    }

    const usosRes = await fetch("/usos");
    if (usosRes.ok) {
      const usos = await usosRes.json();
      const iaDropdown = document.getElementById("ia-dropdown");
      const iaDropdownContainer = document.getElementById("ia-dropdown-container");

      ["hada", "eidolon", "fantasma", "anima"].forEach(ia => {
        const cantidad = usos[ia];
        if (cantidad === -1 || cantidad > 0) {
          const link = document.createElement("a");
          link.href = `/${ia}`;
          link.textContent = ia.charAt(0).toUpperCase() + ia.slice(1);
          iaDropdown.appendChild(link);
        }
      });

      if (iaDropdown.children.length > 0) {
        iaDropdownContainer.style.display = "inline-block";
      }
    }

    // Activa enlace actual
    const currentIA = document.getElementById(`${ia}-link`);
    if (currentIA) currentIA.classList.add("active");

  } catch (err) {
    console.warn("Error al cargar sesión o usos:", err);
  }

  // Dropdown de IAs
  const dropdown = document.getElementById("ia-dropdown-container");
  const dropdownContent = document.getElementById("ia-dropdown");
  if (dropdown && dropdownContent) {
    dropdown.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdown.classList.toggle("active");
    });
    document.addEventListener("click", (e) => {
      if (!dropdown.contains(e.target)) dropdown.classList.remove("active");
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") dropdown.classList.remove("active");
    });
  }

  // Preparar runas sin animación periódica
function poblarRunes(element) {
  element.innerHTML = "";
  const fragment = document.createDocumentFragment();
  for (let i = 0; i < 20; i++) {
    const span = document.createElement("span");
    span.textContent = runes[Math.floor(Math.random() * runes.length)];
    fragment.appendChild(span);
  }
  element.appendChild(fragment);
}

function animarRunesSuavemente(element) {
  const spans = element.querySelectorAll("span");
  const totalCambios = Math.min(4, spans.length);
  for (let i = 0; i < totalCambios; i++) {
    const span = spans[Math.floor(Math.random() * spans.length)];
    span.textContent = runes[Math.floor(Math.random() * runes.length)];
    span.classList.add("flicker");
    setTimeout(() => span.classList.remove("flicker"), 300);
  }
}

// Animación controlada con raf-loop
function iniciarAnimacionRunes() {
  let lastUpdate = 0;
  function loop(ts) {
    if (ts - lastUpdate > 3000) {
      animarRunesSuavemente(glyphsLeft);
      animarRunesSuavemente(glyphsRight);
      lastUpdate = ts;
    }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
}


  poblarRunes(glyphsLeft);
  poblarRunes(glyphsRight);
  iniciarAnimacionRunes();

  // Input de usuario
  input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") enviar();
  });

  async function enviar() {
    const mensaje = input.value.trim();
    if (!mensaje) return;

    appendLinea(`>> ${mensaje}`, "user");
    input.value = "";
    await registrarEvento(`pregunta_${ia}`, mensaje);

    mostrarPensando();

    try {
      const res = await fetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensaje, ia, id: usuario })
      });

      const data = await res.json();
      await registrarEvento(`respuesta_${ia}`, data.respuesta);
      appendLinea(`>> ${data.respuesta}`, "bot");

    } catch (err) {
      appendLinea("⚠️ ERROR: No se pudo conectar con la IA.", "error");
    } finally {
      ocultarPensando();
    }
  }

  function appendLinea(texto, clase = "") {
    const linea = document.createElement("div");
    linea.textContent = texto;
    if (clase) linea.classList.add(clase);
    codeBlock.appendChild(linea);
    codeBlock.scrollTop = codeBlock.scrollHeight;
  }

  function mostrarPensando() {
    const spinner = document.querySelector(".spinner");
    if (spinner) spinner.classList.add("thinking");
  }

  function ocultarPensando() {
    const spinner = document.querySelector(".spinner");
    if (spinner) spinner.classList.remove("thinking");
  }

  async function registrarEvento(tipo, contenido) {
    try {
      await fetch("/log-evento", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tipo, contenido })
      });
    } catch (err) {
      console.error("Error registrando evento:", err);
    }
  }
});

