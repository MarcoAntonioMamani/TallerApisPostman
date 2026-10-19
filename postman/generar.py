"""Genera los archivos del taller que se importan en Postman.

    python postman/generar.py

Crea:
  Taller Petstore.postman_collection.json   colección (formato v2.1)
  Petstore - QA.postman_environment.json     environment
  datos/mascotas.csv, datos/mascotas.json     datos para el Collection Runner
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))


def script(kind, code):
    return {"listen": kind, "script": {"type": "text/javascript", "exec": code.strip("\n").split("\n")}}


def url(raw):
    """Arma el objeto url de Postman a partir de '{{baseUrl}}/pet/{{petId}}'."""
    path_part, _, query = raw.partition("?")
    host, *path = path_part.split("/")
    u = {"raw": raw, "host": [host], "path": path}
    if query:
        u["query"] = [{"key": k, "value": v} for k, v in (p.split("=", 1) for p in query.split("&"))]
    return u


def request(name, method, raw_url, *, body=None, headers=None, pre=None, post=None, desc=""):
    req = {"method": method, "header": headers or [], "url": url(raw_url), "description": desc}
    if body is not None:
        req["body"] = {"mode": "raw", "raw": body, "options": {"raw": {"language": "json"}}}
    item = {"name": name, "request": req, "response": []}
    events = []
    if pre:
        events.append(script("prerequest", pre))
    if post:
        events.append(script("test", post))
    if events:
        item["event"] = events
    return item


PET_BODY = """{
  "id": {{petId}},
  "category": { "id": 1, "name": "Perros" },
  "name": "{{petName}}",
  "photoUrls": [],
  "tags": [],
  "status": "%s"
}"""

API_KEY = [{"key": "api_key", "value": "{{apiKey}}", "type": "text"}]

crud = {
    "name": "CRUD Mascota",
    "description": "Crea, consulta, actualiza y elimina una mascota. Los datos se generan en el pre-request de 01; ejecutar la carpeta completa en orden.",
    "item": [
        request("01 Crear mascota", "POST", "{{baseUrl}}/pet", body=PET_BODY % "available",
                pre="""
// Datos nuevos en cada ejecución
pm.environment.set("petId", Date.now());
pm.environment.set("petName", pm.variables.replaceIn("{{$randomFirstName}}"));
""",
                post="""
pm.test("Status 200", () => pm.response.to.have.status(200));
const json = pm.response.json();
pm.test("Se creó con el nombre enviado", () =>
  pm.expect(json.name).to.eql(pm.environment.get("petName")));
// Guardar el id que confirmó la API
pm.environment.set("petId", json.id);
"""),
        request("02 Consultar mascota", "GET", "{{baseUrl}}/pet/{{petId}}",
                post="""
pm.test("Status 200", () => pm.response.to.have.status(200));
const json = pm.response.json();
pm.test("Es la mascota creada", () => {
  pm.expect(String(json.id)).to.eql(String(pm.environment.get("petId")));
  pm.expect(json.name).to.eql(pm.environment.get("petName"));
});
console.log("Estado actual:", json.status);
"""),
        request("03 Actualizar mascota", "PUT", "{{baseUrl}}/pet", body=PET_BODY % "sold",
                post="""
pm.test("Status 200", () => pm.response.to.have.status(200));
pm.test("Quedó vendida", () =>
  pm.expect(pm.response.json().status).to.eql("sold"));
"""),
        request("04 Eliminar mascota", "DELETE", "{{baseUrl}}/pet/{{petId}}", headers=API_KEY,
                post="""
pm.test("Status 200", () => pm.response.to.have.status(200));
"""),
        request("05 Verificar eliminación", "GET", "{{baseUrl}}/pet/{{petId}}",
                post="""
pm.test("Ya no existe: 404", () => pm.response.to.have.status(404));
"""),
    ],
}

data_driven = {
    "name": "Datos desde archivo",
    "description": "Ejecutar SOLO esta carpeta en el Collection Runner con datos/mascotas.csv o datos/mascotas.json. Cada fila del archivo es una iteración.",
    "item": [
        request("Crear mascota desde datos", "POST", "{{baseUrl}}/pet",
                body="""{
  "id": {{petId}},
  "category": { "id": 1, "name": "{{categoria}}" },
  "name": "{{nombre}}",
  "photoUrls": [],
  "tags": [],
  "status": "{{status}}"
}""",
                pre="""
// El id sigue siendo único; nombre, categoría y status vienen del archivo de datos
pm.environment.set("petId", Date.now());
""",
                post="""
const nombre = pm.iterationData.get("nombre");
const status = pm.iterationData.get("status");

pm.test(`Creó a ${nombre}`, () => pm.response.to.have.status(200));
const json = pm.response.json();
pm.test("Guardó el estado del archivo", () => pm.expect(json.status).to.eql(status));
pm.test("El estado es un valor permitido", () =>
  pm.expect(json.status).to.be.oneOf(["available", "pending", "sold"]));
pm.environment.set("petId", json.id);
"""),
        request("Limpiar: eliminar mascota", "DELETE", "{{baseUrl}}/pet/{{petId}}", headers=API_KEY,
                post="""
pm.test("Mascota de prueba eliminada", () => pm.response.to.have.status(200));
"""),
    ],
}

collection = {
    "info": {
        "_postman_id": str(uuid.uuid5(uuid.NAMESPACE_URL, "taller-apis-petstore")),
        "name": "Taller Petstore",
        "description": "Colección del taller de APIs y Postman. API pública de práctica: https://petstore.swagger.io. Usar con el environment 'Petstore - QA'. Solo datos ficticios.",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "item": [
        request("Buscar mascotas por estado", "GET", "{{baseUrl}}/pet/findByStatus?status={{status}}",
                post="""
pm.test("Status 200", () => pm.response.to.have.status(200));
pm.test("Devuelve una lista", () => pm.expect(pm.response.json()).to.be.an("array"));
"""),
        crud,
        data_driven,
    ],
}

environment = {
    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "taller-apis-petstore-qa")),
    "name": "Petstore - QA",
    "values": [
        {"key": "baseUrl", "value": "https://petstore.swagger.io/v2", "type": "default", "enabled": True},
        {"key": "status", "value": "available", "type": "default", "enabled": True},
        # special-key es la clave PÚBLICA de prueba que publica Swagger Petstore (no es un secreto real)
        {"key": "apiKey", "value": "special-key", "type": "secret", "enabled": True},
        {"key": "petId", "value": "", "type": "default", "enabled": True},
        {"key": "petName", "value": "", "type": "default", "enabled": True},
    ],
    "_postman_variable_scope": "environment",
}

ROWS = [
    ("Firulais", "Perros", "available"),
    ("Michi", "Gatos", "pending"),
    ("Rocky", "Perros", "sold"),
    ("Luna", "Gatos", "available"),
    ("Kira", "Perros", "perdida"),   # estado NO permitido: la API lo acepta igual (defecto real)
]


def write(rel, content):
    path = os.path.join(HERE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("  ✓", rel)


# =====================================================================
# RETO (tarea): Restful Booker. Archivos para el estudiante y SOLUCIÓN solo para el instructor.
# =====================================================================
JSON_HDR = [{"key": "Content-Type", "value": "application/json", "type": "text"},
            {"key": "Accept", "value": "application/json", "type": "text"}]
TOKEN_HDR = JSON_HDR + [{"key": "Cookie", "value": "token={{token}}", "type": "text"}]

BOOKING = """{
  "firstname": "%s",
  "lastname": "%s",
  "totalprice": %s,
  "depositpaid": %s,
  "bookingdates": { "checkin": "%s", "checkout": "%s" },
  "additionalneeds": "%s"
}"""

SAVE_BOOKING = """
pm.test("Status 200", () => pm.response.to.have.status(200));
const json = pm.response.json();
pm.test("Devuelve el id de la reserva", () => pm.expect(json.bookingid).to.be.a("number"));
pm.environment.set("bookingId", json.bookingid);
"""

LOGIN_POST = """
pm.test("Status 200", () => pm.response.to.have.status(200));
const json = pm.response.json();
// Ojo: con credenciales malas la API también responde 200 (con "reason"), por eso se valida el token
pm.test("Devuelve un token", () => pm.expect(json.token).to.be.a("string").and.not.be.empty);
pm.environment.set("token", json.token);
"""

reto_flujo = {"name": "Reserva completa",
              "description": "Ejecutar esta carpeta en el Collection Runner con reto/huespedes.csv (5 iteraciones).",
              "item": [
    request("01 Login", "POST", "{{baseUrl}}/auth", headers=JSON_HDR,
            body='{\n  "username": "{{usuario}}",\n  "password": "{{clave}}"\n}', post=LOGIN_POST),
    request("02 Crear reserva", "POST", "{{baseUrl}}/booking", headers=JSON_HDR,
            body=BOOKING % ("{{firstname}}", "{{lastname}}", "{{totalprice}}", "{{depositpaid}}", "{{checkin}}", "{{checkout}}", "{{additionalneeds}}"),
            pre="""
// Fechas dinámicas: llegada dentro de 30 días y salida según las noches del archivo
const fmt = d => d.toISOString().slice(0, 10);
const llegada = new Date();
llegada.setDate(llegada.getDate() + 30);
const salida = new Date(llegada);
salida.setDate(salida.getDate() + Number(pm.iterationData.get("noches")));
pm.environment.set("checkin", fmt(llegada));
pm.environment.set("checkout", fmt(salida));
""",
            post="""
pm.test("Status 200", () => pm.response.to.have.status(200));
const json = pm.response.json();
pm.test("Devuelve el id de la reserva", () => pm.expect(json.bookingid).to.be.a("number"));
pm.test(`Guardó la reserva de ${pm.iterationData.get("firstname")}`, () => {
  pm.expect(json.booking.firstname).to.eql(pm.iterationData.get("firstname"));
  pm.expect(json.booking.totalprice).to.eql(Number(pm.iterationData.get("totalprice")));
  pm.expect(json.booking.bookingdates.checkin).to.eql(pm.environment.get("checkin"));
});
pm.environment.set("bookingId", json.bookingid);
"""),
    request("03 Consultar reserva", "GET", "{{baseUrl}}/booking/{{bookingId}}", headers=JSON_HDR,
            post="""
pm.test("Status 200", () => pm.response.to.have.status(200));
const json = pm.response.json();
pm.test("Los datos coinciden con el archivo", () => {
  pm.expect(json.firstname).to.eql(pm.iterationData.get("firstname"));
  pm.expect(json.lastname).to.eql(pm.iterationData.get("lastname"));
  pm.expect(json.totalprice).to.eql(Number(pm.iterationData.get("totalprice")));
  pm.expect(json.depositpaid).to.eql(pm.iterationData.get("depositpaid") === "true");
  pm.expect(json.additionalneeds).to.eql(pm.iterationData.get("additionalneeds"));
});
pm.test("Las fechas son las calculadas", () => {
  pm.expect(json.bookingdates.checkin).to.eql(pm.environment.get("checkin"));
  pm.expect(json.bookingdates.checkout).to.eql(pm.environment.get("checkout"));
});
"""),
    request("04 Buscar reserva por nombre", "GET", "{{baseUrl}}/booking?firstname={{firstname}}&lastname={{lastname}}", headers=JSON_HDR,
            post="""
pm.test("Status 200", () => pm.response.to.have.status(200));
const ids = pm.response.json().map(r => r.bookingid);
pm.test("La búsqueda encuentra la reserva creada", () =>
  pm.expect(ids).to.include(Number(pm.environment.get("bookingId"))));
"""),
    request("05 Actualizar sin token (negativo)", "PUT", "{{baseUrl}}/booking/{{bookingId}}", headers=JSON_HDR,
            body=BOOKING % ("{{firstname}}", "{{lastname}}", "1", "{{depositpaid}}", "{{checkin}}", "{{checkout}}", "{{additionalneeds}}"),
            post="""
pm.test("Sin token no se puede modificar: 403", () => pm.response.to.have.status(403));
"""),
    request("06 Actualizar reserva", "PUT", "{{baseUrl}}/booking/{{bookingId}}", headers=TOKEN_HDR,
            body=BOOKING % ("{{firstname}}", "{{lastname}}", "{{nuevoPrecio}}", "true", "{{checkin}}", "{{nuevaSalida}}", "{{additionalneeds}}"),
            pre="""
// Nuevo precio: 100 más que el original. Nueva salida: un día después.
pm.environment.set("nuevoPrecio", Number(pm.iterationData.get("totalprice")) + 100);
const salida = new Date(pm.environment.get("checkout"));
salida.setDate(salida.getDate() + 1);
pm.environment.set("nuevaSalida", salida.toISOString().slice(0, 10));
""",
            post="""
pm.test("Status 200", () => pm.response.to.have.status(200));
const json = pm.response.json();
pm.test("Se aplicaron los cambios", () => {
  pm.expect(json.totalprice).to.eql(Number(pm.environment.get("nuevoPrecio")));
  pm.expect(json.depositpaid).to.be.true;
  pm.expect(json.bookingdates.checkout).to.eql(pm.environment.get("nuevaSalida"));
});
"""),
    request("07 Eliminar reserva", "DELETE", "{{baseUrl}}/booking/{{bookingId}}", headers=TOKEN_HDR,
            post="""
// La API responde 201 al eliminar (es uno de los defectos); lo correcto sería 200 o 204
pm.test("Eliminación aceptada", () => pm.expect(pm.response.code).to.be.oneOf([200, 201, 204]));
"""),
    request("08 Verificar eliminación", "GET", "{{baseUrl}}/booking/{{bookingId}}", headers=JSON_HDR,
            post="""
pm.test("Ya no existe: 404", () => pm.response.to.have.status(404));
"""),
]}

reto_defectos = {"name": "Defectos encontrados",
                 "description": "Cada request prueba el comportamiento CORRECTO esperado. Sus tests FALLAN a propósito: esa es la evidencia del defecto.",
                 "item": [
    request("D1 Login con clave incorrecta debería responder 401", "POST", "{{baseUrl}}/auth", headers=JSON_HDR,
            body='{\n  "username": "{{usuario}}",\n  "password": "clave-incorrecta"\n}',
            post="""
// Defecto: responde 200 con {"reason": "Bad credentials"}
pm.test("Credenciales incorrectas: 401", () => pm.response.to.have.status(401));
"""),
    request("D2 Datos incompletos deberían responder 400", "POST", "{{baseUrl}}/booking", headers=JSON_HDR,
            body='{\n  "firstname": "Incompleto"\n}',
            post="""
// Defecto: responde 500 Internal Server Error (un error del cliente no debería romper el servidor)
pm.test("Datos inválidos: 400", () => pm.response.to.have.status(400));
"""),
    request("D3 Crear debería responder 201", "POST", "{{baseUrl}}/booking", headers=JSON_HDR,
            body=BOOKING % ("Defecto", "Andino", "100", "true", "2026-12-01", "2026-12-02", "Ninguno"),
            post="""
// Defecto: al crear un recurso responde 200 en lugar de 201 Created
pm.test("Recurso creado: 201", () => pm.response.to.have.status(201));
"""),
    request("D4 El health check debería responder 200", "GET", "{{baseUrl}}/ping", headers=JSON_HDR,
            post="""
// Defecto: /ping responde 201 Created, pero no crea nada
pm.test("Servicio disponible: 200", () => pm.response.to.have.status(200));
"""),
]}

reto_collection = {
    "info": {
        "_postman_id": str(uuid.uuid5(uuid.NAMESPACE_URL, "taller-apis-reto-booker-solucion")),
        "name": "Reto Hostal Andino - SOLUCION",
        "description": "Solución de referencia del reto (solo instructor). API pública de práctica: https://restful-booker.herokuapp.com",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "event": [script("test", """
pm.test("Responde en menos de 3 s", () => pm.expect(pm.response.responseTime).to.be.below(3000));
""")],
    "item": [reto_flujo, reto_defectos],
}

reto_env = {
    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "taller-apis-reto-booker-qa")),
    "name": "Restful Booker - QA",
    "values": [
        {"key": "baseUrl", "value": "https://restful-booker.herokuapp.com", "type": "default", "enabled": True},
        # admin / password123 son las credenciales PÚBLICAS de práctica que publica Restful Booker
        {"key": "usuario", "value": "admin", "type": "default", "enabled": True},
        {"key": "clave", "value": "password123", "type": "secret", "enabled": True},
        {"key": "token", "value": "", "type": "secret", "enabled": True},
        {"key": "bookingId", "value": "", "type": "default", "enabled": True},
        # las llenan los scripts en cada iteración
        {"key": "checkin", "value": "", "type": "default", "enabled": True},
        {"key": "checkout", "value": "", "type": "default", "enabled": True},
        {"key": "nuevoPrecio", "value": "", "type": "default", "enabled": True},
        {"key": "nuevaSalida", "value": "", "type": "default", "enabled": True},
    ],
    "_postman_variable_scope": "environment",
}

HUESPEDES = [
    ("Lucia", "Andino", 420, "true", 2, "Desayuno"),
    ("Mateo", "Andino", 300, "false", 3, "Late checkout"),
    ("Valentina", "Andino", 780, "true", 5, "Cama extra"),
    ("Diego", "Andino", 150, "false", 1, "Ninguno"),
    ("Camila", "Andino", 560, "true", 4, "Traslado al aeropuerto"),
]


def write_reto():
    write("reto/huespedes.csv", "firstname,lastname,totalprice,depositpaid,noches,additionalneeds\n"
          + "".join(f"{a},{b},{c},{d},{e},{f}\n" for a, b, c, d, e, f in HUESPEDES))
    write("reto/solucion/Reto Hostal Andino - SOLUCION.postman_collection.json", json.dumps(reto_collection, ensure_ascii=False, indent=2))
    write("reto/solucion/Restful Booker - QA.postman_environment.json", json.dumps(reto_env, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    write_reto()
    print("Generando archivos del taller:")
    write("Taller Petstore.postman_collection.json", json.dumps(collection, ensure_ascii=False, indent=2))
    write("Petstore - QA.postman_environment.json", json.dumps(environment, ensure_ascii=False, indent=2))
    write("datos/mascotas.csv", "nombre,categoria,status\n" + "".join(f"{n},{c},{s}\n" for n, c, s in ROWS))
    write("datos/mascotas.json", json.dumps([{"nombre": n, "categoria": c, "status": s} for n, c, s in ROWS], ensure_ascii=False, indent=2) + "\n")

    # Newman: scripts de npm y un .bat para ejecutar con doble clic o con el Programador de tareas
    col = 'newman run "Taller Petstore.postman_collection.json" -e "Petstore - QA.postman_environment.json"'
    package = {
        "name": "taller-petstore",
        "version": "1.0.0",
        "private": True,
        "description": "Pruebas de API del taller con Newman (requiere: npm install -g newman newman-reporter-htmlextra)",
        "scripts": {
            "test:crud": col + ' --folder "CRUD Mascota"',
            "test:datos": col + ' --folder "Datos desde archivo" -d datos/mascotas.csv',
            "test:reporte": col + ' --folder "CRUD Mascota" -r cli,htmlextra,junit'
                                  ' --reporter-htmlextra-export reports/reporte.html --reporter-junit-export reports/junit.xml',
            # Allure (requiere Java + npm install -g allure-commandline newman-reporter-allure)
            "test:allure": col + ' --folder "CRUD Mascota" --folder "Datos desde archivo" -d datos/mascotas.csv'
                                 ' -r cli,allure --reporter-allure-export allure-results',
            "allure:reporte": "allure generate allure-results --clean -o allure-report && allure open allure-report",
        },
    }
    write("package.json", json.dumps(package, ensure_ascii=False, indent=2) + "\n")
    bat = [
        "@echo off",
        "rem Ejecuta la carpeta CRUD Mascota y genera los reportes en la carpeta reports",
        "rem Requiere: npm install -g newman newman-reporter-htmlextra",
        'cd /d "%~dp0"',
        "if not exist reports mkdir reports",
        'call newman run "Taller Petstore.postman_collection.json" ^',
        '  -e "Petstore - QA.postman_environment.json" ^',
        '  --folder "CRUD Mascota" ^',
        "  -r cli,htmlextra,junit ^",
        "  --reporter-htmlextra-export reports\\reporte.html ^",
        "  --reporter-junit-export reports\\junit.xml",
        "rem El codigo de salida indica si pasaron todos los tests (0 = todo bien)",
        "exit /b %ERRORLEVEL%",
        "",
    ]
    with open(os.path.join(HERE, "ejecutar_pruebas.bat"), "w", encoding="ascii", newline="\r\n") as f:
        f.write("\n".join(bat))
    print("  ✓ ejecutar_pruebas.bat")
