#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OTEC Santa Mónica: asistente paso a paso y portada PDF para cotizaciones.

Requiere Python 3.10 o superior.
Instalar:
    python -m pip install streamlit reportlab svglib pillow defusedxml
Ejecutar:
    python -m streamlit run REPORTE_PDF.py

LOGO: guardar OTEC_Santa_Monica_Opcion_1.svg en la MISMA carpeta que este
archivo (también funciona dentro de assets/). Puede cargarse otro SVG/PNG/JPG
desde el formulario. Se detecta el archivo por nombre, no mediante IA ni OCR.
Un SVG usa svglib y se dibuja como vector en el PDF, sin necesitar Cairo.

PROGRESO: se guarda automáticamente al confirmar un campo (Enter o al salir
del campo) en una base SQLite dentro de .reporte_datos/, junto al script.
El identificador del borrador queda en la URL (?borrador=...). Actualizar esa
misma URL recupera el borrador, su logo cargado y sus pasos pendientes.
Conservar esa URL para volver después. Cada borrador usa un identificador
aleatorio. El enlace da acceso al borrador: usar en equipo propio o acceso privado.
REPORTE_DATA_DIR permite elegir otra carpeta con almacenamiento persistente.
En alojamientos con disco temporal, un reinicio o despliegue puede borrar la
base; descargar un respaldo JSON permite recuperarlo incluso en otro equipo.
No se usan st.cache_data ni Session State como única copia de los datos.

No se conecta a Mercado Público: los datos iniciales son el ejemplo aportado.
Revisar y actualizar los datos antes de descargar. La portada no sustituye la
propuesta técnica, anexos ni la presentación de la oferta en Mercado Público.

Prueba sin interfaz (no requiere Streamlit):
    python REPORTE_PDF.py --demo-pdf portada_ejemplo.pdf
La prueba usa el logo local si existe; si no existe, genera solo texto.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import re
import sqlite3
from uuid import uuid4
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

import reportlab
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph


BASE_DIR = Path(__file__).resolve().parent
LOGO_NAME = "OTEC_Santa_Monica_Opcion_1.svg"
NAVY = colors.HexColor("#153445")
GOLD = colors.HexColor("#B78D45")
INK = colors.HexColor("#223D4C")
MUTED = colors.HexColor("#5A6F7D")
PALE = colors.HexColor("#F0F4F5")
WHITE = colors.white
MAX_LOGO_BYTES = 5 * 1024 * 1024

# Fuentes incluidas por ReportLab: el PDF no depende de las fuentes del equipo.
FUENTES = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("OTEC-Regular", str(FUENTES / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("OTEC-Bold", str(FUENTES / "VeraBd.ttf")))
pdfmetrics.registerFontFamily("OTEC-Regular", normal="OTEC-Regular", bold="OTEC-Bold")


@dataclass
class Datos:
    proceso: str = "1057545-246-COT26"
    modalidad: str = "Compra Ágil"
    titulo: str = "CURSO APLICACIÓN DE IA Y ANÁLISIS DE DATOS"
    comprador: str = "Servicio de Salud Los Ríos"
    rut_comprador: str = "61.607.500-4"
    lugar: str = "A convenir; Valdivia, Región de Los Ríos"
    cupos: int = 20
    plazo: str = "1 día, según lo indicado en la solicitud"
    presupuesto: int = 2_400_000
    cierre_1: str = "11-11-2026 a las 09:01:00"
    cierre_2: str = "13-11-2026 a las 09:20:01"
    alcance: str = (
        "20 cupos para curso de aplicación de IA y análisis de datos, "
        "conforme a las bases técnicas. Se exige adjuntar propuesta detallada "
        "para evaluación; la solicitud indica rechazo si no se adjunta."
    )
    oferente: str = "OTEC Santa Mónica"
    rut_oferente: str = ""
    contacto: str = ""
    fecha: str = ""
    vigencia: str = ""
    detalle: str = ""
    cantidad: int = 1  # 1 Global; no confundir con los 20 cupos.
    valor_unitario: int = 0
    despacho: int = 0
    impuesto: str = "Por definir"
    tasa: int = 19


def pesos(valor: int) -> str:
    return "$ " + f"{valor:,}".replace(",", ".")


def montos(d: Datos) -> tuple[int, int | None, int | None]:
    """CLP enteros. En este formulario el impuesto se aplica al neto + despacho."""
    neto = d.cantidad * d.valor_unitario + d.despacho
    if d.impuesto == "Por definir":
        return neto, None, None
    iva = 0 if d.impuesto == "Exento / sin impuesto" else int(
        (Decimal(neto) * Decimal(d.tasa) / 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    return neto, iva, neto + iva


def logo_local() -> Path | None:
    """Resuelve desde el script: funciona aunque se inicie en otra carpeta."""
    nombres = [LOGO_NAME, "logo.svg", "logo.png", "logo.jpg", "logo.jpeg"]
    for carpeta in (BASE_DIR, BASE_DIR / "assets"):
        for nombre in nombres:
            ruta = carpeta / nombre
            if ruta.is_file():
                return ruta
    return None


def preparar_logo(raw: bytes, nombre: str):
    """Devuelve (tipo, contenido, ancho, alto); rechaza SVG con recursos externos."""
    if not raw or len(raw) > MAX_LOGO_BYTES:
        raise ValueError("El logo debe pesar entre 1 byte y 5 MB.")
    extension = Path(nombre).suffix.lower()
    if extension == ".svg":
        from defusedxml import ElementTree
        from svglib.svglib import svg2rlg

        root = ElementTree.fromstring(raw)
        if root.tag.split("}")[-1].lower() != "svg":
            raise ValueError("El archivo no contiene un SVG válido.")
        for node in root.iter():
            tag = node.tag.split("}")[-1].lower()
            if tag in {"script", "foreignobject"}:
                raise ValueError("El SVG debe contener solo elementos gráficos.")
            for key, value in node.attrib.items():
                if key.split("}")[-1].lower() in {"href", "src"}:
                    if value and not value.startswith("#"):
                        raise ValueError("Exporta el SVG sin imágenes o recursos externos.")
            contenido = " ".join(node.attrib.values()) + " " + (node.text or "")
            if re.search(r"@import", contenido, re.I):
                raise ValueError("El SVG no puede importar estilos externos.")
            for ref in re.findall(r"url\s*\((.*?)\)", contenido, re.I | re.S):
                if not ref.strip(" \t\r\n\"'").startswith("#"):
                    raise ValueError("El SVG contiene un recurso externo.")
        drawing = svg2rlg(BytesIO(raw))
        if drawing is None or drawing.width <= 0 or drawing.height <= 0:
            raise ValueError("No se pudo convertir el SVG; intenta con un PNG.")
        return "svg", drawing, drawing.width, drawing.height
    if extension not in {".png", ".jpg", ".jpeg"}:
        raise ValueError("Usa un logo SVG, PNG o JPG.")
    from PIL import Image

    with Image.open(BytesIO(raw)) as img:
        if img.width * img.height > 20_000_000:
            raise ValueError("El logo supera los 20 megapíxeles; reduce su tamaño.")
        img.load()
        image = img.convert("RGBA")
    return "raster", ImageReader(image), image.width, image.height


def texto(c, contenido, x, y, ancho, alto, size=10, color=INK,
          bold=False, min_size=8, align=TA_LEFT):
    """Caja con ajuste de fuente. Falla si no cabe: nunca corta texto en silencio."""
    contenido = str(contenido).strip() or "Por completar"
    seguro = escape(contenido).replace("\n", "<br/>")
    while size >= min_size:
        style = ParagraphStyle(
            "campo", fontName="OTEC-Bold" if bold else "OTEC-Regular",
            fontSize=size, leading=size * 1.22, textColor=color,
            alignment=align, splitLongWords=True,
        )
        par = Paragraph(seguro, style)
        _, height = par.wrap(ancho, alto)
        if height <= alto:
            par.drawOn(c, x, y + alto - height)
            return
        size -= 0.5
    raise ValueError("Un campo es demasiado largo para la portada. Reduce su texto.")


def etiqueta(c, s, x, y, ancho=500):
    texto(c, s.upper(), x, y, ancho, 12, 7.5, MUTED, True, 7.5)


def generar_pdf(d: Datos, logo=None, es_borrador=False) -> bytes:
    """Genera una portada A4, de una página, sin rutas temporales compartidas."""
    if min(d.valor_unitario, d.despacho, d.presupuesto) < 0 or d.cantidad < 1:
        raise ValueError("Los montos no pueden ser negativos y la cantidad debe ser mayor que cero.")
    if d.cupos < 0 or not 0 <= d.tasa <= 100:
        raise ValueError("Revisa cupos y tasa de impuesto.")
    if d.impuesto not in {"Por definir", "Exento / sin impuesto", "Con impuesto"}:
        raise ValueError("Selecciona un tratamiento de impuesto válido.")
    if len(d.detalle) > 255:
        raise ValueError("El detalle de cotización admite hasta 255 caracteres.")
    out = BytesIO()
    c = canvas.Canvas(out, pagesize=A4)
    w, h = A4
    c.setTitle(f"Propuesta - {d.proceso}")
    c.setAuthor(d.oferente)
    c.setSubject(d.titulo)
    c.setFillColor(NAVY)
    c.rect(0, 0, 13, h, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(42, h - 46, w - 84, 3, fill=1, stroke=0)

    if logo is not None:
        tipo, obj, lw, lh = logo
        scale = min(250 / lw, 70 / lh)
        x, y = 42, 711 + (70 - lh * scale) / 2
        if tipo == "svg":
            c.saveState()
            c.translate(x, y)
            c.scale(scale, scale)
            renderPDF.draw(obj, c, 0, 0)
            c.restoreState()
        else:
            c.drawImage(obj, x, y, width=lw * scale, height=lh * scale, mask="auto")
    else:
        texto(c, d.oferente, 42, 722, 260, 48, 22, NAVY, True, 13)
    etiqueta(c, "Fecha de propuesta", 365, 763, 188)
    texto(c, d.fecha or "Por completar", 365, 742, 188, 20, 10, align=TA_RIGHT)
    texto(c, d.modalidad, 365, 715, 188, 20, 10, GOLD, True, align=TA_RIGHT)

    etiqueta(c, "Portada de propuesta" if not es_borrador else "Portada - borrador con pendientes", 42, 684)
    texto(c, d.titulo or "NOMBRE DEL SERVICIO POR COMPLETAR", 42, 592, 511, 82, 23, NAVY, True, 13)
    texto(c, f"Proceso {d.proceso or 'por completar'}", 42, 567, 511, 21, 11, GOLD, True)

    c.setFillColor(PALE)
    c.roundRect(42, 477, 511, 79, 8, fill=1, stroke=0)
    etiqueta(c, "Organismo comprador", 56, 533, 480)
    texto(c, d.comprador or "Organismo por completar", 56, 505, 480, 25, 15, NAVY, True, 10)
    texto(c, f"RUT {d.rut_comprador or 'por completar'} | {d.lugar or 'Lugar por completar'}",
          56, 483, 480, 20, 9, MUTED)

    for x, label, value in (
        (42, "Cupos", str(d.cupos) if d.cupos else "Por completar"),
        (217, "Presupuesto estimado", pesos(d.presupuesto) if d.presupuesto else "Por completar"),
        (392, "Plazo de entrega", d.plazo),
    ):
        etiqueta(c, label, x, 453, 161)
        texto(c, value, x, 419, 161, 30, 14, NAVY, True, 9)

    c.setStrokeColor(colors.HexColor("#D8E0E4"))
    c.line(42, 411, 553, 411)
    for x, label, value in (
        (42, "Cierre primer llamado", d.cierre_1),
        (307, "Cierre segundo llamado", d.cierre_2),
    ):
        etiqueta(c, label, x, 391, 246)
        texto(c, value, x, 364, 246, 24, 10, INK, True)

    etiqueta(c, "Alcance y requisito clave", 42, 340)
    texto(c, d.alcance, 42, 275, 511, 61, 10.5, INK, min_size=8.5)

    etiqueta(c, "Oferente", 42, 252)
    texto(c, d.oferente, 42, 225, 511, 24, 13, NAVY, True)
    texto(c, f"RUT: {d.rut_oferente or 'por completar'} | Contacto: {d.contacto or 'por completar'}",
          42, 198, 511, 24, 9, MUTED)

    neto, iva, total = montos(d)
    c.setFillColor(NAVY)
    c.roundRect(42, 130, 511, 58, 7, fill=1, stroke=0)
    texto(c, "MONTO TOTAL OFERTADO", 55, 168, 240, 12, 7.5, WHITE, True, 7.5)
    total_text = "Por completar" if d.valor_unitario <= 0 or total is None else pesos(total)
    texto(c, total_text, 55, 139, 235, 27, 20, WHITE, True, 12)
    if d.valor_unitario <= 0:
        desglose = "Oferta económica pendiente"
    elif total is None:
        desglose = f"Neto + despacho: {pesos(neto)}\nImpuesto por definir"
    else:
        desglose = f"Neto + despacho: {pesos(neto)}\nImpuesto: {pesos(iva)}"
    texto(c, desglose, 314, 140, 225, 36, 9, WHITE, align=TA_RIGHT)

    detalle = d.detalle or "Detalle de cotización por completar."
    texto(c, detalle, 42, 79, 511, 44, 9, INK, min_size=8)
    texto(c, f"Vigencia de la oferta: {d.vigencia or 'por completar'}", 42, 60, 511, 15, 8, MUTED)
    c.setStrokeColor(GOLD)
    c.line(42, 50, 553, 50)
    texto(c, "Portada de propuesta. Adjuntar propuesta detallada y anexos exigidos por las bases.",
          42, 29, 511, 16, 7.5, MUTED, min_size=7.5)
    c.showPage()
    c.save()
    return out.getvalue()



PASOS = ["Identidad y logo", "Proceso de compra", "Organismo comprador",
         "Servicio solicitado", "Plazos y montos", "Revisión y portada"]
ETIQUETAS = {
    "oferente": "Nombre o razón social", "rut_oferente": "RUT oferente",
    "contacto": "Contacto", "fecha": "Fecha de propuesta", "proceso": "Código del proceso",
    "titulo": "Nombre del servicio / curso", "modalidad": "Modalidad",
    "comprador": "Organismo comprador", "rut_comprador": "RUT comprador",
    "lugar": "Lugar / dirección de entrega", "cupos": "Cupos / participantes",
    "plazo": "Plazo de entrega", "alcance": "Resumen del servicio y requisito clave",
    "presupuesto": "Presupuesto estimado (CLP)", "cierre_1": "Cierre primer llamado",
    "cierre_2": "Cierre segundo llamado (opcional)", "cantidad": "Unidades globales",
    "valor_unitario": "Valor unitario neto (CLP)", "despacho": "Despacho neto (CLP)",
    "impuesto": "Tratamiento de impuesto", "tasa": "Tasa de impuesto (%)",
    "vigencia": "Vigencia de la oferta", "detalle": "Detalle de cotización (máximo 255 caracteres)",
}
REQUERIDOS = [
    ["oferente", "rut_oferente", "contacto", "fecha"],
    ["proceso", "titulo", "modalidad"],
    ["comprador", "rut_comprador", "lugar"],
    ["cupos", "plazo", "alcance"],
    ["presupuesto", "cierre_1"],
]
LIMITES = {
    "oferente": 150, "rut_oferente": 20, "contacto": 130, "fecha": 40,
    "proceso": 60, "titulo": 160, "modalidad": 40, "comprador": 150,
    "rut_comprador": 20, "lugar": 150, "plazo": 65, "alcance": 450,
    "cierre_1": 70, "cierre_2": 70, "vigencia": 80, "detalle": 255, "impuesto": 40,
}
TOPES = {"cupos": 100000, "cantidad": 100000, "tasa": 100,
         "presupuesto": 10**12, "valor_unitario": 10**12, "despacho": 10**12}


def hoy_chile():
    try:
        return datetime.now(ZoneInfo("America/Santiago")).strftime("%d-%m-%Y")
    except Exception:
        return ""


def nuevo_borrador(ejemplo=False):
    d = asdict(Datos())
    if not ejemplo:
        for campo in LIMITES:
            d[campo] = ""
        d.update(oferente="OTEC Santa Mónica", modalidad="Compra Ágil", cupos=0,
                 presupuesto=0, impuesto="Por definir")
    d["fecha"] = hoy_chile()
    return {"version": 1, "datos": d, "paso": 0, "desbloqueado": 0,
            "estados": ["sin iniciar"] * 5, "logo_modo": "Automático",
            "logo_nombre": "", "logo_base64": "", "actualizado": ""}


def validar_borrador(b):
    """El respaldo usa JSON; no se ejecuta código ni se deserializa pickle."""
    if not isinstance(b, dict) or b.get("version") != 1:
        raise ValueError("El respaldo no es de una versión compatible.")
    d = b.get("datos")
    if not isinstance(d, dict) or set(d) != set(asdict(Datos())):
        raise ValueError("El respaldo no contiene los campos esperados.")
    for campo, limite in LIMITES.items():
        if not isinstance(d[campo], str) or len(d[campo]) > limite:
            raise ValueError(f"Campo inválido o demasiado largo: {campo}.")
    for campo, tope in TOPES.items():
        minimo = 1 if campo == "cantidad" else 0
        if type(d[campo]) is not int or not minimo <= d[campo] <= tope:
            raise ValueError(f"Valor numérico inválido: {campo}.")
    if d["modalidad"] not in {"Compra Ágil", "Licitación pública", "Otra"}:
        raise ValueError("Modalidad inválida.")
    if d["impuesto"] not in {"Por definir", "Exento / sin impuesto", "Con impuesto"}:
        raise ValueError("Tratamiento de impuesto inválido.")
    if type(b.get("desbloqueado")) is not int or not 0 <= b["desbloqueado"] <= 5:
        raise ValueError("Secuencia de pasos inválida.")
    if type(b.get("paso")) is not int or not 0 <= b["paso"] <= b["desbloqueado"]:
        raise ValueError("Paso actual inválido.")
    estados = b.get("estados")
    if not isinstance(estados, list) or len(estados) != 5 or any(
        x not in {"sin iniciar", "en curso", "completo", "pendiente"} for x in estados
    ):
        raise ValueError("Estados de pasos inválidos.")
    if b.get("logo_modo") not in {"Automático", "Cargado", "Sin logo por ahora"}:
        raise ValueError("Modo de logo inválido.")
    if not isinstance(b.get("logo_nombre"), str) or len(b["logo_nombre"]) > 200:
        raise ValueError("Nombre del logo inválido.")
    encoded = b.get("logo_base64")
    if not isinstance(encoded, str) or len(encoded) > 7_000_000:
        raise ValueError("Logo demasiado grande.")
    if encoded:
        raw = base64.b64decode(encoded, validate=True)
        preparar_logo(raw, b["logo_nombre"])
    # Normaliza claves; ignora cualquier metadato desconocido del JSON.
    limpio = nuevo_borrador()
    for campo in limpio:
        if campo != "actualizado":
            limpio[campo] = b[campo]
    limpio["actualizado"] = str(b.get("actualizado", ""))[:80]
    return limpio


def conectar_db():
    carpeta = Path(os.environ.get("REPORTE_DATA_DIR", str(BASE_DIR / ".reporte_datos")))
    carpeta.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(carpeta / "borradores.sqlite3", timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS borradores "
               "(id TEXT PRIMARY KEY, contenido TEXT NOT NULL, revision INTEGER NOT NULL)")
    db.commit()
    return db


def cargar_borrador(identificador):
    db = conectar_db()
    try:
        row = db.execute("SELECT contenido, revision FROM borradores WHERE id = ?",
                         (identificador,)).fetchone()
        return (validar_borrador(json.loads(row[0])), row[1]) if row else (None, -1)
    finally:
        db.close()


def guardar_borrador(identificador, borrador, revision):
    if not re.fullmatch(r"[a-f0-9]{32}", identificador):
        raise ValueError("Identificador de borrador inválido.")
    borrador = validar_borrador(borrador)
    payload = json.dumps(borrador, ensure_ascii=False)
    db = conectar_db()
    try:
        with db:
            if revision == -1:
                db.execute("INSERT INTO borradores VALUES (?, ?, 0)", (identificador, payload))
                return 0
            cursor = db.execute(
                "UPDATE borradores SET contenido = ?, revision = revision + 1 "
                "WHERE id = ? AND revision = ?", (payload, identificador, revision)
            )
            if cursor.rowcount != 1:
                raise ValueError("Este borrador cambió en otra pestaña. Descarga tu respaldo y recarga la última versión guardada.")
            return revision + 1
    finally:
        db.close()


def obtener_logo(b):
    if b["logo_modo"] == "Sin logo por ahora":
        return None
    if b["logo_modo"] == "Cargado":
        return preparar_logo(base64.b64decode(b["logo_base64"], validate=True), b["logo_nombre"]) if b["logo_base64"] else None
    ruta = logo_local()
    if ruta:
        if ruta.stat().st_size > MAX_LOGO_BYTES:
            raise ValueError("El logo local supera los 5 MB.")
        return preparar_logo(ruta.read_bytes(), ruta.name)
    return None


def faltantes_paso(b, paso):
    pendientes = [ETIQUETAS[c] for c in REQUERIDOS[paso]
                  if not str(b["datos"][c]).strip() or b["datos"][c] == 0]
    if paso == 0 and b["logo_modo"] != "Sin logo por ahora":
        try:
            if obtener_logo(b) is None:
                pendientes.append(f"Logo {LOGO_NAME}")
        except Exception:
            pendientes.append("Corregir el archivo del logo")
    return pendientes


def lista_pendientes(b):
    pendientes = []
    for i in range(5):
        faltantes = faltantes_paso(b, i)
        if b["estados"][i] != "completo" or faltantes:
            pendientes.append((i, faltantes or ["Revisar y confirmar este paso"]))
    return pendientes


def main():
    import streamlit as st

    st.set_page_config(page_title="OTEC Santa Mónica | Portada PDF", page_icon="📄", layout="wide")
    st.title("Portada de reporte · OTEC Santa Mónica")
    st.caption("Completa un paso, déjalo pendiente si falta información y continúa. Por ahora generamos solo la portada.")

    ident = st.query_params.get("borrador", "")
    if not re.fullmatch(r"[a-f0-9]{32}", ident):
        ident = uuid4().hex
        st.query_params["borrador"] = ident
    if st.session_state.get("borrador_id") != ident:
        for k in list(st.session_state):
            if k.startswith("w_") or k in {"pdf_bytes", "pdf_firma", "aviso"}:
                del st.session_state[k]
        try:
            b, rev = cargar_borrador(ident)
            if b is None:
                b, rev = nuevo_borrador(), -1
            error = ""
        except Exception as exc:
            b, rev, error = nuevo_borrador(), -1, str(exc)
        st.session_state.update(borrador_id=ident, borrador=b, revision=rev, error_guardado=error)

    def persistir():
        b = st.session_state.borrador
        b["actualizado"] = datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            rev = guardar_borrador(ident, b, st.session_state.revision)
            st.session_state.revision = rev
            st.session_state.error_guardado = ""
        except Exception as exc:
            st.session_state.error_guardado = str(exc)
            return False
        return True

    def cambiar_campo(campo):
        b = st.session_state.borrador
        b["datos"][campo] = st.session_state["w_" + campo]
        paso = b["paso"]
        if paso < 5:
            b["estados"][paso] = "en curso"
        persistir()

    def input_texto(campo, area=False):
        key = "w_" + campo
        if key not in st.session_state:
            st.session_state[key] = st.session_state.borrador["datos"][campo]
        fn = st.text_area if area else st.text_input
        return fn(ETIQUETAS[campo], key=key, max_chars=LIMITES[campo],
                  on_change=cambiar_campo, args=(campo,))

    def input_numero(campo, minimo=0):
        key = "w_" + campo
        if key not in st.session_state:
            st.session_state[key] = st.session_state.borrador["datos"][campo]
        return st.number_input(ETIQUETAS[campo], key=key, min_value=minimo,
                               max_value=TOPES[campo], on_change=cambiar_campo, args=(campo,))

    def input_opciones(campo, opciones):
        key = "w_" + campo
        if key not in st.session_state:
            st.session_state[key] = st.session_state.borrador["datos"][campo]
        return st.selectbox(ETIQUETAS[campo], opciones, key=key,
                            on_change=cambiar_campo, args=(campo,))

    def ir(paso):
        st.session_state.borrador["paso"] = paso
        persistir()
        st.rerun()

    def cargar_logo_ui():
        archivo = st.session_state.get("w_upload_logo")
        if archivo is None:
            return
        try:
            raw = archivo.getvalue()
            preparar_logo(raw, archivo.name)
            b = st.session_state.borrador
            b.update(logo_base64=base64.b64encode(raw).decode("ascii"),
                     logo_nombre=archivo.name[:200], logo_modo="Cargado")
            b["estados"][0] = "en curso"
            st.session_state.w_logo_modo = "Cargado"
            persistir()
        except Exception as exc:
            st.session_state.aviso = f"No se pudo cargar el logo: {exc}"

    def nuevo(ejemplo=False, contenido=None):
        b = contenido if contenido is not None else nuevo_borrador(ejemplo)
        token = uuid4().hex
        # Guardar antes de cambiar la URL. Los borradores previos se conservan.
        guardar_borrador(token, b, -1)
        st.query_params["borrador"] = token
        st.rerun()

    b = st.session_state.borrador
    if st.session_state.revision == -1 and not st.session_state.error_guardado:
        persistir()
    paso = b["paso"]
    pendientes = lista_pendientes(b)

    with st.sidebar:
        st.header("Tu avance")
        completos = sum(b["estados"][i] == "completo" and not faltantes_paso(b, i) for i in range(5))
        st.progress(completos / 5, text=f"{completos} de 5 pasos completos")
        iconos = {"completo": "✅", "pendiente": "⏳", "en curso": "✏️", "sin iniciar": "○"}
        for i, nombre in enumerate(PASOS):
            abierto = i <= b["desbloqueado"]
            icono = "📄" if i == 5 else iconos[b["estados"][i]]
            if st.button(f"{icono if abierto else '🔒'} {i+1}. {nombre}", key=f"nav_{i}",
                         disabled=not abierto, type="primary" if i == paso else "secondary"):
                ir(i)
        st.divider()
        st.subheader("Lista de pendientes")
        if not pendientes:
            st.success("Todos los pasos están completos.")
        for i, items in pendientes:
            with st.expander(f"Paso {i+1}: {PASOS[i]} ({len(items)})"):
                for item in items:
                    st.write(f"• {item}")
                if i <= b["desbloqueado"] and st.button("Completar este paso", key=f"pending_{i}"):
                    ir(i)
        st.divider()
        if st.button("Guardar progreso ahora"):
            if persistir():
                st.success("Progreso guardado.")
        st.caption("Se guarda al presionar Enter o salir de cada campo. Conserva esta URL para volver al mismo borrador.")
        respaldo = json.dumps(b, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button("Descargar respaldo del progreso", respaldo,
                           file_name=f"Borrador_{ident[:8]}.json", mime="application/json")
        with st.expander("Recuperar respaldo / nuevo reporte"):
            archivo = st.file_uploader("Respaldo JSON", type=["json"], key="restore_json")
            if st.button("Importar respaldo", disabled=archivo is None):
                try:
                    if archivo.size > 8 * 1024 * 1024:
                        raise ValueError("El respaldo supera los 8 MB.")
                    restaurado = validar_borrador(json.loads(archivo.getvalue().decode("utf-8")))
                    nuevo(contenido=restaurado)
                except Exception as exc:
                    st.error(f"No se pudo importar: {exc}")
            if st.button("Nuevo reporte vacío"):
                try:
                    nuevo()
                except Exception as exc:
                    st.error(str(exc))
            if st.button("Nuevo con ejemplo Los Ríos"):
                try:
                    nuevo(ejemplo=True)
                except Exception as exc:
                    st.error(str(exc))
            st.caption("Crear o importar abre otro borrador y conserva el anterior en su URL.")
        st.caption("En un servidor con disco temporal, descarga el respaldo antes de reiniciar o actualizar el alojamiento.")

    if st.session_state.error_guardado:
        st.error("No se pudo guardar: " + st.session_state.error_guardado)
        st.info("Descarga un respaldo JSON para conservar lo que llevas escrito.")
        if st.button("Recargar última versión guardada"):
            del st.session_state["borrador_id"]
            st.rerun()
    elif b["actualizado"]:
        st.caption(f"Guardado automático · {b['actualizado']}")
    if "aviso" in st.session_state:
        st.warning(st.session_state.pop("aviso"))

    st.subheader(f"Paso {paso+1} de 6 · {PASOS[paso]}")
    if paso == 0:
        input_texto("oferente")
        input_texto("rut_oferente")
        input_texto("contacto")
        input_texto("fecha")
        st.markdown("**Logo de la portada**")
        opciones = ["Automático", "Cargado", "Sin logo por ahora"]
        if "w_logo_modo" not in st.session_state:
            st.session_state.w_logo_modo = b["logo_modo"]
        def modo_cambiado():
            st.session_state.borrador["logo_modo"] = st.session_state.w_logo_modo
            st.session_state.borrador["estados"][0] = "en curso"
            persistir()
        st.selectbox("Origen del logo", opciones, key="w_logo_modo", on_change=modo_cambiado)
        st.caption(f"Automático: {LOGO_NAME}, junto a REPORTE_PDF.py o dentro de assets/.")
        st.file_uploader("Cargar o reemplazar logo SVG / PNG / JPG", type=["svg", "png", "jpg", "jpeg"],
                         key="w_upload_logo", on_change=cargar_logo_ui)
        try:
            logo = obtener_logo(b)
            if logo is not None:
                st.success("Logo listo: " + (b["logo_nombre"] if b["logo_modo"] == "Cargado" else LOGO_NAME))
            elif b["logo_modo"] == "Sin logo por ahora":
                st.info("La portada usará el nombre de la OTEC como encabezado.")
            else:
                st.warning("Logo no encontrado. Puedes cargarlo o dejar este paso pendiente.")
        except Exception as exc:
            st.warning(f"Logo pendiente: {exc}")
    elif paso == 1:
        input_texto("proceso")
        input_texto("titulo")
        input_opciones("modalidad", ["Compra Ágil", "Licitación pública", "Otra"])
    elif paso == 2:
        input_texto("comprador")
        input_texto("rut_comprador")
        input_texto("lugar")
    elif paso == 3:
        input_numero("cupos")
        input_texto("plazo")
        input_texto("alcance", area=True)
        st.caption("Resume lo esencial de las bases. Esta app no lee anexos ni presenta la cotización en Mercado Público.")
    elif paso == 4:
        input_numero("presupuesto")
        input_texto("cierre_1")
        input_texto("cierre_2")
        st.caption("Escribe los plazos tal como aparecen en la ficha, con fecha y hora.")
        with st.expander("Oferta económica y vigencia (opcional por ahora)"):
            st.caption("Las unidades globales y los cupos son cantidades diferentes.")
            input_numero("cantidad", 1)
            input_numero("valor_unitario")
            input_numero("despacho")
            input_opciones("impuesto", ["Por definir", "Exento / sin impuesto", "Con impuesto"])
            if b["datos"]["impuesto"] == "Con impuesto":
                input_numero("tasa")
            st.caption("La tasa se aplica al neto más despacho. Selecciona el tratamiento que corresponda a tu oferta.")
            input_texto("vigencia")
            input_texto("detalle", area=True)
            neto, iva, total = montos(Datos(**b["datos"]))
            st.write(f"Neto + despacho: {pesos(neto)} · Total: {pesos(total) if total is not None else 'por definir'}")

    if paso < 5:
        faltan = faltantes_paso(b, paso)
        st.divider()
        a, c, e = st.columns([1, 2, 2])
        if a.button("Anterior", disabled=paso == 0):
            ir(paso - 1)
        if c.button("Guardar y continuar", type="primary"):
            if faltan:
                st.warning("Falta completar: " + ", ".join(faltan) + ". También puedes dejar este paso pendiente.")
            else:
                b["estados"][paso] = "completo"
                b["desbloqueado"] = max(b["desbloqueado"], paso + 1)
                ir(paso + 1)
        if e.button("Dejar pendiente y continuar"):
            b["estados"][paso] = "pendiente"
            b["desbloqueado"] = max(b["desbloqueado"], paso + 1)
            ir(paso + 1)
    else:
        d = Datos(**b["datos"])
        st.write("**Reporte:** " + (d.titulo or "Nombre del servicio por completar"))
        st.write("**Proceso:** " + (d.proceso or "Por completar"))
        st.write("**Comprador:** " + (d.comprador or "Por completar"))
        st.write("**Oferente:** " + (d.oferente or "Por completar"))
        if pendientes:
            st.warning(f"Hay {len(pendientes)} pasos por completar o revisar. Puedes descargar una portada marcada como borrador.")
        else:
            st.success("Los pasos de la portada están completos.")
        st.caption("Los montos de oferta y vigencia son opcionales en esta etapa; si faltan, aparecerán como 'por completar'.")
        try:
            logo = obtener_logo(b)
        except Exception as exc:
            logo = None
            st.warning(f"La portada se generará sin imagen: {exc}")
        # Cambiar los metadatos del logo automático también invalida el PDF.
        logo_firma = b["logo_base64"]
        if b["logo_modo"] == "Automático" and logo_local() is not None:
            ruta = logo_local()
            logo_firma = str(ruta.stat().st_mtime_ns) + str(ruta.stat().st_size)
        firma = hashlib.sha256((json.dumps([b["datos"], b["estados"], b["logo_modo"], logo_firma],
                                           sort_keys=True, ensure_ascii=False)).encode("utf-8")).hexdigest()
        if st.button("Generar portada PDF", type="primary"):
            try:
                st.session_state.pdf_bytes = generar_pdf(d, logo, es_borrador=bool(pendientes))
                st.session_state.pdf_firma = firma
                st.success("Portada generada. Ya puedes descargarla.")
            except Exception as exc:
                st.error(f"No se pudo generar: {exc}")
        if st.session_state.get("pdf_firma") == firma:
            codigo = re.sub(r"[^a-zA-Z0-9_-]", "_", d.proceso)[:80] or "borrador"
            st.download_button("Descargar portada PDF", st.session_state.pdf_bytes,
                               file_name=f"Portada_{codigo}.pdf", mime="application/pdf")
        elif st.session_state.get("pdf_bytes"):
            st.info("Los datos cambiaron. Pulsa Generar portada PDF para obtener la versión actualizada.")
        if st.button("Volver al paso anterior"):
            ir(4)
        st.caption("El PDF contiene solo la portada. Agregaremos el contenido del reporte en las siguientes versiones.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-pdf", type=Path, help="Crear PDF de ejemplo sin abrir Streamlit")
    args, _ = parser.parse_known_args()
    if args.demo_pdf:
        ruta_logo = logo_local()
        demo_logo = preparar_logo(ruta_logo.read_bytes(), ruta_logo.name) if ruta_logo else None
        demo = replace(Datos(), fecha="10-11-2026")
        args.demo_pdf.write_bytes(generar_pdf(demo, demo_logo))
        print(f"PDF generado: {args.demo_pdf.resolve()}")
    else:
        main()
