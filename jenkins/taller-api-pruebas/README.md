# Pruebas de API · Taller Petstore

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
