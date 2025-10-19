# ?? Analizador de Access Log (Nginx / Apache)

Analizador avanzado de archivos **access.log** con estadisticas completas, comparacion entre trafico **Cloudflare** y **Directo**, e integracion con exportacion a **Excel** o **CSV**.  
Ideal para analizar el rendimiento de APIs, servidores web o proxies Nginx en produccion.

---

## ?? Indice

- [Descripcion](#descripcion)
- [Caracteristicas principales](#caracteristicas-principales)
- [Requisitos](#requisitos)
- [Configuracion requerida en Nginx](#configuracion-requerida-en-nginx)
- [Uso basico](#uso-basico)
- [Ejemplos de uso](#ejemplos-de-uso)
- [Ejemplo de salida](#ejemplo-de-salida)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Exportaciones](#exportaciones)
- [Linter automatico](#linter-automatico)
- [Autor y version](#autor-y-version)

---

## ?? Descripcion

El script `web.analyze.access_log.py` analiza archivos **access.log** (Nginx o Apache) y genera un reporte detallado con metricas de rendimiento, errores, tiempos de respuesta y comparativas de trafico.  
Permite exportar la informacion a Excel o CSV con diferentes hojas tematicas (general, por codigo, por hora, etc.).

---

## ?? Caracteristicas principales

- ?? **Estadisticas por codigo HTTP** (200, 400, 499, 500, etc.)
- ?? **Analisis por hora** (requests lentos, errores, distribucion)
- ?? **Comparativa Cloudflare vs Directos**
- ?? **Deteccion de endpoints problematicos**
- ?? **Exportacion directa a Excel o CSV**
- ?? **Umbral dinamico de lentitud (`--threshold`)**
- ?? **Sugerencia automatica de umbral** segun percentiles
- ?? **Soporte multi-entorno** (funciona en Linux, Windows y macOS)

---

## ?? Requisitos

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

## ?? Configuracion requerida en Nginx

Para que el analizador funcione correctamente, es **necesario configurar un formato de log personalizado** en tu `nginx.conf` (o en el archivo del sitio) que incluya los campos usados por el script: `status`, `rt`, `urt`, `cf-ray`, `realip`, `request`, `ua`, etc.

Agrega o modifica la seccion del log asi:

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

> ?? **Consejo:** Reinicia Nginx despues de aplicar los cambios:
>
> ```bash
> sudo nginx -t && sudo systemctl reload nginx
> ```

Este formato genera los campos que el script utiliza para identificar:
- El tiempo de respuesta (`rt`)
- El tiempo del upstream (`urt`)
- El origen del trafico (Cloudflare o directo)
- Las cabeceras de usuario y URL completas

---

## ?? Uso basico

Ejecuta el analizador con un archivo de log:

```bash
python3 web.analyze.access_log.py access.log
```

### Parametros disponibles

| Parametro            | Descripcion                                                              |
|----------------------|--------------------------------------------------------------------------|
| `--threshold` o `-t` | Define el umbral de lentitud en segundos (por defecto 1.0s).             |
| `--export` o `-e`    | Exporta resultados (`excel`, `csv`, `both`).                             |
| `--output` o `-o`    | Nombre del archivo de salida. Por defecto: `<nombre_log>_analysis.xlsx`. |

---

## ?? Ejemplos de uso

### ?? 1. Analisis estandar

```bash
python3 web.analyze.access_log.py /var/log/nginx/access.log
```

### ?? 2. Analisis con exportacion a Excel

```bash
python3 web.analyze.access_log.py access.log --export excel
```

### ?? 3. Analisis con threshold personalizado y exportacion doble

```bash
python3 web.analyze.access_log.py access.log --threshold 2 --export both
```

---

## ?? Ejemplo de salida

```
?? ESTADISTICAS GENERALES COMPLETAS
?? Total de requests: 465,396
?? Requests lentos (> 1.0s): 9,980 (2.1%)
? Errores 499: 1,785 (0.38%)
?? Requests Cloudflare: 149,770 (43.2%)
?? Requests Directos: 201,475 (56.8%)
?? Tiempo promedio total: 0.421s
?? Percentil 95: 0.812s
?? Percentil 99: 1.937s
```

---

## ?? Estructura del proyecto

```plaintext
ScriptsTools/
¢|¢w¢w web/
    ¢|¢w¢w analyze.access_log/
        ¢u¢w¢w web.analyze.access_log.py  # Script principal
        ¢u¢w¢w requirements.txt           # Dependencias necesarias
        ¢|¢w¢w README.md                 # Documentacion del proyecto
```

---

## ?? Exportaciones

El script puede generar multiples hojas o archivos CSV, segun el tipo de exportacion seleccionada:

| Hoja / CSV                 | Contenido                                  |
|----------------------------|--------------------------------------------|
| `procesamiento_completado` | Lineas procesadas, rango de fechas         |
| `estadisticas_generales`   | Totales, percentiles, promedios            |
| `distribucion_http`        | Resumen por codigo HTTP                    |
| `cloudflare_vs_directo`    | Comparativa entre Cloudflare y Directo     |
| `endpoints_por_codigo`     | Principales endpoints por codigo HTTP      |
| `top_endpoints`            | Top 25 endpoints mas solicitados           |
| `analisis_horario`         | Distribucion horaria                       |
| `endpoints_lentos`         | Top endpoints mas lentos                   |
| `detalle_endpoints`        | Detalle completo con metricas por endpoint |

---

## ?? Linter automatico

Este proyecto puede validarse automaticamente mediante **GitHub Actions**, para asegurar que todos los scripts cumplan buenas practicas de sintaxis y estilo.

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
      - name: Ejecutar analisis
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
      - name: Revisar codigo Python
        run: flake8 --max-line-length=120 --exclude=.git,__pycache__,venv
```

?? Esto permite que cada vez que hagas **push** o **pull request**, GitHub revise automaticamente:
- Scripts **Bash** (`.sh`) con **ShellCheck**
- Scripts **PowerShell** (`.ps1`) con **PSScriptAnalyzer**
- Scripts **Python** (`.py`) con **Flake8**

Si encuentra errores, los muestra en la pestana **Actions** del repositorio.

---

## ?? Autor y version

**Autor:** Angel Estrada  
**Version:** 1.0.0  
**Licencia:** MIT  
**Repositorio:** [https://github.com/angelestradamx/ScriptsTools](https://github.com/angelestradamx/ScriptsTools)  
**Ultima actualizacion:** Octubre 2025