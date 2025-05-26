document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("terminalForm");
  const input = document.getElementById("userInput");
  const output = document.getElementById("output");

  let usuario = null;

  // Obtener usuario autenticado
  fetch("/session-info")
    .then(res => res.json())
    .then(data => {
      if (!data.usuario) {
        output.innerHTML += "\n⚠️ No has iniciado sesión. Vuelve al inicio.";
        input.disabled = true;
      } else {
        usuario = data.usuario;
      }
    });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const pregunta = input.value.trim();
    if (!pregunta || !usuario) return;

    output.innerHTML += `\n${usuario}: ${pregunta}\n`;
    input.value = "";
    output.scrollTop = output.scrollHeight;

    try {
      const res = await fetch("/minerva/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mensaje: pregunta,
          ia: "minerva",
          id: usuario
        })
      });

      const data = await res.json();
      output.innerHTML += `minerva: ${data.respuesta}\n`;
      output.scrollTop = output.scrollHeight;
    } catch (err) {
      output.innerHTML += "⚠️ Error de conexión con Minerva.\n";
    }
  });
});
