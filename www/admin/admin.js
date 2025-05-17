let personajesMostrados = false;
let editandoNombre = null;
let conexionesActuales = [];
let nodosActuales = [];
let personajeActual = "";

document.addEventListener("DOMContentLoaded", () => {
  const verBtn = document.getElementById("ver-personajes");
  const crearBtn = document.getElementById("crear-personaje");
  const guardarBtn = document.getElementById("guardar-personaje");
  const cancelarBtn = document.getElementById("cancelar-personaje");

  verBtn.addEventListener("click", () => {
    const lista = document.getElementById("lista-personajes");
    personajesMostrados = !personajesMostrados;
    if (personajesMostrados) {
      cargarPersonajes();
      lista.style.display = "block";
    } else {
      lista.style.display = "none";
    }
  });

  crearBtn.addEventListener("click", () => {
    editandoNombre = null;
    abrirModal();
  });

  guardarBtn.addEventListener("click", guardarPersonaje);
  cancelarBtn.addEventListener("click", cerrarModal);

  document.getElementById("cerrar-modal-log").addEventListener("click", cerrarModalLog);
  document.getElementById("cerrar-modal-conexiones").addEventListener("click", cerrarModalConexiones);

  cargarSesiones();
});

// ==== PERSONAJES ====

function abrirModal(nombre = '', clave = '', rol = 'jugador') {
  document.getElementById("modal-title").textContent = editandoNombre ? "Editar Personaje" : "Crear Personaje";
  document.getElementById("nombre-input").value = nombre;
  document.getElementById("clave-input").value = clave;
  document.getElementById("rol-input").value = rol;
  document.getElementById("personaje-modal").style.display = "flex";
}

function cerrarModal() {
  document.getElementById("personaje-modal").style.display = "none";
  editandoNombre = null;
}

async function cargarPersonajes() {
  try {
    const res = await fetch("/admin/personajes");
    const personajes = await res.json();

    const lista = document.getElementById("lista-personajes");
    lista.innerHTML = "";

    personajes.forEach(personaje => {
      const div = document.createElement("div");
      div.className = "personaje-item";

      const nombreElem = document.createElement("strong");
      nombreElem.textContent = personaje.nombre;
      nombreElem.style.cursor = "pointer";
      nombreElem.addEventListener("click", () => abrirLogPersonaje(personaje.nombre));

      const botonesDiv = document.createElement("div");
      botonesDiv.style.display = "flex";
      botonesDiv.style.gap = "8px";

      // Botón Editar
      const btnEditar = document.createElement("button");
      btnEditar.textContent = "Editar";
      btnEditar.addEventListener("click", (e) => {
        e.stopPropagation();
        editarPersonaje(personaje.nombre);
      });
      botonesDiv.appendChild(btnEditar);

      // Botón Conexiones
      const btnConexiones = document.createElement("button");
      btnConexiones.textContent = "Conexiones";
      btnConexiones.addEventListener("click", (e) => {
        e.stopPropagation();
        abrirEditorConexiones(personaje.nombre);
      });
      botonesDiv.appendChild(btnConexiones);

      // Botón Borrar Log
      const btnBorrarLog = document.createElement("button");
      btnBorrarLog.textContent = "🗑️ Borrar Log";
      btnBorrarLog.addEventListener("click", (e) => {
        e.stopPropagation();
        borrarLogPersonaje(personaje.nombre);
      });
      botonesDiv.appendChild(btnBorrarLog);

      // Botón Ficha
      const btnFicha = document.createElement("button");
      btnFicha.textContent = "Ficha";
      btnFicha.addEventListener("click", (e) => {
        e.stopPropagation();
        abrirModalFicha(personaje.nombre);
      });
      botonesDiv.appendChild(btnFicha);

      // Botón Eliminar (solo si no es admin)
      if (personaje.nombre !== "admin") {
        const btnEliminar = document.createElement("button");
        btnEliminar.textContent = "Eliminar";
        btnEliminar.style.backgroundColor = "#ff000044"; // 🔴 fondo rojo
        btnEliminar.style.color = "#ff0000";
        btnEliminar.style.border = "1px solid #ff0000aa";
        btnEliminar.style.padding = "4px 8px";
        btnEliminar.style.borderRadius = "4px";
        btnEliminar.style.cursor = "pointer";

        btnEliminar.addEventListener("click", (e) => {
          e.stopPropagation();
          eliminarPersonaje(personaje.nombre);
        });

        botonesDiv.appendChild(btnEliminar);
      }

      // ====== Inputs de preguntas ======
      const preguntasDiv = document.createElement("div");
      preguntasDiv.style.display = "flex";
      preguntasDiv.style.gap = "5px";
      preguntasDiv.style.alignItems = "center";
      preguntasDiv.style.marginTop = "6px";

      ["anima", "eidolon", "hada", "fantasma"].forEach(ia => {
        const container = document.createElement("div");
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.alignItems = "center";

        const label = document.createElement("label");
        label.textContent = ia.charAt(0).toUpperCase() + ia.slice(1);
        label.style.fontSize = "10px";
        label.style.color = "#00ffff";

        const input = document.createElement("input");
        input.type = "number";
        input.min = -1;
        input.value = personaje.preguntas[ia] ?? 0;
        input.dataset.nombre = personaje.nombre;
        input.dataset.ia = ia;
        input.classList.add("pregunta-input");
        if (input.value == 0) input.classList.add("input-cero");
        input.addEventListener("input", () => {
          if (input.value == 0) {
            input.classList.add("input-cero");
          } else {
            input.classList.remove("input-cero");
          }
        });

        container.appendChild(label);
        container.appendChild(input);
        preguntasDiv.appendChild(container);
      });


      const btnReset = document.createElement("button");
      btnReset.textContent = "Resetear";
      btnReset.addEventListener("click", (e) => {
        e.stopPropagation();
        resetearPreguntas(personaje.nombre);
      });
      preguntasDiv.appendChild(btnReset);

      // ====== Montaje final ======
      const container = document.createElement("div");
      container.style.display = "flex";
      container.style.flexDirection = "column";
      container.style.gap = "6px";

      container.appendChild(nombreElem);
      container.appendChild(botonesDiv);
      container.appendChild(preguntasDiv);

      div.appendChild(container);
      lista.appendChild(div);
    });

    // Botón de guardar cambios de preguntas
    const guardarTodos = document.createElement("button");
    guardarTodos.textContent = "💾 Guardar Cambios";
    guardarTodos.style.marginTop = "10px";
    guardarTodos.addEventListener("click", guardarCambiosPreguntas);
    lista.appendChild(guardarTodos);

  } catch (error) {
    console.error("Error cargando personajes:", error);
  }
}


async function resetearPreguntas(nombre) {
  if (!confirm(`¿Resetear todas las preguntas de ${nombre}?`)) return;

  try {
    const res = await fetch("/admin/resetear-preguntas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre })
    });

    const data = await res.json();
    alert(data.mensaje || "Preguntas reseteadas.");
    cargarPersonajes();
  } catch (error) {
    console.error("Error reseteando preguntas:", error);
  }
}

async function guardarCambiosPreguntas() {
  const inputs = document.querySelectorAll(".pregunta-input");
  const cambios = {};

  inputs.forEach(input => {
    const nombre = input.dataset.nombre;
    const ia = input.dataset.ia;
    const valor = parseInt(input.value);

    if (!cambios[nombre]) cambios[nombre] = {};
    cambios[nombre][ia] = valor;
  });

  try {
    const res = await fetch("/admin/guardar-preguntas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cambios })
    });

    const data = await res.json();
    alert(data.mensaje || "Cambios guardados.");
    cargarPersonajes();
  } catch (error) {
    console.error("Error guardando cambios:", error);
  }
}




async function guardarPersonaje() {
  let nombre = document.getElementById("nombre-input").value.trim();
  let clave = document.getElementById("clave-input").value.trim();
  const rol = document.getElementById("rol-input").value;

  if (!nombre || !clave) {
    alert("Nombre y clave son obligatorios.");
    return;
  }

  if (nombre.toLowerCase() === "admin") {
    clave = "olympus"; // Protección de admin
  }

  try {
    // Si estamos editando y el nombre cambió, eliminar el viejo primero
    if (editandoNombre && editandoNombre !== nombre) {
      if (editandoNombre.toLowerCase() === "admin") {
        alert("No puedes cambiar el nombre del personaje admin.");
        return;
      }

      await fetch("/admin/personajes", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre: editandoNombre })
      });

      // Opcional: también deberías aquí eliminar o renombrar su log, conexiones y ficha si quieres que todo quede consistente
    }

    // Guardar el personaje (nuevo o actualizado)
    const res = await fetch("/admin/personajes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, clave, rol })
    });

    const data = await res.json();
    alert(data.mensaje || "Personaje guardado.");

    cerrarModal();
    cargarPersonajes();
    document.getElementById("lista-personajes").style.display = "block";
    personajesMostrados = true;

  } catch (error) {
    console.error("Error guardando personaje:", error);
  }
}


async function eliminarPersonaje(nombre) {
  if (nombre === "admin") {
    alert("No puedes eliminar el personaje admin.");
    return;
  }

  if (!confirm(`¿Seguro que quieres eliminar a ${nombre}?`)) return;

  try {
    const res = await fetch("/admin/personajes", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre })
    });
    const data = await res.json();
    alert(data.mensaje || "Personaje eliminado.");
    cargarPersonajes();
  } catch (error) {
    console.error("Error eliminando personaje:", error);
  }
}

let cyMini = null;

function actualizarMiniGrafo() {
  if (!document.getElementById('cy-mini')) return;

  if (cyMini) {
    cyMini.destroy();
  }

  cyMini = cytoscape({
    container: document.getElementById('cy-mini'),
    elements: [
      ...nodosActuales.map(n => ({ data: n.data })),
      ...conexionesActuales.map(c => ({ data: c.data }))
    ],
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'font-family': 'Share Tech Mono, monospace',
          'font-size': 10,
          'color': '#00ffff',
          'text-outline-color': '#101010',
          'text-outline-width': 1,
          'background-color': 'rgba(0, 255, 255, 0.2)',
          'border-width': 1,
          'border-color': '#00ffff',
          'width': 20,
          'height': 20
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 1,
          'line-color': 'rgba(0, 255, 255, 0.2)',
          'target-arrow-shape': 'none',
          'curve-style': 'bezier'
        }
      }
    ],
    layout: {
      name: 'cose',
      animate: true,
      animationDuration: 500,
      fit: true,
      padding: 10,
      randomize: false
    }
  });
}


// ==== LOGS ====

async function abrirLogPersonaje(nombre) {
  try {
    const res = await fetch(`/admin/logs/${nombre}.json`);
    const eventos = await res.json();

    const modal = document.getElementById("modal-log");
    const contenido = document.getElementById("contenido-log");
    const titulo = document.getElementById("titulo-log");

    titulo.textContent = `Historial de ${nombre}`;
    contenido.innerHTML = "";

    if (eventos.length === 0) {
      contenido.innerHTML = "<p>No hay eventos registrados.</p>";
    } else {
      eventos.forEach(evento => {
        const div = document.createElement("div");
        div.innerHTML = `
          <div><strong>${evento.timestamp}</strong> - <em>${evento.tipo}</em></div>
          <div style="margin-top: 4px;">${evento.contenido}</div>
        `;
        contenido.appendChild(div);
      });
    }

    modal.style.display = "flex";
  } catch (error) {
    console.error("Error cargando historial del personaje:", error);
  }
}

function cerrarModalLog() {
  document.getElementById("modal-log").style.display = "none";
}

// ==== CONEXIONES ====

async function abrirEditorConexiones(nombre) {
  personajeActual = nombre;
  document.getElementById("titulo-conexiones").textContent = `Conexiones de ${nombre}`;

  try {
    let res = await fetch(`/conexiones/personajes/${nombre}.json`);

    if (res.status === 404) {
      console.warn(`Archivo de conexiones para ${nombre} no encontrado, creando nuevo...`);
      await fetch(`/conexiones/personajes/${nombre}.json`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ elements: { nodes: [], edges: [] } })
      });
      res = await fetch(`/conexiones/personajes/${nombre}.json`);
    }

    const data = await res.json();
    console.log("Datos cargados:", data);

    // Seguridad extra: si falta 'elements', lo inicializamos
    if (!data.elements) {
      console.warn("Warning: archivo sin 'elements'. Inicializando vacío.");
      data.elements = { nodes: [], edges: [] };
    }

    nodosActuales = data.elements.nodes || [];
    conexionesActuales = data.elements.edges || [];

    renderizarConexiones();
    renderizarNodos();
    renderizarSelects();
    document.getElementById("conexiones-modal").style.display = "flex";

  } catch (error) {
    console.error("Error cargando o creando conexiones:", error);
    alert("Error cargando conexiones de este personaje.");
  }
}



function renderizarConexiones() {
  const lista = document.getElementById("lista-conexiones");
  lista.innerHTML = "";

  conexionesActuales.forEach((conexion, index) => {
    const div = document.createElement("div");
    div.style.display = "flex";
    div.style.alignItems = "center";
    div.style.marginBottom = "6px";

    const texto = document.createElement("span");
    texto.textContent = `${conexion.data.source} ➔ ${conexion.data.target}`;
    texto.style.marginRight = "10px";

    const inputLabel = document.createElement("input");
    inputLabel.value = conexion.data.label || "";
    inputLabel.style.flex = "1";
    inputLabel.addEventListener("input", (e) => {
      conexion.data.label = e.target.value;
    });

    const btnEliminar = document.createElement("button");
    btnEliminar.textContent = "Eliminar";
    btnEliminar.style.marginLeft = "10px";
    btnEliminar.addEventListener("click", () => {
      conexionesActuales.splice(index, 1);
      renderizarConexiones();
    });

    div.appendChild(texto);
    div.appendChild(inputLabel);
    div.appendChild(btnEliminar);
    lista.appendChild(div);
  });

  actualizarMiniGrafo(); // ✅ Solo una vez, después de renderizar todo
}


function renderizarNodos() {
  const listaNodos = document.getElementById("lista-nodos");
  listaNodos.innerHTML = "";

  nodosActuales.forEach((nodo) => {
    const div = document.createElement("div");
    div.style.display = "flex";
    div.style.alignItems = "center";
    div.style.marginBottom = "6px";

    const texto = document.createElement("span");
    texto.textContent = nodo.data.label;
    texto.style.marginRight = "10px";

    const btnEliminar = document.createElement("button");
    btnEliminar.textContent = "Eliminar Nodo";
    btnEliminar.addEventListener("click", () => {
      if (confirm(`¿Eliminar el nodo "${nodo.data.label}"?`)) {
        eliminarNodo(nodo.data.id);
      }
    });

    div.appendChild(texto);
    div.appendChild(btnEliminar);
    listaNodos.appendChild(div);
  });
  actualizarMiniGrafo();
}

function eliminarNodo(idNodo) {
  nodosActuales = nodosActuales.filter(n => n.data.id !== idNodo);
  conexionesActuales = conexionesActuales.filter(c => c.data.source !== idNodo && c.data.target !== idNodo);
  renderizarConexiones();
  renderizarNodos();
  renderizarSelects();
}

function renderizarSelects() {
  const sourceSelect = document.getElementById("source-nodo");
  const targetSelect = document.getElementById("target-nodo");

  sourceSelect.innerHTML = "";
  targetSelect.innerHTML = "";

  nodosActuales.forEach((nodo) => {
    const optionSource = document.createElement("option");
    optionSource.value = nodo.data.id;
    optionSource.textContent = nodo.data.label;

    const optionTarget = document.createElement("option");
    optionTarget.value = nodo.data.id;
    optionTarget.textContent = nodo.data.label;

    sourceSelect.appendChild(optionSource);
    targetSelect.appendChild(optionTarget);
  });
}

document.getElementById("añadir-conexion").addEventListener("click", () => {
  const source = document.getElementById("source-nodo").value.trim();
  const target = document.getElementById("target-nodo").value.trim();
  const label = document.getElementById("label-conexion").value.trim();

  if (!source || !target || !label) {
    alert("Todos los campos son obligatorios.");
    return;
  }

  if (source === target) {
    alert("No puedes conectar un personaje consigo mismo.");
    return;
  }

  const newEdge = {
    data: {
      id: `e${Date.now()}`,
      source,
      target,
      label
    }
  };

  conexionesActuales.push(newEdge);
  document.getElementById("label-conexion").value = "";
  renderizarConexiones();
});

document.getElementById("guardar-conexiones").addEventListener("click", async () => {
  try {
    const body = {
      elements: {
        nodes: nodosActuales,
        edges: conexionesActuales
      }
    };

    const res = await fetch(`/conexiones/personajes/${personajeActual}.json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    const data = await res.json();
    alert(data.mensaje || "Conexiones guardadas correctamente.");
    cerrarModalConexiones();
  } catch (error) {
    console.error("Error guardando conexiones:", error);
    alert("Error al guardar las conexiones.");
  }
});

function cerrarModalConexiones() {
  document.getElementById("conexiones-modal").style.display = "none";
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

document.getElementById("crear-nodo").addEventListener("click", () => {
  const id = document.getElementById("nuevo-nodo-id").value.trim();
  const label = document.getElementById("nuevo-nodo-label").value.trim();

  if (!id || !label) {
    alert("Debes rellenar ID y Nombre del nodo.");
    return;
  }

  if (nodosActuales.some(n => n.data.id === id)) {
    alert("Ya existe un nodo con ese ID.");
    return;
  }

  nodosActuales.push({
    data: { id: id, label: label }
  });

  document.getElementById("nuevo-nodo-id").value = "";
  document.getElementById("nuevo-nodo-label").value = "";

  renderizarSelects();
  renderizarNodos();
  alert("Nodo creado correctamente.");
});

async function editarPersonaje(nombre) {
  editandoNombre = nombre;

  try {
    const res = await fetch(`/admin/personajes`);
    const personajes = await res.json();

    const personaje = personajes.find(p => p.nombre.toLowerCase() === nombre.toLowerCase());
    if (!personaje) {
      alert("Personaje no encontrado.");
      return;
    }

    // Ahora pedimos los datos individuales
    const datosRes = await fetch(`/admin/personaje/${nombre}`);
    if (!datosRes.ok) {
      alert("Error cargando datos del personaje.");
      return;
    }

    const datos = await datosRes.json();

    abrirModal(nombre, datos.clave, datos.rol || 'jugador');
  } catch (error) {
    console.error("Error cargando personaje:", error);
  }
}

async function borrarLogPersonaje(nombre) {
  if (!confirm(`¿Seguro que quieres eliminar el historial de ${nombre}? Esta acción no se puede deshacer.`)) return;

  try {
    const res = await fetch(`/admin/logs/${nombre}.json`, {
      method: "DELETE"
    });

    if (res.ok) {
      alert(`Historial de ${nombre} eliminado correctamente.`);
    } else {
      alert("No se pudo eliminar el log.");
    }
  } catch (error) {
    console.error("Error borrando log:", error);
  }
}

document.getElementById("cerrar-modal-ficha").addEventListener("click", () => {
  document.getElementById("modal-ficha").style.display = "none";
});

document.getElementById("guardar-ficha").addEventListener("click", async () => {
  const editor = document.getElementById("editor-ficha");
  const jsonValido = recopilarDatosEditorFicha(editor);

  try {
    const res = await fetch(`/admin/ficha/${personajeActual}.json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(jsonValido)
    });

    const data = await res.json();
    alert(data.mensaje || "Ficha guardada.");
    document.getElementById("modal-ficha").style.display = "none";
  } catch (error) {
    alert("⚠️ Error guardando la ficha.");
    console.error(error);
  }
});



async function abrirModalFicha(nombre = null) {
  // Si no se pasa nombre, lo pedimos al backend
  if (!nombre) {
    try {
      const session = await fetch("/session-info");
      const datos = await session.json();
      if (!datos.usuario) {
        alert("⚠️ Sesión no válida.");
        return;
      }
      nombre = datos.usuario;
    } catch (error) {
      console.error("Error obteniendo usuario:", error);
      alert("⚠️ Error de sesión.");
      return;
    }
  }

  personajeActual = nombre;
  const ruta = `/admin/ficha/${nombre}.json`;

  try {
    let res = await fetch(ruta);

    // Si no existe, la creamos automáticamente
    if (res.status === 404) {
      console.warn(`Ficha de ${nombre} no encontrada. Creando una nueva...`);

      const fichaBase = {
        nombre_personaje: nombre === "admin" ? "Administrador" : nombre,
        nombre_jugador: nombre === "admin" ? "Narrador" : "",
        cabala: "",
        naturaleza: "",
        senda: "",
        arquetipo: "",
        sec_1: "",
        sec_2: "",
        sec_3: "",
        sec_4: "",
        daño: 0,
        rotura: 0,
        mutacion: 0,
        cyber: 0
      };

      const crear = await fetch(ruta, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fichaBase)
      });

      if (!crear.ok) throw new Error("No se pudo crear la ficha.");
      res = await fetch(ruta);
    }

    const datos = await res.json();
    document.getElementById("titulo-ficha").textContent = `Ficha de ${nombre}`;

    const editor = document.getElementById("editor-ficha");
    generarEditorFicha(datos, editor);

    document.getElementById("modal-ficha").style.display = "flex";

  } catch (err) {
    alert("⚠️ Error cargando la ficha.");
    console.error(err);
  }
}


// === NUEVO GENERADOR DE FICHA CON GUARDADO POR CAMPO ===
function generarEditorFicha(datos, parent, prefix = '') {
  const inputs = document.querySelectorAll("#modal-ficha input[data-id]");
  inputs.forEach(input => {
    const key = input.dataset.id;
    if (datos.hasOwnProperty(key)) {
      input.value = datos[key];
    }
  });
}

// === CERRAR MODAL FICHA ===
document.getElementById("cerrar-modal-ficha").addEventListener("click", () => {
  document.getElementById("modal-ficha").style.display = "none";
});


function recopilarDatosEditorFicha() {
  const inputs = document.querySelectorAll("#modal-ficha input[data-id]");
  const resultado = {};

  inputs.forEach(input => {
    const key = input.dataset.id;
    let valor = input.value;
    if (input.type === "number") valor = parseInt(valor, 10);
    resultado[key] = valor;
  });

  return resultado;
}

