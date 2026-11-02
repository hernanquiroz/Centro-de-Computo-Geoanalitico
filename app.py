# -*- coding: utf-8 -*-
"""
============================================================
 CENTRO DE CÓMPUTO GEO-ANALÍTICO  —  ANTIOQUIA & COLOMBIA
============================================================
Dos pantallas holográficas animadas en Streamlit, flotando en 3D
sobre el fondo de la SALA DE CÓMPUTO (oficina con ventanas al
atardecer, skyline, escritorio y persona trabajando):

  • Pantalla izquierda  → Departamento de Antioquia (tema cian)
  • Pantalla derecha   → República de Colombia      (tema dorado)

Cada pantalla muestra:
  - Un mapa holográfico con línea de escaneo continua, nodos de
    municipios/departamentos que parpadean y ondas de pulso
    sobre la capital.
  - Una "hoja Excel" viva: barra de direcciones y fórmulas,
    celda activa que recorre fila por fila, datos sintéticos
    que se recalculan en cada frame y barra de estado de
    cómputo continuo (LISTO / COMPUTANDO / progreso / CPU).

Los datos son 100 % SINTÉTICOS (generados con `random`).

------------------------------------------------------------
 EJECUCIÓN LOCAL
------------------------------------------------------------
    pip install streamlit
    streamlit run app.py

------------------------------------------------------------
 PUBLICAR EN GITHUB + STREAMLIT COMMUNITY CLOUD
------------------------------------------------------------
 1. Crea un repositorio en GitHub con estos archivos:
        app.py
        requirements.txt        (contenido: streamlit)
        sala.jpg                (opcional: tu imagen de la sala)
    Si subes tu imagen como "sala.jpg" junto a app.py, la app la usa
    automáticamente como fondo de la sala de cómputo. Si no existe,
    la sala se dibuja sola con SVG (atardecer, skyline, escritorio).
 2. Sube el código:
        git init
        git add .
        git commit -m "Centro de cómputo geo-analítico"
        git branch -M main
        git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
        git push -u origin main
 3. En https://share.streamlit.io crea una nueva app apuntando
    a ese repositorio y a `app.py`. ¡Listo!

------------------------------------------------------------
 NOTAS
------------------------------------------------------------
 - La animación corre en bucle infinito. Presiona ESC (o el
   botón ⏹ del menú de Streamlit) para pausarla y poder
   ajustar velocidad y filas visibles en la barra lateral.
 - No requiere pandas ni numpy: solo Streamlit + stdlib.
"""

import base64
import os
import random
import time

import streamlit as st

# ============================================================
# 1. DATOS SINTÉTICOS
# ============================================================

MUNICIPIOS = [
    "Medellín", "Envigado", "Itagüí", "Bello", "Rionegro", "Turbo",
    "Apartadó", "Caucasia", "Segovia", "Zaragoza", "Yarumal",
    "Santa Rosa de Osos", "Barbosa", "Copacabana", "Girardota",
    "Caldas", "La Ceja", "El Retiro", "Guatapé", "Jardín",
    "Andes", "Puerto Berrío", "San Carlos", "Urrao", "Dabeiba",
]

DEPARTAMENTOS = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bogotá D.C.",
    "Bolívar", "Boyacá", "Caldas", "Caquetá", "Casanare", "Cauca",
    "Cesar", "Chocó", "Córdoba", "Cundinamarca", "Guainía",
    "Guaviare", "Huila", "La Guajira", "Magdalena", "Meta",
    "Nariño", "N. de Santander", "Putumayo", "Quindío",
    "Risaralda", "San Andrés", "Santander", "Sucre", "Tolima",
    "Valle del Cauca", "Vaupés", "Vichada",
]

TAREAS = [
    "COMPUTANDO MATRIZ",
    "SINCRONIZANDO NODOS",
    "RECALCULANDO FILAS",
    "OPTIMIZANDO CONSULTAS",
    "VALIDANDO REGISTROS",
]


def crear_filas(nombres, rango_v1, rango_v2, rango_v3, rango_v4, fijos=None):
    """Genera las filas de una hoja con valores sintéticos aleatorios."""
    fijos = fijos or {}
    filas = []
    for nombre in nombres:
        f = fijos.get(nombre, {})
        filas.append({
            "nombre": nombre,
            "v1": f.get("v1", random.uniform(*rango_v1)),
            "v2": f.get("v2", random.uniform(*rango_v2)),
            "v3": f.get("v3", random.uniform(*rango_v3)),
            "v4": f.get("v4", random.uniform(*rango_v4)),
        })
    return filas


def tick(filas, idx_activo):
    """Random-walk: la fila 'en cómputo' cambia mucho más rápido que el resto,
    simulando que la CPU está procesando esa fila de la hoja."""
    for i, fila in enumerate(filas):
        amp = 0.06 if i == idx_activo else 0.004
        for k in ("v1", "v2", "v3", "v4"):
            fila[k] = max(fila[k] * (1 + random.uniform(-amp, amp)), 0.01)


FILAS_ANT = crear_filas(
    MUNICIPIOS,
    (8_000, 460_000),     # población
    (120, 8_500),          # PIB (M USD)
    (900, 12_000),         # café (ton)
    (45, 99),              # cobertura (%)
    fijos={"Medellín": {"v1": 2_650_000, "v2": 24_000, "v3": 2_000}},
)

FILAS_COL = crear_filas(
    DEPARTAMENTOS,
    (0.4, 6.8),            # habitantes (millones)
    (1.2, 38),             # PIB (miles de millones USD)
    (60, 12_500),          # exportaciones (M USD)
    (40, 99),              # índice de desarrollo
    fijos={"Bogotá D.C.": {"v1": 8.1, "v2": 44.0, "v3": 9_500}},
)

ESPEC_ANT = {
    "encabezados": ["Municipio", "Población", "PIB (M USD)", "Café (ton)", "Cobertura"],
    "formatos": ["{v1:,.0f}", "{v2:,.1f}", "{v3:,.0f}", "{v4:,.1f}%"],
}

ESPEC_COL = {
    "encabezados": ["Departamento", "Hab. (M)", "PIB (B USD)", "Export. (M)", "Índice"],
    "formatos": ["{v1:,.2f}", "{v2:,.1f}", "{v3:,.0f}", "{v4:,.1f}"],
}


# ============================================================
# 2. FÓRMULAS "EN CÓMPUTO"
# ============================================================

def formulas_ant(filas, idx):
    n = len(filas) + 2
    act = filas[idx]
    return [
        (f"=SUMA(B3:B{n})", f"{sum(x['v1'] for x in filas):,.0f} hab."),
        (f"=PROMEDIO(C3:C{n})", f"{sum(x['v2'] for x in filas) / len(filas):,.1f} M USD"),
        (f"=MAX(D3:D{n})", f"{max(x['v3'] for x in filas):,.0f} ton"),
        (f'=CONTAR.SI(E3:E{n},">80")', f"{sum(1 for x in filas if x['v4'] > 80)} municipios"),
        (f'=BUSCARV("{act["nombre"]}",A:E,2)', f"{act['v1']:,.0f} hab."),
    ]


def formulas_col(filas, idx):
    n = len(filas) + 2
    act = filas[idx]
    return [
        (f"=SUMA(B3:B{n})", f"{sum(x['v1'] for x in filas):,.1f} M hab."),
        (f"=PROMEDIO(C3:C{n})", f"{sum(x['v2'] for x in filas) / len(filas):,.2f} B USD"),
        (f"=MAX(D3:D{n})", f"{max(x['v3'] for x in filas):,.0f} M USD"),
        (f'=CONTAR.SI(E3:E{n},">75")', f"{sum(1 for x in filas if x['v4'] > 75)} deptos."),
        (f'=BUSCARV("{act["nombre"]}",A:E,2)', f"{act['v1']:,.1f} M hab."),
    ]


# ============================================================
# 3. ESTILOS (CSS con animaciones continuas)
# ============================================================

CSS = """
<style>
.stApp { position: relative; z-index: 0; background: radial-gradient(1100px 600px at 25% -10%, #0c1c31 0%, #04070f 58%, #01030a 100%); }
section[data-testid="stAppViewContainer"], .main { background: transparent !important; }
#MainMenu, footer, header { visibility: hidden; }
.main-header { text-align: center; padding: 4px 0 2px; }
.main-header h1 {
  margin: 0; font-size: 1.95rem; letter-spacing: 2px; font-weight: 800;
  background: linear-gradient(90deg, #38bdf8, #a78bfa 50%, #fbbf24);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.main-header p { margin: 2px 0 14px; font-size: .8rem; color: #7c93ad; letter-spacing: 1.5px; }
.dot-live {
  display: inline-block; width: 9px; height: 9px; border-radius: 50%;
  background: #22c55e; box-shadow: 0 0 9px #22c55e; margin-right: 7px;
  animation: parpadeo 1.1s infinite; vertical-align: middle;
}
@keyframes parpadeo { 0%,100% { opacity: 1; } 50% { opacity: .2; } }

/* ─── Sala de cómputo (fondo) ─── */
.fondo-sala { position: fixed; inset: 0; z-index: -1; overflow: hidden; pointer-events: none; }
.fondo-sala svg, .fondo-sala img { width: 100%; height: 100%; object-fit: cover; display: block; }
.fondo-sala::after {
  content: ""; position: fixed; inset: 0;
  background: linear-gradient(rgba(2,6,16,.42), rgba(2,6,16,.74));
}
.block-container { background: transparent !important; padding-top: 1.2rem !important; }
section[data-testid="stSidebar"] { background: rgba(4,8,18,.88) !important; border-right: 1px solid rgba(56,189,248,.14); }
.bwin { animation: bwinBlink 4.5s ease-in-out infinite; }
@keyframes bwinBlink { 0%,100% { opacity: .85; } 50% { opacity: .12; } }

/* ─── Hologramas flotantes (inclinados en 3D) ─── */
.holo-float { animation: flotar 7s ease-in-out infinite; }
.holo-float.der { animation-delay: .9s; }
@keyframes flotar { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-11px); } }
.holo-flotante {
  border-radius: 16px; padding: 12px 14px; margin-bottom: 12px;
  transform: perspective(1300px) rotateY(9deg);
  backdrop-filter: blur(4px);
  box-shadow: 0 18px 42px rgba(0,0,0,.55);
}
.holo-float.der .holo-flotante { transform: perspective(1300px) rotateY(-9deg); }
.tema-cian {
  border: 1px solid rgba(56,189,248,.45);
  background: linear-gradient(165deg, rgba(14,42,72,.64), rgba(3,10,22,.85));
  animation: brilloCian 3.2s ease-in-out infinite;
}
.tema-oro {
  border: 1px solid rgba(251,191,36,.45);
  background: linear-gradient(165deg, rgba(59,44,12,.64), rgba(22,14,3,.85));
  animation: brilloOro 3.2s ease-in-out infinite;
}
@keyframes brilloCian {
  0%,100% { box-shadow: 0 0 14px rgba(56,189,248,.14), inset 0 0 34px rgba(56,189,248,.04); }
  50%     { box-shadow: 0 0 30px rgba(56,189,248,.34), inset 0 0 46px rgba(56,189,248,.10); }
}
@keyframes brilloOro {
  0%,100% { box-shadow: 0 0 14px rgba(251,191,36,.14), inset 0 0 34px rgba(251,191,36,.04); }
  50%     { box-shadow: 0 0 30px rgba(251,191,36,.34), inset 0 0 46px rgba(251,191,36,.10); }
}
.titulo-pantalla {
  display: flex; align-items: center; font: 600 11px/1.6 Consolas, Menlo, monospace;
  letter-spacing: 1px; color: #9fdcf9; margin-bottom: 8px;
}
.tema-oro .titulo-pantalla { color: #fde68a; }
.titulo-pantalla .der { margin-left: auto; opacity: .65; font-weight: 400; }

/* ─── Mapas SVG ─── */
.marco-mapa { border: 1px dashed rgba(148,163,184,.18); border-radius: 12px; overflow: hidden; background: rgba(2,8,18,.40); }
.marco-mapa svg { display: block; width: 100%; height: auto; }
.nodo { animation: nodoBlink 2.6s ease-in-out infinite; }
@keyframes nodoBlink { 0%,100% { opacity: .12; } 50% { opacity: 1; } }
.anillo { transform-box: fill-box; transform-origin: center; animation: anilloPulso 2.1s ease-out infinite; }
@keyframes anilloPulso { 0% { transform: scale(.35); opacity: .95; } 100% { transform: scale(3.1); opacity: 0; } }
.scanline { animation: escaneo 3.8s linear infinite; }
@keyframes escaneo { 0% { transform: translateY(0); } 100% { transform: translateY(415px); } }
.tmapa { fill: #e2e8f0; font: 700 15px 'Segoe UI', sans-serif; letter-spacing: 3px; opacity: .92; }
.tcap  { fill: #ffffff; font: 700 10px Consolas, monospace; letter-spacing: 1px; }

/* ─── Hoja Excel viva ─── */
.hoja { border: 1px solid rgba(120,170,230,.22); border-radius: 10px; padding: 8px; background: rgba(3,9,20,.68); backdrop-filter: blur(5px); box-shadow: 0 10px 30px rgba(0,0,0,.45); }
.fx-bar {
  display: flex; align-items: center; gap: 8px; font: 12px Consolas, monospace;
  background: #0d1420; border: 1px solid #233247; border-radius: 6px;
  padding: 5px 8px; margin-bottom: 7px; white-space: nowrap; overflow: hidden;
}
.addr { border: 1px solid #3b4d66; background: #16202f; color: #7dd3fc; border-radius: 4px; padding: 1px 8px; min-width: 36px; text-align: center; }
.fx { color: #f59e0b; font-style: italic; font-weight: 700; }
.formula { color: #e2e8f0; flex: 1; overflow: hidden; text-overflow: ellipsis; }
.resultado { color: #34d399; font-weight: 700; }

table.xl { width: 100%; border-collapse: collapse; table-layout: fixed; font: 11.5px/1.5 Consolas, Menlo, monospace; color: #dbe4f0; }
.xl th, .xl td { border: 1px solid #26364d; padding: 2.5px 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.xl th.esq, .xl td.numfila { background: #1b2434; color: #8ea3bd; text-align: center; font-size: 10.5px; }
.xl th.letra { background: #233247; color: #a9bcd4; text-align: center; font-size: 10.5px; }
.xl th.hdr { background: #217346; color: #ffffff; text-align: left; font-size: 11px; letter-spacing: .3px; }
.xl td.nom { text-align: left; font-weight: 600; }
.tema-cian .xl td.nom { color: #7dd3fc; }
.tema-oro .xl td.nom { color: #fcd34d; }
.xl td.num { text-align: right; font-variant-numeric: tabular-nums; color: #c9d6e8; }
.xl tr.fila-activa td { background: rgba(245,158,11,.10); }
.xl td.celda-activa { outline: 2px solid #f59e0b; outline-offset: -2px; background: rgba(245,158,11,.22); }

.xl-estado { display: flex; align-items: center; gap: 8px; font: 10.5px Consolas, monospace; color: #8ea3bd; margin-top: 7px; }
.estado-ok { color: #22c55e; font-weight: 700; letter-spacing: 1px; }
.prog { flex: 1; height: 5px; background: #101a2b; border-radius: 3px; overflow: hidden; }
.prog-bar { height: 100%; background: linear-gradient(90deg, #f59e0b, #22c55e); border-radius: 3px; }
.pct { min-width: 34px; text-align: right; }
.tarea { color: #cbd5e1; }
.cursor { animation: parpadeo .8s steps(1) infinite; color: #f59e0b; margin-left: 2px; }
.meta { margin-left: auto; opacity: .75; }

.chips { display: flex; gap: 6px; margin-top: 7px; flex-wrap: wrap; }
.chip { font: 10px Consolas, monospace; color: #9fb6d0; border: 1px solid #233247; background: #0d1521; border-radius: 999px; padding: 2px 9px; white-space: nowrap; }
</style>
"""

ENCABEZADO = """
<div class="main-header">
  <h1>🖥️ CENTRO DE CÓMPUTO GEO-ANALÍTICO</h1>
  <p><span class="dot-live"></span>PROCESAMIENTO CONTINUO · HOJAS DE CÁLCULO VIVAS · DATOS 100 % SINTÉTICOS</p>
</div>
"""


# ============================================================
# 3.5 SALA DE CÓMPUTO (FONDO)
# ============================================================

def sala_svg():
    """Dibuja la sala de cómputo: ventanas con atardecer, skyline con
    ventanitas que parpadean, escritorio con persona y piso con rejilla."""
    rng = random.Random(42)
    edificios, ventanitas = [], []
    x = 70
    while x < 928:
        if 470 < x < 548:            # respeta el mullión entre ventanas
            x = 548
            continue
        w = rng.randint(34, 72)
        h = rng.randint(80, 300)
        if x + w > 472:
            w = 472 - x              # no invadir el mullión
        if x + w > 930:
            w = 930 - x
        if w < 14:
            x += 20
            continue
        edificios.append(f'<rect x="{x}" y="{492 - h}" width="{w}" height="{h}" fill="#0b1024"/>')
        wx = x + 7
        while wx < x + w - 8:
            wy = 492 - h + 10
            while wy < 478:
                if rng.random() < .45:
                    ventanitas.append(
                        f'<rect x="{wx}" y="{wy}" width="5" height="8" fill="#ffd97d" '
                        f'class="bwin" style="animation-delay:{rng.uniform(0, 4.5):.1f}s"/>')
                wy += 18
            wx += 14
        x += w + rng.randint(8, 22)

    rejilla = []
    for gx in range(0, 1441, 120):
        rejilla.append(
            f'<line x1="{gx}" y1="810" x2="{720 + (gx - 720) * 0.12:.0f}" y2="566" '
            f'stroke="#38bdf8" stroke-opacity=".08"/>')
    for gy in [572, 586, 604, 628, 658, 695, 740, 792]:
        rejilla.append(f'<line x1="0" y1="{gy}" x2="1440" y2="{gy}" stroke="#38bdf8" stroke-opacity=".06"/>')

    ed = "".join(edificios)
    vt = "".join(ventanitas)
    rj = "".join(rejilla)
    return f'''
<div class="fondo-sala">
<svg viewBox="0 0 1440 810" preserveAspectRatio="xMidYMax slice" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#131c40"/>
      <stop offset=".45" stop-color="#5b3a78"/>
      <stop offset=".78" stop-color="#c96a52"/>
      <stop offset="1" stop-color="#f2a65e"/>
    </linearGradient>
    <radialGradient id="sol" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="#ffd9a0" stop-opacity=".9"/>
      <stop offset="1" stop-color="#ffd9a0" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="piso" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0a1222"/>
      <stop offset="1" stop-color="#04070e"/>
    </linearGradient>
  </defs>

  <rect width="1440" height="810" fill="#04070e"/>

  <!-- ventanas con atardecer -->
  <rect x="58" y="46" width="420" height="482" fill="url(#cielo)"/>
  <rect x="510" y="46" width="420" height="482" fill="url(#cielo)" opacity=".97"/>
  <circle cx="370" cy="440" r="95" fill="url(#sol)"/>
  <circle cx="370" cy="440" r="24" fill="#ffe9c4" opacity=".92"/>
  {ed}{vt}

  <!-- marcos de las ventanas -->
  <g fill="#0d1420">
    <rect x="46" y="34" width="896" height="12"/>
    <rect x="46" y="528" width="896" height="12"/>
    <rect x="46" y="34" width="12" height="506"/>
    <rect x="930" y="34" width="12" height="506"/>
    <rect x="478" y="46" width="32" height="482"/>
    <rect x="58" y="272" width="420" height="8"/>
    <rect x="510" y="272" width="420" height="8"/>
  </g>

  <!-- interior y piso -->
  <rect y="540" width="1440" height="270" fill="url(#piso)"/>
  {rj}

  <!-- escritorio con persona (silueta desde atrás) -->
  <ellipse cx="1060" cy="650" rx="330" ry="150" fill="#0d1426" opacity=".55"/>
  <rect x="920" y="608" width="280" height="14" rx="7" fill="#070b15"/>
  <rect x="944" y="622" width="12" height="118" fill="#070b15"/>
  <rect x="1164" y="622" width="12" height="118" fill="#070b15"/>
  <rect x="990" y="512" width="104" height="64" rx="6" fill="#070b15"/>
  <rect x="997" y="519" width="90" height="50" rx="3" fill="#7dd3fc" opacity=".22"/>
  <rect x="1034" y="576" width="16" height="32" fill="#070b15"/>
  <circle cx="1042" cy="482" r="29" fill="#05080f"/>
  <path d="M986,610 Q1042,510 1098,610 Z" fill="#05080f"/>

  <!-- reflejos de los hologramas en el piso -->
  <ellipse cx="400" cy="720" rx="280" ry="42" fill="#38bdf8" opacity=".07"/>
  <ellipse cx="1040" cy="720" rx="280" ry="42" fill="#fbbf24" opacity=".07"/>
</svg>
</div>'''


def fondo_sala():
    """Devuelve el HTML del fondo de la sala de cómputo.
    Si existe una imagen propia (sala.jpg / sala.jpeg / sala.png) junto a
    app.py, se usa esa fotografía como fondo; si no, se dibuja la sala con SVG."""
    for nombre in ("sala.jpg", "sala.jpeg", "sala.png"):
        if os.path.exists(nombre):
            with open(nombre, "rb") as fh:
                datos = base64.b64encode(fh.read()).decode()
            mime = "image/png" if nombre.endswith("png") else "image/jpeg"
            return (f'<div class="fondo-sala">'
                    f'<img src="data:{mime};base64,{datos}" alt="Sala de cómputo"/></div>')
    return sala_svg()


# ============================================================
# 4. MAPAS HOLOGRÁFICOS (SVG con animación CSS continua)
# ============================================================

def _svg_map(uid, puntos, c1, c2, titulo, pos_titulo, nodos_pts, capital, etiqueta_cap, alto):
    clip = f'<clipPath id="clip{uid}"><polygon points="{puntos}"/></clipPath>'
    rejilla_h = "".join(
        f'<line x1="0" y1="{y}" x2="400" y2="{y}" stroke="{c1}" stroke-opacity=".10"/>'
        for y in range(0, alto + 1, 24))
    rejilla_v = "".join(
        f'<line x1="{x}" y1="0" x2="{x}" y2="{alto}" stroke="{c1}" stroke-opacity=".10"/>'
        for x in range(0, 401, 24))
    nodos = "".join(
        f'<circle cx="{x}" cy="{y}" r="2.3" fill="{c1}" class="nodo" style="animation-delay:{(i * 0.37) % 2.5:.2f}s"/>'
        for i, (x, y) in enumerate(nodos_pts))
    cx, cy = capital
    anillos = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="9" fill="none" stroke="{c1}" stroke-width="1.4" class="anillo" style="animation-delay:{i * 0.7:.2f}s"/>'
        for i in range(3))
    esquinas = f"""
    <g fill="none" stroke="{c1}" stroke-width="2" opacity=".75">
      <path d="M8,28 L8,8 L28,8"/><path d="M372,8 L392,8 L392,28"/>
      <path d="M392,{alto - 28} L392,{alto - 8} L372,{alto - 8}"/>
      <path d="M28,{alto - 8} L8,{alto - 8} L8,{alto - 28}"/>
    </g>"""
    return f"""
<div class="marco-mapa">
  <svg viewBox="0 0 400 {alto}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      {clip}
      <linearGradient id="fill{uid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{c1}" stop-opacity=".30"/>
        <stop offset="1" stop-color="{c2}" stop-opacity=".05"/>
      </linearGradient>
      <linearGradient id="scan{uid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{c1}" stop-opacity="0"/>
        <stop offset=".5" stop-color="{c1}" stop-opacity=".35"/>
        <stop offset="1" stop-color="{c1}" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <g clip-path="url(#clip{uid})">{rejilla_h}{rejilla_v}</g>
    <polygon points="{puntos}" fill="url(#fill{uid})" stroke="{c1}" stroke-width="2" stroke-linejoin="round"/>
    <polygon points="{puntos}" fill="none" stroke="#ffffff" stroke-opacity=".85" stroke-width=".6" stroke-dasharray="4 5"/>
    {nodos}
    {anillos}
    <circle cx="{cx}" cy="{cy}" r="3.4" fill="#ffffff"/>
    <text x="{pos_titulo[0]}" y="{pos_titulo[1]}" text-anchor="middle" class="tmapa">{titulo}</text>
    <text x="{cx}" y="{cy + 17}" text-anchor="middle" class="tcap">{etiqueta_cap}</text>
    <rect class="scanline" x="0" y="0" width="400" height="26" fill="url(#scan{uid})"/>
    {esquinas}
  </svg>
</div>"""


def mapa_antioquia():
    puntos = ("150,36 226,28 292,62 330,118 344,182 338,244 306,300 "
              "254,344 196,368 140,356 96,318 66,262 58,196 78,132 108,78")
    nodos = [(120, 110), (170, 92), (228, 122), (278, 152), (302, 212),
             (268, 262), (220, 300), (160, 322), (112, 272), (92, 200),
             (142, 182), (202, 202), (252, 224), (182, 252)]
    return _svg_map(
        uid="A", puntos=puntos, c1="#38bdf8", c2="#0e7490",
        titulo="ANTIOQUIA", pos_titulo=(200, 20),
        nodos_pts=nodos, capital=(170, 190), etiqueta_cap="MEDELLÍN", alto=400)


def mapa_colombia():
    puntos = ("262,18 300,44 344,62 372,96 384,150 396,224 344,318 306,414 "
              "258,428 208,422 158,398 100,368 60,318 44,252 62,180 92,124 "
              "128,96 158,108 172,132 186,108 212,76 232,48")
    nodos = [(150, 160), (222, 72), (196, 105), (238, 52), (255, 150),
             (200, 225), (105, 290), (240, 290), (258, 415), (75, 235),
             (150, 385), (150, 120), (330, 240), (135, 225), (120, 250),
             (160, 270), (175, 330)]
    return _svg_map(
        uid="C", puntos=puntos, c1="#fbbf24", c2="#b45309",
        titulo="REPÚBLICA DE COLOMBIA", pos_titulo=(130, 26),
        nodos_pts=nodos, capital=(200, 225), etiqueta_cap="BOGOTÁ D.C.", alto=440)


# ============================================================
# 5. HOJA EXCEL VIVA (HTML que se recalcula cada frame)
# ============================================================

def hoja_html(filas, idx_activo, espec, formulas_fn, letra, visibles,
              tarea, ciclo, elapsed, regs, cpu, ram, tema):
    n = len(filas)
    visibles = min(visibles, n)
    formula, resultado = formulas_fn(filas, idx_activo)[idx_activo % 5]
    addr = f"{letra}{idx_activo + 3}"
    pct = int(idx_activo / max(n - 1, 1) * 100)

    # Ventana de desplazamiento: la celda activa siempre visible
    inicio = max(0, min(idx_activo - visibles + 2, n - visibles))
    vis = filas[inicio:inicio + visibles]

    letras_th = "".join(f'<th class="letra">{c}</th>' for c in "ABCDE")
    hdr_th = "".join(f'<th class="hdr">{h}</th>' for h in espec["encabezados"])

    trs = []
    for j, fila in enumerate(vis):
        i = inicio + j
        activa = (i == idx_activo)
        cls_f = ' class="fila-activa"' if activa else ""
        tds = [f'<td class="numfila">{i + 3}</td>',
               f'<td class="nom">{fila["nombre"]}</td>']
        for letra_col, fmt in zip("BCDE", espec["formatos"]):
            val = fmt.format(**fila)
            cls_c = "num" + (" celda-activa" if (activa and letra_col == letra) else "")
            tds.append(f'<td class="{cls_c}">{val}</td>')
        trs.append(f'<tr{cls_f}>{"".join(tds)}</tr>')

    return f"""
<div class="hoja">
  <div class="fx-bar">
    <span class="addr">{addr}</span>
    <span class="fx">fx</span>
    <span class="formula">{formula}</span>
    <span class="resultado">→ {resultado}</span>
  </div>
  <table class="xl">
    <colgroup>
      <col style="width:8%"><col style="width:32%">
      <col style="width:15%"><col style="width:15%">
      <col style="width:15%"><col style="width:15%">
    </colgroup>
    <tr><th class="esq"></th>{letras_th}</tr>
    <tr><th class="esq"></th>{hdr_th}</tr>
    {''.join(trs)}
  </table>
  <div class="xl-estado">
    <span class="estado-ok">LISTO</span>
    <div class="prog"><div class="prog-bar" style="width:{pct}%"></div></div>
    <span class="pct">{pct}%</span>
    <span class="tarea">{tarea}<span class="cursor">▮</span></span>
    <span class="meta">Ciclo {ciclo} · Fila {idx_activo + 1}/{n}</span>
  </div>
  <div class="chips">
    <span class="chip">⏱ {elapsed}</span>
    <span class="chip">🔁 {regs:,} registros</span>
    <span class="chip">🧮 CPU {cpu:.0f}%</span>
    <span class="chip">💾 RAM {ram:.1f} GB</span>
  </div>
</div>"""


# ============================================================
# 6. APP PRINCIPAL — BUCLE DE ANIMACIÓN CONTINUA
# ============================================================

def main():
    st.set_page_config(
        page_title="Centro de Cómputo Geo-Analítico",
        page_icon="🖥️",
        layout="wide",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(fondo_sala(), unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Parámetros")
        delay = st.slider("Intervalo de refresco (s)", 0.05, 1.5, 0.35, 0.05)
        visibles = st.slider("Filas visibles por hoja", 4, 12, 7)
        st.caption(
            "ℹ️ Presiona **ESC** (o ⏹ del menú de Streamlit) para pausar "
            "la animación y ajustar estos parámetros.\n\n"
            "🖼️ Coloca tu imagen como `sala.jpg` junto a app.py para usarla "
            "como fondo de la sala (si no existe, la sala se dibuja sola).\n\n"
            "🎲 Todos los datos son sintéticos."
        )

    st.markdown(ENCABEZADO, unsafe_allow_html=True)

    col_izq, col_der = st.columns(2, gap="medium")

    # Hologramas flotantes (mapas): sus animaciones CSS corren sin parar
    col_izq.markdown(
        f"""<div class="holo-float">
        <div class="holo-flotante tema-cian">
        <div class="titulo-pantalla"><span class="dot-live"></span>EN VIVO · Hoja: ANTIOQUIA.xlsx
        <span class="der">MATRIZ {len(MUNICIPIOS)}×5</span></div>
        {mapa_antioquia()}</div></div>""",
        unsafe_allow_html=True,
    )
    col_der.markdown(
        f"""<div class="holo-float der">
        <div class="holo-flotante tema-oro">
        <div class="titulo-pantalla"><span class="dot-live"></span>EN VIVO · Hoja: COLOMBIA.xlsx
        <span class="der">MATRIZ {len(DEPARTAMENTOS)}×5</span></div>
        {mapa_colombia()}</div></div>""",
        unsafe_allow_html=True,
    )

    hoja_izq = col_izq.empty()
    hoja_der = col_der.empty()

    frame = 0
    ciclo = 1
    regs = 12_384
    cpu = 47.0
    t0 = time.time()

    while True:
        idx_ant = frame % len(FILAS_ANT)
        idx_col = frame % len(FILAS_COL)
        if frame > 0 and idx_ant == 0:
            ciclo += 1

        tick(FILAS_ANT, idx_ant)
        tick(FILAS_COL, idx_col)

        cpu = min(96.0, max(8.0, cpu + random.uniform(-3, 3)))
        ram = 1.1 + (frame % 41) * 0.02
        regs += random.randint(3, 11)

        t = time.time() - t0
        elapsed = f"{int(t // 60):02d}:{int(t % 60):02d}"
        tarea = TAREAS[(frame // 3) % len(TAREAS)]
        letra = "BCDE"[frame % 4]

        hoja_izq.markdown(
            hoja_html(FILAS_ANT, idx_ant, ESPEC_ANT, formulas_ant, letra,
                      visibles, tarea, ciclo, elapsed, regs, cpu, ram, "cian"),
            unsafe_allow_html=True,
        )
        hoja_der.markdown(
            hoja_html(FILAS_COL, idx_col, ESPEC_COL, formulas_col, letra,
                      visibles, tarea, ciclo, elapsed, regs, cpu, ram, "oro"),
            unsafe_allow_html=True,
        )

        time.sleep(delay)
        frame += 1


if __name__ == "__main__":
    main()

