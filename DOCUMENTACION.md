# Documentación técnica del deck

Cómo está construido el taller por dentro: arquitectura, archivos, estado, comunicación entre ventanas y cómo extenderlo.
Para usarlo, ver [README.md](README.md).

## 1. Arquitectura general

El proyecto es una **página estática** sin build ni dependencias: HTML, CSS y JavaScript puro.

```
index.html  (cascarón del deck)
 ├── barra lateral: partes, temas, avance, botones
 ├── escenario: <iframe src="tema.html">   ← cada tema es una página independiente
 ├── ventana del proyector  index.html?view=audience      ┐
 ├── ventana del break      index.html?view=audience&brk=1 ┴─ sincronizadas por BroadcastChannel('taller-deck')
 └── localStorage: tallerApis.v3 (orden, avance)  ·  tallerApis.break (preferencias del break)

pm/pm.js + pm/pm.css   simulador de Postman (Parte 2)
ci/ci.js + ci/ci.css   pestañas, terminal animada y réplica de Jenkins (Parte 4)
servidor.py            servidor HTTP local sin caché
postman/generar.py     genera colecciones, environments y datos de práctica
jenkins/generar_repo.py genera el proyecto que se sube a GitHub y ejecuta Jenkins
```

Cada tema se puede abrir solo (por ejemplo `pm_cli.html`) o dentro del deck. Los temas no dependen de `index.html`.

## 2. `index.html`: el deck

### 2.1 Catálogo: `SECTIONS` y `SLIDES`

```js
const SECTIONS = [
  { id:'inicio', label:null },                       // sin portada
  { id:'p1', n:1, label:'Conceptos de APIs', subtitle:'…', color:'#59a9e6', cover:true },
  { id:'p2', n:2, …, planned:['Tema futuro', …] },   // planned: aparecen como "en preparación"
  { id:'reto', n:3, … }, { id:'ci', n:4, … }, { id:'perf', n:5, … },
  { id:'fin', label:null },
];
const SLIDES = [
  { id:'que-es-api', section:'p1', title:'¿Qué es una API?', subtitle:'…', src:'que_es_api.html' },  // iframe
  { id:'portada', section:'inicio', title:'Portada', html:'PORTADA' },                              // generada
];
```

- El **orden de `SECTIONS`** define el orden de las partes. `cover:true` genera una portada automática con la lista de temas (`htmlCover`).
- `html:'PORTADA'` y `html:'CIERRE'` se generan en `htmlPortada()` y `htmlCierre()`.
- El `id` de cada tema es su clave en el estado guardado: **no cambiarlo** una vez publicado, o se pierde el avance de ese tema.

### 2.2 Estado (`localStorage['tallerApis.v3']`)

```js
{ order:   ['portada','sobre-mi', …],   // orden elegido por el usuario (arrastrar)
  sec:     { 'vus':'perf', … },         // parte a la que pertenece cada tema
  hidden:  [ids], hiddenSec: [ids],     // temas y partes ocultos
  closed:  [ids de partes colapsadas],
  done:    [ids vistos],                // avance ✓
  current: 'id actual' }
```

`loadState()` mezcla lo guardado con el catálogo actual:
- Un tema **nuevo** se inserta después del tema que lo precede en `SLIDES`.
- Un tema o parte que ya no existe se descarta. Si su parte guardada no existe, vuelve a la parte por defecto (así se migró `p3/p4` → `reto/ci/perf`).
- `sequence()` calcula el orden real de presentación: partes en orden, portada de cada parte y temas visibles.

Funciones principales: `renderList()` (barra lateral y arrastrar y soltar), `renderStage()` (iframe o HTML generado), `refresh()` (redibuja y guarda), `go(±1)`, `toggleDone(id)`.

### 2.3 Proyección y vista del presentador

1. `openProjector()` usa la **Window Management API** (`getScreenDetails`) para listar pantallas. Si no está disponible, abre una ventana normal.
2. Abre `index.html?view=audience` en la pantalla elegida (`AUDIENCE = true`: solo contenido, sin barra).
3. La ventana original pasa a **vista del presentador**: tema actual, siguiente, cronómetro y próximos temas.

Mensajes por `BroadcastChannel('taller-deck')`:

| Mensaje | De → a | Qué hace |
|---|---|---|
| `{t:'ready'}` / `{t:'ping'}` | proyector → presentador | el proyector está vivo (ping cada 1,5 s) |
| `{t:'go', id, black}` | presentador → proyector | mostrar este tema |
| `{t:'nav', d:±1}` | proyector → presentador | avanzar o retroceder con el teclado del proyector |
| `{t:'black', on}` | ambos | pantalla negra (`B`) |
| `{t:'closed'}` / `{t:'end'}` | ambos | cerrar el proyector cancela la proyección |
| `{t:'break', brk}` | presentador → ventanas | iniciar, actualizar o terminar el break |

> La Window Management API y BroadcastChannel requieren `http://` (no `file://`) y Chrome o Edge.

### 2.4 Break

`brkStart(min, msg, sound, target)` guarda `{end, paused, remain, msg, where}`. `brkRender()` dibuja la cuenta regresiva. El sonido se genera con **WebAudio** (`chime()`), sin archivos de audio. El destino puede ser esta pantalla, el proyector, ambos, otra pantalla o una ventana aparte (`?view=audience&brk=1`).

### 2.5 Atajos de teclado

| Tecla | Acción |
|---|---|
| `→` `Espacio` `PageDown` / `←` `PageUp` | siguiente / anterior |
| `Inicio` / `Fin` | primer / último tema |
| `V` | marcar el tema como visto |
| `T` | mostrar u ocultar la barra lateral |
| `P` `F` `F5` | proyectar (elegir pantalla) |
| `B` | pantalla negra |
| `D` | break (en el break: `Espacio` pausa, `+`/`-` ±1 min, `Enter`/`Esc` termina) |
| `Esc` | cerrar ventanas emergentes |

## 3. Simulador de Postman: `pm/pm.js`

Réplica de la interfaz de Postman que se llena **paso a paso**. Lo usan casi todos los temas de la Parte 2.

```html
<link rel="stylesheet" href="pm/pm.css">
<div id="lab"></div>
<script src="pm/pm.js"></script>
<script>
PMLab.mount(document.getElementById('lab'), {
  title: 'Mi laboratorio',
  intro: 'Texto inicial (HTML)',
  state: { ws:'Mi workspace', env:'Petstore - QA', envs:[…], cols:[…], req:{…} },
  steps: [
    { t:'Título', d:'Explicación (HTML)', hl:'url',          // zona resaltada
      set:{ req:{ url:'{{baseUrl}}/pet' } },                 // cambios al estado (merge profundo)
      fn: s => { … },                                        // o cambios con código
      type:'req.url' },                                      // campo que se escribe letra por letra
  ]
});
</script>
```

- **Estado acumulado:** cada paso parte del estado del anterior. `mount` precalcula todos los estados, así se puede saltar a cualquier paso.
- **Vistas** (`view`): `request` (por defecto), `env` (tabla de variables), `runner` (Collection Runner y resultados), `html` (HTML libre en `viewHtml`).
- **Barra lateral** (`side`): `collections`, `environments` o `history`.
- **Superposiciones:** `menu:{x,y,items:[[texto, atajo], '-', …]}` y `modal:{title, sub, fields, opts, html, btns}`.
- **Environment:** `envs:[{name, cloud, vars:[[clave, inicial, actual, secreto?, 'local'|'shared']]}]`. Con `cloud:true` aparece la columna **Share** de Postman 12.
- **Zonas para `hl`:** `ws, search, side, side-add, rail-col, rail-env, rail-hist, tabs, plus, env, crumb, save, method, url, send, rt-params, rt-auth, rt-headers, rt-body, rt-scripts, ed, resp, status, time, size, rbody, rtests, modal, menu, view, env-table`, más `item:<nombre>`, `mi:<opción de menú>`, `var:<variable>`, `share:<variable>`, `run-*`. Cualquier elemento con `data-t="…"` se puede resaltar.
- Al resaltar, el elemento se desplaza a la vista sin correr la página hacia los lados.

## 4. Parte 4: `ci/ci.js`

```js
CI.tabs();        // <div class="tabs" id="tabs"><button data-t="x">  +  <section class="pane" id="p-x">
CI.terms(SEQ);    // <div class="steps2" data-term="tId"><div class="st" data-s="0">…  +  <div class="term" id="tId"><pre>
// SEQ = { tId: [ [ ['p','C:\\> '], ['w','comando\n'], ['', 'salida\n'], ['g','ok'] ], … ] }
// clases: p = prompt (la 'w' siguiente se escribe letra por letra), w, g (verde), r (rojo), y, u, d (gris)
```

`ci/ci.css` incluye la réplica de Jenkins (`.jk`, `.jk-top`, `.jk-side`, `.sv` Stage View, `.jk-console`) y del reporte Allure.

Temas con lógica propia:
- `ci_git_comandos.html`: modelo de commits (`{id, parents, lane, x}`) para el repositorio local y para GitHub, con `commit`, `switch`, `merge` (fast-forward o commit de merge), `push` (rechazado si GitHub tiene commits que no tienes), `fetch`, `pull`, `revert` y `reset`. Dibuja en SVG; los commits huérfanos aparecen punteados.
- `ci_ejecutar.html`: arma el comando de Newman a partir de los parámetros y calcula el resultado con los **conteos reales** de la colección (CRUD: 5 requests y 8 assertions por iteración; Datos: 2 y 4 por fila; la fila Kira falla).

## 5. Generadores

### `postman/generar.py`
Genera la colección **Taller Petstore** (v2.1), el environment **Petstore - QA**, `datos/mascotas.csv|json`, `package.json`, `ejecutar_pruebas.bat` y los archivos del **reto** (`reto/huespedes.csv` y `reto/solucion/`). Las colecciones fueron validadas contra el esquema oficial v2.1.

### `jenkins/generar_repo.py`
Arma `jenkins/taller-api-pruebas/` a partir de `postman/`: copia la colección y los datos, deja la `apiKey` vacía en el environment y escribe `package.json` (newman y reporteros con versión fija), `Jenkinsfile`, `.gitignore` y `README.md`.

**Jenkinsfile:**
- Parámetros: `CARPETA`, `ESTADO`, `DATOS`, `ITERACIONES`, `DETENER_EN_FALLO`.
- `tools { nodejs 'node-lts' }`, triggers `cron` y `pollSCM`.
- Credencial `petstore-api-key` con `withCredentials`.
- Newman dentro de `catchError` (si fallan tests, el build queda UNSTABLE).
- `post { always { junit; allure } }`.

### `promo/generar_promo.py`
Video promocional (MP4 4:5, GIF y PNG) con Pillow + imageio-ffmpeg. No forma parte del deck.

> Python no está en el PATH de este equipo: usar la ruta completa, por ejemplo
> `C:\Users\<usuario>\AppData\Local\Programs\Python\Python313\python.exe postman\generar.py`.

## 6. Agregar un tema

1. Crear `mi_tema.html` en la raíz con el estilo oscuro (`pm/pm.css` y, si aplica, `ci/ci.css`). Textos dirigidos al **estudiante**.
2. Registrarlo en `SLIDES`, después del tema que debe precederlo:
   ```js
   { id:'mi-tema', section:'p2', title:'Mi tema', subtitle:'…', src:'mi_tema.html' },
   ```
3. Recargar el deck: aparece en su lugar sin perder el avance guardado.

Para una **parte nueva**, agregar una entrada en `SECTIONS` con un `id` nuevo (no reutilizar ids viejos).

## 7. Seguridad y datos

- Solo **APIs públicas de práctica** y **datos ficticios**. Ninguna credencial real en el código.
- Las claves que aparecen (`special-key`, `DEMO_KEY`, `admin/password123`, `emilys/emilyspass`, `qa/taller123`) son **públicas**, publicadas por cada servicio para practicar.
- `postman/reto/solucion/` es la solución del reto: **no se publica** (está en `.gitignore`).
