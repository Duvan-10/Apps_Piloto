const API_BASE = 'http://localhost:5000';
let torneoSeleccionado = null;

document.addEventListener('DOMContentLoaded', () => {
    const dateEl = document.getElementById('current-date');
    if (dateEl) {
        dateEl.innerText = new Intl.DateTimeFormat('es-ES', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
        }).format(new Date());
    }

    inicializarFotoPerfil();
    cargarFotoPerfilGuardada();

    cargarMenuTorneos();
});

// --- NAVEGACIÓN ---
function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(sec => sec.classList.add('d-none'));
    document.querySelectorAll('.nav-links a').forEach(link => link.classList.remove('active'));

    const section = document.getElementById('sec-' + sectionId);
    const link = document.getElementById('link-' + sectionId);

    if (section) section.classList.remove('d-none');
    if (link) link.classList.add('active');

    if (sectionId === 'torneos') {
        volverAListaTorneos();
    }
}

/*
================================================================================
GUIA DE ESCALADO PARA NUEVOS TORNEOS
================================================================================
1. En backend, agrega el torneo dentro de TORNEOS_CONFIG en app.py usando el mismo
   esquema: slug -> { nombre, api_id, url_logo }.
2. El menú principal NO debe tocarse manualmente. Este frontend llama a /api/torneos
   y pinta automáticamente las tarjetas en función del JSON que reciba.
3. Si agregas otro torneo en el backend, solo asegúrate de que su api_id tenga una
   ruta válida en /api/partidos/<id>. El render ya está preparado para recibir una
   lista de objetos con equipo_local, equipo_visitante, logo_local y logo_visitante.
4. Para no romper la navegación, conserva estas funciones como contrato estable:
   - cargarMenuTorneos()
   - seleccionarTorneo()
   - volverAListaTorneos()
   - cargarPredicciones()
   - renderizarPartidos()
5. Cualquier mejora visual nueva debe ir sobre las clases existentes de las tarjetas
   y no reemplazando la estructura HTML que estas funciones generan. Eso mantiene la
   compatibilidad con el router visual de la pantalla de Torneos.
================================================================================
*/

// --- LÓGICA DE TORNEOS ---
function cargarMenuTorneos() {
    const grid = document.getElementById('grid-torneos');
    if (!grid) return;

    grid.innerHTML = `
        <div class="col-12 py-5 text-center text-secondary">
            <div class="spinner-border spinner-border-sm me-2" role="status"></div>
            Cargando torneos...
        </div>`;

    fetch(`${API_BASE}/api/torneos`)
        .then(res => res.json())
        .then(torneos => {
            grid.innerHTML = '';

            torneos.forEach(torneo => {
                const safeNombre = torneo.nombre.replace(/'/g, "\\'");
                const logoFallback = torneo.url_logo_fallback || 'https://crests.football-data.org/CL.png';
                grid.innerHTML += `
                    <div class="col-12 col-sm-6 col-lg-4 col-xxl-3 mb-4">
                        <button type="button" class="torneo-item-minimal"
                                onclick="seleccionarTorneo('${safeNombre}', ${torneo.api_id}, '${torneo.url_logo}', '${logoFallback}')">
                            <div class="torneo-icon-container">
                                <img src="${torneo.url_logo}" alt="${torneo.nombre}" onerror="this.onerror=null;this.src='${logoFallback}'">
                            </div>
                            <span class="torneo-card-title">${torneo.nombre}</span>
                        </button>
                    </div>`;
            });
        })
        .catch(() => {
            grid.innerHTML = '<p class="text-danger mb-0">Error conectando con el servidor Python.</p>';
        });
}

function seleccionarTorneo(nombre, id, logoUrl, logoFallback) {
    torneoSeleccionado = {
        nombre,
        api_id: id,
        url_logo: logoUrl,
        url_logo_fallback: logoFallback,
    };

    document.getElementById('vista-lista-torneos').classList.add('d-none');
    document.getElementById('vista-detalles-torneo').classList.remove('d-none');
    document.getElementById('titulo-torneo-actual').innerText = nombre;
    document.getElementById('breadcrumb-torneo-actual').innerText = nombre;

    cargarPredicciones(id);
}

function volverAListaTorneos() {
    document.getElementById('vista-detalles-torneo').classList.add('d-none');
    document.getElementById('vista-lista-torneos').classList.remove('d-none');
}

// --- CARGA DE PARTIDOS CON LOGOS DE CLUBES ---
function cargarPredicciones(leagueId = torneoSeleccionado?.api_id) {
    if (!leagueId) return;

    const contenedor = document.getElementById('contenedor-predicciones');
    if (!contenedor) return;

    contenedor.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-info" role="status"></div>
        </div>`;

    fetch(`${API_BASE}/api/partidos/${leagueId}`)
        .then(res => res.json())
        .then(data => {
            renderizarPartidos(Array.isArray(data) ? data : []);
        })
        .catch(() => {
            contenedor.innerHTML = '<div class="col-12"><p class="text-danger">No se pudieron cargar los partidos.</p></div>';
        });
}

function renderizarPartidos(partidos) {
    const contenedor = document.getElementById('contenedor-predicciones');
    if (!contenedor) return;

    if (!Array.isArray(partidos) || partidos.length === 0) {
        contenedor.innerHTML = `
            <div class="col-12">
                <div class="empty-state-card">
                    <h4 class="mb-2">No hay partidos disponibles</h4>
                    <p class="mb-0">La API respondió correctamente, pero no hay cruces para este torneo en este momento.</p>
                </div>
            </div>`;
        return;
    }

    contenedor.innerHTML = partidos.map(partido => `
        <div class="col-12 col-md-6 col-xl-4 mb-4">
            <article class="match-card">
                <div class="match-card-header">
                    <span class="match-tag">${partido.etapa || 'PARTIDO'}</span>
                    <span class="match-date">${formatearFecha(partido.fecha)}</span>
                </div>

                <div class="match-versus">
                    <div class="team-block">
                        <div class="team-logo-wrap">
                            <img src="${partido.logo_local}" alt="${partido.equipo_local}" class="team-logo" onerror="this.src='https://via.placeholder.com/120x120?text=Club'">
                        </div>
                        <div class="team-name">${partido.equipo_local}</div>
                    </div>

                    <div class="vs-badge">VS</div>

                    <div class="team-block">
                        <div class="team-logo-wrap">
                            <img src="${partido.logo_visitante}" alt="${partido.equipo_visitante}" class="team-logo" onerror="this.src='https://via.placeholder.com/120x120?text=Club'">
                        </div>
                        <div class="team-name">${partido.equipo_visitante}</div>
                    </div>
                </div>

                <div class="match-footer">
                    <span>Jornada ${partido.jornada ?? '-'}</span>
                    <span class="match-status">${partido.estado || 'PENDIENTE'}</span>
                </div>
            </article>
        </div>`).join('');
}

function formatearFecha(fechaISO) {
    if (!fechaISO) return 'Sin fecha';

    const fecha = new Date(fechaISO);
    if (Number.isNaN(fecha.getTime())) return fechaISO;

    return new Intl.DateTimeFormat('es-ES', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
    }).format(fecha);
}

function actualizarFotoLocal(event) {
    const input = event.target;
    const archivo = input.files && input.files[0];

    if (!archivo) {
        return;
    }

    const lector = new FileReader();
    lector.onload = () => {
        const dataUrl = lector.result;
        if (typeof dataUrl !== 'string') {
            return;
        }

        guardarFotoPerfil(dataUrl);
        aplicarFotoPerfil(dataUrl);
        limpiarSeleccionArchivo(input);
    };

    lector.readAsDataURL(archivo);
}

function cargarFotoPerfilGuardada() {
    const fotoGuardada = obtenerFotoPerfilGuardada();
    if (fotoGuardada) {
        aplicarFotoPerfil(fotoGuardada);
    }
}

function aplicarFotoPerfil(src) {
    const sidebarImg = document.getElementById('sidebar-profile-img');
    const mainImg = document.getElementById('main-profile-img');

    if (sidebarImg) {
        sidebarImg.src = src;
    }

    if (mainImg) {
        mainImg.src = src;
    }
}

function inicializarFotoPerfil() {
    const fileInput = document.getElementById('fileInput');
    const cambiarFotoBtn = document.getElementById('btn-cambiar-foto');

    if (fileInput) {
        fileInput.addEventListener('change', actualizarFotoLocal);
    }

    if (cambiarFotoBtn && fileInput) {
        cambiarFotoBtn.addEventListener('click', () => {
            fileInput.click();
        });
    }
}

function guardarFotoPerfil(src) {
    try {
        localStorage.setItem('perfil_foto', src);
        return;
    } catch (error) {
        // Fallback para navegadores o contextos donde localStorage no esté disponible.
    }

    try {
        sessionStorage.setItem('perfil_foto', src);
    } catch (error) {
        window.__perfilFotoTemporal = src;
    }
}

function obtenerFotoPerfilGuardada() {
    try {
        const local = localStorage.getItem('perfil_foto');
        if (local) return local;
    } catch (error) {
        // Continuar con el fallback.
    }

    try {
        const session = sessionStorage.getItem('perfil_foto');
        if (session) return session;
    } catch (error) {
        // Continuar con el fallback.
    }

    return window.__perfilFotoTemporal || null;
}

function limpiarSeleccionArchivo(input) {
    if (input) {
        input.value = '';
    }
}

window.actualizarFotoLocal = actualizarFotoLocal;