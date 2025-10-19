# ?? Analizador de Access Log (Nginx / Apache)

Analizador avanzado de archivos **access.log** con estad¨ªsticas completas, comparaci¨®n entre tr¨¢fico **Cloudflare** y **Directo**, e integraci¨®n con exportaci¨®n a **Excel** o **CSV**.  
Ideal para analizar el rendimiento de APIs, servidores web o proxies Nginx en producci¨®n.

---

## ?? ¨ªndice

- [Descripci¨®n](#descripci¨®n)
- [Caracter¨ªsticas principales](#caracter¨ªsticas-principales)
- [Requisitos](#requisitos)
- [Configuraci¨®n requerida en Nginx](#configuraci¨®n-requerida-en-nginx)
- [Uso b¨¢sico](#uso-b¨¢sico)
- [Ejemplos de uso](#ejemplos-de-uso)
- [Ejemplo de salida](#ejemplo-de-salida)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Exportaciones](#exportaciones)
- [Linter autom¨¢tico](#linter-autom¨¢tico)
- [Autor y versi¨®n](#autor-y-versi¨®n)

---

## ?? Descripci¨®n

El script `web.analyze.access_log.py` analiza archivos **access.log** (Nginx o Apache) y genera un reporte detallado con m¨¦tricas de rendimiento, errores, tiempos de respuesta y comparativas de tr¨¢fico.  
Permite exportar la informaci¨®n a Excel o CSV con diferentes hojas tem¨¢ticas (general, por c¨®digo, por hora, etc.).

---

## ?? Caracter¨ªsticas principales

- ?? **Estad¨ªsticas por c¨®digo HTTP** (200, 400, 499, 500, etc.)
- ?? **An¨¢lisis por hora** (requests lentos, errores, distribuci¨®n)
- ?? **Comparativa Cloudflare vs Directos**
- ?? **Detecci¨®n de endpoints problem¨¢ticos**
- ?? **Exportaci¨®n directa a Excel o CSV**
- ?? **Umbral din¨¢mico de lentitud (`--threshold`)**
- ?? **Sugerencia autom¨¢tica de umbral** seg¨²n percentiles
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

## ?? Configuraci¨®n requerida en Nginx

Para que el analizador funcione correctamente, es **necesario configurar un formato de log personalizado** en tu `nginx.conf` (o en el archivo del sitio) que incluya los campos usados por el script: `status`, `rt`, `urt`, `cf-ray`, `realip`, `request`, `ua`, etc.

Agrega o modifica la secci¨®n del log as¨ª:

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

> ?? **Consejo:** Reinicia Nginx despu¨¦s de aplicar los cambios:
>
> ```bash
> sudo nginx -t && sudo systemctl reload nginx
> ```

Este formato genera los campos que el script utiliza para identificar:
- El tiempo de respuesta (`rt`)
- El tiempo del upstream (`urt`)
- El origen del tr¨¢fico (Cloudflare o directo)
- Las cabeceras de usuario y URL completas

---

## ?? Uso b¨¢sico

Ejecuta el analizador con un archivo de log:

```bash
python3 web.analyze.access_log.py access.log
```

### Par¨¢metros disponibles

| Par¨¢metro            | Descripci¨®n                                                              |
|----------------------|--------------------------------------------------------------------------|
| `--threshold` o `-t` | Define el umbral de lentitud en segundos (por defecto 1.0s).             |
| `--export` o `-e`    | Exporta resultados (`excel`, `csv`, `both`).                             |
| `--output` o `-o`    | Nombre del archivo de salida. Por defecto: `<nombre_log>_analysis.xlsx`. |

---

## ?? Ejemplos de uso

### ?? 1. An¨¢lisis est¨¢ndar

```bash
python3 web.analyze.access_log.py /var/log/nginx/access.log
```

### ?? 2. An¨¢lisis con exportaci¨®n a Excel

```bash
python3 web.analyze.access_log.py access.log --export excel
```

### ?? 3. An¨¢lisis con threshold personalizado y exportaci¨®n doble

```bash
python3 web.analyze.access_log.py access.log --threshold 2 --export both
```

---

## ?? Ejemplo de salida

```
?? ESTAD¨ªSTICAS GENERALES COMPLETAS
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
©¸©¤©¤ web/
    ©¸©¤©¤ analyze.access_log/
        ©À©¤©¤ web.analyze.access_log.py  # Script principal
        ©À©¤©¤ requirements.txt           # Dependencias necesarias
        ©¸©¤©¤ README.md                 # Documentaci¨®n del proyecto
```

---

## ?? Exportaciones

El script puede generar m¨²ltiples hojas o archivos CSV, seg¨²n el tipo de exportaci¨®n seleccionada:

| Hoja / CSV                 | Contenido                                  |
|----------------------------|--------------------------------------------|
| `procesamiento_completado` | L¨ªneas procesadas, rango de fechas         |
| `estadisticas_generales`   | Totales, percentiles, promedios            |
| `distribucion_http`        | Resumen por c¨®digo HTTP                    |
| `cloudflare_vs_directo`    | Comparativa entre Cloudflare y Directo     |
| `endpoints_por_codigo`     | Principales endpoints por c¨®digo HTTP      |
| `top_endpoints`            | Top 25 endpoints m¨¢s solicitados           |
| `analisis_horario`         | Distribuci¨®n horaria                       |
| `endpoints_lentos`         | Top endpoints m¨¢s lentos                   |
| `detalle_endpoints`        | Detalle completo con m¨¦tricas por endpoint |

---

## ?? Linter autom¨¢tico

Este proyecto puede validarse autom¨¢ticamente mediante **GitHub Actions**, para asegurar que todos los scripts cumplan buenas pr¨¢cticas de sintaxis y estilo.

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
      - name: Ejecutar an¨¢lisis
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
      - name: Revisar c¨®digo Python
        run: flake8 --max-line-length=120 --exclude=.git,__pycache__,venv
```

?? Esto permite que cada vez que hagas **push** o **pull request**, GitHub revise autom¨¢ticamente:
- Scripts **Bash** (`.sh`) con **ShellCheck**
- Scripts **PowerShell** (`.ps1`) con **PSScriptAnalyzer**
- Scripts **Python** (`.py`) con **Flake8**

Si encuentra errores, los muestra en la pesta?a **Actions** del repositorio.

---

## ?? Autor y versi¨®n

**Autor:** ¨¢ngel Estrada  
**Versi¨®n:** 1.0.0  
**Licencia:** MIT  
**Repositorio:** [https://github.com/angelestradamx/ScriptsTools](https://github.com/angelestradamx/ScriptsTools)  
**¨²ltima actualizaci¨®n:** Octubre 2025