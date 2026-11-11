#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OTEC Santa Mónica: formulario y portada PDF para cotizaciones.

Requiere Python 3.10 o superior.
Instalar:
    python -m pip install streamlit reportlab svglib pillow defusedxml
Ejecutar:
    python -m streamlit run REPORTE_PDF.py

LOGO: guardar OTEC_Santa_Monica_Opcion_1.svg en la MISMA carpeta que este
archivo (también funciona dentro de assets/). Puede cargarse otro SVG/PNG/JPG
desde el formulario. Se detecta el archivo por nombre, no mediante IA ni OCR.
Un SVG usa svglib y se dibuja como vector en el PDF, sin necesitar Cairo.

No se conecta a Mercado Público: los datos iniciales son el ejemplo aportado.
Revisar y actualizar los datos antes de descargar. La portada no sustituye la
propuesta técnica, anexos ni la presentación de la oferta en Mercado Público.

Prueba sin interfaz (no requiere Streamlit):
    python REPORTE_PDF.py --demo-pdf portada_ejemplo.pdf
La prueba usa el logo local si existe; si no existe, genera solo texto.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
import re
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
    contenido = str(contenido).strip() or "No informado"
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


def generar_pdf(d: Datos, logo=None) -> bytes:
    """Genera una portada A4, de una página, sin rutas temporales compartidas."""
    if not all(x.strip() for x in (d.proceso, d.titulo, d.comprador, d.oferente)):
        raise ValueError("Completa código, título, organismo comprador y oferente.")
    if min(d.valor_unitario, d.despacho, d.presupuesto) < 0 or d.cantidad < 1:
        raise ValueError("Los montos no pueden ser negativos y la cantidad debe ser mayor que cero.")
    if d.cupos < 1 or not 0 <= d.tasa <= 100:
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

    etiqueta(c, "Propuesta técnica y económica", 42, 684)
    texto(c, d.titulo, 42, 592, 511, 82, 23, NAVY, True, 13)
    texto(c, f"Proceso {d.proceso}", 42, 567, 511, 21, 11, GOLD, True)

    c.setFillColor(PALE)
    c.roundRect(42, 477, 511, 79, 8, fill=1, stroke=0)
    etiqueta(c, "Organismo comprador", 56, 533, 480)
    texto(c, d.comprador, 56, 505, 480, 25, 15, NAVY, True, 10)
    texto(c, f"RUT {d.rut_comprador or 'por completar'} | {d.lugar}",
          56, 483, 480, 20, 9, MUTED)

    for x, label, value in (
        (42, "Cupos", str(d.cupos)),
        (217, "Presupuesto estimado", pesos(d.presupuesto)),
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
    if total is None:
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


def main():
    import streamlit as st

    st.set_page_config(page_title="OTEC Santa Mónica | Portada PDF", page_icon="📄", layout="wide")
    st.title("Portada de propuesta · Mercado Público")
    st.caption("Completa los datos y descarga una portada A4 con tu logo.")
    st.info("Datos iniciales del ejemplo proporcionado. Revisa plazos y bases antes de usar la propuesta.")
    base = Datos()

    with st.sidebar:
        st.header("Logo de la OTEC")
        uploaded = st.file_uploader("Cargar logo (opcional)", type=["svg", "png", "jpg", "jpeg"])
        auto = logo_local()
        logo = None
        logo_error = False
        try:
            if uploaded is not None:
                logo = preparar_logo(uploaded.getvalue(), uploaded.name)
                st.success(f"Logo cargado: {uploaded.name}")
            elif auto is not None:
                if auto.stat().st_size > MAX_LOGO_BYTES:
                    raise ValueError("El logo local supera los 5 MB.")
                logo = preparar_logo(auto.read_bytes(), auto.name)
                st.success(f"Logo detectado: {auto.name}")
            else:
                st.warning(f"Guarda {LOGO_NAME} junto a REPORTE_PDF.py o carga el archivo aquí.")
        except Exception as exc:
            logo_error = True
            st.error(f"No se pudo leer el logo: {exc}")
        solo_texto = st.checkbox("Generar sin imagen de logo", value=False)
        if solo_texto:
            logo = None
        if logo is not None and logo[0] == "raster":
            st.caption("El logo conservará su proporción en el PDF.")
        st.caption("El SVG se incorpora como vector. Si usa filtros o efectos no compatibles, exporta una versión PNG.")

    st.subheader("1. Datos esenciales del proceso")
    a, b = st.columns(2)
    proceso = a.text_input("Código del proceso", base.proceso, max_chars=60)
    modalidad = b.selectbox("Modalidad", ["Compra Ágil", "Licitación pública", "Otra"])
    titulo = st.text_input("Nombre del servicio / curso", base.titulo, max_chars=160)
    comprador = a.text_input("Organismo comprador", base.comprador, max_chars=150)
    rut_comprador = b.text_input("RUT comprador", base.rut_comprador, max_chars=20)
    lugar = st.text_input("Lugar / dirección de entrega", base.lugar, max_chars=150)
    a, b, c = st.columns(3)
    cupos = a.number_input("Cupos / participantes", min_value=1, max_value=100000, value=base.cupos)
    presupuesto = b.number_input("Presupuesto estimado (CLP)", min_value=0, max_value=10**12, value=base.presupuesto, step=1000)
    plazo = c.text_input("Plazo de entrega", base.plazo, max_chars=65)
    a, b = st.columns(2)
    cierre_1 = a.text_input("Cierre primer llamado (hora de la ficha)", base.cierre_1, max_chars=70)
    cierre_2 = b.text_input("Cierre segundo llamado (si aplica)", base.cierre_2, max_chars=70)
    alcance = st.text_area("Resumen del servicio y requisitos relevantes", base.alcance, height=110, max_chars=450)
    st.caption("Las bases y el anexo mencionados no fueron cargados. Este formulario no analiza su contenido.")

    st.subheader("2. Datos del oferente")
    a, b = st.columns(2)
    oferente = a.text_input("Nombre o razón social", base.oferente, max_chars=150)
    rut_oferente = b.text_input("RUT oferente", max_chars=20)
    contacto = st.text_input("Contacto: nombre, correo o teléfono", max_chars=130)
    a, b = st.columns(2)
    try:
        hoy = datetime.now(ZoneInfo("America/Santiago")).strftime("%d-%m-%Y")
    except Exception:
        hoy = ""  # Permite ingreso manual si no está instalada la base de zonas.
    fecha = a.text_input("Fecha de la propuesta", hoy, max_chars=40)
    vigencia = b.text_input("Vigencia de la oferta", placeholder="Ej.: hasta el 30-11-2026", max_chars=80)

    st.subheader("3. Oferta económica")
    st.caption("El ejemplo solicita 1 Global para 20 cupos. Los montos se ingresan en pesos chilenos enteros.")
    a, b, c = st.columns(3)
    cantidad = a.number_input("Cantidad de unidades globales", min_value=1, max_value=100000, value=1)
    valor_unitario = b.number_input("Valor unitario neto (CLP)", min_value=0, max_value=10**12, value=0, step=1000)
    despacho = c.number_input("Despacho neto (CLP)", min_value=0, max_value=10**12, value=0, step=1000)
    a, b = st.columns(2)
    impuesto = a.selectbox("Tratamiento de impuesto", ["Por definir", "Exento / sin impuesto", "Con impuesto"])
    tasa = b.number_input("Tasa de impuesto (%)", min_value=0, max_value=100, value=19, disabled=impuesto != "Con impuesto")
    st.caption("Selecciona el tratamiento que corresponda a tu oferta. El cálculo aplica la tasa al neto más despacho.")
    detalle = st.text_area("Detalle breve de la cotización (máximo 255 caracteres)", max_chars=255, height=90)
    st.caption(f"{len(detalle)}/255 caracteres")

    d = Datos(
        proceso=proceso, modalidad=modalidad, titulo=titulo, comprador=comprador,
        rut_comprador=rut_comprador, lugar=lugar, cupos=int(cupos), plazo=plazo,
        presupuesto=int(presupuesto), cierre_1=cierre_1, cierre_2=cierre_2,
        alcance=alcance, oferente=oferente, rut_oferente=rut_oferente,
        contacto=contacto, fecha=fecha, vigencia=vigencia, detalle=detalle,
        cantidad=int(cantidad), valor_unitario=int(valor_unitario),
        despacho=int(despacho), impuesto=impuesto, tasa=int(tasa),
    )
    neto, iva, total = montos(d)
    a, b, c = st.columns(3)
    a.metric("Neto + despacho", pesos(neto))
    b.metric("Impuesto", "Por definir" if iva is None else pesos(iva))
    c.metric("Total oferta", "Por definir" if total is None else pesos(total))
    if total is not None and presupuesto > 0 and total > presupuesto:
        st.warning("El total ingresado supera el presupuesto estimado del ejemplo.")
    if not rut_oferente.strip() or not contacto.strip() or not vigencia.strip() or valor_unitario == 0:
        st.warning("Hay datos de oferta pendientes. En el PDF aparecerán como 'por completar'.")
    if logo_error and not solo_texto:
        st.error("Corrige el logo o selecciona generar sin imagen de logo.")
        return
    if logo is None and not solo_texto:
        st.info("Para descargar, carga el logo o selecciona generar sin imagen de logo.")
        return
    try:
        pdf = generar_pdf(d, logo)
    except Exception as exc:
        st.error(f"No se pudo generar la portada: {exc}")
        return
    # Se regenera con cada cambio: el botón siempre descarga los datos visibles.
    codigo_archivo = re.sub(r"[^a-zA-Z0-9_-]", "_", proceso)[:80] or "propuesta"
    st.download_button("Descargar portada PDF", data=pdf,
                       file_name=f"Portada_{codigo_archivo}.pdf", mime="application/pdf")
    st.caption("Esta app prepara una portada; la propuesta detallada y los anexos se adjuntan por separado en Mercado Público.")


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

