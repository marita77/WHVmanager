#!/usr/bin/env python3
"""
WHV Auto-Update — Generador de página
Scrapea yomeanimo.com y regenera index.html con datos frescos.
Corre automáticamente via GitHub Actions todos los días.
"""

import requests
import json
import re
from datetime import datetime
from html.parser import HTMLParser

# ── SCRAPING ──────────────────────────────────────────────────────────────────

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self._skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","head"): self._skip = True
    def handle_endtag(self, tag):
        if tag in ("script","style","head"): self._skip = False
    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t: self.text.append(t)
    def get_text(self): return " ".join(self.text).lower()

def fetch(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        p = TextParser()
        p.feed(r.text)
        return p.get_text()
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return ""

def get_estado_visa(url):
    texto = fetch(url)
    if not texto:
        return "❓"
    cerrado = ["no disp","cerrad","no se puede aplicar","proxima apertura","próxima apertura","closed","inscripciones cerradas"]
    abierto = ["disponible","sí, se puede aplicar","si, se puede aplicar","hay cupos","se pueden aplicar","inscripciones abiertas","abiert"]
    for c in cerrado:
        if c in texto: return "🔴 CERRADA"
    for a in abierto:
        if a in texto: return "✅ ABIERTA"
    return "❓ Verificar"

def scrape_calendario():
    print("Scrapeando calendario principal...")
    texto = fetch("https://www.yomeanimo.com/calendario-work-and-travel-argentina")
    paises_urls = {
        "australia":    "https://www.yomeanimo.com/guias-working-holiday/australia",
        "irlanda":      "https://www.yomeanimo.com/guias-working-holiday/irlanda",
        "espana":       "https://www.yomeanimo.com/guias-working-holiday/espana",
        "alemania":     "https://www.yomeanimo.com/guias-working-holiday/alemania",
        "japon":        "https://www.yomeanimo.com/guias-working-holiday/japon",
        "corea":        "https://www.yomeanimo.com/guias-working-holiday/corea",
        "francia":      "https://www.yomeanimo.com/guias-working-holiday/francia",
        "portugal":     "https://www.yomeanimo.com/guias-working-holiday/portugal",
        "noruega":      "https://www.yomeanimo.com/guias-working-holiday/noruega",
        "polonia":      "https://www.yomeanimo.com/guias-working-holiday/polonia",
        "hungria":      "https://www.yomeanimo.com/guias-working-holiday/hungria",
        "austria":      "https://www.yomeanimo.com/guias-working-holiday/austria",
        "eslovaquia":   "https://www.yomeanimo.com/guias-working-holiday/eslovaquia",
        "dinamarca":    "https://www.yomeanimo.com/guias-working-holiday/dinamarca",
        "nueva_zelanda":"https://www.yomeanimo.com/guias-working-holiday/nueva-zelanda",
    }
    estados = {}
    for pais, url in paises_urls.items():
        print(f"  Consultando {pais}...")
        estados[pais] = get_estado_visa(url)
    return estados

# ── DATOS BASE (se mantienen, solo el estado se actualiza) ─────────────────────

VISAS_DATA = [
    {
        "id":"australia","pais":"Australia","flag":"🇦🇺","key":"australia",
        "cupos":"3.400","edad":"18–30","costo":"AUD 495 (~USD 320)",
        "fondos":"AUD 5.000 (~USD 3.200)","duracion":"12 meses + ext.",
        "exterior":"Sí (desde cualquier país excepto Australia)",
        "docs":["Pasaporte vigente","Examen de salud (médico panel Home Affairs)","Antecedentes penales apostillados","Certificado de inglés (requerido desde 2024)","Seguro médico amplio","Extractos con AUD 5.000"],
        "nota":"Renovación de cupos: 1 julio cada año. Online 100%.",
        "fuente":"https://immi.homeaffairs.gov.au",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/australia",
    },
    {
        "id":"irlanda","pais":"Irlanda","flag":"🇮🇪","key":"irlanda",
        "cupos":"200","edad":"18–35","costo":"EUR 335 (~USD 365)",
        "fondos":"EUR 3.000 mínimo","duracion":"12 meses",
        "exterior":"Sí (con autorización post-preselección)",
        "docs":["Pasaporte vigente (mín 1 año)","Antecedentes penales apostillados","Seguro (hosp + repatriación)","Extractos con EUR 3.000","Carta de motivación (obligatoria)","CV actualizado"],
        "nota":"⚠ Los 200 cupos se agotan en MINUTOS al abrir. Preparar todo antes.",
        "fuente":"https://irishimmigration.ie",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/irlanda",
    },
    {
        "id":"nz","pais":"Nueva Zelanda","flag":"🇳🇿","key":"nueva_zelanda",
        "cupos":"1.000","edad":"18–35","costo":"NZD 208 (~USD 125)",
        "fondos":"NZD 4.200 (~USD 2.530)","duracion":"12 meses",
        "exterior":"Sí (cualquier país incluida NZ)",
        "docs":["Pasaporte vigente","Examen médico + RX tórax (médico panel NZ)","Antecedentes penales apostillados","Seguro mín NZD 500.000","Extractos con NZD 4.200"],
        "nota":"Abre 23/09/2026. Cupos se agotan en minutos. Preparar antes.",
        "fuente":"https://immigration.govt.nz",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/nueva-zelanda",
    },
    {
        "id":"alemania","pais":"Alemania","flag":"🇩🇪","key":"alemania",
        "cupos":"Ilimitados","edad":"18–30","costo":"EUR 75 (~USD 82)",
        "fondos":"EUR 2.000","duracion":"12 meses + ext.",
        "exterior":"Sí (excepto desde Alemania)",
        "docs":["Pasaporte vigente","2 fotos","Antecedentes apostillados","Seguro válido en Alemania","Extractos EUR 2.000","Carta de motivación (obligatoria)","CV en alemán/inglés (obligatorio)","Cert. alemán A1 (recomendado)"],
        "nota":"Turnos escasos. Buscar a las 19-20hs ARG (se liberan a las 00hs ALE).",
        "fuente":"https://make-it-in-germany.com",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/alemania",
    },
    {
        "id":"japon","pais":"Japón","flag":"🇯🇵","key":"japon",
        "cupos":"400 (por tandas)","edad":"18–30","costo":"Gratuita",
        "fondos":"~USD 1.700 equiv.","duracion":"12 meses",
        "exterior":"No — solo presencial en Buenos Aires",
        "docs":["Pasaporte vigente (mín 1 año)","2 fotos","Antecedentes apostillados","Seguro de viaje","Extractos ~USD 1.700","Carta de motivación (obligatoria)","CV (obligatorio)","Pasaje retorno o fondos"],
        "nota":"Posible entrevista presencial. Cupos divididos en 4 tandas trimestrales.",
        "fuente":"https://mofa.go.jp",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/japon",
    },
    {
        "id":"corea","pais":"Corea del Sur","flag":"🇰🇷","key":"corea",
        "cupos":"200","edad":"18–34","costo":"~USD 40",
        "fondos":"~USD 3.000","duracion":"12 meses + ext.",
        "exterior":"No — solo presencial en Buenos Aires",
        "docs":["Pasaporte vigente","1 foto","Antecedentes apostillados","Seguro de viaje","Extractos ~USD 3.000","Carta de motivación (obligatoria)","CV (obligatorio)","⚠ Mín. 1 año de universidad (obligatorio)"],
        "nota":"Nunca se agotaron los 200 cupos. 1 año universitario obligatorio.",
        "fuente":"https://hikorea.go.kr",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/corea",
    },
    {
        "id":"francia","pais":"Francia","flag":"🇫🇷","key":"francia",
        "cupos":"900","edad":"18–35","costo":"EUR 99 (~USD 108)",
        "fondos":"EUR 2.500","duracion":"12 meses",
        "exterior":"No — solo desde Buenos Aires",
        "docs":["Pasaporte vigente","1 foto","Antecedentes apostillados","Seguro mín EUR 30.000","Extractos EUR 2.500","Carta de motivación (obligatoria)","CV (obligatorio)","Alojamiento inicial","Pasaje ida y vuelta"],
        "nota":"900 cupos, suelen durar todo el año.",
        "fuente":"https://france-visas.gouv.fr",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/francia",
    },
    {
        "id":"espana","pais":"España","flag":"🇪🇸","key":"espana",
        "cupos":"500","edad":"18–35","costo":"ARS 153.000 + ARS 17.000 (NIE)",
        "fondos":"EUR 14.208 total (EUR 1.184/mes × 12)","duracion":"12 meses + ext.",
        "exterior":"No — solo desde Argentina",
        "docs":["Pasaporte vigente","1 foto","Antecedentes apostillados","Seguro (hosp + repatriación)","Extractos EUR 14.208","DNI vigente (residencia ARG)","⚠⚠ MÍNIMO 2 AÑOS UNIVERSITARIOS — OBLIGATORIO","Formulario del consulado"],
        "nota":"Sin 2 años uni: NO se aprueba. No familiares a cargo. Consulados: BsAs, Córdoba, Rosario, Mendoza, Bahía Blanca.",
        "fuente":"https://exteriores.gob.es",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/espana",
    },
    {
        "id":"portugal","pais":"Portugal","flag":"🇵🇹","key":"portugal",
        "cupos":"100","edad":"18–30","costo":"EUR 90 (~USD 98)",
        "fondos":"EUR 1.500","duracion":"12 meses",
        "exterior":"No — solo desde Buenos Aires / Córdoba",
        "docs":["Pasaporte vigente","2 fotos","Antecedentes apostillados","Seguro de viaje","Extractos EUR 1.500","Carta de motivación","CV","Pasaje retorno"],
        "nota":"Solo 100 cupos. Confirmar disponibilidad antes de iniciar trámite.",
        "fuente":"https://imigracao.pt",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/portugal",
    },
    {
        "id":"noruega","pais":"Noruega","flag":"🇳🇴","key":"noruega",
        "cupos":"300","edad":"18–30","costo":"EUR 65 (~USD 71)",
        "fondos":"EUR 2.000","duracion":"12 meses",
        "exterior":"No — solo desde Argentina (desde 2025)",
        "docs":["Pasaporte vigente","2 fotos","Antecedentes apostillados","Seguro de viaje","Extractos EUR 2.000","Carta de motivación (obligatoria)","CV (obligatorio)","Pasaje retorno"],
        "nota":"En 2025 los 300 cupos se agotaron en ~3 meses. Tramitar pronto.",
        "fuente":"https://udi.no",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/noruega",
    },
    {
        "id":"polonia","pais":"Polonia","flag":"🇵🇱","key":"polonia",
        "cupos":"400","edad":"18–30","costo":"EUR 60 (~USD 65)",
        "fondos":"EUR 1.500","duracion":"12 meses",
        "exterior":"No — solo desde Buenos Aires",
        "docs":["Pasaporte vigente","2 fotos","Antecedentes apostillados","Seguro de viaje","Extractos EUR 1.500","Carta de motivación (recomendada)","CV (recomendado)"],
        "nota":"Nunca se agotaron los 400 cupos. Trámite sencillo.",
        "fuente":"https://gov.pl/web/diplomacy",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/polonia",
    },
    {
        "id":"hungria","pais":"Hungría","flag":"🇭🇺","key":"hungria",
        "cupos":"200","edad":"18–35","costo":"EUR 50 (~USD 55)",
        "fondos":"EUR 1.500","duracion":"12 meses",
        "exterior":"No — solo desde Argentina (desde 2025)",
        "docs":["Pasaporte vigente","2 fotos","Antecedentes apostillados","Seguro de viaje","Extractos EUR 1.500","Carta de motivación (obligatoria)","CV (obligatorio)"],
        "nota":"200 cupos, dura casi todo el año. Budapest, bajo costo de vida.",
        "fuente":"https://konzuliszolgalat.gov.hu",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/hungria",
    },
    {
        "id":"austria","pais":"Austria","flag":"🇦🇹","key":"austria",
        "cupos":"200","edad":"18–30 ⚠️","costo":"EUR 100 (~USD 109)",
        "fondos":"EUR 2.000","duracion":"12 meses",
        "exterior":"No — solo desde Buenos Aires",
        "docs":["Pasaporte vigente","2 fotos","Antecedentes apostillados","Seguro de viaje","Extractos EUR 2.000","Carta de motivación (obligatoria)","CV (obligatorio)"],
        "nota":"⚠ NO ingresar con 31 años (verificar en bmi.gv.at). Turnos muy escasos.",
        "fuente":"https://bmi.gv.at",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/austria",
    },
    {
        "id":"eslovaquia","pais":"Eslovaquia","flag":"🇸🇰","key":"eslovaquia",
        "cupos":"100","edad":"18–30","costo":"EUR 60 (~USD 65)",
        "fondos":"EUR 1.500 (estimado)","duracion":"12 meses",
        "exterior":"No — solo desde Buenos Aires",
        "docs":["Pasaporte vigente","2 fotos","Antecedentes apostillados","Seguro de viaje","Extractos EUR 1.500","Carta de motivación (recomendada)","CV (recomendado)"],
        "nota":"Visa nueva. Bratislava, bajo costo de vida.",
        "fuente":"https://mzv.sk",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/eslovaquia",
    },
    {
        "id":"dinamarca","pais":"Dinamarca","flag":"🇩🇰","key":"dinamarca",
        "cupos":"150 (75 x semestre)","edad":"18–30","costo":"EUR 70 (~USD 76)",
        "fondos":"EUR 2.000","duracion":"12 meses",
        "exterior":"No — solo desde Buenos Aires",
        "docs":["Pasaporte vigente","2 fotos","Antecedentes apostillados","Seguro de viaje","Extractos EUR 2.000","Carta de motivación (obligatoria)","CV (obligatorio)"],
        "nota":"Se agotan el mismo día de apertura. 2do lote 2026: septiembre.",
        "fuente":"https://nyidanmark.dk",
        "guia":"https://www.yomeanimo.com/guias-working-holiday/dinamarca",
    },
]

# ── GENERADOR HTML ─────────────────────────────────────────────────────────────

def generar_html(estados):
    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    fecha_corta = datetime.now().strftime("%d/%m/%Y")

    # Contar abiertas/cerradas
    abiertas = sum(1 for v in VISAS_DATA if "ABIERTA" in estados.get(v["key"], ""))
    cerradas  = sum(1 for v in VISAS_DATA if "CERRADA" in estados.get(v["key"], ""))

    # Generar cards de visas
    def make_card(v):
        estado = estados.get(v["key"], "❓ Sin datos")
        color_border = "card-open" if "ABIERTA" in estado else ("card-closed" if "CERRADA" in estado else "card-warn")
        badge_color  = "badge-open" if "ABIERTA" in estado else ("badge-closed" if "CERRADA" in estado else "badge-warn")
        docs_html = "".join(f"<li>{d}</li>" for d in v["docs"])
        return f"""
<div class="vcard {color_border}" id="card-{v['id']}">
  <div class="vcard-header">
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
      <span style="font-size:1.4rem">{v['flag']}</span>
      <span class="vcard-name">{v['pais']}</span>
      <span class="badge {badge_color}">{estado}</span>
    </div>
  </div>
  <div class="vcard-grid">
    <div class="info-block"><div class="info-lbl">Cupos</div><div class="info-val">{v['cupos']}</div></div>
    <div class="info-block"><div class="info-lbl">Edad</div><div class="info-val">{v['edad']}</div></div>
    <div class="info-block"><div class="info-lbl">Costo visa</div><div class="info-val">{v['costo']}</div></div>
    <div class="info-block full"><div class="info-lbl">Fondos mínimos requeridos</div><div class="info-val hl">{v['fondos']}</div></div>
    <div class="info-block"><div class="info-lbl">Duración</div><div class="info-val">{v['duracion']}</div></div>
    <div class="info-block full"><div class="info-lbl">Aplicar desde el exterior</div><div class="info-val">{v['exterior']}</div></div>
  </div>
  <div class="docs-box">
    <div class="docs-title">Documentos requeridos</div>
    <ul class="docs-list">{docs_html}</ul>
  </div>
  <div class="nota-box">{v['nota']}</div>
  <div class="links-row">
    <a href="{v['fuente']}" target="_blank" class="lbtn lbtn-oficial">Fuente oficial</a>
    <a href="{v['guia']}" target="_blank" class="lbtn lbtn-guia">Guía YoMeAnimo</a>
  </div>
</div>"""

    cards_html = "\n".join(make_card(v) for v in VISAS_DATA)

    # Navegación rápida
    nav_html = ""
    for v in VISAS_DATA:
        estado = estados.get(v["key"], "")
        cls = "nav-open" if "ABIERTA" in estado else ("nav-closed" if "CERRADA" in estado else "nav-warn")
        nav_html += f'<button class="nav-btn {cls}" onclick="document.getElementById(\'card-{v[\'id\']}\').scrollIntoView({{behavior:\'smooth\'}})">{v["flag"]} {v["pais"]}</button>\n'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WHV Manager — Pasaporte Argentino 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0d0f14;--sur:#141720;--sur2:#1c2030;--brd:#252a3a;--txt:#e8eaf2;--mut:#6b7494;--acc:#4f8ef7;--grn:#3dd68c;--red:#f05c5c;--amb:#f5a623;--pur:#a78bfa;--teal:#2dd4bf;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);color:var(--txt);font-family:'DM Sans',sans-serif;font-weight:300;line-height:1.6;}}
header{{border-bottom:1px solid var(--brd);padding:18px 36px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:rgba(13,15,20,0.94);backdrop-filter:blur(12px);z-index:100;flex-wrap:wrap;gap:8px;}}
.logo{{font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;letter-spacing:0.08em;text-transform:uppercase;}}
.logo span{{color:var(--acc);}}
.header-meta{{font-family:'DM Mono',monospace;font-size:0.65rem;color:var(--mut);text-align:right;}}
.live-dot{{display:inline-block;width:6px;height:6px;background:var(--grn);border-radius:50%;margin-right:5px;animation:pulse 2s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
nav{{display:flex;padding:0 36px;border-bottom:1px solid var(--brd);overflow-x:auto;scrollbar-width:none;}}
nav::-webkit-scrollbar{{display:none;}}
.tab{{font-family:'Syne',sans-serif;font-size:0.72rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:var(--mut);padding:13px 18px;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;transition:all .2s;}}
.tab:hover{{color:var(--txt);}} .tab.active{{color:var(--acc);border-bottom-color:var(--acc);}}
main{{padding:36px;max-width:1400px;margin:0 auto;}}
.sec{{display:none;}} .sec.active{{display:block;}}
.alert-bar{{border:1px solid;border-radius:10px;padding:13px 18px;margin-bottom:18px;display:flex;align-items:flex-start;gap:12px;font-size:0.82rem;}}
.alert-bar.red{{background:rgba(240,92,92,.1);border-color:rgba(240,92,92,.25);}}
.alert-bar.red strong{{color:var(--red);}}
.alert-bar.grn{{background:rgba(61,214,140,.08);border-color:rgba(61,214,140,.2);}}
.alert-bar.grn strong{{color:var(--grn);}}
.alert-bar.amb{{background:rgba(245,166,35,.08);border-color:rgba(245,166,35,.2);}}
.alert-bar.amb strong{{color:var(--amb);}}
.sec-lbl{{font-family:'Syne',sans-serif;font-size:0.65rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin-bottom:16px;display:flex;align-items:center;gap:10px;}}
.sec-lbl::after{{content:'';flex:1;height:1px;background:var(--brd);}}
.g4{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:28px;}}
@media(max-width:900px){{.g4{{grid-template-columns:repeat(2,1fr);}}}}
.stat{{background:var(--sur);border:1px solid var(--brd);border-radius:12px;padding:18px;}}
.stat.b{{border-color:rgba(79,142,247,.2);}} .stat.g{{border-color:rgba(61,214,140,.2);}}
.stat.r{{border-color:rgba(240,92,92,.2);}} .stat.a{{border-color:rgba(245,166,35,.2);}}
.stat-lbl{{font-family:'DM Mono',monospace;font-size:.62rem;color:var(--mut);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;}}
.stat-val{{font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:700;line-height:1;margin-bottom:3px;}}
.stat-sub{{font-size:.72rem;color:var(--mut);}}
.check-item{{background:var(--sur);border:1px solid var(--brd);border-radius:10px;padding:12px 15px;display:flex;align-items:flex-start;gap:11px;cursor:pointer;margin-bottom:8px;transition:border-color .2s;}}
.check-item:hover{{border-color:#353c58;}}
.check-item.done{{opacity:.5;}}
.cbox{{width:18px;height:18px;border:1.5px solid var(--brd);border-radius:4px;flex-shrink:0;margin-top:2px;position:relative;transition:all .15s;}}
.check-item.done .cbox{{background:var(--grn);border-color:var(--grn);}}
.check-item.done .cbox::after{{content:'';position:absolute;left:3px;top:1px;width:8px;height:10px;border:2px solid #0d0f14;border-top:none;border-left:none;transform:rotate(40deg);}}
.ct{{font-weight:500;font-size:.86rem;margin-bottom:2px;}}
.cd{{font-size:.74rem;color:var(--mut);}}
.udot{{width:5px;height:5px;border-radius:50%;flex-shrink:0;margin-top:7px;}}
.udot.r{{background:var(--red);}} .udot.a{{background:var(--amb);}} .udot.g{{background:var(--grn);}}
.vnav{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;}}
.nav-btn{{font-family:'DM Mono',monospace;font-size:.65rem;padding:4px 11px;border-radius:20px;border:1px solid var(--brd);background:var(--sur);color:var(--mut);cursor:pointer;transition:all .15s;white-space:nowrap;}}
.nav-btn:hover{{color:var(--txt);}}
.nav-open{{border-color:rgba(61,214,140,.2);color:var(--grn);}}
.nav-closed{{border-color:rgba(240,92,92,.2);color:var(--red);}}
.nav-warn{{border-color:rgba(245,166,35,.2);color:var(--amb);}}
.vcard{{background:var(--sur);border:1px solid var(--brd);border-radius:14px;padding:22px;margin-bottom:18px;scroll-margin-top:110px;}}
.card-open{{border-left:3px solid var(--grn);}} .card-closed{{border-left:3px solid var(--red);}} .card-warn{{border-left:3px solid var(--amb);}}
.vcard-header{{margin-bottom:16px;}}
.vcard-name{{font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;}}
.badge{{font-family:'DM Mono',monospace;font-size:.6rem;padding:3px 9px;border-radius:4px;font-weight:500;}}
.badge-open{{background:rgba(61,214,140,.12);color:var(--grn);}}
.badge-closed{{background:rgba(240,92,92,.12);color:var(--red);}}
.badge-warn{{background:rgba(245,166,35,.12);color:var(--amb);}}
.vcard-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;}}
@media(max-width:700px){{.vcard-grid{{grid-template-columns:repeat(2,1fr);}}}}
.info-block{{background:var(--sur2);border-radius:8px;padding:10px;}}
.info-block.full{{grid-column:1/-1;}}
.info-lbl{{font-family:'DM Mono',monospace;font-size:.58rem;color:var(--mut);text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px;}}
.info-val{{font-size:.82rem;font-weight:500;}}
.info-val.hl{{color:var(--amb);font-weight:600;}}
.docs-box{{background:var(--sur2);border-radius:10px;padding:14px;margin-bottom:12px;}}
.docs-title{{font-family:'Syne',sans-serif;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);margin-bottom:8px;}}
.docs-list{{padding-left:16px;font-size:.8rem;}}
.docs-list li{{padding:2px 0;}}
.nota-box{{font-size:.78rem;color:var(--mut);background:rgba(79,142,247,.04);border:1px solid rgba(79,142,247,.1);border-radius:8px;padding:10px 14px;margin-bottom:12px;}}
.links-row{{display:flex;flex-wrap:wrap;gap:8px;}}
.lbtn{{font-family:'DM Mono',monospace;font-size:.65rem;padding:5px 13px;border-radius:6px;text-decoration:none;border:1px solid;transition:opacity .15s;}}
.lbtn:hover{{opacity:.75;}}
.lbtn-oficial{{background:rgba(79,142,247,.1);border-color:rgba(79,142,247,.2);color:var(--acc);}}
.lbtn-guia{{background:rgba(61,214,140,.08);border-color:rgba(61,214,140,.15);color:var(--grn);}}
.twrap{{overflow-x:auto;border-radius:10px;border:1px solid var(--brd);margin-bottom:20px;}}
table{{width:100%;border-collapse:collapse;font-size:.79rem;}}
th{{background:var(--sur2);padding:10px 12px;text-align:left;font-family:'Syne',sans-serif;font-size:.62rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);border-bottom:1px solid var(--brd);white-space:nowrap;}}
td{{padding:9px 12px;border-bottom:1px solid var(--brd);}}
tr:hover td{{background:var(--sur);}}
.cost-wrap{{margin-bottom:9px;}}
.cost-lbl{{display:flex;justify-content:space-between;font-size:.78rem;margin-bottom:4px;}}
.cost-lbl .pais{{font-weight:500;}} .cost-lbl .monto{{font-family:'DM Mono',monospace;color:var(--acc);}}
.cost-bg{{background:var(--sur2);border-radius:3px;height:5px;}}
.cost-fill{{height:5px;border-radius:3px;}}
.cl-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;}}
@media(max-width:700px){{.cl-grid{{grid-template-columns:1fr;}}}}
footer{{border-top:1px solid var(--brd);padding:18px 36px;margin-top:40px;display:flex;justify-content:space-between;align-items:center;font-family:'DM Mono',monospace;font-size:.62rem;color:var(--mut);flex-wrap:wrap;gap:6px;}}
::-webkit-scrollbar{{width:3px;height:3px;}}::-webkit-scrollbar-thumb{{background:var(--brd);border-radius:2px;}}
</style>
</head>
<body>
<header>
  <div class="logo">WHV<span>.</span>Manager</div>
  <div class="header-meta">
    <div><span class="live-dot"></span>Pasaporte Argentino · Actualizado automáticamente</div>
    <div>Última actualización: {hoy} · Fuente: yomeanimo.com</div>
  </div>
</header>
<nav>
  <div class="tab active" onclick="showTab('dash',this)">Dashboard</div>
  <div class="tab" onclick="showTab('visas',this)">Todas las visas</div>
  <div class="tab" onclick="showTab('docs',this)">Documentos</div>
  <div class="tab" onclick="showTab('checklist',this)">Checklist</div>
  <div class="tab" onclick="showTab('costos',this)">Costos</div>
</nav>
<main>

<!-- DASHBOARD -->
<section id="dash" class="sec active">
  <div class="alert-bar red"><span>🔴</span><div><strong>IRLANDA — {estados.get('irlanda','❓')}</strong> · Próxima apertura: ~junio 2026 · Cupos se agotan en MINUTOS</div></div>
  <div class="alert-bar grn"><span>✅</span><div><strong>ESPAÑA — {estados.get('espana','❓')}</strong> · 500 cupos · Fondos: EUR 14.208 · <strong>Reqiere 2 años universitarios (OBLIGATORIO)</strong></div></div>
  <div class="alert-bar amb"><span>📅</span><div><strong>Datos actualizados automáticamente todos los días.</strong> Última consulta: {fecha_corta} · Fuente: yomeanimo.com</div></div>
  <div class="sec-lbl">Resumen</div>
  <div class="g4">
    <div class="stat g"><div class="stat-lbl">Visas abiertas</div><div class="stat-val" style="color:var(--grn)">{abiertas}</div><div class="stat-sub">de 15 destinos</div></div>
    <div class="stat r"><div class="stat-lbl">Visas cerradas</div><div class="stat-val" style="color:var(--red)">{cerradas}</div><div class="stat-sub">IRL · NZ · DIN y otras</div></div>
    <div class="stat a"><div class="stat-lbl">Próxima apertura</div><div class="stat-val" style="color:var(--amb)">Jun</div><div class="stat-sub">Irlanda — 200 cupos</div></div>
    <div class="stat b"><div class="stat-lbl">Actualización</div><div class="stat-val" style="color:var(--acc)">Auto</div><div class="stat-sub">Cada día · GitHub Actions</div></div>
  </div>
  <div class="sec-lbl">Acciones urgentes</div>
  <div id="dash-cl"></div>
</section>

<!-- VISAS -->
<section id="visas" class="sec">
  <div class="sec-lbl">Navegación rápida</div>
  <div class="vnav">{nav_html}</div>
  <div class="sec-lbl">Fichas completas — 15 destinos · Estado consultado el {fecha_corta}</div>
  {cards_html}
</section>

<!-- DOCUMENTOS -->
<section id="docs" class="sec">
  <div class="sec-lbl">Documentos universales (todos los países)</div>
  <div class="alert-bar amb"><span>📌</span><div>Pasaporte vigente · Foto · Antecedentes penales apostillados (rnr.gob.ar → cancilleria.gob.ar) · Seguro de viaje · Extractos bancarios · Formulario de solicitud · Pago de tasa</div></div>
  <div class="sec-lbl">Documentos específicos por destino</div>
  <div class="twrap"><table>
    <thead><tr><th>País</th><th>Carta motivación</th><th>CV</th><th>Universidad</th><th>Examen médico</th><th>Alojamiento</th><th>Apostilla extra</th></tr></thead>
    <tbody>
      <tr><td>🇦🇺 Australia</td><td>—</td><td>—</td><td>—</td><td>✅ Panel + inglés</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇳🇿 Nueva Zelanda</td><td>Recmd.</td><td>—</td><td>—</td><td>✅ + RX tórax</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇮🇪 Irlanda</td><td>✅ Obligatoria</td><td>✅</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇩🇪 Alemania</td><td>✅ Obligatoria</td><td>✅</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇯🇵 Japón</td><td>✅ Obligatoria</td><td>✅</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇰🇷 Corea del Sur</td><td>✅ Obligatoria</td><td>✅</td><td>⚠ Mín. 1 año</td><td>Posible</td><td>—</td><td>Antecedentes + estudios</td></tr>
      <tr><td>🇫🇷 Francia</td><td>✅ Obligatoria</td><td>✅</td><td>—</td><td>—</td><td>✅ Inicial</td><td>Antecedentes</td></tr>
      <tr><td>🇪🇸 España</td><td>—</td><td>—</td><td>⚠⚠ Mín. 2 años OBLIG.</td><td>—</td><td>—</td><td>Antecedentes (+ posible partida nacim.)</td></tr>
      <tr><td>🇵🇹 Portugal</td><td>✅ Obligatoria</td><td>✅</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇳🇴 Noruega</td><td>✅ Obligatoria</td><td>✅</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇵🇱 Polonia</td><td>Recmd.</td><td>Recmd.</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇭🇺 Hungría</td><td>✅ Obligatoria</td><td>✅</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇦🇹 Austria</td><td>✅ Obligatoria</td><td>✅</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇸🇰 Eslovaquia</td><td>Recmd.</td><td>Recmd.</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
      <tr><td>🇩🇰 Dinamarca</td><td>✅ Obligatoria</td><td>✅</td><td>—</td><td>—</td><td>—</td><td>Antecedentes</td></tr>
    </tbody>
  </table></div>
  <div class="alert-bar amb"><span>🏛</span><div><strong>Apostillas:</strong> cancilleria.gob.ar/es/servicios/apostilla · Normal: 1–3 sem · Urgente: 48–72hs · Antecedentes: rnr.gob.ar (pedir primero, puede demorar 4 semanas)</div></div>
</section>

<!-- CHECKLIST -->
<section id="checklist" class="sec">
  <div class="cl-grid">
    <div><div class="sec-lbl">🔴 Urgente — esta semana</div><div id="cl-r"></div></div>
    <div><div class="sec-lbl">🟡 Pronto — 2–4 semanas</div><div id="cl-a"></div></div>
  </div>
  <div class="sec-lbl">🟢 Anticipar</div>
  <div id="cl-g"></div>
</section>

<!-- COSTOS -->
<section id="costos" class="sec">
  <div class="sec-lbl">Capital inicial estimado (USD) — visa + fondos + vuelo + apostillas</div>
  <div style="background:var(--sur);border:1px solid var(--brd);border-radius:12px;padding:22px;margin-bottom:20px" id="cbars"></div>
  <div class="alert-bar red"><span>⚠️</span><div>España requiere EUR 14.208 de fondos (sustento 12 meses completos). Es el mayor capital inicial de todos los destinos.</div></div>
  <div class="sec-lbl">Tabla detallada</div>
  <div class="twrap"><table><thead><tr><th>País</th><th>Tasa visa</th><th>Fondos mín.</th><th>Vuelo aprox.</th><th>Total arranque</th></tr></thead>
  <tbody>
    <tr><td>🇦🇺 Australia</td><td>AUD 495 (~$320)</td><td>AUD 5.000 (~$3.200)</td><td>$1.200–1.800</td><td style="font-family:'DM Mono',monospace;color:var(--red)">$4.770+</td></tr>
    <tr><td>🇳🇿 Nueva Zelanda</td><td>NZD 208 (~$125)</td><td>NZD 4.200 (~$2.530)</td><td>$1.200–1.800</td><td style="font-family:'DM Mono',monospace;color:var(--amb)">$3.905+</td></tr>
    <tr><td>🇮🇪 Irlanda</td><td>EUR 335 (~$365)</td><td>EUR 3.000 (~$3.270)</td><td>$900–1.500</td><td style="font-family:'DM Mono',monospace;color:var(--amb)">$4.685+</td></tr>
    <tr><td>🇩🇪 Alemania</td><td>EUR 75 (~$82)</td><td>EUR 2.000 (~$2.180)</td><td>$700–1.200</td><td style="font-family:'DM Mono',monospace;color:var(--grn)">$3.012+</td></tr>
    <tr><td>🇯🇵 Japón</td><td>Gratuita</td><td>~$1.700</td><td>$800–1.500</td><td style="font-family:'DM Mono',monospace;color:var(--grn)">$2.550+</td></tr>
    <tr><td>🇰🇷 Corea del Sur</td><td>~$40</td><td>~$3.000</td><td>$700–1.300</td><td style="font-family:'DM Mono',monospace;color:var(--amb)">$3.790+</td></tr>
    <tr><td>🇫🇷 Francia</td><td>EUR 99 (~$108)</td><td>EUR 2.500 (~$2.730)</td><td>$700–1.200</td><td style="font-family:'DM Mono',monospace;color:var(--grn)">$3.588+</td></tr>
    <tr><td>🇪🇸 España</td><td>ARS 170.000</td><td>EUR 14.208 (~$15.500)</td><td>$700–1.200</td><td style="font-family:'DM Mono',monospace;color:var(--red)">$16.450+ ⚠️</td></tr>
    <tr><td>🇵🇹 Portugal</td><td>EUR 90 (~$98)</td><td>EUR 1.500 (~$1.635)</td><td>$700–1.200</td><td style="font-family:'DM Mono',monospace;color:var(--grn)">$1.983+</td></tr>
    <tr><td>🇳🇴 Noruega</td><td>EUR 65 (~$71)</td><td>EUR 2.000 (~$2.180)</td><td>$700–1.200</td><td style="font-family:'DM Mono',monospace;color:var(--grn)">$3.001+</td></tr>
    <tr><td>🇵🇱 Polonia</td><td>EUR 60 (~$65)</td><td>EUR 1.500 (~$1.635)</td><td>$700–1.200</td><td style="font-family:'DM Mono',monospace;color:var(--grn)">$2.450+</td></tr>
    <tr><td>🇭🇺 Hungría</td><td>EUR 50 (~$55)</td><td>EUR 1.500 (~$1.635)</td><td>$700–1.200</td><td style="font-family:'DM Mono',monospace;color:var(--grn)">$2.440+</td></tr>
  </tbody></table></div>
</section>

</main>
<footer>
  <span>WHV Manager · Pasaporte Argentino · Actualización automática diaria</span>
  <span>yomeanimo.com · irishimmigration.ie · exteriores.gob.es · Verificar en fuente oficial antes de aplicar</span>
</footer>
<script>
function showTab(id,el){{document.querySelectorAll('.sec').forEach(s=>s.classList.remove('active'));document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.getElementById(id).classList.add('active');if(el)el.classList.add('active');}}
function toggleCheck(el){{el.classList.toggle('done');try{{const s={{}};document.querySelectorAll('.check-item').forEach((e,i)=>{{s[i]=e.classList.contains('done');}});localStorage.setItem('whv3',JSON.stringify(s));}}catch(e){{}}}}
function mkCheck(t,d,dot){{const e=document.createElement('div');e.className='check-item';e.onclick=function(){{toggleCheck(this);}};e.innerHTML=`<div class="udot ${{dot}}"></div><div class="cbox"></div><div><div class="ct">${{t}}</div><div class="cd">${{d}}</div></div>`;return e;}}
const rItems=[
  ["Solicitar antecedente penal","rnr.gob.ar — puede demorar hasta 4 semanas. Iniciar YA.","r"],
  ["Verificar vencimiento del pasaporte","Mínimo 18 meses desde la fecha estimada de viaje.","r"],
  ["Si apuntás a España: verificar 2 años universitarios","Requisito excluyente. Sin esto no se aprueba.","r"],
];
const aItems=[
  ["Apostillar antecedentes en Cancillería","cancilleria.gob.ar — 1–3 sem normal, 48–72hs urgente.","a"],
  ["Contratar seguro de viaje","Con hospitalización + repatriación. USD 30–100/mes.","a"],
  ["Armar extractos bancarios","Con el saldo mínimo del destino elegido.","a"],
  ["Redactar carta de motivación","Obligatoria en Irlanda, Alemania, Japón, Corea, Francia, Noruega, Hungría, Austria, Dinamarca.","a"],
];
const gItems=[
  ["Actualizar CV en inglés o idioma del destino","Requerido en la mayoría de visas europeas y asiáticas.","g"],
  ["Buscar turno consular","Para Alemania y Austria los turnos son muy escasos.","g"],
  ["Para Irlanda: preparar docs desde ahora","Cuando abra (~jun 2026) tendrás minutos para actuar.","g"],
  ["Seguir t.me/YoMeAnimo","Alertas de apertura de Irlanda y otros destinos.","g"],
];
["r","a","g"].forEach(tipo=>{{
  const items=tipo==="r"?rItems:tipo==="a"?aItems:gItems;
  const cl=document.getElementById("cl-"+tipo);
  if(cl) items.forEach(([t,d,dot])=>cl.appendChild(mkCheck(t,d,dot)));
  if(tipo==="r"){{const dc=document.getElementById("dash-cl");if(dc)items.forEach(([t,d,dot])=>dc.appendChild(mkCheck(t,d,dot)));}}
  if(tipo==="a"){{const dc=document.getElementById("dash-cl");if(dc)items.slice(0,2).forEach(([t,d,dot])=>dc.appendChild(mkCheck(t,d,dot)));}}
}});
const costs=[["🇵🇹 Portugal",1983,"#3dd68c"],["🇭🇺 Hungría",2440,"#3dd68c"],["🇯🇵 Japón",2550,"#2dd4bf"],["🇵🇱 Polonia",2450,"#3dd68c"],["🇩🇪 Alemania",3012,"#4f8ef7"],["🇳🇴 Noruega",3001,"#4f8ef7"],["🇫🇷 Francia",3588,"#4f8ef7"],["🇰🇷 Corea",3790,"#f5a623"],["🇮🇪 Irlanda",4685,"#f5a623"],["🇦🇺 Australia",4770,"#f05c5c"],["🇳🇿 Nueva Zelanda",3905,"#f5a623"],["🇪🇸 España",16450,"#f05c5c"]];
const cb=document.getElementById("cbars");
costs.forEach(([p,v,c])=>{{cb.innerHTML+=`<div class="cost-wrap"><div class="cost-lbl"><span class="pais">${{p}}</span><span class="monto">USD ${{v.toLocaleString()}}+</span></div><div class="cost-bg"><div class="cost-fill" style="width:${{Math.round(v/17000*100)}}%;background:${{c}}"></div></div></div>`;
}});
try{{const s=JSON.parse(localStorage.getItem('whv3')||'{{}}');document.querySelectorAll('.check-item').forEach((e,i)=>{{if(s[i])e.classList.add('done');}});}}catch(e){{}}
</script>
</body>
</html>"""
    return html

# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print(f"WHV Auto-Update — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 50)

    print("\nPaso 1: Scrapeando estados de visas...")
    estados = scrape_calendario()

    print("\nEstados detectados:")
    for pais, estado in estados.items():
        print(f"  {pais}: {estado}")

    print("\nPaso 2: Generando index.html...")
    html = generar_html(estados)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html generado: {len(html):,} caracteres")
    print("\nListo! GitHub Pages se actualizará en ~2 minutos.")

if __name__ == "__main__":
    main()
