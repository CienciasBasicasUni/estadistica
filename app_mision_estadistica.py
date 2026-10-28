import io
import json
import pathlib
import random
from html import escape as esc

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Misión Estadística", page_icon="🏆", layout="wide")

RUTA = pathlib.Path("estado_mision.json")
COLORES = ["#ff5d8f", "#2ee6d6", "#ffd23f", "#8dff6a", "#b794ff", "#ff9a3c", "#4dabff", "#ff7ad9", "#c7f464", "#f4a261"]
EMOJIS = ["🦊", "🐯", "🦉", "🐬", "🦄", "🐲", "🦅", "🐺", "🐼", "🦁"]

# Comodines: clave -> (emoji, nombre, efecto)
COMODINES = {
    "pista": ("💡", "Pista", "El docente da una pista, pero la ronda pierde 1 punto."),
    "doble": ("✖️", "Doble", "Duplica los puntos de la ronda."),
    "segunda": ("🔁", "Segunda oportunidad", "Si fallan, pueden reintentar sin penalización."),
    "pasar": ("⏭️", "Pasar", "La ronda vale 5 puntos sin responder."),
}

INSIGNIAS = {
    "🔥 Racha": "3 rondas seguidas con 70 % o más del puntaje.",
    "💯 Perfecta": "Puntaje máximo en una ronda.",
    "🚀 Remontada": "Estuvo en último lugar y llegó al podio (con 4 equipos o más).",
    "⚡ Rayo": "Mayor bono de velocidad en la ronda relámpago.",
    "🎲 Audaz": "Ganó una apuesta de 3 puntos o más.",
}


def R(icono, nombre, tema, ejercicio, respuesta, tipo="normal", mx=10.0, reb=2.0, seg=120):
    return {"icono": icono, "nombre": nombre, "tema": tema, "ejercicio": ejercicio,
            "respuesta_docente": respuesta, "tipo": tipo, "max": mx, "rebote": reb, "seg": seg}


RONDAS = [
    R("🕵️", "Detectives de la probabilidad", "Experimento aleatorio, espacio muestral, eventos y probabilidad",
      "Se lanza una moneda dos veces. Identifiquen el experimento, el espacio muestral, la probabilidad de obtener exactamente una cara y la probabilidad de obtener dos sellos.",
      "Espacio muestral: {CC, CS, SC, SS} (C=cara, S=sello). P(exactamente una cara)=2/4=0,5. P(dos sellos)=1/4=0,25."),
    R("🔬", "Equipo investigador", "Técnicas de muestreo",
      "Una universidad tiene 1.000 estudiantes: 500 de Ingeniería, 300 de Administración y 200 de Psicología. Se desea seleccionar una muestra estratificada proporcional de 100 estudiantes. ¿Cuántos se seleccionan de cada programa y por qué?",
      "Ingeniería: 50; Administración: 30; Psicología: 20. Se conserva la proporción de cada estrato en la población."),
    R("⚔️", "Batalla de los eventos", "Eventos mutuamente excluyentes e independientes; suma y producto",
      "La probabilidad de aprobar Estadística es 0,8 y la de aprobar Física es 0,7. Supongan que los eventos son independientes. ¿Cuál es la probabilidad de aprobar ambas asignaturas y cuál es la probabilidad de no aprobar ninguna?",
      "P(ambas)=0,8×0,7=0,56. P(no aprobar ninguna)=(0,2)(0,3)=0,06."),
    R("🔔", "¿Qué distribución utilizarías?", "Binomial, Poisson, normal, exponencial y distribuciones muestrales",
      "Relacionen cada situación con una distribución:\n(1) número de respuestas correctas al adivinar 6 preguntas de verdadero/falso;\n(2) cantidad de llamadas por hora;\n(3) estaturas aproximadamente acampanadas;\n(4) tiempo entre llamadas.",
      "(1) Binomial; (2) Poisson; (3) Normal; (4) Exponencial. La distribución de las medias de muestras es una distribución muestral."),
    R("📏", "Tamaño de la muestra", "Tamaño de muestra para proporciones y medias",
      "Para estimar una proporción con 95 % de confianza, margen de error 4 % y sin una proporción previa, utilicen Z=1,96 y p=0,5. ¿Cuál es el tamaño de muestra mínimo? Redondeen siempre hacia arriba.",
      "n=Z²p(1-p)/E²=(1,96²×0,5×0,5)/(0,04²)=600,25. Se redondea hacia arriba: n=601."),
    R("⚖️", "Tribunal estadístico", "Sesgos, errores de muestreo y ética",
      "Un investigador quiere conocer la satisfacción de todos los estudiantes, pero encuesta únicamente a quienes encuentra en la biblioteca. ¿Qué tipo de muestreo utiliza? ¿Qué sesgo puede presentarse y cómo mejoraría el diseño?",
      "Muestreo por conveniencia. Puede haber sesgo de selección y falta de representatividad. Se puede construir un marco muestral y seleccionar aleatoriamente, eventualmente estratificando por programa o semestre."),
    # ---- nuevas rondas
    R("📐", "Intervalos de confianza", "Estimación por intervalo para la media",
      "Una muestra de 36 estudiantes tiene un tiempo medio de estudio semanal de 50 horas. Se sabe que la desviación estándar poblacional es 12 horas. Construyan un intervalo de confianza del 95 % para la media poblacional (Z=1,96) e interpreten el resultado.",
      "Error estándar = 12/√36 = 2. Margen = 1,96×2 = 3,92. IC = (46,08; 53,92). Con 95 % de confianza, la media poblacional está entre 46,08 y 53,92 horas semanales."),
    R("📈", "Teorema del límite central", "Distribución muestral de la media",
      "El peso de un producto tiene media 100 g y desviación estándar 15 g. Se toma una muestra aleatoria de 36 productos. ¿Cuál es el error estándar de la media muestral y cuál es la probabilidad de que la media de la muestra supere 103 g?",
      "Error estándar = 15/√36 = 2,5. Z=(103−100)/2,5=1,2. P(X̄>103)=1−0,8849=0,1151 (≈11,5 %). Por el TLC, la media muestral es aproximadamente normal."),
    R("🧪", "Prueba de hipótesis", "Prueba Z para una media",
      "Una empresa afirma que el tiempo medio de entrega es 50 minutos. Una muestra de 25 pedidos arroja una media de 53 minutos. Supongan σ=10 y α=0,05 (prueba bilateral, Z crítico=±1,96). Planteen H0 y H1, calculen el estadístico Z y tomen una decisión.",
      "H0: μ=50; H1: μ≠50. Z=(53−50)/(10/√25)=3/2=1,5. Como |1,5|<1,96 no se rechaza H0: no hay evidencia suficiente de que la media sea distinta de 50 minutos."),
    R("🚦", "Errores tipo I y tipo II", "Nivel de significancia y errores de decisión",
      "Un laboratorio prueba un medicamento con H0: el medicamento no tiene efecto. Expliquen con palabras qué significa cometer un error tipo I y un error tipo II en este caso, y qué probabilidad representa α.",
      "Error tipo I: concluir que el medicamento sí tiene efecto cuando no lo tiene (rechazar una H0 verdadera); su probabilidad es α. Error tipo II: concluir que no tiene efecto cuando sí lo tiene (no rechazar una H0 falsa); su probabilidad es β."),
    R("🎰", "Binomial y Poisson", "Cálculo de probabilidades discretas",
      "Respondan: (a) si se adivinan 6 preguntas de verdadero/falso, ¿cuál es la probabilidad de acertar exactamente 4? (b) Un call center recibe en promedio 3 llamadas por hora; ¿cuál es la probabilidad de recibir exactamente 2 en una hora?",
      "(a) Binomial n=6, p=0,5: P(X=4)=C(6,4)(0,5)^6=15/64≈0,2344. (b) Poisson λ=3: P(X=2)=e^(−3)·3²/2!≈0,2240."),
    R("🌐", "La campana de Gauss", "Distribución normal y tabla Z",
      "Las estaturas de un grupo se distribuyen normalmente con media 170 cm y desviación estándar 10 cm. ¿Cuál es la probabilidad de que una persona mida entre 160 y 180 cm? ¿Y de que mida más de 190 cm?",
      "Entre 160 y 180: Z de −1 a 1 → 0,8413−0,1587=0,6826 (≈68,3 %). Más de 190: Z=2 → 1−0,9772=0,0228 (≈2,3 %)."),
    R("➕", "La regla de la suma", "Suma de probabilidades e independencia",
      "Para dos eventos A y B se sabe que P(A)=0,5, P(B)=0,4 y P(A∩B)=0,2. Calculen P(A∪B) y determinen si A y B son independientes.",
      "P(A∪B)=0,5+0,4−0,2=0,7. Como P(A)·P(B)=0,2=P(A∩B), los eventos A y B son independientes."),
    R("🧮", "Muestreo sistemático", "Marco muestral e intervalo de selección",
      "Una facultad tiene 1.200 estudiantes en una lista numerada y se quiere una muestra sistemática de 60. Calculen el intervalo de selección k y, si el arranque aleatorio es 7, escriban los tres primeros elegidos.",
      "k=N/n=1.200/60=20. Con arranque 7: 7, 27 y 47 (se suma 20 cada vez)."),
    R("⚡", "Ronda relámpago", "Verdadero o falso: conceptos clave",
      "Respondan verdadero (V) o falso (F). Un punto por acierto y bono al equipo más rápido:\n1. La media muestral siempre es igual a la media poblacional.\n2. Al aumentar el tamaño de la muestra, el error estándar de la media disminuye.\n3. Dos eventos mutuamente excluyentes con probabilidad positiva no pueden ser independientes.\n4. Si el valor p es menor que α, no se rechaza H0.\n5. La distribución de Poisson cuenta los éxitos en n ensayos de Bernoulli independientes.",
      "1 F (varía de muestra en muestra). 2 V (σ/√n). 3 V (P(A∩B)=0 ≠ P(A)P(B)). 4 F (se rechaza H0). 5 F (eso describe la binomial; Poisson cuenta eventos en un intervalo). Bono de velocidad (0–2) para el equipo que responda primero y bien.",
      tipo="relampago", mx=5.0, reb=2.0, seg=60),
    R("👑", "Reto final de Bayes", "Teorema de Bayes y probabilidad condicional",
      "Una máquina A produce el 60 % de los productos y tiene 2 % de defectos. La máquina B produce el 40 % y tiene 5 % de defectos. Si un producto es defectuoso, ¿cuál es la probabilidad de que provenga de B?",
      "P(B | defectuoso) = (0,40 × 0,05) / [(0,60 × 0,02) + (0,40 × 0,05)] = 0,625 = 62,5 %.",
      tipo="final", mx=5.0, reb=0.0, seg=180),
]

CLAVES = ["configurado", "equipos", "rondas", "puntajes", "rebotes", "comodines", "apuestas", "ronda_actual"]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700;800&family=Poppins:wght@400;500;600&display=swap');
html, body, .stApp { font-family: 'Poppins', sans-serif; }
.stApp {
  background:
    radial-gradient(900px 500px at 8% -8%, #4b2a9a 0%, transparent 60%),
    radial-gradient(800px 500px at 100% 0%, #0f5a8c 0%, transparent 55%),
    #0b1030;
  color: #eef1ff;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #0f1538; border-right: 1px solid rgba(255,255,255,.10); }
.stMarkdown, .stMarkdown p, [data-testid="stWidgetLabel"] p, label { color: #eef1ff; }
h1, h2, h3 { font-family: 'Baloo 2', cursive; }
button[data-baseweb="tab"] { font-family: 'Baloo 2', cursive; font-size: 1.2rem; font-weight: 700; }
.stButton > button, [data-testid="stFormSubmitButton"] button, .stDownloadButton button {
  border-radius: 14px; font-weight: 700; border: 0;
}
button[kind^="primary"] { background: linear-gradient(135deg, #ffd23f, #ff9a3c); color: #2b1a00; }
[data-testid="stForm"] {
  background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.14); border-radius: 22px;
}
.hero { text-align: center; padding: 18px 0 6px; }
.hero h1 {
  font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 4.2rem; line-height: 1; margin: 0;
  background: linear-gradient(90deg, #ffd23f, #ff7ad9 50%, #2ee6d6);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { margin: 6px 0 0; font-size: 1.15rem; color: #c9d1ff; }
.teams { display: flex; gap: 14px; flex-wrap: wrap; margin: 14px 0 22px; }
.team {
  flex: 1 1 190px; position: relative; text-align: center; padding: 14px 16px 16px;
  background: linear-gradient(160deg, rgba(255,255,255,.12), rgba(255,255,255,.03));
  border: 2px solid var(--c); border-radius: 22px; box-shadow: 0 0 24px -8px var(--c);
}
.team .medal { position: absolute; top: 8px; right: 12px; font-size: 1.4rem; }
.team .emo { font-size: 2.3rem; line-height: 1.1; }
.team .tn { font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 1.2rem; }
.team .tp { font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 2.6rem; line-height: 1; color: var(--c); }
.team .tp small { font-size: .95rem; color: #cfd6ff; font-weight: 500; }
.bar { height: 8px; margin-top: 10px; background: rgba(255,255,255,.13); border-radius: 99px; overflow: hidden; }
.bar span { display: block; height: 100%; background: var(--c); border-radius: 99px; }
.coms { margin-top: 8px; font-size: 1.15rem; letter-spacing: 4px; }
.coms .off { opacity: .22; filter: grayscale(1); }
.badge {
  display: inline-block; margin: 4px 3px 0; padding: 2px 10px; border-radius: 99px;
  background: rgba(255,255,255,.16); font-size: .82rem; font-weight: 600;
}
.steps { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin: 10px 0 16px; }
.step {
  width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 1.2rem;
  background: rgba(255,255,255,.08); border: 2px solid rgba(255,255,255,.22);
}
.step.done { background: #26d98f; color: #03281a; border-color: #26d98f; }
.step.now {
  background: linear-gradient(135deg, #ffd23f, #ff9a3c); color: #2b1a00; border-color: #fff;
  transform: scale(1.2); box-shadow: 0 0 26px #ffd23faa; animation: latido 1.4s ease-in-out infinite alternate;
}
@keyframes latido { to { box-shadow: 0 0 40px #ffd23f; } }
@media (prefers-reduced-motion: reduce) { .step.now { animation: none; } }
.reto {
  margin: 10px 0 18px; padding: 34px 42px; border-radius: 32px;
  background: linear-gradient(145deg, rgba(124,92,255,.40), rgba(46,230,214,.16));
  border: 2px solid rgba(255,255,255,.28); box-shadow: 0 24px 60px -24px #000;
}
.reto.rel { background: linear-gradient(145deg, rgba(255,154,60,.42), rgba(255,93,143,.22)); }
.reto.fin { background: linear-gradient(145deg, rgba(255,210,63,.40), rgba(255,122,217,.24)); }
.ribbon {
  display: inline-block; padding: 6px 20px; border-radius: 99px; font-family: 'Baloo 2', cursive;
  font-weight: 800; font-size: 1.15rem; color: #fff; background: linear-gradient(90deg, #ff5d8f, #ff9a3c);
}
.rtitle { font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 3.2rem; line-height: 1.1; margin: 14px 0 8px; }
.chip { display: inline-block; margin-bottom: 18px; padding: 6px 16px; border-radius: 99px; background: rgba(0,0,0,.35); font-size: 1.05rem; }
.enun {
  font-weight: 600; line-height: 1.45; padding: 24px 30px; border-radius: 18px;
  background: rgba(5,10,35,.50); border-left: 9px solid #ffd23f;
}
.turno {
  text-align: center; padding: 14px; border-radius: 22px; font-size: 1.1rem;
  background: linear-gradient(135deg, rgba(255,93,143,.35), rgba(255,154,60,.25)); border: 2px solid #ff9a3c;
}
.turno b { font-family: 'Baloo 2', cursive; font-size: 2rem; display: block; line-height: 1.1; }
.panel-title { font-family: 'Baloo 2', cursive; font-size: 1.7rem; font-weight: 800; margin: 6px 0 2px; }
.equipo-tag { font-weight: 700; padding: 3px 12px; border-radius: 99px; background: var(--c); color: #12122b; display: inline-block; margin-bottom: 4px; }
.podium { display: flex; align-items: flex-end; justify-content: center; gap: 18px; margin: 26px 0 10px; }
.pod { width: 210px; text-align: center; }
.pod .emo { font-size: 3rem; }
.pod .pn { font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 1.4rem; }
.pod .pp { font-size: 1.1rem; margin-bottom: 6px; color: #dfe4ff; }
.pod .blk { border-radius: 20px 20px 0 0; display: flex; justify-content: center; padding-top: 12px; font-size: 3.2rem; }
.campeon {
  text-align: center; margin: 12px 0; padding: 22px; border-radius: 26px;
  font-family: 'Baloo 2', cursive; font-weight: 800; font-size: 2.4rem;
  background: linear-gradient(135deg, rgba(255,210,63,.35), rgba(255,122,217,.25)); border: 2px solid #ffd23f;
}
"""

TIMER = """
<style>
body{margin:0;font-family:'Segoe UI',sans-serif;color:#fff;background:transparent}
.w{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:12px 22px;border-radius:22px;
   background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.22)}
#t{font-size:68px;font-weight:800;min-width:200px;letter-spacing:3px;font-variant-numeric:tabular-nums}
#t.low{color:#ff5d8f}
button{border:0;border-radius:12px;padding:10px 16px;font-weight:700;font-size:15px;cursor:pointer;background:#2ee6d6;color:#06122b}
button.g{background:rgba(255,255,255,.16);color:#fff}
</style>
<div class="w"><div id="t">02:00</div><div>
<button id="b" onclick="go()">▶ Iniciar</button>
<button class="g" onclick="set(30)">30 s</button>
<button class="g" onclick="set(60)">1 min</button>
<button class="g" onclick="set(120)">2 min</button>
<button class="g" onclick="set(180)">3 min</button></div></div>
<script>
let s=__S__,iv=null;const t=document.getElementById('t'),b=document.getElementById('b');
function draw(){t.textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');t.className=(s<=10&&s>0)?'low':''}
function set(n){clearInterval(iv);iv=null;s=n;b.textContent='▶ Iniciar';draw()}
function beep(){try{const c=new AudioContext(),o=c.createOscillator();o.connect(c.destination);o.frequency.value=880;o.start();setTimeout(()=>o.stop(),800)}catch(e){}}
function go(){if(iv){clearInterval(iv);iv=null;b.textContent='▶ Seguir';return}
 if(s<=0)return;b.textContent='⏸ Pausa';
 iv=setInterval(()=>{s--;draw();if(s<=0){clearInterval(iv);iv=null;b.textContent='▶ Iniciar';beep()}},1000)}
draw();
</script>
"""

SFX = """
<script>
const P={ok:[[660,.12],[880,.2]],fail:[[330,.18],[247,.18],[196,.35]],
 fan:[[523,.14],[659,.14],[784,.14],[1047,.5]],drum:[[196,.07],[196,.07],[262,.07],[330,.18]],
 card:[[988,.07],[1319,.16]]};
try{const c=new AudioContext();let t=c.currentTime;
(P['__N__']||[]).forEach(([f,d])=>{const o=c.createOscillator(),g=c.createGain();o.type='triangle';o.frequency.value=f;
o.connect(g);g.connect(c.destination);g.gain.setValueAtTime(.25,t);g.gain.exponentialRampToValueAtTime(.001,t+d);
o.start(t);o.stop(t+d);t+=d})}catch(e){}
</script><!--__K__-->
"""


def h(contenido):
    st.markdown(contenido, unsafe_allow_html=True)


# ------------------------------------------------------------------ estado
def guardar_estado():
    try:
        RUTA.write_text(json.dumps({k: st.session_state[k] for k in CLAVES}, ensure_ascii=False))
    except Exception:
        pass


def cargar_estado():
    try:
        if RUTA.exists():
            return json.loads(RUTA.read_text())
    except Exception:
        pass
    return {}


def init_state():
    primera = "cargado" not in st.session_state
    st.session_state["cargado"] = True
    guardado = cargar_estado() if primera else {}
    base = {
        "configurado": False, "equipos": [], "rondas": [dict(r) for r in RONDAS],
        "puntajes": {}, "rebotes": {}, "comodines": {}, "apuestas": {},
        "ronda_actual": 0, "turno": None, "revelar": False, "sfx": None, "sfx_k": 0,
    }
    for k, v in base.items():
        if k not in st.session_state:
            st.session_state[k] = guardado.get(k, v)
    if len(st.session_state.rondas) != len(RONDAS):
        st.session_state.rondas = [dict(r) for r in RONDAS]
    st.session_state.setdefault("ronda_sel", min(st.session_state.ronda_actual, len(RONDAS) - 1))


init_state()
n = len(st.session_state.rondas)


def inicializar_puntajes():
    for e in st.session_state.equipos:
        st.session_state.puntajes.setdefault(e, {})
        st.session_state.rebotes.setdefault(e, {})
        st.session_state.comodines.setdefault(e, {})
        st.session_state.apuestas.setdefault(e, {})
        for i in range(n):
            st.session_state.puntajes[e].setdefault(str(i), 0.0)
            st.session_state.rebotes[e].setdefault(str(i), 0.0)


def tipo(i):
    return st.session_state.rondas[i]["tipo"]


def maximo(i):
    return float(st.session_state.rondas[i]["max"])


def num(i):
    return sum(1 for j in range(i + 1) if tipo(j) == "normal")


def pts(e, i):
    return float(st.session_state.puntajes[e].get(str(i), 0))


def reb(e, i):
    return float(st.session_state.rebotes[e].get(str(i), 0))


def uso(e, i):
    return st.session_state.comodines.get(e, {}).get(str(i))


def efectivo(e, i):
    base, c = pts(e, i), uso(e, i)
    if c == "doble":
        base *= 2
    elif c == "pista":
        base = max(0.0, base - 1)
    elif c == "pasar":
        base = min(5.0, maximo(i))
    return base


def delta_ap(e, i):
    a = st.session_state.apuestas.get(e, {}).get(str(i))
    if not a:
        return 0.0
    return float(a["m"]) if a["g"] else -float(a["m"])


def total(e):
    return (sum(efectivo(e, i) for i in range(n))
            + sum(reb(e, i) for i in range(n))
            + sum(delta_ap(e, i) for i in range(n)))


def criterio(e):
    """Total; desempate: puntaje del reto final y luego bonos/rebotes."""
    return (total(e), efectivo(e, n - 1), sum(reb(e, i) for i in range(n)))


def clasificacion():
    orden = sorted(st.session_state.equipos, key=criterio, reverse=True)
    res, pos = [], 0
    for k, e in enumerate(orden):
        if k == 0 or criterio(e) != criterio(orden[k - 1]):
            pos = k + 1
        res.append((pos, e))
    return res


def jugadas():
    eq = st.session_state.equipos
    return [i for i in range(n) if any(pts(e, i) > 0 or reb(e, i) > 0 or uso(e, i) for e in eq)]


def insignias():
    eq = st.session_state.equipos
    res = {e: [] for e in eq}
    jug = jugadas()
    pos = {e: p for p, e in clasificacion()}
    for e in eq:
        racha = mejor = 0
        for i in jug:
            if efectivo(e, i) >= 0.7 * maximo(i):
                racha += 1
                mejor = max(mejor, racha)
            else:
                racha = 0
        if mejor >= 3:
            res[e].append("🔥 Racha")
        if any(pts(e, i) >= maximo(i) for i in jug):
            res[e].append("💯 Perfecta")
    rel = [i for i in range(n) if tipo(i) == "relampago"]
    if rel:
        vals = {e: reb(e, rel[0]) for e in eq}
        mx = max(vals.values())
        for e in eq:
            if mx > 0 and vals[e] == mx:
                res[e].append("⚡ Rayo")
    for e in eq:
        if any(a["g"] and a["m"] >= 3 for a in st.session_state.apuestas.get(e, {}).values()):
            res[e].append("🎲 Audaz")
    if len(eq) >= 4 and len(jug) >= 3:
        acum, estuvo_ultimo = {e: 0.0 for e in eq}, set()
        for i in jug:
            for e in eq:
                acum[e] += efectivo(e, i) + reb(e, i) + delta_ap(e, i)
            if len(set(acum.values())) > 1:
                mn = min(acum.values())
                estuvo_ultimo |= {e for e in eq if acum[e] == mn}
        for e in estuvo_ultimo:
            if pos[e] <= 3:
                res[e].append("🚀 Remontada")
    return res


def etiqueta(k):
    r = st.session_state.rondas[k]
    cab = {"normal": "Ronda %d" % num(k), "relampago": "Relámpago", "final": "Reto final"}[r["tipo"]]
    return r["icono"] + "  " + cab + ": " + r["nombre"]


def colname(i):
    return {"normal": "R%d" % num(i), "relampago": "Relámpago", "final": "Final"}[tipo(i)]


def fmt_com(c):
    return "— Ninguno —" if c == "ninguno" else "%s %s" % (COMODINES[c][0], COMODINES[c][1])


def tabla():
    filas = []
    for pos, e in clasificacion():
        f = {"Pos": pos, "Equipo": e}
        for i in ACT:
            f[colname(i)] = efectivo(e, i)
        f["Rebotes"] = sum(reb(e, i) for i in range(n))
        f["Apuestas"] = sum(delta_ap(e, i) for i in range(n))
        f["Total"] = total(e)
        filas.append(f)
    return pd.DataFrame(filas)


def excel_bytes():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        tabla().to_excel(w, index=False, sheet_name="Resultados")
    return buf.getvalue()


# --------------------------------------------------------------- callbacks
def sonar(nombre):
    st.session_state.sfx = nombre
    st.session_state.sfx_k += 1


def ir(delta):
    act = ACT
    actual = st.session_state.ronda_sel
    pos = act.index(actual) if actual in act else 0
    st.session_state.ronda_sel = act[max(0, min(len(act) - 1, pos + delta))]


def guardar_ronda(i):
    ss = st.session_state
    r = ss.rondas[i]
    perdio = hubo_comodin = False
    for e in ss.equipos:
        ss.puntajes[e][str(i)] = ss["n_%d_%s" % (i, e)]
        if r["rebote"] > 0:
            ss.rebotes[e][str(i)] = ss["r_%d_%s" % (i, e)]
        c = ss["c_%d_%s" % (i, e)]
        if c == "ninguno":
            ss.comodines[e].pop(str(i), None)
        else:
            hubo_comodin = hubo_comodin or ss.comodines[e].get(str(i)) != c
            ss.comodines[e][str(i)] = c
        ss.apuestas[e].pop(str(i), None)
        m = min(float(ss["a_%d_%s" % (i, e)]), float(int(max(0.0, total(e)))))
        if m > 0:
            g = bool(ss["g_%d_%s" % (i, e)])
            ss.apuestas[e][str(i)] = {"m": m, "g": g}
            perdio = perdio or not g
    guardar_estado()
    sonar("fail" if perdio else ("card" if hubo_comodin else "ok"))
    st.toast("✅ Puntajes guardados")


def guardar_edicion(i):
    r = st.session_state.rondas[i]
    r["nombre"] = st.session_state["en_%d" % i]
    r["tema"] = st.session_state["et_%d" % i]
    r["ejercicio"] = st.session_state["ee_%d" % i]
    r["respuesta_docente"] = st.session_state["er_%d" % i]
    guardar_estado()
    st.toast("✅ Ronda actualizada")


def sortear():
    st.session_state.turno = random.choice(st.session_state.equipos)
    sonar("drum")


def revelar():
    st.session_state.revelar = True
    sonar("fan")
    st.balloons()


# ------------------------------------------------------------------- vista
h("<style>" + CSS + "</style>")
h('<div class="hero"><h1>🏆 Misión Estadística</h1><p>Estadística Inferencial: ¡cada ronda cuenta!</p></div>')

with st.sidebar:
    st.header("⚙️ Equipos")
    if not st.session_state.configurado:
        cantidad = st.number_input("Cantidad de equipos", min_value=2, max_value=10, value=4, step=1)
        nombres = [st.text_input("Equipo %d" % (i + 1), value="Equipo %d" % (i + 1), key="nombre_equipo_%d" % i)
                   for i in range(int(cantidad))]
        if st.button("🚀 Crear equipos y comenzar", type="primary"):
            nombres = [x.strip() or "Equipo %d" % (i + 1) for i, x in enumerate(nombres)]
            if len(set(nombres)) != len(nombres):
                st.error("Cada equipo debe tener un nombre diferente.")
            else:
                st.session_state.equipos = nombres
                st.session_state.configurado = True
                inicializar_puntajes()
                guardar_estado()
                st.rerun()
    else:
        st.success("%d equipos en juego" % len(st.session_state.equipos))

if not st.session_state.configurado:
    st.info("👈 Define los equipos en el panel izquierdo para iniciar la misión.")
    st.stop()

inicializar_puntajes()
equipos = st.session_state.equipos

with st.sidebar:
    st.header("🖥️ Pantalla")
    proyector = st.toggle("Modo proyector (oculta respuestas y calificación)", value=True)
    sonido = st.toggle("🔊 Efectos de sonido", value=True)
    tam = st.slider("Tamaño del enunciado (px)", 22, 72, 40)
    st.header("🧩 Rondas a jugar")
    sel = st.multiselect("Rondas", list(range(n)), default=list(range(n)), format_func=etiqueta,
                         key="activas_sel", label_visibility="collapsed")
    st.header("💾 Sesión")
    st.download_button("Descargar respaldo (JSON)",
                       data=json.dumps({k: st.session_state[k] for k in CLAVES}, ensure_ascii=False),
                       file_name="respaldo_mision.json", mime="application/json")
    if st.button("🔄 Reiniciar equipos y puntajes"):
        for k in ["configurado", "equipos", "puntajes", "rebotes", "comodines", "apuestas",
                  "ronda_actual", "ronda_sel", "turno", "revelar", "sfx"]:
            st.session_state.pop(k, None)
        RUTA.unlink(missing_ok=True)
        st.rerun()

ACT = sorted(sel) or list(range(n))
if st.session_state.ronda_sel not in ACT:
    st.session_state.ronda_sel = ACT[0]

# Marcador siempre visible
ins = insignias()
total_general = sum(total(e) for e in equipos)
tope = max(1.0, max(total(e) for e in equipos))
tarjetas = ""
for pos, e in clasificacion():
    k = equipos.index(e)
    medalla = "⭐" if total_general == 0 else {1: "🥇", 2: "🥈", 3: "🥉"}.get(pos, "#%d" % pos)
    usados = set(st.session_state.comodines[e].values())
    coms = "".join('<span class="%s" title="%s">%s</span>' % ("off" if c in usados else "", esc(v[1]), v[0])
                   for c, v in COMODINES.items())
    bad = "".join('<span class="badge">%s</span>' % b for b in ins[e])
    tarjetas += (
        '<div class="team" style="--c:%s"><div class="medal">%s</div><div class="emo">%s</div>'
        '<div class="tn">%s</div><div class="tp">%g<small> pts</small></div>'
        '<div class="bar"><span style="width:%d%%"></span></div>'
        '<div class="coms">%s</div><div>%s</div></div>'
        % (COLORES[k % len(COLORES)], medalla, EMOJIS[k % len(EMOJIS)], esc(e), total(e),
           max(0, int(100 * total(e) / tope)), coms, bad)
    )
h('<div class="teams">%s</div>' % tarjetas)

tabs = st.tabs(["🎮 Escenario", "📊 Marcador", "🏁 Podio final", "📜 Reglas", "✏️ Editor"])

# ---------------------------------------------------------------- Escenario
with tabs[0]:
    i = st.session_state.ronda_sel
    st.session_state.ronda_actual = i
    ronda = st.session_state.rondas[i]
    t_i = ronda["tipo"]
    jug = jugadas()
    normales = sum(1 for j in range(n) if tipo(j) == "normal")

    pasos = ""
    for k in ACT:
        clase = "now" if k == i else ("done" if k in jug else "")
        simbolo = {"relampago": "⚡", "final": "👑"}.get(tipo(k), num(k))
        pasos += '<div class="step %s">%s</div>' % (clase, simbolo)
    h('<div class="steps">%s</div>' % pasos)

    pos_act = ACT.index(i)
    c1, c2, c3 = st.columns([1, 5, 1])
    c1.button("◀ Anterior", on_click=ir, args=(-1,), disabled=pos_act == 0, key="prev")
    c2.selectbox("Ronda", ACT, format_func=etiqueta, key="ronda_sel", label_visibility="collapsed")
    c3.button("Siguiente ▶", on_click=ir, args=(1,), disabled=pos_act == len(ACT) - 1, key="next")

    cinta = {"normal": "Ronda %d de %d" % (num(i), normales),
             "relampago": "⚡ Ronda relámpago", "final": "👑 Reto final"}[t_i]
    clase_card = {"normal": "", "relampago": " rel", "final": " fin"}[t_i]
    h(
        '<div class="reto%s"><span class="ribbon">%s</span>'
        '<div class="rtitle">%s %s</div><div class="chip">📚 %s</div>'
        '<div class="enun" style="font-size:%dpx">%s</div></div>'
        % (clase_card, cinta, ronda["icono"], esc(ronda["nombre"]), esc(ronda["tema"]), tam,
           esc(ronda["ejercicio"]).replace("\n", "<br>"))
    )

    ct, cv = st.columns([2, 1])
    with ct:
        components.html(TIMER.replace("__S__", str(int(ronda["seg"]))), height=130)
    with cv:
        st.button("🎲 Sortear vocero", on_click=sortear, key="sorteo")
        if st.session_state.turno in equipos:
            h('<div class="turno">🎤 Responde<b>%s</b></div>' % esc(st.session_state.turno))

    if not proyector:
        st.divider()
        h('<div class="panel-title">🧑‍🏫 Panel del docente</div>')
        with st.expander("🔑 Respuesta orientativa"):
            st.warning(ronda["respuesta_docente"])
        tope_i = maximo(i)
        etq_reb = "Bono velocidad (0–%g)" if t_i == "relampago" else "Rebote (0–%g)"
        with st.form("form_%d" % i):
            cols = st.columns(min(4, len(equipos)))
            for k, e in enumerate(equipos):
                with cols[k % len(cols)]:
                    h('<span class="equipo-tag" style="--c:%s">%s %s</span>'
                      % (COLORES[k % len(COLORES)], EMOJIS[k % len(EMOJIS)], esc(e)))
                    st.number_input("Puntos (0–%g)" % tope_i, min_value=0.0, max_value=tope_i, step=0.5,
                                    value=pts(e, i), key="n_%d_%s" % (i, e))
                    if ronda["rebote"] > 0:
                        st.number_input(etq_reb % ronda["rebote"], min_value=0.0, max_value=float(ronda["rebote"]),
                                        step=0.5, value=reb(e, i), key="r_%d_%s" % (i, e))
                    otros = {c for r_, c in st.session_state.comodines[e].items() if r_ != str(i)}
                    ops = ["ninguno"] + [c for c in COMODINES if c not in otros]
                    st.selectbox("Comodín", ops, index=ops.index(uso(e, i) or "ninguno"),
                                 format_func=fmt_com, key="c_%d_%s" % (i, e))
                    ap = st.session_state.apuestas[e].get(str(i), {"m": 0.0, "g": False})
                    st.number_input("Apuesta (0–5)", min_value=0.0, max_value=5.0, step=1.0,
                                    value=float(ap["m"]), key="a_%d_%s" % (i, e))
                    st.checkbox("Ganó la apuesta", value=bool(ap["g"]), key="g_%d_%s" % (i, e))
            st.form_submit_button("💾 Guardar puntajes de la ronda", type="primary",
                                  on_click=guardar_ronda, args=(i,))

# ----------------------------------------------------------------- Marcador
with tabs[1]:
    df = tabla()
    st.dataframe(df, hide_index=True)
    cols_r = [colname(k) for k in ACT] + ["Rebotes"]
    st.markdown("#### Puntos acumulados por equipo")
    st.bar_chart(df.set_index("Equipo")[cols_r])
    st.markdown("#### Insignias ganadas")
    hay = False
    for e in equipos:
        if ins[e]:
            hay = True
            st.write("**%s**: %s" % (e, "  ".join(ins[e])))
    if not hay:
        st.caption("Aún no hay insignias. ¡Que empiece la competencia!")

# -------------------------------------------------------------------- Podio
with tabs[2]:
    if not st.session_state.revelar:
        h('<div class="campeon">🥁 ¿Quién ganó la misión?</div>')
        st.button("🎉 Revelar podio", on_click=revelar, type="primary", key="rev")
    else:
        cl = clasificacion()
        top = cl[:3]
        cfg = {1: ("#ffd23f", 250, "🥇"), 2: ("#d7dee6", 190, "🥈"), 3: ("#cd7f32", 140, "🥉")}
        orden = [top[1]] if len(top) > 1 else []
        orden += [top[0]] + ([top[2]] if len(top) > 2 else [])
        bloques = ""
        for pos, e in orden:
            color, alto, med = cfg[min(pos, 3)]
            k = equipos.index(e)
            bloques += (
                '<div class="pod"><div class="emo">%s</div><div class="pn">%s</div><div class="pp">%g pts</div>'
                '<div class="blk" style="height:%dpx;background:linear-gradient(180deg,%s,%s44)">%s</div></div>'
                % (EMOJIS[k % len(EMOJIS)], esc(e), total(e), alto, color, color, med)
            )
        ganadores = [e for p, e in cl if p == 1]
        h('<div class="podium">%s</div>' % bloques)
        if len(ganadores) == 1:
            h('<div class="campeon">🏆 ¡Campeón: %s!</div>' % esc(ganadores[0]))
        else:
            h('<div class="campeon">🤝 Empate: %s</div>' % esc(", ".join(ganadores)))
        resto = cl[3:]
        if resto:
            st.markdown("#### Resto de la clasificación")
            for pos, e in resto:
                st.write("**%d. %s** — %g puntos" % (pos, e, total(e)))
        c1, c2 = st.columns(2)
        c1.download_button("⬇️ Descargar resultados en Excel", data=excel_bytes(),
                           file_name="resultados_mision_estadistica.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if c2.button("🙈 Ocultar podio"):
            st.session_state.revelar = False
            st.rerun()

# ------------------------------------------------------------------- Reglas
with tabs[3]:
    st.markdown("### 📜 Reglas de la misión")
    st.markdown(
        "**Puntaje.** Cada ronda vale hasta 10 puntos, más un *rebote* de hasta 2 si otro equipo "
        "completa o corrige la respuesta. La ronda relámpago vale hasta 5 puntos (1 por acierto) más un "
        "*bono de velocidad* de hasta 2. El reto final vale hasta 5 puntos."
    )
    st.markdown("**🃏 Comodines.** Cada equipo tiene uno de cada tipo y solo puede usarlos una vez por partida, uno por ronda:")
    for c, (emo, nom, efecto) in COMODINES.items():
        st.markdown("- %s **%s**: %s" % (emo, nom, efecto))
    st.markdown(
        "**🎲 Apuestas.** Antes de responder, un equipo puede apostar hasta 5 puntos (sin superar los que "
        "tiene). Si acierta, suma lo apostado; si falla, lo pierde."
    )
    st.markdown("**🏅 Insignias.** Se otorgan automáticamente:")
    for nom, desc in INSIGNIAS.items():
        st.markdown("- %s: %s" % (nom, desc))
    st.markdown(
        "**⚖️ Desempate.** Gana el equipo con más puntos; si hay empate, el que tenga más puntos en el reto "
        "final y, después, más bonos y rebotes."
    )

# ------------------------------------------------------------------- Editor
with tabs[4]:
    st.write("Adapta nombre, tema, enunciado y respuesta de cada ronda.")
    for k, r in enumerate(st.session_state.rondas):
        with st.expander(etiqueta(k)):
            st.text_input("Nombre", value=r["nombre"], key="en_%d" % k)
            st.text_input("Tema", value=r["tema"], key="et_%d" % k)
            st.text_area("Enunciado para estudiantes", value=r["ejercicio"], height=140, key="ee_%d" % k)
            st.text_area("Respuesta orientativa (solo docente)", value=r["respuesta_docente"], height=100, key="er_%d" % k)
            st.button("💾 Guardar cambios", on_click=guardar_edicion, args=(k,), key="ge_%d" % k)

# Efecto de sonido pendiente
if st.session_state.sfx:
    if sonido:
        components.html(SFX.replace("__N__", st.session_state.sfx).replace("__K__", str(st.session_state.sfx_k)), height=0)
    st.session_state.sfx = None
