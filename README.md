# Taller · APIs y Postman

Deck interactivo tipo PowerPoint en HTML. Se abre con `index.html`.

## Cómo levantarlo

Requisitos: **Python 3** (solo para el servidor local) y **Chrome o Edge**. No hay dependencias ni build.

**Opción 1 · doble clic**

`levantar.bat` busca Python, levanta el servidor y abre el navegador en `http://127.0.0.1:8765/index.html`.

**Opción 2 · desde la terminal** (dentro de esta carpeta)

```bat
py servidor.py
```

o, si `py` no existe:

```bat
python servidor.py
```

o con la ruta completa (en este equipo Python no está en el PATH):

```bat
"%LOCALAPPDATA%\Programs\Python\Python313\python.exe" servidor.py
```

- Otro puerto: `py servidor.py 9000`, o `levantar.bat 9000`.
- Detenerlo: `Ctrl+C` o cerrar la ventana.
- Abrir: **http://127.0.0.1:8765/** (si ves una versión vieja, `Ctrl+F5`).

**Opción 3 · sin servidor**

Doble clic en `index.html`. Sirve para revisar los temas, pero la **proyección con vista del presentador** y la **selección de pantalla** necesitan `http://`, no `file://`.

> ¿Por qué `servidor.py` y no `python -m http.server`? Porque le indica al navegador que no guarde copias en caché: al editar un `.html` siempre se ve la última versión.

### Regenerar los archivos de práctica

```bat
py postman\generar.py          :: colección, environment, datos, package.json y archivos del reto
py jenkins\generar_repo.py     :: proyecto para GitHub/Jenkins (jenkins\taller-api-pruebas)
```

### Ejecutar la colección con Newman (requiere Node.js)

```bat
npm install -g newman newman-reporter-htmlextra
cd postman
newman run "Taller Petstore.postman_collection.json" -e "Petstore - QA.postman_environment.json" --folder "CRUD Mascota"
npm run test:reporte
```

La documentación técnica del código (arquitectura, estado, mensajes entre ventanas, simulador de Postman, generadores) está en [DOCUMENTACION.md](DOCUMENTACION.md).

## Estructura
| Parte | Archivos |
|---|---|
| Inicio | Portada (generada en `index.html`) y `sobre_mi.html` (foto y QR en `img/`) |
| **Parte 1 · Conceptos de APIs** | `que_es_api.html`, `api_comunicacion_apps.html`, `anatomia_endpoint.html`, `request_response.html`, `metodos_http.html`, `api_base_datos.html`, `status_codes.html`, `rest_vs_soap.html`, `devtools_network.html`, `tipos_pruebas_api.html`, `repaso_apis.html` |
| **Parte 2 · Postman paso a paso** | `pm_swagger.html`, `pm_que_es.html`, `pm_workspaces.html`, `pm_primer_request.html`, `pm_variables.html`, `pm_crud.html`, `pm_auth.html`, `pm_tests.html`, `pm_runner.html`, `pm_orden.html`, `pm_agendar.html`, `pm_cli.html`, `pm_newman.html`, `pm_allure.html`, `pm_datos.html`, `pm_monitor.html` (en construcción; el resto figura en `SECTIONS.planned`) |
| **Parte 3 · Reto** | `reto_booker.html`: tarea individual con Restful Booker en un solo nivel completo: 6 pasos (environment, colección, 8 requests encadenados con tests, Runner con CSV, caza de defectos, entrega), checklist y rúbrica de 100 puntos. Plazo y medio de entrega: constantes `PLAZO` y `MEDIO` al inicio del script |
| **Parte 4 · Git, GitHub y Jenkins** | `ci_git.html` (flujo de Git animado, instalar, crear el repo, subir, día a día), `ci_git_comandos.html` (gráfica interactiva de commits: commit, ramas, merge, push, pull, fetch, revert, reset + chuleta), `ci_jenkins.html` (CI/CD, simulación de un build, vocabulario), `ci_instalar.html` (Java 21, Jenkins LTS o Docker, plugins, Tools, credenciales), `ci_primer_job.html` (job “hola-jenkins” sin repositorio), `ci_pipeline.html` (Jenkinsfile bloque por bloque y job desde SCM), `ci_ejecutar.html` (Build with Parameters, Stage View, consola y Allure). Estilos y utilidades en `ci/` |
| **Parte 5 · Performance** | `k6_vus_concurrencia_demo.html`, `k6_hpa_pods_503_simulacion_v4.html` |
| Final | Cierre (generado en `index.html`) |

## Agregar un tema
1. Copiar el `.html` a esta carpeta (mismo estilo oscuro, textos dirigidos al estudiante).
2. Agregar una línea en `SLIDES` dentro de `index.html`:
   ```js
   { id:'pm-interfaz', section:'p2', title:'La interfaz de Postman', subtitle:'...', src:'postman_interfaz.html' },
   ```
   `section`: `p1`, `p2`, `reto`, `ci` o `perf`. Los temas planificados de la Parte 2 están en `SECTIONS` (campo `planned`).

## Archivos para importar en Postman (`postman/`)
Se regeneran con `python postman/generar.py`. Validados contra el esquema oficial de colecciones v2.1.
- `Taller Petstore.postman_collection.json`: carpetas *CRUD Mascota* (POST/GET/PUT/DELETE encadenados) y *Datos desde archivo*.
- `Petstore - QA.postman_environment.json`: baseUrl, status, apiKey (`special-key`, la clave pública de Petstore), petId y petName.
- `package.json` (scripts `npm run test:crud`, `test:datos`, `test:reporte`) y `ejecutar_pruebas.bat` (doble clic o Programador de tareas).
- `datos/mascotas.csv` y `datos/mascotas.json`: 5 filas. La última (Kira, `perdida`) hace fallar un test **a propósito**: la API acepta un estado que su documentación no permite.
- **Exportar en Postman 12** (lo enseña `pm_cli.html`): colección con ⋯ → More → Export collection → Other → v2.1. En el environment, primero hay que hacer clic en ☁ **Share** en cada valor que Newman necesita (baseUrl, status, apiKey): Export solo incluye los valores compartidos y, si no, el archivo sale con `baseUrl` vacío.
- Newman: `newman run "postman/Taller Petstore.postman_collection.json" -e "postman/Petstore - QA.postman_environment.json" --folder "CRUD Mascota"` (requiere Node.js).

### Reto (`postman/reto/`)
- `huespedes.csv`: 5 huéspedes para ejecutar la carpeta “Reserva completa” en el Runner (descargable desde la página del reto).
- `solucion/`: **solo para el instructor**. Colección con la carpeta “Reserva completa” (01 Login → 08 Verificar eliminación; 5 iteraciones = 40 requests en verde) y la carpeta “Defectos encontrados” (D1–D4, tests que fallan a propósito), más el environment. Verificada contra la API real el 2026-10-12. **No compartir esta carpeta con el estudiante.**
- Defectos reales de Restful Booker (respuestas del bonus): DELETE → 201; /ping → 201; login con clave mala → 200 `{"reason":"Bad credentials"}`; crear con datos incompletos o precio negativo → 500; PUT no reemplaza todo (conserva `additionalneeds`); crear → 200 en vez de 201.

### Proyecto para GitHub y Jenkins (`jenkins/taller-api-pruebas/`)
Se regenera con `python jenkins/generar_repo.py` (toma la colección, el environment y los datos de `postman/`). Es la carpeta que el estudiante sube a GitHub en la Parte 4:
- `postman/` (environment con la **apiKey vacía**: Jenkins la pone desde la credencial `petstore-api-key`), `datos/`, `package.json` (newman 6.2.3, newman-reporter-allure 3.13.0, htmlextra 1.23.1 como devDependencies), `.gitignore`, `README.md`.
- `Jenkinsfile`: parámetros CARPETA, ESTADO, DATOS, ITERACIONES y DETENER_EN_FALLO; `tools { nodejs 'node-lts' }`; triggers `cron('H 7 * * 1-5')` y `pollSCM`; Newman con `catchError` → UNSTABLE si fallan tests; `post { always { junit; allure } }`. Sirve en agentes Windows (`bat`) y Linux (`sh`).
- Requisitos en Jenkins: plugins NodeJS, Allure y Pipeline: Stage View (además de los sugeridos); Tools `node-lts` y `allure`; credencial Secret text `petstore-api-key`.
- **No se probó en un Jenkins real** desde este equipo (no hay Jenkins ni Node instalados): hacer un ensayo completo antes del taller.

## Simulador de Postman (Parte 2)
`pm/pm.css` + `pm/pm.js` dibujan una réplica de Postman que se llena paso a paso. Cada diapositiva llama a
`PMLab.mount(elemento, { state, steps })`. Cada paso define qué se resalta (`hl`), qué cambia (`set`/`fn`)
y qué campo se escribe letra por letra (`type`). Ver el comentario al inicio de `pm/pm.js`.

## APIs públicas de práctica (verificadas desde la red del banco el 2026-10-06)
| API | Uso | Nota |
|---|---|---|
| petstore.swagger.io/v2 | Swagger + CRUD | POST responde 200 (no 201); datos compartidos |
| httpbin.org | Basic Auth `/basic-auth/qa/taller123` | sin credenciales → 401; en el navegador abre una ventana de login (es lo esperado) |
| dummyjson.com | Bearer: `POST /auth/login` → `/auth/me` | usuario demo `emilys` |
| api.nasa.gov | API Key `?api_key=` | `DEMO_KEY` = 10 req/hora por IP: no alcanza para un grupo |
| restful-booker.herokuapp.com | encadenar con token | |
| reqres.in | — | ya no exige la key (responde 200 sin ella) |

## Funciones del deck
- Reordenar con arrastrar (también entre partes), ocultar temas o partes completas, colapsar partes.
- Avance: ☐ por tema, ☑ por parte, marcar/desmarcar todo, "Continuar donde me quedé". Se guarda en el navegador.
- 📽 Proyectar (`P` / `F5`): elegir pantalla; en el proyector solo el contenido y en la laptop la vista del presentador
  (actual, siguiente, cronómetro, próximos temas, `B` pantalla negra). Cerrar la ventana del proyector cancela la proyección.
- ☕ Break (`D`): cuenta regresiva configurable (5/10/15/20 min o personalizada) con mensaje editable, sonido al terminar
  y aviso al faltar 1 minuto. Durante el break: `Espacio` pausa, `+`/`-` suma o resta 1 minuto, `Enter`/`Esc` lo termina.
  Al iniciarlo se elige dónde mostrarlo: esta pantalla, el proyector, ambos, otra pantalla detectada o una ventana aparte.
  Si se muestra en otra pantalla, en la laptop queda un panel pequeño con el reloj y los controles.

## Pendiente
- [ ] Parte 2: temas planificados en `SECTIONS.planned` (colecciones: crear, editar, duplicar, importar y exportar; el formato JSON).
- [ ] Reto: definir plazo y medio de entrega (constantes `PLAZO` y `MEDIO` en `reto_booker.html`).
- [ ] Ensayo completo de la Parte 4 en un Jenkins real (Node, Allure, credencial, proxy corporativo).
- [ ] Ejecutar Newman y Allure una vez en el equipo del taller.
- [ ] Probar la proyección con un proyector real.
- [ ] Validar con seguridad/compliance el uso de cuentas Postman y GitHub (sincronizan con la nube). Solo datos ficticios.
