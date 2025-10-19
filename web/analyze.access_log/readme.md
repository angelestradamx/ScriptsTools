# 🧩 Analizador de Access Log (Nginx / Apache)

Analizador avanzado de archivos **access.log** con estadísticas completas, comparación entre tráfico **Cloudflare** y **Directo**, e integración con exportación a **Excel** o **CSV**.  
Ideal para analizar el rendimiento de APIs, servidores web o proxies Nginx en producción.

---

## 📚 Índice

- [Descripción](#descripción)
- [Características principales](#características-principales)
- [Requisitos](#requisitos)
- [Configuración requerida en Nginx](#configuración-requerida-en-nginx)
- [Uso básico](#uso-básico)
- [Ejemplos de uso](#ejemplos-de-uso)
- [Ejemplo de salida](#ejemplo-de-salida)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Exportaciones](#exportaciones)
- [Linter automático](#linter-automático)
- [Autor y versión](#autor-y-versión)

---

## 📘 Descripción

El script `web.analyze.access_log.py` analiza archivos **access.log** (Nginx o Apache) y genera un reporte detallado con métricas de rendimiento, errores, tiempos de respuesta y comparativas de tráfico.  
Permite exportar la información a Excel o CSV con diferentes hojas temáticas (general, por código, por hora, etc.).

---

## 🚀 Características principales

- 📊 **Estadísticas por código HTTP** (200, 400, 499, 500, etc.)
- 🕐 **Análisis por hora** (requests lentos, errores, distribución)
- ☁️ **Comparativa Cloudflare vs Directos**
- 🧭 **Detección de endpoints problemáticos**
- 📈 **Exportación directa a Excel o CSV**
- ⚙️ **Umbral dinámico de lentitud (`--threshold`)**
- 💡 **Sugerencia automática de umbral** según percentiles
- 🧩 **Soporte multi-entorno** (funciona en Linux, Windows y macOS)

---

## 🧰 Requisitos

Instala las dependencias necesarias antes de ejecutar el script:

```bash
pip install -r requirements.txt
```

**Contenido del archivo `requirements.txt`:**

```
pandas==2.3.3
openpyxl==3.1.5
requests==2.32.5
```

---

## ⚙️ Configuración requerida en Nginx

Para que el analizador funcione correctamente, es **necesario configurar un formato de log personalizado** en tu `nginx.conf` (o en el archivo del sitio) que incluya los campos usados por the script: `status`, `rt`, `urt`, `cf-ray`, `realip`, `request`, `ua`, etc.

Agrega o modifica la sección del log así:

```nginx
http {
    # Formato de log compatible con el analizador
    log_format apilog '$remote_addr (cf-node) realip=$http_cf_connecting_ip '
                      '- $time_local "$request" status=$status $body_bytes_sent '
                      'rt=$request_time urt=$upstream_response_time '
                      'referer="$http_referer" ua="$http_user_agent" '
                      'url="$scheme://$host$request_uri" cf_ray="$cf_ray_safe"';

    access_log /var/log/nginx/access.log apilog;
    # IPs de Cloudflare
    include /etc/nginx/cloudflare-ips.conf;

    # Reconocer la IP real que pasa Cloudflare
    real_ip_header CF-Connecting-IP;
    real_ip_recursive on;
}
```

> 💡 **Consejo:** Reinicia Nginx después de aplicar los cambios:
>
> ```bash
> sudo nginx -t && sudo systemctl reload nginx
> ```

Este formato genera los campos que el script utiliza para identificar:
- El tiempo de respuesta (`rt`)
- El tiempo del upstream (`urt`)
- El origen del tráfico (Cloudflare o directo)
- Las cabeceras de usuario y URL completas

---

## ⚙️ Uso básico

Ejecuta el analizador con un archivo de log:

```bash
python3 web.analyze.access_log.py access.log
```

### Parámetros disponibles

| Parámetro            | Descripción                                                              |
|----------------------|--------------------------------------------------------------------------|
| `--threshold` o `-t` | Define el umbral de lentitud en segundos (por defecto 1.0s).             |
| `--export` o `-e`    | Exporta resultados (`excel`, `csv`, `both`).                             |
| `--output` o `-o`    | Nombre del archivo de salida. Por defecto: `<nombre_log>_analysis.xlsx`. |

---

## 🧾 Ejemplos de uso

### 🔹 1. Análisis estándar

```bash
python3 web.analyze.access_log.py /var/log/nginx/access.log
```

### 🔹 2. Análisis con exportación a Excel

```bash
python3 web.analyze.access_log.py access.log --export excel
```

### 🔹 3. Análisis con threshold personalizado y exportación doble

```bash
python3 web.analyze.access_log.py access.log --threshold 2 --export both
```

---

## 📊 Ejemplo de salida

```
📈 ESTADÍSTICAS GENERALES COMPLETAS
📊 Total de requests: 465,396
🐌 Requests lentos (> 1.0s): 9,980 (2.1%)
❌ Errores 499: 1,785 (0.38%)
☁️ Requests Cloudflare: 149,770 (43.2%)
🔗 Requests Directos: 201,475 (56.8%)
⏱️ Tiempo promedio total: 0.421s
📊 Percentil 95: 0.812s
📊 Percentil 99: 1.937s
```

---

## 📁 Estructura del proyecto

```plaintext
ScriptsTools/
└── web/
    └── analyze.access_log/
        ├── web.analyze.access_log.py  # Script principal
        ├── requirements.txt           # Dependencias necesarias
        └── README.md                 # Documentación del proyecto
```

---

## 📦 Exportaciones

El script puede generar múltiples hojas o archivos CSV, según el tipo de exportación seleccionada:

| Hoja / CSV                 | Contenido                                  |
|----------------------------|--------------------------------------------|
| `procesamiento_completado` | Líneas procesadas, rango de fechas         |
| `estadisticas_generales`   | Totales, percentiles, promedios            |
| `distribucion_http`        | Resumen por código HTTP                    |
| `cloudflare_vs_directo`    | Comparativa entre Cloudflare y Directo     |
| `endpoints_por_codigo`     | Principales endpoints por código HTTP      |
| `top_endpoints`            | Top 25 endpoints más solicitados           |
| `analisis_horario`         | Distribución horaria                       |
| `endpoints_lentos`         | Top endpoints más lentos                   |
| `detalle_endpoints`        | Detalle completo con métricas por endpoint |

---

## 🧪 Linter automático

Este proyecto puede validarse automáticamente mediante **GitHub Actions**, para asegurar que todos los scripts cumplan buenas prácticas de sintaxis y estilo.

### Archivo del flujo: `.github/workflows/lint.yml`

```yaml
name: Lint Scripts
on: [push, pull_request]

jobs:
  bash:
    name: Validar scripts Bash
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Ejecutar ShellCheck
        uses: ludeeus/action-shellcheck@v2
        with:
          scandir: './'

  powershell:
    name: Analizar PowerShell
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Instalar PSScriptAnalyzer
        run: Install-Module PSScriptAnalyzer -Force -Scope CurrentUser
      - name: Ejecutar análisis
        run: Invoke-ScriptAnalyzer -Path . -Recurse -Severity Warning -ReportSummary

  python:
    name: Linter Python (Flake8)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Instalar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Instalar Flake8
        run: pip install flake8
      - name: Revisar código Python
        run: flake8 --max-line-length=120 --exclude=.git,__pycache__,venv
```

💡 Esto permite que cada vez que hagas **push** o **pull request**, GitHub revise automáticamente:
- Scripts **Bash** (`.sh`) con **ShellCheck**
- Scripts **PowerShell** (`.ps1`) con **PSScriptAnalyzer**
- Scripts **Python** (`.py`) con **Flake8**

Si encuentra errores, los muestra en la pestaña **Actions** del repositorio.

---

## 👤 Autor y versión

**Autor:** Ángel Estrada  
**Versión:** 1.0.0  
**Licencia:** MIT  
**Repositorio:** [https://github.com/angelestradamx/ScriptsTools](https://github.com/angelestradamx/ScriptsTools)  
**Última actualización:** Octubre 2025