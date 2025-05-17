document.addEventListener("DOMContentLoaded", async () => {
  let enModoPago = false;
  let puntosAPagar = 0;
  let puntosCurados = 0;
  let objetivo = null;
  let modo = null;

  try {
    const res = await fetch("/ficha/personajes/personaje.json");
    const data = await res.json();

    document.querySelectorAll("[data-id]").forEach(el => {
      const key = el.getAttribute("data-id");
      if (["daño", "rotura", "mutacion", "cyber"].includes(key)) return;
      if (data[key]) el.innerText = data[key];
    });

    ["daño", "rotura", "mutacion", "cyber"].forEach(seccion => {
      const bloque = document.querySelector(`.indicador-toggle[data-id="${seccion}"]`);
      if (!bloque) return;

      const puntos = bloque.querySelectorAll(".item");

      let nivel = 0;
      const valor = data[seccion];
      if (Array.isArray(valor)) {
        nivel = valor.reduce((acc, v) => acc + (v ? 1 : 0), 0);
      } else if (typeof valor === "number") {
        nivel = valor;
      }

      activarHasta(puntos, nivel);

      puntos.forEach((punto, index) => {
        punto.addEventListener("click", async () => {
          const nivelActual = contarActivos(puntos);
          const nuevoNivel = (nivelActual === index + 1) ? 0 : index + 1;

          if (enModoPago) {
            if (
              ["mutacion", "cyber"].includes(seccion) &&
              !punto.classList.contains("activo") &&
              punto.classList.contains("seleccion-coste")
            ) {
              const nivelMutacion = contarActivos(document.querySelectorAll(`.indicador-toggle[data-id="mutacion"] .item`));
              const nivelCyber = contarActivos(document.querySelectorAll(`.indicador-toggle[data-id="cyber"] .item`));
              const total = nivelMutacion + nivelCyber;
          
              if (total >= 5) {
                mostrarMensajePago(true, `No puedes superar 5 puntos combinados entre mutación y cyber.`);
                return;
              }
          
              const seleccionables = Array.from(bloque.querySelectorAll(".item.seleccion-coste"));
              const indexEnSeleccionables = seleccionables.indexOf(punto);
          
              if (indexEnSeleccionables >= 0) {
                const nuevos = seleccionables.slice(0, indexEnSeleccionables + 1).filter(p => !p.classList.contains("activo"));
                nuevos.forEach(p => p.classList.add("activo"));
                puntosCurados += nuevos.length;
              }
          
              await guardarCambios(seccion, contarActivos(puntos));
          
              if (puntosCurados >= puntosAPagar) {
                activarHasta(objetivo.puntos, objetivo.nuevoNivel);
                await guardarCambios(modo, objetivo.nuevoNivel);
                reiniciarModoPago();
              } else {
                mostrarMensajePago(true, `Has pagado ${puntosCurados} / ${puntosAPagar} punto(s).`);
              }
            }
            return;
          }
          

          if (["daño", "rotura"].includes(seccion)) {
            if (nuevoNivel > nivelActual) {
              activarHasta(puntos, nuevoNivel);
              await guardarCambios(seccion, nuevoNivel);
            } else {
              const mutacionNivel = contarActivos(document.querySelectorAll(`.indicador-toggle[data-id="mutacion"] .item`));
              const cyberNivel = contarActivos(document.querySelectorAll(`.indicador-toggle[data-id="cyber"] .item`));

              const libres = (3 - mutacionNivel) + (3 - cyberNivel);
              const coste = nivelActual - nuevoNivel;

              if (libres < coste || mutacionNivel + cyberNivel >= 5) {
                mostrarMensajePago(true, `No hay suficiente espacio libre en mutación o cyber para pagar ${coste} punto(s).`);
                return;
              }

              puntosAPagar = coste;
              puntosCurados = 0;
              objetivo = { puntos, nuevoNivel };
              enModoPago = true;
              modo = seccion;

              activarSeleccionDePago(coste);
              mostrarMensajePago(true, `Selecciona ${puntosAPagar} punto(s) en mutación o cyber para curar ${seccion}.`);
            }
          } else if (["mutacion", "cyber"].includes(seccion)) {
            if (nuevoNivel > nivelActual) {
              const nivelMutacion = contarActivos(document.querySelectorAll(`.indicador-toggle[data-id="mutacion"] .item`));
              const nivelCyber = contarActivos(document.querySelectorAll(`.indicador-toggle[data-id="cyber"] .item`));
              const total = nivelMutacion + nivelCyber;

              if (nuevoNivel > 3 || (nuevoNivel + (seccion === "mutacion" ? nivelCyber : nivelMutacion)) > 5) {
                mostrarMensajePago(true, `No puedes superar 5 puntos entre mutación y cyber.`);
                return;
              }

              activarHasta(puntos, nuevoNivel);
              await guardarCambios(seccion, nuevoNivel);
            } else {
              alert("No puedes reducir puntos en esta sección.");
            }
          }
        });
      });
    });

    function activarHasta(lista, n) {
      lista.forEach((el, i) => {
        el.classList.toggle("activo", i < n);
      });
    }

    function contarActivos(lista) {
      return Array.from(lista).filter(el => el.classList.contains("activo")).length;
    }

    async function guardarCambios(clave, nuevoValor) {
      try {
        const body = { [clave]: nuevoValor };
        const res = await fetch("/ficha/guardar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error("No se pudo guardar");
      } catch (e) {
        console.error("Error guardando cambio:", e);
      }
    }

    function activarSeleccionDePago() {
      ["mutacion", "cyber"].forEach(seccion => {
        const bloque = document.querySelector(`.indicador-toggle[data-id="${seccion}"]`);
        bloque.classList.add("modo-pago");
    
        const vacios = Array.from(bloque.querySelectorAll(".item")).filter(el => !el.classList.contains("activo"));
        const seleccionables = vacios.slice(0, puntosAPagar);
    
        seleccionables.forEach((el, i) => {
          el.classList.add("seleccion-coste");
    
          // Efecto hover visual
          el.addEventListener("mouseenter", () => {
            seleccionables.slice(0, i + 1).forEach(c => c.classList.add("hover-previa"));
          });
    
          el.addEventListener("mouseleave", () => {
            seleccionables.forEach(c => c.classList.remove("hover-previa"));
          });
        });
      });
    }
    

    function reiniciarModoPago() {
      enModoPago = false;
      puntosAPagar = 0;
      puntosCurados = 0;
      objetivo = null;
      modo = null;

      ["mutacion", "cyber"].forEach(seccion => {
        const bloque = document.querySelector(`.indicador-toggle[data-id="${seccion}"]`);
        bloque.classList.remove("modo-pago");
        bloque.querySelectorAll(".item").forEach(el => {
          el.classList.remove("seleccion-coste");
        });
      });

      mostrarMensajePago(false);
    }

    function mostrarMensajePago(mostrar, texto = "") {
      let div = document.querySelector("#mensaje-pago");
      if (!div) {
        div = document.createElement("div");
        div.id = "mensaje-pago";
        div.style.marginTop = "10px";
        div.style.fontWeight = "bold";
        div.style.color = "red";
        div.style.textAlign = "center";
        document.querySelector(".contenedor").appendChild(div);
      }
      div.style.display = mostrar ? "block" : "none";
      div.textContent = texto;
    }

  } catch (err) {
    console.error("Error cargando datos de personaje:", err);
  }
});
