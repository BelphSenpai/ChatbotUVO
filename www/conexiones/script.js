const popup = document.getElementById('popup');

async function iniciarGrafoConexiones() {
  try {
    const resSesion = await fetch('/session-info');
    const { usuario: id } = await resSesion.json();

    // Enlace a la ficha (sin parámetros)
    const linkFicha = document.getElementById("ficha-link");
    if (linkFicha) {
      linkFicha.href = "/ficha";
    }

    const res = await fetch(`/conexiones/personajes/${id}.json`);
    if (!res.ok) throw new Error("Archivo no encontrado");
    const data = await res.json();

    const cy = cytoscape({
      container: document.getElementById('cy'),
      elements: [...data.elements.nodes, ...data.elements.edges],
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'font-family': 'Share Tech Mono, monospace',
            'font-size': 14,
            'color': '#00ffff',
            'text-outline-color': '#101010',
            'text-outline-width': 1,
            'background-color': 'rgba(10, 90, 90, 0.03)',
            'background-opacity': 0.5,
            'border-width': 2,
            'border-color': '#00ffff',
            'border-opacity': 0.8,
            'shape': 'ellipse',
            'text-valign': 'center',
            'text-halign': 'center'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 1,
            'line-color': 'rgba(0, 255, 255, 0.08)',
            'target-arrow-shape': 'none',
            'curve-style': 'bezier',
            'line-style': 'dashed'
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: true,
        animationEasing: 'ease-out',
        animationDuration: 1000,
        randomize: false,
        gravity: 1,
        numIter: 1000,
        nodeRepulsion: 2048,
        edgeElasticity: 100
      }
    });

    setTimeout(() => {
      cy.resize();
      cy.fit();
    }, 300);

    window.addEventListener("resize", () => {
      cy.resize();
      cy.fit();
    });

    const canvas = document.querySelector('canvas');
    let lastMouseDownTime = 0;

    canvas.addEventListener('mousedown', () => {
      lastMouseDownTime = Date.now();
    });

    canvas.addEventListener('mouseup', (e) => {
      const elapsed = Date.now() - lastMouseDownTime;
      if (elapsed > 250) return;

      const rect = canvas.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      let clickedNode = null;

      cy.nodes().forEach(node => {
        const pos = node.renderedPosition();
        const dist = Math.hypot(pos.x - clickX, pos.y - clickY);
        if (dist < 30) clickedNode = node;
      });

      if (clickedNode) {
        const edges = clickedNode.connectedEdges().map(edge => {
          const other = edge.source().id() === clickedNode.id() ? edge.target() : edge.source();
          return `<li>${edge.data('label')} con <strong>${other.data('label')}</strong></li>`;
        });

        popup.innerHTML = `<strong>${clickedNode.data('label')}</strong><ul>${edges.join('')}</ul>`;
        popup.style.left = (clickX + 20) + 'px';
        popup.style.top = (clickY + 20) + 'px';
        popup.style.display = 'block';
      } else {
        popup.style.display = 'none';
      }
    });

  } catch (err) {
    console.error("Error al cargar el grafo de conexiones:", err);
    popup.innerHTML = `[ERROR] No se pudo cargar el archivo de conexiones`;
    popup.style.display = 'block';
    popup.style.left = '20px';
    popup.style.top = '20px';
  }
}

window.addEventListener("DOMContentLoaded", iniciarGrafoConexiones);
