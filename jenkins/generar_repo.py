"""
Genera el proyecto listo para subir a GitHub y ejecutar en Jenkins (Parte 4 del taller).

Toma la colección, el environment y los datos de ../postman (generados por postman/generar.py)
y arma la carpeta  jenkins/taller-api-pruebas/  con:

  postman/   colección + environment (la apiKey va VACÍA: la pone Jenkins desde sus credenciales)
  datos/     mascotas.csv y mascotas.json
  package.json   newman + reporteros como dependencias del proyecto (npm install)
  Jenkinsfile    pipeline con parámetros, Newman, JUnit y Allure
  .gitignore     lo que NO se sube (node_modules, reportes, resultados)
  README.md      cómo ejecutarlo en local y en Jenkins

Uso:  python generar_repo.py
"""
import json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "postman")
OUT = os.path.join(HERE, "taller-api-pruebas")
COL = "Taller Petstore.postman_collection.json"
ENV = "Petstore - QA.postman_environment.json"


def write(rel, content, newline="\n"):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline=newline) as f:
        f.write(content)
    print("  ✓", rel)


JENKINSFILE = r"""// =====================================================================
//  Pipeline del taller: pruebas de API con Newman + reporte Allure
//  Funciona en agentes Windows y Linux.
//  Requiere en Jenkins: plugins Pipeline, Git, NodeJS, JUnit, Allure
//  y en "Tools": NodeJS con el nombre 'node-lts' y Allure Commandline con el nombre 'allure'.
// =====================================================================

// Ejecuta un comando en el sistema del agente (bat en Windows, sh en Linux)
def ejecutar(String comando) {
    if (isUnix()) { sh comando } else { bat comando }
}

pipeline {
    agent any

    tools { nodejs 'node-lts' }

    // Lo que la persona elige al presionar "Build with Parameters"
    parameters {
        choice(name: 'CARPETA', choices: ['CRUD Mascota', 'Datos desde archivo', 'Todas'],
               description: 'Qué parte de la colección ejecutar')
        choice(name: 'ESTADO', choices: ['available', 'pending', 'sold'],
               description: 'Valor de la variable {{status}} para "Buscar mascotas por estado"')
        choice(name: 'DATOS', choices: ['mascotas.csv', 'mascotas.json'],
               description: 'Archivo de datos para la carpeta "Datos desde archivo"')
        string(name: 'ITERACIONES', defaultValue: '1', trim: true,
               description: 'Repeticiones de "CRUD Mascota" (cuando no se usa archivo de datos)')
        booleanParam(name: 'DETENER_EN_FALLO', defaultValue: false,
                     description: 'Cortar la ejecución en el primer test que falle (--bail)')
    }

    options {
        timeout(time: 15, unit: 'MINUTES')               // nunca queda colgado
        buildDiscarder(logRotator(numToKeepStr: '20'))   // guarda los últimos 20 builds
    }

    triggers {
        cron('H 7 * * 1-5')       // de lunes a viernes, alrededor de las 07:00 (con valores por defecto)
        pollSCM('H/5 * * * *')    // cada ~5 min revisa GitHub y ejecuta si hay commits nuevos
    }

    stages {
        stage('Preparar') {
            steps {
                // Limpia resultados de builds anteriores (el historial de Allure lo guarda el plugin)
                dir('allure-results') { deleteDir() }
                dir('reports') { deleteDir() }
                ejecutar 'node -v'
                ejecutar 'npm install --no-audit --no-fund'
            }
        }

        stage('Pruebas de API') {
            steps {
                script {
                    // Arma el comando de Newman según los parámetros elegidos
                    def args = "--env-var \"status=${params.ESTADO}\""
                    if (params.CARPETA == 'Datos desde archivo') {
                        args += " --folder \"Datos desde archivo\" -d \"datos/${params.DATOS}\""
                    } else if (params.CARPETA == 'Todas') {
                        args += " -d \"datos/${params.DATOS}\""
                    } else {
                        if (!(params.ITERACIONES ==~ /\d+/)) { error "ITERACIONES debe ser un número: '${params.ITERACIONES}'" }
                        args += " --folder \"CRUD Mascota\" -n ${params.ITERACIONES}"
                    }
                    if (params.DETENER_EN_FALLO) { args += ' --bail' }

                    // La apiKey sale de las credenciales de Jenkins: no está en el repositorio
                    // y Jenkins la oculta (****) en el log.
                    def clave = isUnix() ? '"apiKey=$API_KEY"' : '"apiKey=%API_KEY%"'
                    withCredentials([string(credentialsId: 'petstore-api-key', variable: 'API_KEY')]) {
                        // Si fallan tests, el build queda INESTABLE (amarillo) y se publican igual los reportes
                        catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                            ejecutar "npx newman run \"postman/Taller Petstore.postman_collection.json\" " +
                                     "-e \"postman/Petstore - QA.postman_environment.json\" " +
                                     "--env-var ${clave} ${args} " +
                                     "-r cli,junit,allure " +
                                     "--reporter-junit-export reports/junit.xml " +
                                     "--reporter-allure-export allure-results"
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            allure includeProperties: false, results: [[path: 'allure-results']]
        }
        success  { echo 'Todas las pruebas pasaron.' }
        unstable { echo 'Hay pruebas que fallaron: revisa el reporte de Allure.' }
        failure  { echo 'El pipeline no pudo completarse: revisa la consola.' }
    }
}
"""

GITIGNORE = """# Dependencias (se instalan con npm install)
node_modules/

# Resultados y reportes (los genera cada ejecución)
reports/
allure-results/
allure-report/
newman/

# Nunca subir secretos ni environments con valores reales
*.local.json
.env
"""

README = """# Pruebas de API · Taller Petstore

Pruebas automatizadas de la API pública de práctica [Swagger Petstore](https://petstore.swagger.io)
con **Postman + Newman**, ejecutadas en **Jenkins** con reporte **Allure**.

## Estructura
| Ruta | Contenido |
|---|---|
| `postman/` | Colección y environment exportados de Postman (v2.1) |
| `datos/` | Archivos de datos para las pruebas data-driven |
| `package.json` | Newman y sus reporteros como dependencias |
| `Jenkinsfile` | El pipeline |

## Ejecutar en tu PC
Requiere Node.js LTS.
```
npm install
npm test
```
`npm test` pasa la apiKey pública de práctica de Petstore por parámetro (`--env-var`).
En Jenkins la clave sale de la credencial `petstore-api-key`.

## Ejecutar en Jenkins
1. Plugins: Pipeline, Git, NodeJS, JUnit y Allure.
2. Tools: NodeJS con el nombre `node-lts` y Allure Commandline con el nombre `allure`.
3. Credencial *Secret text* con el id `petstore-api-key`.
4. Nuevo item → **Pipeline** → *Pipeline script from SCM* → Git → URL de este repositorio → rama `*/main` → Script Path `Jenkinsfile`.
5. El primer build carga los parámetros; desde el segundo aparece **Build with Parameters**.

> Solo datos ficticios. No subas tokens, contraseñas ni datos reales a un repositorio.
"""


def main():
    print("Generando", os.path.relpath(OUT, HERE))
    col = json.load(open(os.path.join(SRC, COL), encoding="utf-8"))
    env = json.load(open(os.path.join(SRC, ENV), encoding="utf-8"))
    for v in env["values"]:
        if v["key"] == "apiKey":
            v["value"] = ""       # la pone Jenkins (credencial) o --env-var en local
    write("postman/" + COL, json.dumps(col, ensure_ascii=False, indent=2) + "\n")
    write("postman/" + ENV, json.dumps(env, ensure_ascii=False, indent=2) + "\n")
    for f in ("mascotas.csv", "mascotas.json"):
        os.makedirs(os.path.join(OUT, "datos"), exist_ok=True)
        shutil.copyfile(os.path.join(SRC, "datos", f), os.path.join(OUT, "datos", f))
        print("  ✓ datos/" + f)

    base = f'newman run "postman/{COL}" -e "postman/{ENV}" --env-var "apiKey=special-key"'
    package = {
        "name": "taller-api-pruebas",
        "version": "1.0.0",
        "private": True,
        "description": "Pruebas de API del taller (Petstore) con Newman, para ejecutar en Jenkins",
        "scripts": {
            "test": base + ' --folder "CRUD Mascota"',
            "test:datos": base + ' --folder "Datos desde archivo" -d datos/mascotas.csv',
            "test:allure": base + ' --folder "CRUD Mascota" -r cli,allure --reporter-allure-export allure-results',
        },
        "devDependencies": {
            "newman": "6.2.3",
            "newman-reporter-allure": "3.13.0",
            "newman-reporter-htmlextra": "1.23.1",
        },
    }
    write("package.json", json.dumps(package, ensure_ascii=False, indent=2) + "\n")
    write("Jenkinsfile", JENKINSFILE.lstrip())
    write(".gitignore", GITIGNORE)
    write("README.md", README)


if __name__ == "__main__":
    main()
