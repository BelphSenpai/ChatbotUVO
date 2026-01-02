const popup = document.getElementById('popup');

async function iniciarGrafoTramas() {
  try {
    const resSesion = await fetch('/session-info');
    const { usuario: id } = await resSesion.json();

    const linkFicha = document.getElementById("ficha-link");
    if (linkFicha) {
      linkFicha.href = "/ficha";
    }

    const res = await fetch(`/tramas/personajes/${id}.json`);
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

    // Evento TAP compatible con touch + click
    cy.on('tap', 'node', (event) => {
      const node = event.target;
      const pos = event.renderedPosition || node.renderedPosition();

      const edges = node.connectedEdges().map(edge => {
        const other = edge.source().id() === node.id() ? edge.target() : edge.source();
        return `<li>${edge.data('label')} con <strong>${other.data('label')}</strong></li>`;
      });

      popup.innerHTML = `<strong>${node.data('label')}</strong><ul>${edges.join('')}</ul>`;

      // Calculamos la posición asegurando que no se salga de la pantalla
      const x = Math.min(pos.x + 20, window.innerWidth - 200);
      const y = Math.min(pos.y + 20, window.innerHeight - 100);
      popup.style.left = `${x}px`;
      popup.style.top = `${y}px`;
      popup.style.display = 'block';
    });

    // Ocultar popup si se toca fuera de nodos
    cy.on('tap', (event) => {
      if (event.target === cy) {
        popup.style.display = 'none';
      }
    });

  } catch (err) {
    console.error("Error al cargar el grafo de tramas:", err);
    popup.innerHTML = `[ERROR] No se pudo cargar el archivo de tramas`;
    popup.style.display = 'block';
    popup.style.left = '20px';
    popup.style.top = '20px';
  }
}

window.addEventListener("DOMContentLoaded", iniciarGrafoTramas);
