# 🧰 ScriptsTools — Colección de utilidades para administración de sistemas

Repositorio central con **scripts desarrollados para automatizar tareas de infraestructura**, mejorar la **seguridad**, optimizar **rendimiento** y simplificar la **gestión de servidores Linux, Windows y entornos virtualizados**.

Incluye herramientas para:
- 🔒 Seguridad y firewall
- 🌐 Configuración web y Nginx
- 🩺 Monitoreo de rendimiento
- 💾 Bases de datos SQL Server / PostgreSQL
- ⚙️ Redes y diagnóstico
- 🖥️ Virtualización (Proxmox, Docker)
- 🧩 Utilidades generales (bash, PowerShell)

---

## 📚 Índice de categorías

| Categoría            | Descripción                                              | Ruta                              |
|----------------------|----------------------------------------------------------|-----------------------------------|
| 🔒 **Seguridad**     | Scripts de iptables, fail2ban, Cloudflare y bloqueo de IPs | [seguridad/](seguridad)           |
| 🩺 **Monitoreo**     | Scripts de diagnóstico y métricas de rendimiento          | [monitoreo/](monitoreo)           |
| 🌐 **Web**          | Configuración y análisis de servidores Nginx/Apache       | [web/](web)                       |
| 💾 **Bases de Datos** | Scripts SQL, monitoreo y optimización de índices         | [basesdedatos/](basesdedatos)     |
| ⚙️ **Redes**        | VLAN, diagnóstico, tráfico y control de conexiones        | [redes/](redes)                   |
| 🖥️ **Virtualización** | Proxmox, Docker y gestión de entornos virtuales         | [virtualizacion/](virtualizacion) |
| 🧩 **Utils**        | Scripts generales en bash y PowerShell                    | [utils/](utils)                   |

---

## 🧱 Estructura general del repositorio

```plaintext
ScriptsTools/
├── seguridad/
│   ├── fail2ban/
│   ├── iptables/
│   └── cloudflare/
│       └── README.md
├── monitoreo/
│   ├── linux/
│   ├── windows/
│   └── sqlserver/
│       └── README.md
├── redes/
│   ├── vlan/
│   └── diagnostics/
│       └── README.md
├── web/
│   ├── nginx/
│   ├── certificates/
│   └── analyze.access_log/
│       └── README.md
├── basesdedatos/
│   ├── sqlserver/
│   └── postgres/
│       └── README.md
├── virtualizacion/
│   ├── proxmox/
│   └── docker/
│       └── README.md
├── utils/
│   ├── bash/
│   └── powershell/
│       └── README.md
├── .github/workflows/lint.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md   ← este archivo
```

---

## ⚙️ Convenciones de nombres

Los scripts siguen una convención clara para identificar el entorno, la acción y el objetivo:

```
<entorno>.<accion>.<target>.<extensión>
```

**Ejemplos:**
- `linux.backup.minio.sh`
- `windows.iis.reset.ps1`
- `sqlserver.check.top_queries.sql`

---

## 🧩 Buenas prácticas para scripts de Shell

### 1️⃣ Shebang
La primera línea define el intérprete:

```bash
#!/usr/bin/env bash
```

Esto garantiza compatibilidad en cualquier sistema con `bash` en el PATH.

---

### 2️⃣ Modo estricto

Activa comprobaciones para evitar errores silenciosos:

```bash
set -euo pipefail
```

| Opción        | Significado                                                  |
|---------------|-------------------------------------------------------------|
| `-e`          | Detiene la ejecución si un comando falla.                   |
| `-u`          | Falla si se usa una variable no declarada.                 |
| `-o pipefail` | Propaga el error de cualquier comando dentro de una tubería.|

---

### 3️⃣ Ejemplo completo

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Iniciando backup..."
resultado=$(rsync -av /origen /destino)
echo "Resultado: $resultado"
```

---

## 🧰 Requisitos generales

- Bash 5.0+
- Python 3.10+
- PowerShell 7+
- Acceso a red y permisos de ejecución en el entorno

---

## 🧪 Linter automático (GitHub Actions)

El repositorio incluye un flujo de trabajo para **validar automáticamente** todos los scripts con herramientas de análisis estático.

**Archivo:** `.github/workflows/lint.yml`

```yaml
name: Lint Scripts
on: [push, pull_request]

jobs:
  bash:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run ShellCheck
        uses: ludeeus/action-shellcheck@v2
        with:
          scandir: './'

  powershell:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install PSScriptAnalyzer
        run: Install-Module PSScriptAnalyzer -Force -Scope CurrentUser
      - name: Analyze PowerShell
        run: Invoke-ScriptAnalyzer -Path . -Recurse -Severity Warning -ReportSummary

  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Flake8
        run: pip install flake8
      - name: Lint Python
        run: flake8 --max-line-length=120 --exclude=.git,__pycache__,venv
```

💡 *Cada vez que haces un push o PR, GitHub revisa automáticamente la calidad del código.*

---

## 👤 Autor y mantenimiento

**Autor:** Ángel Estrada  
**Licencia:** MIT  
**Repositorio:** [https://github.com/angelestradamx/ScriptsTools](https://github.com/angelestradamx/ScriptsTools)  
**Última actualización:** Octubre 2025