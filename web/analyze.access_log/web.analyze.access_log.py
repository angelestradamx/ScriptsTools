#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis completo de access.log con exportación a Excel/CSV y a pantalla 
"""

import re
import os
import sys
import csv
import pandas as pd
import argparse
from collections import defaultdict
import statistics
from datetime import datetime


class ComprehensiveLogAnalyzer:
    def __init__(self, log_file, threshold=None):
        self.log_file = log_file
        # Si no se especifica threshold, calcular automáticamente
        self.threshold = threshold if threshold is not None else self.suggest_threshold()
        self.endpoints = defaultdict(list)
        self.hourly_stats = defaultdict(lambda: defaultdict(int))
        self.status_codes = defaultdict(int)
        self.cloudflare_stats = {'cloudflare': 0, 'direct': 0}
        self.http_requests_by_code = defaultdict(lambda: defaultdict(int))
        self.export_data = {}
        self.first_timestamp = None
        self.last_timestamp = None

    def suggest_threshold(self):
        """Sugiere un threshold basado en percentiles comunes"""
        # Para logs de aplicaciones web:
        # - < 100ms: Excelente
        # - 100-500ms: Bueno
        # - 500ms-1s: Aceptable
        # - > 1s: Lento
        # - > 3s: Muy lento
        return 1.0  # 1 segundo como valor por defecto

    def parse_log(self):
        """Parse el archivo de log"""
        if not os.path.exists(self.log_file):
            print(f"❌ Error: Archivo {self.log_file} no encontrado")
            return False

        print(f"🔍 Analizando: {self.log_file}")
        print(f"⏱️  Umbral para lento: {self.threshold}s")
        print(f"{'='*80}")

        total_lines = 0
        parsed_lines = 0

        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                total_lines += 1
                if self.parse_line(line):
                    parsed_lines += 1

                if total_lines % 10000 == 0:
                    print(f"📖 Líneas procesadas: {total_lines:,}...")

        print(f"\n{'='*80}")
        print("✅ PROCESAMIENTO COMPLETADO")
        print(f"{'='*80}")
        print(f"📊 Líneas totales: {total_lines:,}")
        print(f"✅ Líneas parseadas: {parsed_lines:,}")
        print(f"🌐 Endpoints únicos: {len(self.endpoints):,}")

        # Mostrar rango de fechas
        self.show_date_range()

        return True

    def parse_line(self, line):
        """Parse una línea individual del log"""
        try:
            # Extraer información básica
            method, url, status, response_time, timestamp, is_cloudflare = self.extract_data(
                line)
            if not all([method, url, status is not None]):
                return False

            # Actualizar primera y última timestamp
            if timestamp:
                if self.first_timestamp is None:
                    self.first_timestamp = timestamp
                self.last_timestamp = timestamp

            clean_url = url.split('?')[0]
            endpoint = f"{method} {clean_url}"

            # Extraer hora CORREGIDO
            hour = "unknown"
            if timestamp and ":" in timestamp:
                try:
                    # Formato: 25/Sep/2025:00:00:10 -0600
                    # Extraer la hora correctamente
                    hour_part = timestamp.split(':')[1]
                    hour = f"{int(hour_part):02d}:00"
                except Exception as e:
                    hour = "unknown"

            self.endpoints[endpoint].append({
                'status': status,
                'response_time': response_time,
                'hour': hour,
                'timestamp': timestamp,
                'url': clean_url,
                'method': method,
                'is_cloudflare': is_cloudflare
            })

            # Estadísticas Cloudflare vs Directo
            if is_cloudflare:
                self.cloudflare_stats['cloudflare'] += 1
            else:
                self.cloudflare_stats['direct'] += 1

            # Estadísticas por hora
            if hour != "unknown":
                self.hourly_stats[hour]['total'] += 1
                if response_time > self.threshold:
                    self.hourly_stats[hour]['slow'] += 1
                if status == 499:
                    self.hourly_stats[hour]['error_499'] += 1
                if is_cloudflare:
                    self.hourly_stats[hour]['cloudflare'] += 1
                else:
                    self.hourly_stats[hour]['direct'] += 1

            # Estadísticas por código de estado
            self.status_codes[status] += 1

            # Estadísticas por código HTTP y URL
            self.http_requests_by_code[status][endpoint] += 1

            return True

        except Exception as e:
            print(f"⚠️  Error parsing line: {e}")
            return False

    def extract_data(self, line):
        """Extrae datos de una línea de log"""
        method, url, status, response_time, timestamp, is_cloudflare = None, None, None, 0.0, None, False

        # Detectar Cloudflare (presencia de "cf-node")
        is_cloudflare = self._is_cloudflare_ip(line)

        # Timestamp completo
        ts_match = re.search(r'(\d+/\w+/\d+:\d+:\d+:\d+ -\d+)', line)
        if ts_match:
            timestamp = ts_match.group(1)

        # Método y URL
        quote_match = re.search(r'"(\w+) (\S+)', line)
        if quote_match:
            method, url = quote_match.groups()

        # Status
        status_match = re.search(r'status=(\d+)', line)
        if status_match:
            status = int(status_match.group(1))

        # Tiempo de respuesta
        rt_match = re.search(r'rt=(\d+\.\d+)', line)
        if rt_match:
            response_time = float(rt_match.group(1))

        return method, url, status, response_time, timestamp, is_cloudflare

    def _is_cloudflare_ip(self, line: str) -> bool:
        """Detecta si la IP pertenece a Cloudflare, verificando etiqueta o rango IP"""
        import re, ipaddress, requests

        # Detección rápida por texto cf-node
        if "(cf-node)" in line or "cf-node" in line:
            return True

        # Buscar IP inicial
        ip_match = re.search(r"^(\S+)", line)
        if not ip_match:
            return False
        ip = ip_match.group(1)

        cf_ranges = [
            "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22",
            "103.31.4.0/22", "141.101.64.0/18", "108.162.192.0/18",
            "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22",
            "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
            "172.64.0.0/13", "131.0.72.0/22"
        ]

        try:
            ipv4 = requests.get("https://www.cloudflare.com/ips-v4", timeout=5).text.splitlines()
            ipv6 = requests.get("https://www.cloudflare.com/ips-v6", timeout=5).text.splitlines()
            cf_ranges = [r.strip() for r in (ipv4 + ipv6) if r.strip()]
        except Exception:
            pass

        try:
            ip_obj = ipaddress.ip_address(ip)
            return any(ip_obj in ipaddress.ip_network(r, strict=False) for r in cf_ranges)
        except Exception:
            return False

    def show_date_range(self):
        """Muestra el rango de fechas del log"""
        if self.first_timestamp and self.last_timestamp:
            print(f"📅 Rango de fechas del log:")
            print(
                f"   🟢 Inicio: {self.format_timestamp(self.first_timestamp)}")
            print(f"   🔴 Fin:    {self.format_timestamp(self.last_timestamp)}")

            # Calcular duración
            try:
                start_dt = self.parse_timestamp(self.first_timestamp)
                end_dt = self.parse_timestamp(self.last_timestamp)
                duration = end_dt - start_dt
                print(f"   ⏳ Duración: {self.format_duration(duration)}")
            except BaseException:
                print(f"   ⏳ Duración: No se pudo calcular")
        else:
            print(f"📅 No se pudieron extraer las fechas del log")

    def parse_timestamp(self, timestamp_str):
        """Convierte string de timestamp a datetime object"""
        try:
            # Formato: 25/Sep/2025:00:00:10 -0600
            date_part = timestamp_str.split(' ')[0]  # "25/Sep/2025:00:00:10"
            return datetime.strptime(date_part, '%d/%b/%Y:%H:%M:%S')
        except Exception as e:
            return None

    def format_timestamp(self, timestamp_str):
        """Formatea el timestamp para mejor legibilidad"""
        try:
            dt = self.parse_timestamp(timestamp_str)
            if dt:
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return timestamp_str
        except BaseException:
            return timestamp_str

    def format_duration(self, duration):
        """Formatea la duración en formato legible"""
        days = duration.days
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days} día{'s' if days > 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hora{'s' if hours > 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minuto{'s' if minutes > 1 else ''}")
        if seconds > 0 or not parts:
            parts.append(f"{seconds} segundo{'s' if seconds > 1 else ''}")

        return ", ".join(parts)

    def get_http_code_description(self, code):
        """Devuelve la descripción del código HTTP"""
        descriptions = {
            200: "OK - Successful",
            201: "Created",
            202: "Accepted",
            204: "No Content",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            499: "Client Closed Request",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        return descriptions.get(code, "")

    def generate_comprehensive_report(self):
        """Genera reporte completo en pantalla"""
        if not self.endpoints:
            print("❌ No hay datos para generar reporte")
            return

        all_requests = []
        for requests in self.endpoints.values():
            all_requests.extend(requests)

        total_requests = len(all_requests)
        if total_requests == 0:
            print("❌ No hay requests para analizar")
            return

        # Calcular percentiles para sugerir threshold si no se especificó
        if hasattr(self, 'user_threshold') and not self.user_threshold:
            self.suggest_better_threshold(all_requests)

        slow_requests = [
            r for r in all_requests if r['response_time'] > self.threshold]
        error_499 = [r for r in all_requests if r['status'] == 499]
        cloudflare_requests = [r for r in all_requests if r['is_cloudflare']]
        direct_requests = [r for r in all_requests if not r['is_cloudflare']]

        # ESTADÍSTICAS GENERALES MEJORADAS
        print(f"\n{'='*80}")
        print("📈 ESTADÍSTICAS GENERALES COMPLETAS")
        print(f"{'='*80}")
        print(f"📊 Total de requests: {total_requests:,}")
        print(
            f"🐌 Requests lentos (> {self.threshold}s): {len(slow_requests):,} ({len(slow_requests)/total_requests*100:.1f}%)")
        print(
            f"❌ Errores 499: {len(error_499):,} ({len(error_499)/total_requests*100:.1f}%)")
        print(
            f"☁️  Requests Cloudflare: {len(cloudflare_requests):,} ({len(cloudflare_requests)/total_requests*100:.1f}%)")
        print(
            f"🔗 Requests Directos: {len(direct_requests):,} ({len(direct_requests)/total_requests*100:.1f}%)")

        # Tiempos promedios
        if all_requests:
            response_times = [r['response_time'] for r in all_requests]
            avg_time_total = statistics.mean(response_times)
            p95 = statistics.quantiles(response_times, n=20)[
                18]  # Percentil 95
            p99 = statistics.quantiles(response_times, n=100)[
                98]  # Percentil 99

            avg_time_cf = statistics.mean(
                [r['response_time'] for r in cloudflare_requests]) if cloudflare_requests else 0
            avg_time_direct = statistics.mean(
                [r['response_time'] for r in direct_requests]) if direct_requests else 0

            print(f"⏱️  Tiempo promedio total: {avg_time_total:.3f}s")
            print(f"📊 Percentil 95: {p95:.3f}s")
            print(f"📊 Percentil 99: {p99:.3f}s")
            print(f"⏱️  Tiempo promedio Cloudflare: {avg_time_cf:.3f}s")
            print(f"⏱️  Tiempo promedio Directo: {avg_time_direct:.3f}s")

        if error_499:
            avg_499 = statistics.mean([r['response_time'] for r in error_499])
            max_499 = max([r['response_time'] for r in error_499])
            print(f"💥 Tiempo promedio en 499: {avg_499:.3f}s")
            print(f"💥 Tiempo máximo en 499: {max_499:.3f}s")

        # 1. DISTRIBUCIÓN DETALLADA POR CÓDIGOS HTTP
        self.print_http_status_distribution()

        # 2. TABLA CLOUDFLARE VS DIRECTOS
        self.print_cloudflare_vs_direct()

        # 3. ENDPOINTS POR CÓDIGO HTTP (200, 202, 400, etc.)
        self.print_endpoints_by_http_code()

        # 4. TABLA PRINCIPAL - ENDPOINTS INDIVIDUALES
        self.print_endpoints_table()

        # 5. ANÁLISIS POR HORA
        self.print_hourly_analysis()

        # 6. ENDPOINTS MÁS LENTOS
        self.print_slowest_endpoints()

    def suggest_better_threshold(self, all_requests):
        """Sugiere un threshold mejor basado en percentiles"""
        if not all_requests:
            return

        response_times = [r['response_time'] for r in all_requests]

        try:
            # Calcular percentiles
            p75 = statistics.quantiles(response_times, n=4)[2]  # Percentil 75
            p90 = statistics.quantiles(response_times, n=10)[8]  # Percentil 90

            # Sugerir threshold basado en percentil 90 + margen
            suggested = min(p90 * 1.5, 3.0)  # Máximo 3 segundos
            suggested = max(suggested, 0.5)   # Mínimo 0.5 segundos

            print(
                f"💡 Threshold sugerido basado en percentiles: {suggested:.2f}s")
            print(f"   (Percentil 75: {p75:.3f}s, Percentil 90: {p90:.3f}s)")

        except BaseException:
            # Fallback si no se pueden calcular percentiles
            avg_time = statistics.mean(response_times)
            suggested = min(avg_time * 2, 3.0)
            suggested = max(suggested, 0.5)
            print(f"💡 Threshold sugerido basado en promedio: {suggested:.2f}s")

    def print_http_status_distribution(self):
        """Distribución detallada por códigos HTTP"""
        print(f"\n{'='*80}")
        print("🔢 DISTRIBUCIÓN DETALLADA POR CÓDIGOS HTTP")
        print(f"{'='*80}")
        print(
            f"{'CÓDIGO':<8} {'TOTAL':>8} {'%':>6} {'CLOUDFLARE':>10} {'DIRECTO':>8} {'AVG(s)':>8}")
        print(f"{'-'*80}")

        total_requests = sum(self.status_codes.values())
        if total_requests == 0:
            print("No hay datos para mostrar")
            return

        for code in sorted(self.status_codes.keys()):
            count = self.status_codes[code]
            percentage = (count / total_requests) * 100

            # Calcular distribución Cloudflare vs Directo para este código
            cf_count = 0
            direct_count = 0
            avg_time = 0.0

            requests_this_code = []
            for endpoint_requests in self.endpoints.values():
                for req in endpoint_requests:
                    if req['status'] == code:
                        requests_this_code.append(req)
                        if req['is_cloudflare']:
                            cf_count += 1
                        else:
                            direct_count += 1

            if requests_this_code:
                avg_time = statistics.mean(
                    [r['response_time'] for r in requests_this_code])

            # Descripción del código HTTP
            code_desc = self.get_http_code_description(code)

            print(
                f"{code:<8} {count:>8} {percentage:>5.1f}% {cf_count:>10} {direct_count:>8} {avg_time:>7.3f}s")
            if code_desc:
                print(f"         {code_desc}")

    def print_cloudflare_vs_direct(self):
        """Tabla comparativa Cloudflare vs Directos"""
        print(f"\n{'='*100}")
        print("☁️ vs 🔗 COMPARATIVA CLOUDFLARE vs DIRECTOS")
        print(f"{'='*100}")
        print(f"{'MÉTRICA':<25} {'CLOUDFLARE':>12} {'DIRECTO':>12} {'DIFERENCIA':>12} {'%CF':>8} {'%DIR':>8}")
        print(f"{'-'*100}")

        cf_total = self.cloudflare_stats['cloudflare']
        direct_total = self.cloudflare_stats['direct']
        total = cf_total + direct_total

        if total == 0:
            print("No hay datos para mostrar")
            return

        # Requests totales
        pct_cf = (cf_total / total) * 100
        pct_direct = (direct_total / total) * 100
        diff = cf_total - direct_total
        print(f"{'Total Requests':<25} {cf_total:>12,} {direct_total:>12,} {diff:>12,} {pct_cf:>7.1f}% {pct_direct:>7.1f}%")

        # Requests lentos
        cf_slow = sum(1 for reqs in self.endpoints.values() for req in reqs
                      if req['is_cloudflare'] and req['response_time'] > self.threshold)
        direct_slow = sum(1 for reqs in self.endpoints.values() for req in reqs
                          if not req['is_cloudflare'] and req['response_time'] > self.threshold)

        pct_cf_slow = (cf_slow / cf_total) * 100 if cf_total > 0 else 0
        pct_direct_slow = (direct_slow / direct_total) * \
        100 if direct_total > 0 else 0
        diff_slow = cf_slow - direct_slow

        print(f"{'Requests Lentos':<25} {cf_slow:>12,} {direct_slow:>12,} {diff_slow:>12,} {pct_cf_slow:>7.1f}% {pct_direct_slow:>7.1f}%")

        # Errores 499
        cf_499 = sum(1 for reqs in self.endpoints.values() for req in reqs
                     if req['is_cloudflare'] and req['status'] == 499)
        direct_499 = sum(1 for reqs in self.endpoints.values() for req in reqs
                         if not req['is_cloudflare'] and req['status'] == 499)

        pct_cf_499 = (cf_499 / cf_total) * 100 if cf_total > 0 else 0
        pct_direct_499 = (direct_499 / direct_total) * \
        100 if direct_total > 0 else 0
        diff_499 = cf_499 - direct_499

        print(f"{'Errores 499':<25} {cf_499:>12,} {direct_499:>12,} {diff_499:>12,} {pct_cf_499:>7.1f}% {pct_direct_499:>7.1f}%")

        # Tiempos promedio
        cf_times = [req['response_time'] for reqs in self.endpoints.values()
                    for req in reqs if req['is_cloudflare']]
        direct_times = [req['response_time'] for reqs in self.endpoints.values(
        ) for req in reqs if not req['is_cloudflare']]

        if cf_times and direct_times:
            avg_cf = statistics.mean(cf_times)
            avg_direct = statistics.mean(direct_times)
            diff_avg = avg_cf - avg_direct

            print(
                f"{'Tiempo Promedio':<25} {avg_cf:>11.3f}s {avg_direct:>11.3f}s {diff_avg:>11.3f}s {'-':>8} {'-':>8}")

    def print_endpoints_by_http_code(self):
        """Endpoints por código HTTP específico"""
        important_codes = [200, 202, 400, 404, 499, 500]

        for code in important_codes:
            if code in self.http_requests_by_code:
                endpoints = self.http_requests_by_code[code]
                total_requests = sum(endpoints.values())

                if total_requests > 0:
                    print(f"\n{'='*80}")
                    print(
                        f"📊 ENDPOINTS CON CÓDIGO HTTP {code} - {self.get_http_code_description(code)}")
                    print(f"{'='*80}")
                    print(
                        f"{'ENDPOINT':<60} {'REQUESTS':>8} {'%':>6} {'AVG(s)':>7}")
                    print(f"{'-'*80}")

                    # Calcular tiempos promedio para cada endpoint
                    endpoint_stats = []
                    for endpoint, count in endpoints.items():
                        # Encontrar requests específicos para este endpoint y
                        # código
                        endpoint_requests = [
                            r for r in self.endpoints[endpoint] if r['status'] == code]
                        if endpoint_requests:
                            avg_time = statistics.mean(
                                [r['response_time'] for r in endpoint_requests])
                            percentage = (count / total_requests) * 100
                            endpoint_stats.append(
                                (endpoint, count, percentage, avg_time))

                    # Ordenar por cantidad de requests
                    endpoint_stats.sort(key=lambda x: x[1], reverse=True)

                    # Top 15
                    for endpoint, count, pct, avg_time in endpoint_stats[:15]:
                        display_ep = endpoint[:58] + \
                            ".." if len(endpoint) > 60 else endpoint
                        print(
                            f"{display_ep:<60} {count:>8} {pct:>5.1f}% {avg_time:>6.2f}s")

    def print_endpoints_table(self):
        """Tabla de endpoints individuales"""
        print(f"\n{'='*120}")
        print("🏆 TOP 25 ENDPOINTS INDIVIDUALES MÁS SOLICITADOS")
        print(f"{'='*120}")
        print(f"{'ENDPOINT':<60} {'TOTAL':>6} {'CF':>4} {'DIR':>4} {'AVG(s)':>7} {'499':>4} {'>1s':>5} {'%LENTO':>7}")
        print(f"{'-'*120}")

        endpoint_stats = []
        for endpoint, requests in self.endpoints.items():
            times = [r['response_time'] for r in requests]
            cf_count = sum(1 for r in requests if r['is_cloudflare'])
            direct_count = len(requests) - cf_count

            endpoint_stats.append({
                'endpoint': endpoint,
                'total': len(requests),
                'cf_count': cf_count,
                'direct_count': direct_count,
                'avg_time': statistics.mean(times) if times else 0.0,
                'errors_499': sum(1 for r in requests if r['status'] == 499),
                'slow_count': sum(1 for r in requests if r['response_time'] > self.threshold)
            })

        endpoint_stats.sort(key=lambda x: x['total'], reverse=True)

        for ep in endpoint_stats[:25]:
            pct_slow = (ep['slow_count'] / ep['total']) * \
                100 if ep['total'] > 0 else 0
            display_ep = ep['endpoint'][:58] + \
                ".." if len(ep['endpoint']) > 60 else ep['endpoint']

            print(f"{display_ep:<60} {ep['total']:>6} {ep['cf_count']:>4} {ep['direct_count']:>4} "
                  f"{ep['avg_time']:>6.2f}s {ep['errors_499']:>4} {ep['slow_count']:>5} {pct_slow:>6.1f}%")

    def print_hourly_analysis(self):
        """Análisis por hora"""
        if not self.hourly_stats:
            print("\n⚠️  No se pudieron extraer datos horarios")
            return

        print(f"\n{'='*100}")
        print("🕐 DISTRIBUCIÓN POR HORARIO")
        print(f"{'='*100}")
        print(
            f"{'HORA':<6} {'TOTAL':>8} {'CF':>6} {'DIR':>6} {'LENTOS':>6} {'499':>5} {'AVG(s)':>7}")
        print(f"{'-'*100}")

        # Calcular tiempos promedio por hora
        hourly_times = defaultdict(list)
        for endpoint, requests in self.endpoints.items():
            for r in requests:
                if r['hour'] != "unknown":
                    hourly_times[r['hour']].append(r['response_time'])

        for hour in sorted(self.hourly_stats.keys()):
            stats = self.hourly_stats[hour]
            total = stats['total']
            cf = stats.get('cloudflare', 0)
            direct = stats.get('direct', 0)
            slow = stats.get('slow', 0)
            errors_499 = stats.get('error_499', 0)
            avg_time = statistics.mean(
                hourly_times[hour]) if hourly_times[hour] else 0

            print(
                f"{hour:<6} {total:>8} {cf:>6} {direct:>6} {slow:>6} {errors_499:>5} {avg_time:>6.2f}s")

    def print_slowest_endpoints(self):
        """Endpoints más lentos"""
        print(f"\n{'='*100}")
        print("🐌 TOP 15 ENDPOINTS MÁS LENTOS (por tiempo promedio)")
        print(f"{'='*100}")
        print(
            f"{'ENDPOINT':<60} {'TOTAL':>6} {'AVG(s)':>7} {'MAX(s)':>7} {'>1s':>6} {'499':>4}")
        print(f"{'-'*100}")

        endpoint_stats = []
        for endpoint, requests in self.endpoints.items():
            if len(requests) >= 10:  # Mínimo 10 requests
                times = [r['response_time'] for r in requests]
                if times:  # Verificar que hay tiempos
                    endpoint_stats.append({
                        'endpoint': endpoint,
                        'total': len(requests),
                        'avg_time': statistics.mean(times),
                        'max_time': max(times),
                        'slow_count': sum(1 for r in requests if r['response_time'] > self.threshold),
                        'errors_499': sum(1 for r in requests if r['status'] == 499)
                    })

        endpoint_stats.sort(key=lambda x: x['avg_time'], reverse=True)

        for ep in endpoint_stats[:15]:
            display_ep = ep['endpoint'][:58] + \
                ".." if len(ep['endpoint']) > 60 else ep['endpoint']
            print(f"{display_ep:<60} {ep['total']:>6} {ep['avg_time']:>6.2f}s "
                  f"{ep['max_time']:>6.2f}s {ep['slow_count']:>6} {ep['errors_499']:>4}")

    # MÉTODOS DE EXPORTACIÓN (se mantienen igual)
    def prepare_export_data(self):
        """Prepara todos los datos para exportación"""
        self.export_data = {
            'procesamiento_completado': self._get_processing_stats(),
            'estadisticas_generales': self._get_general_stats(),
            'distribucion_http': self._get_http_distribution(),
            'cloudflare_vs_directo': self._get_cloudflare_stats(),
            'endpoints_por_codigo': self._get_endpoints_by_code(),
            'top_endpoints': self._get_top_endpoints(),
            'analisis_horario': self._get_hourly_analysis(),
            'endpoints_lentos': self._get_slow_endpoints(),
            'detalle_endpoints': self._get_detailed_endpoints()
        }

    def _get_general_stats(self):
        """Prepara estadísticas generales para exportación"""
        all_requests = []
        for requests in self.endpoints.values():
            all_requests.extend(requests)

        total_requests = len(all_requests)
        if total_requests == 0:
            return []

        slow_requests = [
            r for r in all_requests if r['response_time'] > self.threshold]
        error_499 = [r for r in all_requests if r['status'] == 499]
        cloudflare_requests = [r for r in all_requests if r['is_cloudflare']]
        direct_requests = [r for r in all_requests if not r['is_cloudflare']]

        # Calcular tiempos promedio
        response_times = [r['response_time'] for r in all_requests]
        avg_time_total = statistics.mean(
            response_times) if response_times else 0
        p95 = statistics.quantiles(response_times, n=20)[
            18] if len(response_times) >= 20 else 0
        p99 = statistics.quantiles(response_times, n=100)[
            98] if len(response_times) >= 100 else 0

        avg_time_cf = statistics.mean(
            [r['response_time'] for r in cloudflare_requests]) if cloudflare_requests else 0
        avg_time_direct = statistics.mean(
            [r['response_time'] for r in direct_requests]) if direct_requests else 0

        # Añadir estadísticas de procesamiento
        return [
            {
                'Metrica': 'Total Requests',
                'Valor': total_requests,
                'Porcentaje': '100%'
            }, {
                'Metrica': 'Requests Lentos',
                'Valor': len(slow_requests),
                'Porcentaje': f"{(len(slow_requests)/total_requests*100):.1f}%"
            }, {
                'Metrica': 'Errores 499',
                'Valor': len(error_499),
                'Porcentaje': f"{(len(error_499)/total_requests*100):.1f}%"
            }, {
                'Metrica': 'Cloudflare Requests',
                'Valor': len(cloudflare_requests),
                'Porcentaje': f"{(len(cloudflare_requests)/total_requests*100):.1f}%"
            }, {
                'Metrica': 'Direct Requests',
                'Valor': len(direct_requests),
                'Porcentaje': f"{(len(direct_requests)/total_requests*100):.1f}%"
            }, {
                'Metrica': 'Tiempo Promedio Total',
                'Valor': f"{avg_time_total:.3f}s",
                'Porcentaje': '-'
            }, {
                'Metrica': 'Percentil 95',
                'Valor': f"{p95:.3f}s",
                'Porcentaje': '-'
            }, {
                'Metrica': 'Percentil 99',
                'Valor': f"{p99:.3f}s",
                'Porcentaje': '-'
            }, {
                'Metrica': 'Tiempo Promedio Cloudflare',
                'Valor': f"{avg_time_cf:.3f}s",
                'Porcentaje': '-'
            }, {
                'Metrica': 'Tiempo Promedio Directo',
                'Valor': f"{avg_time_direct:.3f}s",
                'Porcentaje': '-'
            }
        ]

    def _get_processing_stats(self):
        """Prepara estadísticas de procesamiento para exportación"""
        all_requests = []
        for requests in self.endpoints.values():
            all_requests.extend(requests)

        total_lines = 0
        # Contar líneas totales en el archivo
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                total_lines = sum(1 for _ in f)

        parsed_lines = len(all_requests)

        return [
            {
                'Metrica': 'Lineas totales en archivo',
                'Valor': total_lines,
                'Porcentaje': '100%'
            }, {
                'Metrica': 'Lineas parseadas correctamente',
                'Valor': parsed_lines,
                'Porcentaje': f"{(parsed_lines/total_lines*100):.1f}%" if total_lines > 0 else "0%"
            }, {
                'Metrica': 'Endpoints unicos encontrados',
                'Valor': len(self.endpoints),
                'Porcentaje': '-'
            }, {
                'Metrica': 'Umbral para requests lentos',
                'Valor': f"{self.threshold}s",
                'Porcentaje': '-'
            }, {
                'Metrica': 'Rango de fechas - Inicio',
                'Valor': self.format_timestamp(self.first_timestamp) if self.first_timestamp else 'No disponible',
                'Porcentaje': '-'
            }, {
                'Metrica': 'Rango de fechas - Fin',
                'Valor': self.format_timestamp(self.last_timestamp) if self.last_timestamp else 'No disponible',
                'Porcentaje': '-'
            }
        ]

    def _get_http_distribution(self):
        """Prepara distribución HTTP para exportación"""
        data = []
        total_requests = sum(self.status_codes.values())

        if total_requests == 0:
            return data

        for code in sorted(self.status_codes.keys()):
            count = self.status_codes[code]
            percentage = (count / total_requests) * 100

            data.append({
                'Codigo_HTTP': code,
                'Descripcion': self.get_http_code_description(code),
                'Total_Requests': count,
                'Porcentaje': f"{percentage:.1f}%",
                'Porcentaje_Numero': percentage
            })

        return data

    def _get_cloudflare_stats(self):
        """Prepara stats Cloudflare vs Directo para exportación"""
        cf_total = self.cloudflare_stats['cloudflare']
        direct_total = self.cloudflare_stats['direct']
        total = cf_total + direct_total

        if total == 0:
            return []

        return [{
            'Metrica': 'Total Requests',
            'Cloudflare': cf_total,
            'Directo': direct_total,
            'Diferencia': cf_total - direct_total,
            'Porcentaje_CF': f"{(cf_total/total*100):.1f}%",
            'Porcentaje_DIR': f"{(direct_total/total*100):.1f}%"
        }]

    def _get_endpoints_by_code(self):
        """Prepara endpoints por código HTTP para exportación"""
        data = []
        important_codes = [200, 202, 400, 404, 499, 500]

        for code in important_codes:
            if code in self.http_requests_by_code:
                for endpoint, count in self.http_requests_by_code[code].items(
                ):
                    # Calcular tiempo promedio para este endpoint y código
                    endpoint_requests = [
                        r for r in self.endpoints[endpoint] if r['status'] == code]
                    avg_time = statistics.mean(
                        [r['response_time'] for r in endpoint_requests]) if endpoint_requests else 0

                    data.append({
                        'Codigo_HTTP': code,
                        'Descripcion': self.get_http_code_description(code),
                        'Endpoint': endpoint,
                        'Total_Requests': count,
                        'Tiempo_Promedio': avg_time
                    })

        return data

    def _get_top_endpoints(self):
        """Prepara top endpoints para exportación"""
        data = []

        for endpoint, requests in sorted(self.endpoints.items(),
                                         key=lambda x: len(x[1]), reverse=True)[:50]:
            times = [r['response_time'] for r in requests]
            cf_count = sum(1 for r in requests if r['is_cloudflare'])
            direct_count = len(requests) - cf_count

            data.append({
                'Endpoint': endpoint,
                'Total_Requests': len(requests),
                'Cloudflare_Requests': cf_count,
                'Direct_Requests': direct_count,
                'Tiempo_Promedio': statistics.mean(times) if times else 0.0,
                'Tiempo_Maximo': max(times) if times else 0.0,
                'Errores_499': sum(1 for r in requests if r['status'] == 499),
                'Requests_Lentos': sum(1 for r in requests if r['response_time'] > self.threshold),
                'Porcentaje_Lentos': (sum(1 for r in requests if r['response_time'] > self.threshold) / len(requests)) * 100 if len(requests) > 0 else 0
            })

        return data

    def _get_hourly_analysis(self):
        """Prepara análisis horario para exportación"""
        data = []

        for hour in sorted(self.hourly_stats.keys()):
            stats = self.hourly_stats[hour]
            total = stats['total']
            cf = stats.get('cloudflare', 0)
            direct = stats.get('direct', 0)
            slow = stats.get('slow', 0)
            errors_499 = stats.get('error_499', 0)

            data.append({
                'Hora': hour,
                'Total_Requests': total,
                'Cloudflare_Requests': cf,
                'Direct_Requests': direct,
                'Requests_Lentos': slow,
                'Errores_499': errors_499,
                'Porcentaje_Lentos': (slow / total * 100) if total > 0 else 0,
                'Porcentaje_Errores': (errors_499 / total * 100) if total > 0 else 0
            })

        return data

    def _get_slow_endpoints(self):
        """Prepara endpoints lentos para exportación"""
        data = []

        endpoint_stats = []
        for endpoint, requests in self.endpoints.items():
            if len(requests) >= 5:  # Mínimo 5 requests
                times = [r['response_time'] for r in requests]
                if times:  # Verificar que hay tiempos
                    endpoint_stats.append({
                        'endpoint': endpoint,
                        'total': len(requests),
                        'avg_time': statistics.mean(times),
                        'max_time': max(times),
                        'slow_count': sum(1 for r in requests if r['response_time'] > self.threshold)
                    })

        endpoint_stats.sort(key=lambda x: x['avg_time'], reverse=True)

        for ep in endpoint_stats[:50]:
            data.append({
                'Endpoint': ep['endpoint'],
                'Total_Requests': ep['total'],
                'Tiempo_Promedio': ep['avg_time'],
                'Tiempo_Maximo': ep['max_time'],
                'Requests_Lentos': ep['slow_count'],
                'Porcentaje_Lentos': (ep['slow_count'] / ep['total'] * 100) if ep['total'] > 0 else 0
            })

        return data

    def _get_detailed_endpoints(self):
        """Prepara detalle completo de endpoints para exportación"""
        data = []

        for endpoint, requests in self.endpoints.items():
            times = [r['response_time'] for r in requests]
            status_dist = defaultdict(int)
            hour_dist = defaultdict(int)

            for req in requests:
                status_dist[req['status']] += 1
                hour_dist[req['hour']] += 1

            # Status más común
            most_common_status = max(status_dist.items(), key=lambda x: x[1])[
                0] if status_dist else 0

            data.append({
                'Endpoint': endpoint,
                'Metodo': endpoint.split(' ')[0],
                'URL': endpoint.split(' ')[1] if ' ' in endpoint else endpoint,
                'Total_Requests': len(requests),
                'Tiempo_Promedio': statistics.mean(times) if times else 0.0,
                'Tiempo_Maximo': max(times) if times else 0.0,
                'Tiempo_Minimo': min(times) if times else 0.0,
                'Status_Mas_Comun': most_common_status,
                'Errores_499': status_dist.get(499, 0),
                'Requests_200': status_dist.get(200, 0),
                'Requests_Lentos': sum(1 for r in requests if r['response_time'] > self.threshold),
                'Cloudflare_Requests': sum(1 for r in requests if r['is_cloudflare']),
                'Direct_Requests': sum(1 for r in requests if not r['is_cloudflare'])
            })

        return data

    def export_to_excel(self, filename=None):
        """Exporta todos los datos a un archivo Excel"""
        if not filename:
            base_name = os.path.splitext(self.log_file)[0]
            filename = f"{base_name}_analysis.xlsx"

        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Crear cada hoja del Excel
                for sheet_name, data in self.export_data.items():
                    if data:  # Solo crear hoja si hay datos
                        df = pd.DataFrame(data)
                        df.to_excel(
                            writer, sheet_name=sheet_name[:31], index=False)

                        # Autoajustar columnas
                        worksheet = writer.sheets[sheet_name[:31]]
                        for column in worksheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(str(cell.value))
                                except BaseException:
                                    pass
                            adjusted_width = min(max_length + 2, 50)
                            worksheet.column_dimensions[column_letter].width = adjusted_width

            print(f"✅ Archivo Excel exportado: {filename}")
            return True

        except Exception as e:
            print(f"❌ Error exportando a Excel: {e}")
            return False

    def export_to_csv(self, directory=None):
        """Exporta todos los datos a archivos CSV individuales"""
        if not directory:
            directory = os.path.dirname(self.log_file) or "."

        base_name = os.path.splitext(os.path.basename(self.log_file))[0]

        try:
            for sheet_name, data in self.export_data.items():
                if data:
                    filename = os.path.join(
                        directory, f"{base_name}_{sheet_name}.csv")
                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        if data:
                            fieldnames = data[0].keys()
                            writer = csv.DictWriter(
                                csvfile, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(data)
                    print(f"✅ CSV exportado: {filename}")

            return True

        except Exception as e:
            print(f"❌ Error exportando a CSV: {e}")
            return False

# Agregar validaciones al inicio
def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    try:
        import pandas
        import openpyxl
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("Instala con: pip install pandas openpyxl")
        sys.exit(1)

def main():
    check_dependencies()
    parser = argparse.ArgumentParser(
        description='Analiza access.log con exportación a Excel/CSV')
    parser.add_argument('log_file', help='Archivo de log a analizar')
    parser.add_argument('--threshold', '-t', type=float, default=None,
                        help='Umbral para requests lentos (segundos). Si no se especifica, se calcula automáticamente')
    parser.add_argument('--export', '-e', choices=['excel', 'csv', 'both'],
                        help='Exportar resultados a Excel/CSV')
    parser.add_argument('--output', '-o', help='Nombre del archivo de salida')

    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"❌ Error: Archivo {args.log_file} no encontrado")
        sys.exit(1)

    analyzer = ComprehensiveLogAnalyzer(args.log_file, args.threshold)

    if analyzer.parse_log():
        # Siempre mostrar reporte en pantalla
        print(f"\n{'='*80}")
        print("📊 GENERANDO REPORTE COMPLETO EN PANTALLA")
        print(f"{'='*80}")
        analyzer.generate_comprehensive_report()

        # Exportar si se solicita
        if args.export:
            print(f"\n{'='*80}")
            print("💾 PROCESANDO EXPORTACIÓN")
            print(f"{'='*80}")

            # Preparar datos para exportación
            analyzer.prepare_export_data()

            if args.export in ['excel', 'both']:
                output_file = args.output or f"{os.path.splitext(args.log_file)[0]}_analysis.xlsx"
                analyzer.export_to_excel(output_file)
            if args.export in ['csv', 'both']:
                analyzer.export_to_csv()

            print(f"✅ Exportación completada exitosamente!")
    else:
        print("❌ Error al procesar el archivo de log")


if __name__ == "__main__":
    main()
