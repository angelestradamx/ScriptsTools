# Scripts de Administración de Sistemas

Este proyecto contiene scripts para la gestión de seguridad, monitoreo, redes, bases de datos y virtualización.

## Estructura del Proyecto
- **seguridad/**: Scripts relacionados con la seguridad del sistema.
- **monitoreo/**: Scripts para monitorear sistemas.
- **redes/**: Herramientas y scripts para la gestión de redes.
- **web/**: Scripts para configuración de servidores web.
- **basesdedatos/**: Scripts para manejar bases de datos.
- **virtualizacion/**: Herramientas para virtualización.
- **utils/**: Utilidades generales.

```bash
ScriptsTools/
├─ security/
│  ├─ fail2ban/
│  │  ├─ jails/
│  │  └─ filters/
│  ├─ iptables/
│  └─ cloudflare/
│     └─ README.md
├─ monitoring/
│  ├─ linux/
│  ├─ windows/
│  └─ sqlserver/
│     └─ README.md
├─ networks/
│  ├─ vlan/
│  └─ diagnostics/
│     └─ README.md
├─ web/
│  ├─ nginx/
│  └─ certificates/
│     └─ README.md
├─ databases/
│  ├─ sqlserver/
│  └─ postgres/
│     └─ README.md
├─ virtualization/
│  ├─ proxmox/
│  └─ docker/
│     └─ README.md
├─ utils/
│  ├─ bash/
│  └─ powershell/
│     └─ README.md
├─ .env.example
├─ .gitignore
├─ LICENSE
├─ CHANGELOG.md
└─ README.md
```


## Cómo Empezar
Copia el archivo `.env.example` a `.env` y ajusta las variables según sea necesario.

## Convenciones

- **Nombres de archivo**: `<os|app>.<accion>.<target>.<ext>`
- **Ejemplos**:
  - `linux.backup.minio.sh`
  - `windows.iis.reset.ps1`
  - `sqlserver.check.top_queries.sql`

## Aspectos Importantes de los Scripts de Shell

### Shebang

El **shebang** es la primera línea de un script de shell que indica al sistema operativo qué intérprete usar para ejecutar el script. La sintaxis común es:

```bash
#!/usr/bin/env bash
```

#### Detalles
- **`#!`**: Indica que lo que sigue es el camino al intérprete.
- **`/usr/bin/env`**: Este comando se utiliza para encontrar el ejecutable `bash` en el `PATH`, lo que permite que el script se ejecute con la versión de `bash` que el usuario tenga configurada, en lugar de una ruta específica que podría no existir en todos los sistemas.

### Modo Estricto

**Definición**: El **modo estricto** es una forma de hacer que un script sea más robusto y menos propenso a errores. Se activa con la línea:

```bash
set -euo pipefail
```

#### Desglose de las Opciones
- **`set -e`**: Hace que el script termine inmediatamente si un comando falla (devuelve un código de error distinto de cero).
- **`set -u`**: Hace que termine el script si se hace referencia a una variable no definida.
- **`set -o pipefail`**: Cambia el comportamiento de las tuberías (pipes) para que devuelvan el código de salida de la última parte que falló. Sin esto, si un comando en una tubería falla, pero el siguiente comando tiene éxito, la tubería devolverá un código de éxito.

#### Ejemplo de Uso

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Iniciando el script..."
# Acciones que podrían fallar
resultado=$(comando_que_puede_fallar) 
echo "Resultado: $resultado"
```

## Requisitos
- bash
- herramientas específicas según el script

## Cómo Empezar
Copia el archivo `.env.example` a `.env` y ajusta las variables según sea necesario.
```
### Nota
Asegúrate de completar las secciones como **Requisitos** y **Cómo Empezar** de acuerdo a las necesidades específicas de tu proyecto. Ahora, tu `README.md` será un recurso útil para cualquier persona que interactúe con tu código. Si necesitas más asistencia o ajustes, ¡hazmelo saber!

## Configuración rápida: si has hecho este tipo de cosas antes
SSH 	git@github.com:angelestradamx/ScriptsTools.git
HTTPS 	https://github.com/angelestradamx/ScriptsTools.git

## … o crear un nuevo repositorio en la línea de comandos
echo "# ScriptsTools" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/angelestradamx/ScriptsTools.git
git push -u origin main

## … o inserte un repositorio existente desde la línea de comandos
git remote add origin https://github.com/angelestradamx/ScriptsTools.git
git branch -M main
git push -u origin main
