# 🌐 Scripts Web — Configuración y análisis de servicios web

Colección de scripts y utilidades relacionados con servidores web, proxies inversos, certificados SSL, y análisis de tráfico mediante Cloudflare y Nginx.

---

## 📚 Submódulos disponibles

| Módulo                    | Descripción                                                    | Ruta                                  |
|---------------------------|----------------------------------------------------------------|---------------------------------------|
| 🧩 **analyze.access_log** | Analizador de logs de Nginx/Apache con exportación a Excel/CSV | [analyze.access_log/](analyze.access_log) |
| ⚙️ **nginx**             | Configuración avanzada de Nginx (reverse proxy, caching, SSL, logs) | [nginx/](nginx)                       |
| 🔐 **certificates**      | Scripts para automatizar emisión y renovación de certificados SSL | [certificates/](certificates)         |

---

## 🧠 Objetivo del módulo

Centralizar herramientas relacionadas con la **administración web**:  
- Monitorear tráfico HTTP/HTTPS  
- Analizar rendimiento de endpoints  
- Automatizar configuración de servidores web  
- Gestionar certificados de seguridad  

---

## ⚙️ Ejemplo de uso

Ejecutar el analizador de logs:

```bash
cd analyze.access_log
python3 web.analyze.access_log.py /var/log/nginx/access.log --export excel
```

---

## 🧩 Recomendaciones

- Revisa los `README.md` de cada subcarpeta para instrucciones detalladas.
- Asegúrate de tener permisos de lectura sobre los logs (`/var/log/nginx/access.log`).
- Puedes automatizar su ejecución diaria con `cron` or GitHub Actions.

---

## 👤 Mantenimiento

**Autor:** Ángel Estrada  
**Versión:** 1.0.0  
**Licencia:** MIT  
**Última actualización:** Octubre 2025