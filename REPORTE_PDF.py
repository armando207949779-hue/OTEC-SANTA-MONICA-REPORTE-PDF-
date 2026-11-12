# VERSION: 8.4 - SML / Diego titular y Daniel alternativo (sin oferta alternativa de precio)
# CURSO: Power BI con IA: Fundamentos y Aplicaciones para Profesionales
# CODIGO: 837-465-COT26 | MODALIDAD: Compra Ágil
# FECHA: 11-11-2026 America/Santiago
# ORGANISMO: Servicio Médico Legal | OFERTA: $2.690.000 CLP, exenta de IVA (a validar al emitir)
# Código base adaptado desde formulario editorial de OTEC Santa Mónica.
# Los datos de acceso, calendario y facturación deben revisarse en la ficha oficial.
# -*- coding: utf-8 -*-
#
# INSTRUCCIONES DE USO Y ADAPTACION A FUTURAS LICITACIONES
# 1. Instalar: python -m pip install -r requirements.txt
#    Dependencias: streamlit, reportlab, svglib, pillow, defusedxml.
# 2. Ejecutar: python -m streamlit run Generador_Propuesta_SML_837-465-COT26_DOS_RELATORES.py (Python 3.10 o superior).
# 3. La pestaña «Generar PDF» solo tiene logo opcional del comprador y botones.
#    La pestaña «Detalles y edición» contiene el formulario, con apartados cerrados.
#    El formulario pregunta por comprador, modalidad, lugar, participantes,
#    objetivos, contenidos, horas, docente, materiales, requisitos y precio.
#    Revisar cada respuesta, cargar los documentos y pulsar Generar reporte PDF.
# 4. Logo del oferente: se busca OTEC_Santa_Monica_Opcion_1.svg en la carpeta
#    o en assets/, logos/ e images/. Puede reemplazarse en «Detalles» por
#    SVG, PNG o JPG. Si no existe, se utiliza cabecera institucional en texto.
# 5. Para otra licitacion, editar DATOS_LICITACION, MODULOS, RELATOR_INICIAL,
#    ADJUNTOS_DECLARADOS, REQ_COMPRA, REQ_RELATOR y REQ_CERT. Actualizar este
#    encabezado. Los totales de horas y precios se calculan desde las respuestas.
# 6. PREGUNTAS controla los campos; INTRODUCCIONES los textos de apertura;
#    generar_pdf() controla la estructura. Usar lenguaje de propuesta comercial.
#    Las notas de carga y revision pertenecen al formulario, no al informe.
# 7. Descargar las preguntas y respuestas o el esqueleto Markdown para trabajar
#    con IA. Revisar los antecedentes antes de incorporar cambios al codigo.
# 8. Adjuntar CV y respaldos de Diego Zamorano y Daniel Vargas si se presentan
#    ambos en la oferta. El ZIP incluye únicamente archivos cargados.
# 9. No se deben atribuir certificaciones no documentadas. El PDF no incluye
#    costos internos ni márgenes. El contacto institucional aparece siempre en
#    su propia sección, independiente del anexo administrativo opcional.
# 10. Formulario completo, sin bloqueos. No hay guardado persistente de progreso;
#     conservar la sesion abierta y descargar los documentos antes de cerrarla.
#
# PRUEBA LOCAL: python Generador_Propuesta_SML_837-465-COT26_DOS_RELATORES.py --demo-pdf propuesta.pdf
# El logo institucional es opcional; sin él se usa una portada tipográfica.
"""Formulario reutilizable por preguntas y generador de propuesta PDF A4."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import re
import unicodedata
import zipfile
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

import reportlab
from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    CondPageBreak, HRFlowable, Flowable,
)

BASE_DIR = Path(__file__).resolve().parent
LOGO_NAME = "OTEC_Santa_Monica_Opcion_1.svg"
PDF_RENDER_VERSION = "v8.2-sml-powerbi-contacto-20261111"
# Gama inspirada en las presentaciones Beamer clásicas: azul estructural,
# azul petróleo, fondos casi blancos y reglas finas. Se usa con moderación.
BEAMER_PALETA = {
    "principal": "#193C65",       # azul de secciones y cabeceras
    "acento": "#277586",          # azul petróleo para detalles
    "texto": "#242A32",           # negro tinta, adecuado para impresión
    "secundario": "#5D6570",      # gris azulado
    "fondo_tabla": "#F1F5F8",     # fondo claro de encabezados
    "linea": "#C5D0D9",          # reglas y separadores
}
NAVY = colors.HexColor(BEAMER_PALETA["principal"])
GOLD = colors.HexColor(BEAMER_PALETA["acento"])  # alias conservado
INK = colors.HexColor(BEAMER_PALETA["texto"])
MUTED = colors.HexColor(BEAMER_PALETA["secundario"])
PALE = colors.HexColor(BEAMER_PALETA["fondo_tabla"])
LINE = colors.HexColor(BEAMER_PALETA["linea"])
MAX_LOGO = 5 * 1024 * 1024
MAX_FILE = 20 * 1024 * 1024
MAX_ZIP = 200 * 1024 * 1024
FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("OTEC", str(FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("OTEC-Bold", str(FONT_DIR / "VeraBd.ttf")))
pdfmetrics.registerFontFamily("OTEC", normal="OTEC", bold="OTEC-Bold")

# Tipografía de informe clásico: serif para el cuerpo y sans para tablas.
# Si la máquina no dispone de DejaVu Serif o Liberation Serif, ReportLab usa
# Times-Roman/Times-Bold, sin depender de paquetes LaTeX externos.
def configurar_fuentes_editoriales():
    posibilidades = [
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
         Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")),
        (Path("/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"),
         Path("/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf")),
        (Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
         Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf")),
        (Path("C:/Windows/Fonts/georgia.ttf"),
         Path("C:/Windows/Fonts/georgiab.ttf")),
    ]
    for normal, negrita in posibilidades:
        if normal.is_file() and negrita.is_file():
            try:
                pdfmetrics.registerFont(TTFont("InformeSerif", str(normal)))
                pdfmetrics.registerFont(TTFont("InformeSerif-Bold", str(negrita)))
                pdfmetrics.registerFontFamily("InformeSerif", normal="InformeSerif",
                                              bold="InformeSerif-Bold")
                return "InformeSerif", "InformeSerif-Bold"
            except (OSError, ValueError):
                pass
    return "Times-Roman", "Times-Bold"

FUENTE_SERIF, FUENTE_SERIF_BOLD = configurar_fuentes_editoriales()
FUENTE_SANS, FUENTE_SANS_BOLD = "OTEC", "OTEC-Bold"

PASOS = ["Proceso y comprador", "Identificación del oferente", "Quiénes somos y visión",
         "Objetivos", "Participantes", "Contenidos y horas", "Lugar y ejecución",
         "Relator y respaldos", "Requisitos de compra", "Certificación",
         "Oferta económica", "Logo y documentación adjunta", "Revisión y PDF"]
ESTADOS = ["Por verificar", "Comprometido", "Declarado", "Respaldado", "A evaluación del comprador", "Cumple", "No cumple", "No aplica"]
CATEGORIAS_ADJUNTOS = ["Bases técnicas", "CV y respaldos relator", "CV relator", "Respaldo relator", "Propuesta / otro", "Orden de compra"]
ADJUNTOS_DECLARADOS = [{'nombre': 'CV - Diego Zamorano y Antecedentes.pdf', 'categoria': 'CV y respaldos relator'},
                       {'nombre': 'CV - Daniel Vargas H Compilado.pdf', 'categoria': 'CV y respaldos relator'}]
RELATOR_INICIAL = {'rol': 'Relator principal (prioridad 1)', 'nombre': 'Diego Antonio Zamorano Pérez',
 'rut': '20.185.347-8',
 'titulo': 'Ingeniero Civil Industrial, Pontificia Universidad Católica de Valparaíso (título acreditado)',
 'experiencia': 'Diego Antonio Zamorano Pérez cuenta con experiencia laboral en el desarrollo '
                'de reportes financieros y operativos automatizados mediante Power BI para Siel '
                'Consultores, así como en el diseño de módulos de control BI en Hubconsulting SpA. '
                'Declara manejo avanzado de Power BI, SQL, Excel y Python para análisis de datos. '
                'Además, posee experiencia documentada como relator de inteligencia artificial para '
                'instituciones públicas, incluyendo la Subsecretaría de Educación Parvularia y el '
                'Servicio Local de Educación Pública Llanquihue.',
 'disponibilidad': 'Relator propuesto para ejecutar el programa virtual durante noviembre/diciembre de '
                   '2026, según coordinación de calendario con el Servicio Médico Legal.'}
RELATOR_ALTERNATIVO = {
 'rol': 'Relator alternativo de contingencia (prioridad 2)',
 'nombre': 'Daniel Cristóbal Vargas Herrera',
 'rut': '20.522.550-1',
 'titulo': 'Ingeniero Civil Industrial, Pontificia Universidad Católica de Valparaíso',
 'experiencia': (
     'Daniel Cristóbal Vargas Herrera es Ingeniero Civil Industrial y cuenta con formación '
     'en Data Science, Machine Learning e Inteligencia Artificial mediante diplomado de 96 horas '
     'de la Pontificia Universidad Católica de Valparaíso. Su experiencia incluye implementación '
     'de soluciones de análisis de datos e inteligencia artificial y relatorías para organismos '
     'públicos, entre ellos la Subsecretaría de Educación Parvularia y SLEP Llanquihue. '
     'Sus antecedentes respaldan su experiencia en capacitación, analítica e IA aplicada.'),
 'disponibilidad': (
     'Profesional alternativo de respaldo. Su eventual sustitución del relator principal '
     'se realizará exclusivamente ante una contingencia, previa autorización del Servicio '
     'Médico Legal y sin modificar precio, temario, duración ni entregables.'),
}
REQ_RELATOR_ALTERNATIVO = [
    'Título profesional de Ingeniería Civil Industrial',
    'Formación académica en ciencia de datos e inteligencia artificial',
    'Experiencia en capacitación en inteligencia artificial para instituciones públicas',
    'Participación en proyectos de análisis de datos e inteligencia artificial',
]

MODALIDADES = ["Compra Ágil", "Licitación pública", "Licitación privada", "Convenio Marco",
               "Trato directo", "Compra por cotización", "Subasta Inversa Electrónica",
               "Contratos para la Innovación", "Diálogo Competitivo de Innovación", "Otra"]

# paso, clave, pregunta, tipo, obligatorio. Las respuestas viven en b['datos'].
PREGUNTAS = [
 (0,"proceso","¿Cuál es el código del proceso?","texto",True),
 (0,"modalidad","¿Cuál es la modalidad de contratación?","modalidad",True),
 (0,"titulo","¿Cuál es el nombre del servicio o actividad?","texto",True),
 (0,"comprador","¿Qué organismo solicita el servicio?","texto",True),
 (0,"rut_comprador","¿Cuál es el RUT del comprador?","texto",True),
 (0,"rubro","¿A qué rubro o categoría pertenece el servicio?","texto",False),
 (0,"id_item","¿Cuál es el ID del ítem en la ficha?","texto",False),
 (0,"numero_oc","¿Cuál es el número de la orden de compra, si ya fue emitida?","texto",False),
 (0,"requisitos_oc","¿Qué condiciones adicionales establece la orden de compra?","area",False),
 (0,"publicacion","¿Cuándo se publicó el proceso? Fecha y hora.","texto",False),
 (0,"cierre_1","¿Cuándo cierra el primer llamado? Fecha y hora.","texto",True),
 (0,"cierre_2","¿Cuándo cierra el segundo llamado, si corresponde?","texto",False),
 (0,"plazo_ficha","¿Qué plazo de entrega indica la ficha?","texto",False),
 (0,"presupuesto","¿Cuál es el presupuesto estimado en CLP?","entero",True),
 (0,"tipo_presupuesto","¿Qué tipo de presupuesto indica la ficha?","texto",False),
 (0,"contacto_comprador","¿Quién coordina por parte del comprador?","texto",False),
 (1,"oferente","¿Cuál es la razón social del oferente?","texto",True),
 (1,"nombre_comercial","¿Cuál es el nombre comercial?","texto",True),
 (1,"rut_oferente","¿Cuál es el RUT de la empresa?","texto",True),
 (1,"domicilio_empresa","¿Cuál es el domicilio de la empresa?","area",True),
 (1,"contacto_oferta","¿Quién es el contacto de la licitación por parte del oferente?","texto",False),
 (1,"cargo_contacto","¿Cuál es el cargo del contacto de la licitación?","texto",False),
 (1,"telefono","¿Cuál es el teléfono del contacto de la licitación?","texto",True),
 (1,"correo","¿Cuál es el correo del contacto de la licitación?","texto",True),
 (1,"representante","¿Quién es la representante legal?","texto",True),
 (1,"rut_representante","¿Cuál es el RUT de la representante?","texto",True),
 (1,"cargo_representante","¿Cuál es su cargo?","texto",False),
 (1,"banco","¿Cuál es el banco de la empresa?","texto",False),
 (1,"tipo_cuenta","¿Cuál es el tipo de cuenta?","texto",False),
 (1,"cuenta","¿Cuál es el número de cuenta?","texto",False),
 (1,"correo_pagos","¿Cuál es el correo para pagos?","texto",False),
 (2,"quienes","¿Quiénes somos y cuál es nuestra propuesta de valor?","area",True),
 (2,"vision","¿Cuál es nuestra visión institucional?","area",True),
 (2,"que_ofrecemos","¿Qué servicio integral ofrecemos para este proceso?","area",True),
 (3,"objetivo_general","¿Qué resultado busca lograr la actividad? Objetivo general.","area",True),
 (3,"objetivos_especificos","¿Qué resultados específicos se esperan? Uno por línea.","area",True),
 (4,"participantes","¿A qué universo de participantes está dirigida?","area",True),
 (4,"cupos","¿Cuántos cupos o participantes contempla?","entero",True),
 (4,"prerrequisitos","¿Qué conocimientos previos necesitan?","area",False),
 (4,"modalidad_curso","¿Cómo se desarrollará la actividad?","modalidad_curso",True),
 (5,"horas_exigidas","¿Cuántas horas de capacitación exigen los términos de referencia?","decimal",True),
 (5,"metodologia","¿Cómo enseñaremos y acompañaremos el aprendizaje?","area",True),
 (5,"herramientas","¿Qué funciones deben cumplir las herramientas, sin comprometer marcas?","area",True),
 (6,"region","¿En qué región se ejecuta?","texto",True),
 (6,"comuna","¿En qué comuna o ciudad se ejecuta?","texto",True),
 (6,"lugar","¿Cuál es el recinto o dirección de ejecución?","texto",True),
 (6,"quien_lugar","¿Quién dispone el lugar?","responsable",True),
 (6,"periodo_ejecucion","¿Qué período de ejecución señalan las bases?","texto",True),
 (6,"fecha_ejecucion","¿Cómo se coordinarán las fechas de ejecución?","area",False),
 (6,"equipamiento","¿Qué equipamiento y conectividad se requiere y quién lo aporta?","area",True),
 (6,"cafeteria","¿Hay servicios adicionales de apoyo?","area",False),
 (6,"materiales","¿Qué materiales se entregarán?","area",True),
 (7,"perfil_docente","¿Qué perfil resulta apropiado para desarrollar los contenidos?","area",True),
 (7,"referencia_cv","¿Dónde se presenta el CV y sus respaldos?","area",True),
 (8,"observaciones","¿Qué observaciones o condiciones debe evaluar el comprador?","area",False),
 (9,"evaluacion","¿Cómo se evaluará el aprendizaje y cuál será la escala?","area",True),
 (9,"aprobacion","¿Qué condiciones de asistencia y aprobación se proponen?","area",False),
 (9,"entrega_certificados","¿Cuándo y cómo se entregarán certificados e informe?","area",True),
 (9,"destino_informe","¿A qué unidad se entregará el informe final?","texto",True),
 (10,"cantidad","¿Cuántas unidades globales se cotizan?","entero",True),
 (10,"valor_unitario","¿Cuál es el valor unitario del servicio en CLP, antes de impuestos si corresponden?","entero",False),
 (10,"despacho","¿Cuál es el valor neto de despacho en CLP?","entero",False),
 (10,"impuesto","¿Qué tratamiento de impuesto corresponde?","impuesto",False),
 (10,"tasa","¿Qué tasa de impuesto se aplica, si corresponde?","entero",False),
 (10,"incluye_precio","¿Qué incluye el precio propuesto?","area",False),
 (10,"detalle","¿Cuál es el detalle breve para Mercado Público? Máximo 255 caracteres.","corto",False),
 (11,"adjuntos_esperados","¿Cuántos archivos adjuntos tendrá el expediente?","entero",False),
 (11,"adjuntos_solicitados","¿Qué archivos menciona o exige la ficha? Uno por línea.","area",False),
 (11,"documentacion_adjunta","¿Cómo se describen los documentos que acompañan la oferta?","area",True),
 (12,"fecha_propuesta","¿Cuál es la fecha de emisión de la propuesta?","texto",True),
]
REQ_COMPRA = ['Capacitación online teórico-práctica para 12 a 16 participantes',
 'Duración total de 24 horas y período noviembre/diciembre 2026',
 'Módulos 1 a 8 del programa Power BI con IA',
 'Metodología práctica con demostraciones y ejercicios guiados',
 'Evaluación final de aprendizaje',
 'Certificados individuales de participación',
 'Coordinación técnica con la contraparte del SML',
 'Confidencialidad y seguridad de la información']
REQ_RELATOR = ['Título profesional de Ingeniería Civil Industrial',
 'Experiencia laboral aplicando Microsoft Power BI',
 'Experiencia en reportes automatizados e indicadores de gestión',
 'Competencias en Power Query, modelado y DAX',
 'Experiencia aplicando herramientas de inteligencia artificial',
 'Experiencia de relatoría y formación para el sector público',
 'Capacidad para desarrollar el proyecto integrador y evaluar aprendizajes']
REQ_CERT = ['Evaluación final de aprendizaje del curso',
 'Diplomas individuales de participación',
 'Identificación de curso, participante, duración y fecha en diplomas',
 'Certificados digitales con mecanismo de verificación',
 'Entrega de resultados finales a la contraparte técnica']
MODULOS = [('Bloque I - Fundamentos y preparación',
  'Módulo 1. Introducción al análisis de datos con Power BI e IA',
  'Fundamentos de inteligencia de negocios; componentes de Power BI Desktop; oportunidades y límites de '
  'la IA como apoyo al análisis de datos.',
  2,
  'Virtual'),
 ('Bloque I - Fundamentos y preparación',
  'Módulo 2. Conexión y carga de datos',
  'Importación desde Excel y archivos estructurados; conexión a fuentes; validación de campos, tipos de '
  'datos y estructuras.',
  2,
  'Virtual'),
 ('Bloque I - Fundamentos y preparación',
  'Módulo 3. Transformación y limpieza con Power Query',
  'Limpieza, tipado, tratamiento de nulos, eliminación de duplicados, combinación de consultas y '
  'transformaciones reproducibles; práctica guiada.',
  4,
  'Virtual'),
 ('Bloque I - Fundamentos y preparación',
  'Módulo 4. Modelado de datos',
  'Relaciones, cardinalidad, modelo de hechos y dimensiones, organización y calidad del modelo para la '
  'elaboración de reportes.',
  3,
  'Virtual'),
 ('Bloque II - Análisis, visualización e IA',
  'Módulo 5. Cálculos con DAX',
  'Medidas, columnas calculadas, funciones básicas de agregación, contexto de filtro e indicadores KPI; '
  'apoyo de IA para proponer y revisar expresiones.',
  4,
  'Virtual'),
 ('Bloque II - Análisis, visualización e IA',
  'Módulo 6. Visualización y diseño de tableros',
  'Construcción de dashboards, gráficos, segmentadores, filtros, navegación e indicadores; diseño '
  'centrado en la lectura y la toma de decisiones.',
  3,
  'Virtual'),
 ('Bloque II - Análisis, visualización e IA',
  'Módulo 7. Publicación y uso del servicio en la nube',
  'Se incluye una demostración práctica de publicación de reportes en Microsoft Power BI '
  'Service, administración de espacios de trabajo, permisos, actualización y distribución '
  'de información. Las actividades individuales se adaptarán a las licencias y accesos '
  'disponibles, sin afectar el desarrollo completo del módulo.',
  2,
  'Virtual'),
 ('Bloque II - Análisis, visualización e IA',
  'Módulo 8. Proyecto integrador con IA',
  'Proyecto práctico con datos simulados: cargar, transformar, modelar, calcular, visualizar y preparar '
  'un tablero; IA como apoyo y revisión de resultados.',
  4,
  'Virtual')]


def hoy():
    try:
        return datetime.now(ZoneInfo("America/Santiago")).strftime("%d-%m-%Y")
    except Exception:
        return datetime.now().strftime("%d-%m-%Y")


DATOS_LICITACION = {'proceso': '837-465-COT26',
 'modalidad': 'Compra Ágil',
 'titulo': 'Curso en Power BI con IA: Fundamentos y Aplicaciones para Profesionales',
 'comprador': 'SERVICIO MÉDICO LEGAL',
 'rut_comprador': '61.003.000-9',
 'rubro': 'Capacitación y formación de profesionales en análisis de datos e inteligencia artificial',
 'id_item': '',
 'numero_oc': '',
 'requisitos_oc': '',
 'publicacion': '',
 'cierre_1': '16-11-2026 10:00:00',
 'cierre_2': '',
 'plazo_ficha': 'No indicado en antecedentes adjuntos',
 'presupuesto': 6900000,
 'tipo_presupuesto': 'Disponibilidad presupuestaria certificada, CDP N.º 775/2026',
 'contacto_comprador': 'Contraparte técnica a designar por el Servicio Médico Legal',
 'oferente': 'CENTRO DE CAPACITACION SANTA MONICA LIMITADA',
 'nombre_comercial': 'CENTRO DE CAPACITACION SANTA MONICA',
 'rut_oferente': '76.176.857-3',
 'domicilio_empresa': 'Isabel La Católica 4394, oficina 517, piso 5, bloque B, Las Condes, Santiago, '
                      'Región Metropolitana',
 'contacto_oferta': 'ENRIQUE BRUN URRUTIA',
 'cargo_contacto': 'Director de Administración y Finanzas',
 'telefono': '+56 9 6359 6523',
 'correo': 'ebrun@otecsantamonica.com',
 'representante': 'María Carmen Urrutia Peña',
 'rut_representante': '11.518.133-5',
 'cargo_representante': 'Representante legal',
 'banco': '',
 'tipo_cuenta': '',
 'cuenta': '',
 'correo_pagos': '',
 'quienes': 'CENTRO DE CAPACITACION SANTA MONICA LIMITADA desarrolla actividades de capacitación '
            'orientadas al fortalecimiento de competencias laborales y tecnológicas para organizaciones '
            'públicas y privadas. El enfoque formativo combina aplicación práctica, acompañamiento '
            'durante las sesiones y evaluación del aprendizaje.\n'
            '\n'
            'Para el Servicio Médico Legal se presenta una capacitación específica en Microsoft Power BI '
            'e inteligencia artificial, enfocada en generar información analítica confiable para apoyar '
            'decisiones institucionales.',
 'vision': 'Fortalecer las capacidades de los equipos mediante formación pertinente, aplicable y '
           'orientada a resultados; favorecer la comprensión de los datos, su transformación en '
           'conocimiento útil y el uso responsable de herramientas digitales.',
 'que_ofrecemos': 'Ejecución integral de un curso virtual teórico-práctico de 24 horas para 12 a 16 '
                  'profesionales, compuesto por ocho módulos oficiales. Incluye relatoría especializada, '
                  'materiales y bases de práctica, ejercicios guiados, proyecto integrador con IA, '
                  'evaluación final y diplomas individuales.',
 'objetivo_general': 'Implementar soluciones de análisis de datos utilizando Microsoft Power BI y '
                     'herramientas de Inteligencia Artificial, integrando procesos de conexión, '
                     'transformación, modelado, cálculo, visualización y publicación de información, con '
                     'el fin de generar reportes y tableros confiables que apoyen la toma de decisiones '
                     'en contextos organizacionales.',
 'objetivos_especificos': 'Identificar los componentes de Power BI y los usos pertinentes de IA en el '
                          'análisis de datos.\n'
                          'Conectar e importar información desde diferentes fuentes de datos.\n'
                          'Transformar y depurar datos con Power Query para disponer de bases '
                          'confiables.\n'
                          'Construir modelos de datos y relaciones adecuadas al análisis.\n'
                          'Elaborar métricas e indicadores empleando cálculos DAX.\n'
                          'Diseñar tableros y visualizaciones útiles para la toma de decisiones.\n'
                          'Publicar reportes y comprender su uso en el servicio Power BI en la nube.\n'
                          'Aplicar lo aprendido en un proyecto analítico integrador con apoyo de IA.',
 'participantes': 'Profesionales que requieran incorporar herramientas modernas de análisis de datos y '
                  'mejorar su productividad mediante Microsoft Power BI e inteligencia artificial. El '
                  'servicio considera entre 12 y 16 asistentes.',
 'cupos': 16,
 'prerrequisitos': 'No se establece un requisito previo obligatorio en los términos de referencia. Se '
                   'recomienda manejo básico de computador y planillas de cálculo para aprovechar los '
                   'ejercicios.',
 'modalidad_curso': 'Virtual',
 'horas_exigidas': 24.0,
 'metodologia': 'Clases virtuales en vivo de carácter teórico-práctico. Cada módulo combinará explicación '
                'breve, demostración en Microsoft Power BI, práctica guiada con bases de datos simuladas, '
                'análisis de casos y retroalimentación. Las actividades avanzarán desde conexión y '
                'preparación de datos hasta la construcción de reportes y un proyecto integrador.\n'
                '\n'
                'La inteligencia artificial se incorporará como apoyo a tareas de análisis, formulación y '
                'revisión de expresiones, interpretación y comunicación de resultados. Los participantes '
                'verificarán críticamente los productos generados por las herramientas. La evaluación '
                'final comprobará el aprendizaje aplicado.',
 'herramientas': 'Microsoft Power BI Desktop, Power Query, lenguaje DAX y Power BI Service. '
                 'El relator demostrará la publicación de un informe en Power BI Service durante '
                 'el módulo 7. Los participantes trabajarán con archivos de práctica en Excel/CSV '
                 'y herramientas de IA como apoyo al análisis. Los accesos y licencias individuales '
                 'se coordinarán previamente con la contraparte técnica.',
 'region': 'Región Metropolitana',
 'comuna': 'Santiago',
 'lugar': 'Capacitación 100% virtual, sin asistencia presencial. Organismo comprador: Servicio Médico '
          'Legal, sede de referencia Isabel Riquelme, Santiago.',
 'quien_lugar': 'Proveedor',
 'periodo_ejecucion': 'Noviembre/diciembre de 2026. Las clases se realizarán en modalidad virtual, en las '
                      'fechas que se coordinen con la contraparte técnica.',
 'fecha_ejecucion': 'Se propondrá un cronograma de sesiones que totalice 24 horas, sujeto a coordinación '
                    'y aceptación del Servicio Médico Legal durante noviembre/diciembre de 2026.',
 'equipamiento': 'El proveedor habilitará el medio de videoconferencia y entregará recursos digitales '
                 'para los ejercicios. Los requerimientos de computador, conectividad, instalación de '
                 'Power BI y licencias para publicación se comunicarán y coordinarán antes del inicio del '
                 'curso.',
 'cafeteria': '',
 'materiales': 'Kit de aprendizaje digital con presentaciones, guías por módulo, archivos y bases de '
               'datos simuladas, ejercicios de Power Query y DAX, ejemplos de visualización, '
               'instrucciones del proyecto integrador y rúbrica de evaluación. No se utilizarán datos '
               'institucionales reservados en herramientas de IA de terceros.',
 'perfil_docente': 'La ejecución de las 24 horas se propone a cargo de Diego Antonio Zamorano Pérez, '
                   'con experiencia laboral en Microsoft Power BI, inteligencia de negocios, análisis de datos e '
                   'inteligencia artificial aplicada. Los términos de referencia no establecen título '
                   'profesional, certificación Microsoft ni años mínimos obligatorios.',
 'referencia_cv': 'Se presentan los CV de Diego Antonio Zamorano Pérez (principal) y Daniel Cristóbal Vargas Herrera (alternativo), con currículums, '
                  'certificados y respaldos de experiencias de relatoría. El oferente confirma específicamente '
                  'el dominio de Diego Zamorano en Power Query, DAX y Power BI Service.',
 'observaciones': 'El curso se ejecutará bajo las condiciones de confidencialidad y coordinación '
                  'establecidas por el Servicio Médico Legal. El calendario específico será acordado con '
                  'la contraparte técnica; el compromiso ofertado comprende íntegramente las 24 horas y '
                  'los ocho módulos descritos.',
 'evaluacion': 'Se aplicará una evaluación final de aprendizaje mediante un ejercicio práctico '
               'integrador: importación y depuración de datos, modelado, cálculo de indicadores, '
               'visualización y análisis apoyado por IA. Se utilizará una pauta de evaluación consistente '
               'y se conservará el registro individual de resultados.',
 'aprobacion': 'La pauta de evaluación y las condiciones de aprobación se informarán a los participantes '
               'al inicio y se coordinarán con la contraparte técnica, manteniendo como requisito central '
               'la evaluación final exigida.',
 'entrega_certificados': 'Se entregarán diplomas digitales individuales de participación, con nombre de '
                         'participante, nombre del curso, duración y fechas de ejecución; se contempla un '
                         'identificador verificable. Se entregará además un resumen de asistencia y '
                         'resultados de evaluación a la contraparte técnica al cierre del servicio.',
 'destino_informe': 'contraparte técnica o unidad de capacitación que designe el Servicio Médico Legal',
 'cantidad': 1,
 'valor_unitario': 2690000,
 'despacho': 0,
 'impuesto': 'Exento / sin impuesto',
 'tasa': 19,
 'incluye_precio': 'Precio global por 24 horas virtuales para hasta 16 participantes. Incluye relatoría, '
                   'planificación y preparación de sesiones, uso de plataforma de videoconferencia, '
                   'materiales digitales, ejercicios guiados, proyecto integrador con IA, evaluación '
                   'final, diplomas individuales y coordinación técnica. No contempla actividades '
                   'presenciales ni traslados.',
 'detalle': 'Curso Power BI con IA, 24 horas virtuales, para 12 a 16 participantes. Ocho módulos, '
            'ejercicios prácticos, proyecto integrador, evaluación final y diplomas individuales. Oferta '
            'global: $2.690.000 exenta.',
 'adjuntos_esperados': 2,
 'adjuntos_solicitados': 'Currículum y antecedentes de ambos profesionales propuestos (respaldo técnico complementario).',
 'documentacion_adjunta': 'Se acompañan los CV de Diego Antonio Zamorano Pérez y Daniel Cristóbal Vargas Herrera, con certificados de título y '
                          'antecedentes documentales de relatorías. La propuesta contiene además el '
                          'programa, metodología, cumplimiento de términos técnicos, evaluación y valor '
                          'global del servicio.',
 'fecha_propuesta': '11-11-2026'}

# Textos de apertura editables. Las llaves se completan desde DATOS_LICITACION.
INTRODUCCIONES = {'proceso': 'La propuesta responde a la Compra Ágil {proceso}, convocada por {comprador}, para la '
            'prestación integral de un curso de Power BI con inteligencia artificial.',
 'objetivos': 'El programa desarrolla capacidades progresivas para transformar datos en información '
              'confiable, utilizando Power BI y herramientas de IA como apoyo práctico.',
 'programa': 'El curso contempla 24 horas de capacitación virtual, organizadas en ocho módulos que '
             'avanzan desde los fundamentos y la preparación de datos hasta la elaboración de un proyecto '
             'integrador.',
 'metodologia': 'Las actividades están diseñadas para favorecer la aplicación inmediata: demostración, '
                'práctica guiada, resolución de casos y retroalimentación mediante datos simulados.',
 'logistica': 'La capacitación se ejecutará mediante clases virtuales. El calendario se coordinará con el '
              'Servicio Médico Legal durante noviembre/diciembre de 2026.',
 'relator': 'La relatoría principal de las 24 horas estará a cargo de Diego Antonio Zamorano Pérez, cuyo perfil reúne '
            'experiencia aplicada en Power BI, control de gestión, análisis de datos e inteligencia '
            'artificial. Daniel Cristóbal Vargas Herrera se presenta únicamente como profesional alternativo de contingencia, sujeto a aprobación previa del Servicio Médico Legal y sin cambio de precio, duración ni contenidos. Ambos currículums y antecedentes se acompañan al expediente.',
 'requisitos': 'La siguiente matriz vincula los requerimientos expresos del Servicio Médico Legal con los '
               'compromisos concretos asumidos en esta oferta.',
 'certificacion': 'El aprendizaje se comprobará con una evaluación final práctica y se respaldará '
                  'mediante diplomas individuales de participación y registro de resultados.',
 'economica': 'La propuesta económica considera un servicio global de 24 horas virtuales para 12 a 16 '
              'participantes, con todos los componentes descritos en este documento.',
 'documentos': 'Los antecedentes del relator se incluyen en el expediente para complementar la evaluación '
               'técnica.',
 'identificacion': 'Los siguientes datos corresponden al oferente, conforme a la información facilitada '
                   'en el código base.'}

def datos_licitacion():
    d=copy.deepcopy(DATOS_LICITACION)
    d["fecha_propuesta"]=d["fecha_propuesta"] or hoy()
    return d



def items_check(textos):
    return [{"id": uuid4().hex[:12], "requisito": s, "estado": "Por verificar", "respaldo": ""} for s in textos]


def nuevo(ejemplo_activo=True):
    d = datos_licitacion()
    if not ejemplo_activo:
        for _, k, _, tipo, _ in PREGUNTAS:
            if k in {"oferente", "nombre_comercial", "rut_oferente", "domicilio_empresa",
                     "contacto_oferta", "cargo_contacto", "telefono", "correo",
                     "representante", "rut_representante", "cargo_representante"}:
                continue
            if tipo in {"entero", "decimal"}:
                d[k] = 0.0 if tipo == "decimal" else 0
            elif k not in {"modalidad", "modalidad_curso", "quien_lugar", "impuesto"}:
                d[k] = ""
        d.update(cantidad=1, tasa=19, fecha_propuesta=hoy())
    rows = [{"id": uuid4().hex[:12], "jornada": a, "nombre": n, "contenido": c,
             "horas": float(h), "tipo": t} for a,n,c,h,t in MODULOS] if ejemplo_activo else []
    rel = copy.deepcopy(RELATOR_INICIAL)
    rel["id"] = uuid4().hex[:12]
    rel["checklist"] = items_check(REQ_RELATOR)
    soportes_rel = [
        ("Respaldado", "Certificado de profesionales del Registro Civil, incluido en el CV adjunto."),
        ("Declarado", "Siel Consultores: reportes financieros y operativos automatizados en Power BI, según CV."),
        ("Declarado", "Experiencia en control BI, reportabilidad y KPI, según CV."),
        ("Declarado", "Competencias técnicas confirmadas por el oferente; ejercicios contemplados en módulos 3, 4 y 5."),
        ("Declarado", "Capacitaciones en IA y aplicación de herramientas de IA generativa, según CV."),
        ("Respaldado", "Certificados de relatoría para la Subsecretaría de Educación Parvularia y SLEP Llanquihue."),
        ("Comprometido", "Relatoría de los ocho módulos, proyecto práctico y evaluación final del programa."),
    ]
    for row, (estado, respaldo) in zip(rel["checklist"], soportes_rel):
        row.update(estado=estado, respaldo=respaldo)
    alt = copy.deepcopy(RELATOR_ALTERNATIVO)
    alt["id"] = uuid4().hex[:12]
    alt["checklist"] = items_check(REQ_RELATOR_ALTERNATIVO)
    for row, (estado, respaldo) in zip(alt["checklist"], [
        ("Respaldado", "Ingeniero Civil Industrial PUCV; documentos en su compilado de antecedentes."),
        ("Respaldado", "Diplomado Data Science, Machine Learning, IA y Deep Learning de 96 horas, PUCV."),
        ("Respaldado", "Constancias de relatoría en instituciones públicas, incluidos SLEP Llanquihue y Subsecretaría de Educación Parvularia."),
        ("Declarado", "Experiencia profesional en análisis de datos e implementación de IA, según currículum."),
    ]):
        row.update(estado=estado, respaldo=respaldo)
    compra = items_check(REQ_COMPRA)
    soportes_compra = [
        "Clases virtuales teórico-prácticas; cobertura de hasta 16 profesionales.",
        "Programa de ocho módulos, 24 horas; ejecución noviembre/diciembre 2026.",
        "Programa desglosado en los ocho módulos de los términos de referencia.",
        "Demostraciones, ejercicios guiados, práctica progresiva y proyecto integrador.",
        "Evaluación final aplicada mediante ejercicio integrador y registro de resultados.",
        "Diplomas individuales digitales con identificación del participante.",
        "Coordinador técnico del proveedor y calendario concertado con la contraparte institucional.",
        "Ejercicios con datos simulados y cumplimiento de las cláusulas de reserva del SML.",
    ]
    for row,respaldo in zip(compra,soportes_compra):
        row.update(estado="Comprometido",respaldo=respaldo)
    cert = items_check(REQ_CERT)
    for row,respaldo in zip(cert,[
        "Evaluación práctica final y registro individual de aprendizaje.",
        "Diploma individual digital de participación al terminar el curso.",
        "El diploma identificará al participante, curso, duración y fechas de ejecución.",
        "Identificador único o código de verificación para cada diploma.",
        "Resumen final de asistencia, evaluación y entregables."]):
        row.update(estado="Comprometido",respaldo=respaldo)
    return {"version":6,"datos":d,"modulos":rows,"docentes":[rel,alt],
            "compra":compra,"certificacion":cert,
            "logos":{"oferente":{"nombre":"","base64":""},"comprador":{"nombre":"","base64":""}},
            "archivos":[],"declarados":copy.deepcopy(ADJUNTOS_DECLARADOS),
            "marcar_borrador":False,"incluir_revision":False,"incluir_admin":False}


def slug(s, maximo=90):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_-]+", "_", s).strip("_")[:maximo] or "Sin_nombre"


def limpiar(s):
    return str(s).replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")


def pesos(n):
    return "$ " + f"{int(n):,}".replace(",", ".")


def montos(d):
    neto = int(d["cantidad"]) * int(d["valor_unitario"]) + int(d["despacho"])
    if d["impuesto"] == "Por definir":
        return neto, None, None
    iva = 0 if d["impuesto"] == "Exento / sin impuesto" else int(
        (Decimal(neto)*Decimal(d["tasa"])/100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return neto, iva, neto + iva


def horas(b):
    total = {}
    for m in b["modulos"]:
        total[m["tipo"]] = total.get(m["tipo"], 0) + float(m["horas"])
    return total


def intervalo(inicio, fin):
    def parse(s):
        return datetime.strptime(s.replace(" a las ", " ").strip(), "%d-%m-%Y %H:%M:%S")
    try:
        delta = parse(fin)-parse(inicio)
        if delta.total_seconds()<0:
            return "REVISAR: cierre anterior a la publicación"
        dias, resto = divmod(int(delta.total_seconds()), 86400)
        hh, resto = divmod(resto, 3600)
        mm, ss = divmod(resto,60)
        return f"{dias} días corridos, {hh} h {mm} min {ss} s"
    except (ValueError, TypeError):
        return "Por calcular: usar DD-MM-AAAA HH:MM:SS"


def logo_local(rol="oferente"):
    if rol != "oferente":
        return None  # Nunca utilizar el logo del oferente como el del comprador.
    nombres = [LOGO_NAME, "logo_otec.svg", "logo.svg", "logo_otec.png", "logo.png"]
    raices = list(dict.fromkeys([BASE_DIR, Path.cwd()]))
    carpetas = [carpeta for raiz in raices for carpeta in
                [raiz, raiz/"assets", raiz/"logos", raiz/"images", raiz/"static"]]
    # Priorizar el nombre exacto de GitHub, incluso si hay logos genéricos.
    for nombre in nombres:
        for carpeta in carpetas:
            if not carpeta.is_dir():
                continue
            archivos = {p.name.casefold():p for p in carpeta.iterdir() if p.is_file()}
            if nombre.casefold() in archivos:
                return archivos[nombre.casefold()]
    return None


def preparar_raster(raw):
    """Lee PNG/JPEG y usa sus límites visibles sin alterar el archivo original."""
    from PIL import Image
    if not raw or len(raw)>MAX_LOGO:
        raise ValueError("La imagen del logo supera los 5 MB o está vacía.")
    with Image.open(BytesIO(raw)) as im:
        if im.format not in {"PNG", "JPEG"}:
            raise ValueError("La imagen incrustada debe ser PNG o JPEG.")
        if im.width*im.height>20000000:
            raise ValueError("El logo supera los 20 megapíxeles.")
        im.load()
        imagen=im.convert("RGBA")
    alfa=imagen.getchannel("A")
    # Para encuadrar el logo ignorar ruido prácticamente invisible (alfa 1-2).
    # Se conserva la imagen original; solo se calcula el área para dibujarla.
    limites=alfa.point(lambda v:255 if v>2 else 0).getbbox() or alfa.getbbox()
    if limites is None:
        raise ValueError("La imagen del logo es completamente transparente.")
    x0,y0,x1,y1=limites
    return ("raster", {"reader":ImageReader(imagen), "ancho":imagen.width,
            "alto":imagen.height, "limites":limites}, x1-x0, y1-y0)


def imagen_data_uri(ref):
    """Admite PNG/JPEG incrustados; nunca abre URL ni archivos externos."""
    m=re.fullmatch(r"data:image/(?:png|jpeg|jpg);base64,([A-Za-z0-9+/=\s]+)",ref,re.I)
    if not m:
        raise ValueError("Solo se admiten imágenes PNG/JPEG incrustadas en base64.")
    contenido=base64.b64decode(re.sub(r"\s+","",m.group(1)),validate=True)
    preparar_raster(contenido)
    return contenido


def preparar_logo(raw, nombre):
    if not raw or len(raw)>MAX_LOGO:
        raise ValueError("El logo debe pesar entre 1 byte y 5 MB.")
    if Path(nombre).suffix.lower()==".svg":
        from defusedxml import ElementTree
        from svglib.svglib import svg2rlg
        root = ElementTree.fromstring(raw)
        if root.tag.split("}")[-1].lower()!="svg":
            raise ValueError("No es un SVG válido.")
        imagenes_incrustadas={}
        for node in root.iter():
            if node.tag.split("}")[-1].lower() in {"script", "foreignobject"}:
                raise ValueError("El SVG debe contener solo elementos gráficos.")
            for k,v in node.attrib.items():
                if k.split("}")[-1].lower() in {"href","src"} and v and not v.startswith("#"):
                    if node.tag.split("}")[-1].lower()=="image" and v.lower().startswith("data:image/"):
                        imagenes_incrustadas[id(node)]=imagen_data_uri(v)
                    else:
                        raise ValueError("El SVG referencia una URL o archivo externo. Usa una imagen incrustada o un PNG.")
            contenido = " ".join(node.attrib.values())+" "+(node.text or "")
            if re.search(r"@import", contenido, re.I):
                raise ValueError("No se permiten estilos externos en el SVG.")
            for ref in re.findall(r"url\s*\((.*?)\)",contenido,re.I|re.S):
                if not ref.strip(" \t\r\n\"'").startswith("#"):
                    raise ValueError("El SVG referencia un recurso externo.")
        # El logo real de OTEC es un SVG que envuelve un PNG transparente.
        # Dibujarlo directamente evita que algunos renderizadores SVG pierdan
        # su transparencia y permite aprovechar el espacio visible del logo.
        hijos=list(root)
        if len(hijos)==1 and id(hijos[0]) in imagenes_incrustadas:
            nodo=hijos[0]
            try:
                vb=[float(x) for x in root.get("viewBox", "").replace(","," ").split()]
                plano=(not root.get("transform") and not nodo.get("transform") and
                       float(nodo.get("x",0))==0 and float(nodo.get("y",0))==0 and
                       len(vb)==4 and vb[:2]==[0,0] and
                       float(nodo.get("width",0))==vb[2] and float(nodo.get("height",0))==vb[3])
                if plano:
                    return preparar_raster(imagenes_incrustadas[id(nodo)])
            except (ValueError,TypeError):
                pass
        obj = svg2rlg(BytesIO(raw))
        if obj is None or obj.width<=0 or obj.height<=0:
            raise ValueError("No se pudo interpretar el SVG. Prueba con PNG.")
        return "svg", obj, obj.width, obj.height
    if Path(nombre).suffix.lower() not in {".png",".jpg",".jpeg"}:
        raise ValueError("Usa SVG, PNG o JPG.")
    return preparar_raster(raw)


def bytes_logo(b, rol):
    item=b.get("logos", {}).get(rol, {"base64":"", "nombre":""})
    if item["base64"]:
        return base64.b64decode(item["base64"],validate=True),item["nombre"]
    ruta=logo_local(rol)
    if ruta:
        if ruta.stat().st_size>MAX_LOGO:
            raise ValueError("El logo local supera los 5 MB.")
        return ruta.read_bytes(),ruta.name
    return None,""


def dibujar_logo(c, logo, x, y, w, h, etiqueta):
    if logo:
        tipo,obj,lw,lh=logo
        escala=min(w/lw,h/lh)
        xx,yy=x+(w-lw*escala)/2,y+(h-lh*escala)/2
        if tipo=="svg":
            c.saveState(); c.translate(xx,yy); c.scale(escala,escala)
            renderPDF.draw(obj,c,0,0); c.restoreState()
        else:
            x0,y0,x1,y1=obj["limites"]
            c.saveState()
            recorte=c.beginPath(); recorte.rect(xx,yy,lw*escala,lh*escala)
            c.clipPath(recorte,stroke=0,fill=0)
            c.drawImage(obj["reader"],xx-x0*escala,yy-(obj["alto"]-y1)*escala,
                        width=obj["ancho"]*escala,height=obj["alto"]*escala,mask="auto")
            c.restoreState()
    else:
        c.setStrokeColor(LINE); c.roundRect(x,y,w,h,5,stroke=1,fill=0)
        c.setFont("OTEC",8); c.setFillColor(MUTED)
        c.drawCentredString(x+w/2,y+h/2+4,etiqueta)
        c.drawCentredString(x+w/2,y+h/2-10,"Pendiente de cargar")


def validar(b):
    b=copy.deepcopy(b)
    if b.get("version")!=6: raise ValueError("Versión de formulario no compatible.")
    plantilla=nuevo()
    if not isinstance(b.get("datos"),dict):
        raise ValueError("El respaldo no contiene respuestas.")
    for _,k,_,tipo,_ in PREGUNTAS:
        v=b["datos"].get(k,plantilla["datos"][k])
        if tipo in {"entero","decimal"}:
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not 0<=v<=10**12:
                raise ValueError(f"Número inválido: {k}")
            if tipo=="entero":
                if int(v)!=v: raise ValueError(f"Se requiere un entero: {k}")
                v=int(v)
        elif not isinstance(v,str) or len(v)>(255 if tipo=="corto" else 12000 if tipo=="area" else 500):
            raise ValueError(f"Texto inválido o muy largo: {k}")
        b["datos"][k]=v
    if b["datos"]["modalidad"] not in MODALIDADES or b["datos"]["impuesto"] not in ["Por definir","Con impuesto","Exento / sin impuesto"]:
        raise ValueError("Modalidad o impuesto inválido.")
    if b["datos"]["cantidad"]<1 or b["datos"]["tasa"]>100 or b["datos"]["adjuntos_esperados"]>100:
        raise ValueError("Revisa cantidad, tasa o número de adjuntos.")
    for key in ["modulos","docentes","compra","certificacion","archivos","declarados"]:
        if not isinstance(b.get(key),list) or len(b[key])>100:
            raise ValueError(f"Lista inválida: {key}")
    for m in b["modulos"]:
        if not isinstance(m,dict) or any(not isinstance(m.get(k),str) or len(m[k])>5000 for k in ["id","jornada","nombre","contenido","tipo"]):
            raise ValueError("Módulo inválido.")
        if m["tipo"] not in ["Presencial","Autónomo","Virtual"] or isinstance(m.get("horas"),bool) or not isinstance(m.get("horas"),(int,float)) or not 0<=m["horas"]<=10000:
            raise ValueError("Horas o tipo de módulo inválido.")
    listas=[b["compra"],b["certificacion"]]
    for docente in b["docentes"]:
        if any(not isinstance(docente.get(k),str) or len(docente[k])>5000 for k in ["id","nombre","rut","titulo","experiencia","disponibilidad"]):
            raise ValueError("Ficha docente inválida.")
        listas.append(docente.get("checklist",[]))
    for lista in listas:
        if not isinstance(lista,list) or len(lista)>100: raise ValueError("Checklist inválido.")
        for row in lista:
            if not isinstance(row,dict) or row.get("estado") not in ESTADOS or any(not isinstance(row.get(k),str) or len(row[k])>5000 for k in ["id","requisito","respaldo"]):
                raise ValueError("Requisito inválido.")
    for rol in ["oferente", "comprador"]:
        item=b.get("logos",{}).get(rol,{"nombre":"", "base64":""})
        if not isinstance(item.get("nombre"),str) or len(item["nombre"])>200 or not isinstance(item.get("base64"),str) or len(item["base64"])>7000000:
            raise ValueError("Logo inválido.")
        if item["base64"]: preparar_logo(base64.b64decode(item["base64"],validate=True),item["nombre"])
    for a in b["archivos"]:
        if not isinstance(a.get("descripcion",""),str) or len(a.get("descripcion",""))>500:
            raise ValueError("Descripción de documento inválida.")
        if any(not isinstance(a.get(k),str) or len(a[k])>300 for k in ["id","nombre","guardado","categoria","sha256"]):
            raise ValueError("Archivo inválido.")
        if Path(a["guardado"]).name!=a["guardado"] or a["guardado"] in {".",".."}:
            raise ValueError("Ruta de archivo inválida.")
        if not isinstance(a.get("base64"),str) or len(a["base64"])>28000000:
            raise ValueError("Contenido de adjunto inválido.")
    for item in b["declarados"]:
        if any(not isinstance(item.get(k),str) or len(item[k])>500 for k in ["nombre","categoria"]):
            raise ValueError("Documento declarado inválido.")
    for k in ["marcar_borrador","incluir_revision","incluir_admin"]:
        if type(b.get(k)) is not bool: raise ValueError("Opción inválida.")
    # Solo conservar claves previstas.
    return {k:b.get(k,v) for k,v in plantilla.items()}


def agregar_archivo(b,nombre,raw,categoria):
    if not raw or len(raw)>MAX_FILE: raise ValueError("Cada adjunto debe pesar entre 1 byte y 20 MB.")
    suf=Path(nombre).suffix.lower()
    if suf not in {".pdf",".doc",".docx",".xls",".xlsx",".png",".jpg",".jpeg",".svg",".txt"}:
        raise ValueError("Formato de adjunto no permitido.")
    h=hashlib.sha256(raw).hexdigest()
    for a in b["archivos"]:
        if a["sha256"]==h and a["nombre"]==nombre:
            return False
    if len(b["archivos"])>=int(b["datos"]["adjuntos_esperados"]):
        raise ValueError("Aumenta la cantidad de archivos esperados antes de cargar más documentos.")
    if sum(a.get("bytes",0) for a in b["archivos"])+len(raw)>100*1024*1024:
        raise ValueError("El total de adjuntos de esta sesión supera los 100 MB.")
    a={"id":uuid4().hex[:12],"nombre":Path(nombre).name[:200],"categoria":categoria,
       "guardado":slug(Path(nombre).stem,90)+"_"+h[:12]+suf,"sha256":h,"bytes":len(raw)}
    a["descripcion"]=titulo_documento(categoria)
    a["base64"]=base64.b64encode(raw).decode("ascii")
    b["archivos"].append(a)
    return True


def disponibles(b,token=None):
    return [a for a in b["archivos"] if a.get("base64")]


def faltantes(b,paso,token=None):
    d=b["datos"]
    r=[pregunta for p,k,pregunta,t,req in PREGUNTAS if p==paso and req and
       (not str(d[k]).strip() or (t in {"entero","decimal"} and d[k]<=0))]
    if paso==5:
        if not b["modulos"]: r.append("Agregar módulos y contenidos.")
        if abs(sum(horas(b).values())-float(d["horas_exigidas"]))>.01:
            r.append("La suma de horas del programa no coincide con las horas exigidas.")
    if paso==0 and d["numero_oc"].strip() and not any(a["categoria"]=="Orden de compra" for a in b["archivos"]):
        r.append("Orden de compra indicada: cargar el documento para revisión.")
    if paso==7:
        for i,doc in enumerate(b["docentes"],1):
            if not doc["nombre"].strip() or "EJEMPLO" in doc["nombre"].upper() or not doc["rut"].strip() or "COMPLETAR" in doc["rut"].upper():
                r.append(f"Completar identidad del relator {i}.")
            for requisito in doc["checklist"]:
                if requisito["estado"] in {"Por verificar","No cumple","A evaluación del comprador"}:
                    r.append(f"Relator {i}: {requisito['requisito']} - {requisito['estado']}.")
        if not b["docentes"]: r.append("Agregar al menos un relator.")
        cats={a["categoria"] for a in (disponibles(b,token) if token else b["archivos"])}
        if "CV y respaldos relator" not in cats:
            if "CV relator" not in cats: r.append("CV declarado: cargarlo para incorporarlo al ZIP.")
            if "Respaldo relator" not in cats: r.append("Respaldos declarados: cargarlos para incorporarlos al ZIP.")
    if paso in {8,9}:
        lista=b["compra" if paso==8 else "certificacion"]
        r += [x["requisito"]+" - "+x["estado"] for x in lista if x["estado"] in {"Por verificar","No cumple","A evaluación del comprador"}]
    if paso==11:
        for rol in ["oferente"]:
            try:
                raw,nombre=bytes_logo(b,rol)
                if raw: preparar_logo(raw,nombre)
            except Exception as e: r.append(f"Revisar logo {rol}: {e}")
        count=len(disponibles(b,token)) if token else len(b["archivos"])
        if "CV y respaldos relator" not in {a["categoria"] for a in b["archivos"]}:
            r.append("Adjuntar CV y respaldos del relator al expediente antes del envío.")
        if count<int(d["adjuntos_esperados"]): r.append(f"Adjuntos: {count} de {d['adjuntos_esperados']} disponibles.")
        if count>int(d["adjuntos_esperados"]): r.append("Ajustar cantidad esperada de adjuntos: hay más archivos cargados.")
    return r


def pendientes(b,token=None):
    return [(i,faltantes(b,i,token)) for i in range(12) if faltantes(b,i,token)]


def exportar_zip(b,pdf):
    out=BytesIO()
    carpeta=slug(b["datos"]["proceso"],50)+"_"+slug(b["datos"]["titulo"],80)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(carpeta+"/Reportes/Propuesta.pdf",pdf)
        z.writestr(carpeta+"/Reportes/Preguntas_y_respuestas.md",esqueleto_markdown(b))
        for a in disponibles(b):
            z.writestr(carpeta+"/Adjuntos/"+a["guardado"],base64.b64decode(a["base64"]))
    return out.getvalue()


def esqueleto_markdown(b,solo_estructura=False):
    d=b["datos"]
    out=["# PROPUESTA TÉCNICA Y ECONÓMICA", "",
         "Instrucción para IA: conserva esta estructura; completa lo pendiente solo con antecedentes aportados. Distingue requisitos de las bases y compromisos propuestos. No inventes experiencia, personas, acreditaciones ni archivos adjuntos.", ""]
    for i,nombre in enumerate(PASOS):
        out += [f"## {i+1}. {nombre}",""]
        for p,k,pregunta,t,req in PREGUNTAS:
            if p==i:
                out += [f"### {pregunta}", "[COMPLETAR]" if solo_estructura else str(d[k] or "[PENDIENTE]"), ""]
        if i==5:
            out += ["### Módulos: bloque / nombre / contenidos / horas de capacitación / modalidad",""]
            out += ["[AGREGAR MÓDULOS]"] if solo_estructura else [f"- {m['jornada']} | {m['nombre']} | {m['contenido']} | {m['horas']:g} h | {m['tipo']}" for m in b["modulos"]]
        if i==7:
            for doc in b["docentes"]:
                out += ["### Relator: nombre / RUT / título / experiencia / disponibilidad", "[COMPLETAR]" if solo_estructura else f"{doc.get('rol', 'Relator')} | {doc['nombre']} | {doc['rut']} | {doc['titulo']} | {doc['experiencia']} | {doc['disponibilidad']}"]
                out += [f"- [ ] {x['requisito']}" if solo_estructura else f"- {x['requisito']}: {etiqueta_estado(x['estado'])}. Respaldo: {x['respaldo'] or '[PENDIENTE]'}" for x in doc["checklist"]]
        if i in {8,9}:
            out += [f"- [ ] {x['requisito']}" if solo_estructura else f"- {x['requisito']}: {etiqueta_estado(x['estado'])}. Respaldo: {x['respaldo'] or '[PENDIENTE]'}" for x in b["compra" if i==8 else "certificacion"]]
        if i==11 and not solo_estructura:
            out += [f"- Documento declarado: {a['nombre']} | Categoría: {a['categoria']}" for a in b["declarados"]]
            out += [f"- Documento: {descripcion_documento(a)} | Categoría: {a['categoria']}" for a in b["archivos"]]
        out += [""]
    return "\n".join(out)


ESTADOS_VISUALES = {
    "Por verificar": ("pendiente", "Por revisar"),
    "Comprometido": ("tick", "Incluido"),
    "Declarado": ("tick", "Informado"),
    "Respaldado": ("tick", "Con respaldo"),
    "A evaluación del comprador": ("alerta", "Observación"),
    "Cumple": ("tick", "En orden"),
    "No cumple": ("cruz", "No cumple"),
    "No aplica": ("neutro", "No aplica"),
}


def etiqueta_estado(estado):
    tipo, texto = ESTADOS_VISUALES.get(estado, ("pendiente", "Por revisar"))
    return {"tick":"✓", "alerta":"△", "cruz":"✕", "pendiente":"○", "neutro":"–"}[tipo]+" "+texto


class EstadoPDF(Flowable):
    """Estado documental sobrio, sin iconos ni afirmaciones añadidas.

    Conserva literalmente el estado informado por el usuario. El color de
    advertencia no sustituye la revisión documental del organismo comprador.
    """
    def __init__(self, estado):
        super().__init__()
        self.estado = estado
        self.color = {
            "A evaluación del comprador": colors.HexColor("#906B35"),
            "No cumple": colors.HexColor("#984B4B"),
            "Por verificar": MUTED,
        }.get(estado, NAVY)
        self.parrafo = Paragraph(
            escape(estado),
            ParagraphStyle("estado_editorial", fontName=FUENTE_SANS,
                           fontSize=7.25, leading=10, textColor=self.color),
        )

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        _, self.height = self.parrafo.wrap(max(10, availWidth-1), availHeight)
        return self.width, self.height

    def draw(self):
        self.parrafo.drawOn(self.canv, 0, 0)


def comparar_presupuesto(d):
    """Porcentaje sobre el presupuesto del comprador; incluye impuestos aplicables."""
    total=montos(d)[2]; presupuesto=int(d["presupuesto"])
    if total is None or presupuesto<=0: return None
    diferencia=presupuesto-total
    porcentaje=(Decimal(abs(diferencia))*100/Decimal(presupuesto)).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
    numero=f"{porcentaje:.2f}".replace(".",",")
    if diferencia>0:
        return {"porcentaje":f"{numero} % BAJO EL PRESUPUESTO", "diferencia":f"Diferencia a favor del comprador: {pesos(diferencia)}."}
    if diferencia<0:
        return {"porcentaje":f"{numero} % SOBRE EL PRESUPUESTO", "diferencia":f"Diferencia sobre el presupuesto: {pesos(-diferencia)}."}
    return {"porcentaje":"0,00 % - IGUAL AL PRESUPUESTO", "diferencia":"La oferta coincide con el presupuesto del comprador."}


def titulo_documento(categoria):
    return {
        "Anexo Nº 1":"Anexo Nº 1: Identificación del oferente",
        "CV y respaldos relator":"Currículum del relator y antecedentes de competencias y certificaciones",
        "CV relator":"Currículum del relator",
        "Respaldo relator":"Antecedentes de competencias y certificaciones del relator",
        "Bases técnicas":"Bases técnicas del servicio",
        "Orden de compra":"Orden de compra del servicio",
    }.get(categoria,"Antecedente complementario de la oferta")


def descripcion_documento(archivo):
    return archivo.get("descripcion", "").strip() or titulo_documento(archivo["categoria"])


def estilos_pdf():
    """Jerarquía tipográfica inspirada en LaTeX article/report.

    Márgenes A4, cuerpo serif, color estructural Beamer y tablas discretas.
    Evita paneles, tarjetas, pictogramas y encabezados sobredimensionados.
    """
    return {
        "body": ParagraphStyle(
            "cuerpo_informe", fontName=FUENTE_SERIF, fontSize=10,
            leading=15.2, textColor=INK, spaceAfter=8.5,
            alignment=TA_JUSTIFY, allowWidows=0, allowOrphans=0),
        "small": ParagraphStyle(
            "tabla_informe", fontName=FUENTE_SERIF, fontSize=8.45,
            leading=12.0, textColor=INK, spaceAfter=0,
            allowWidows=0, allowOrphans=0),
        "h1": ParagraphStyle(
            "seccion_informe", fontName=FUENTE_SERIF_BOLD,
            fontSize=15.2, leading=19.5, textColor=NAVY,
            spaceBefore=15, spaceAfter=9, keepWithNext=True),
        "h2": ParagraphStyle(
            "subseccion_informe", fontName=FUENTE_SERIF_BOLD,
            fontSize=10.7, leading=14.2, textColor=NAVY,
            spaceBefore=13, spaceAfter=5.5, keepWithNext=True),
        "th": ParagraphStyle(
            "cabecera_tabla", fontName=FUENTE_SANS_BOLD,
            fontSize=7.8, leading=10.5, textColor=NAVY, spaceAfter=0),
        "note": ParagraphStyle(
            "nota_informe", fontName=FUENTE_SERIF, fontSize=9.1,
            leading=13.3, textColor=MUTED, spaceAfter=8),
        "label": ParagraphStyle(
            "etiqueta_informe", fontName=FUENTE_SANS_BOLD,
            fontSize=8.3, leading=11, textColor=MUTED, spaceAfter=0),
        "enumeracion": ParagraphStyle(
            "enumeracion_editorial", fontName=FUENTE_SERIF, fontSize=10,
            leading=14.8, textColor=INK, spaceAfter=5,
            alignment=TA_JUSTIFY, leftIndent=19, firstLineIndent=-16,
            allowWidows=0, allowOrphans=0),
        "money": ParagraphStyle(
            "monto_informe", fontName=FUENTE_SERIF_BOLD,
            fontSize=10.3, leading=14, textColor=NAVY),
    }


class CanvasConTotal(Canvas):
    """Numera «Página n de N» sin alterar el cuerpo ni las tablas del PDF."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estados_de_pagina = []
        self._destinos_pagina = []

    def showPage(self):
        self._estados_de_pagina.append(dict(self.__dict__))
        self._destinos_pagina = []
        self._startPage()

    def save(self):
        numero_total = len(self._estados_de_pagina)
        for estado in self._estados_de_pagina:
            self.__dict__.update(estado)
            for destino in self._destinos_pagina:
                self.bookmarkPage(destino)
            if self._pageNumber > 1:
                ancho, _ = A4
                self.saveState()
                self.setFillColor(MUTED)
                self.setFont(FUENTE_SANS, 7.3)
                self.drawRightString(ancho - 57, 31,
                                     f"Página {self._pageNumber} de {numero_total}")
                self.restoreState()
            super().showPage()
        super().save()


class DocumentoEditorial(SimpleDocTemplate):
    """Crea marcadores PDF navegables para cada sección del informe."""
    def afterFlowable(self, flowable):
        clave = getattr(flowable, "_marca_seccion", None)
        if clave:
            self.canv._destinos_pagina.append(clave)
            self.canv.bookmarkPage(clave)
            self.canv.addOutlineEntry(flowable._titulo_seccion, clave, level=0)


def generar_pdf(b, token=None, solo_portada=False):
    b = validar(b)
    d = b["datos"]
    sty = estilos_pdf()
    margen_izq, margen_der = 61, 57
    ancho = A4[0] - margen_izq - margen_der
    total_curso = sum(horas(b).values())
    total_precio = montos(d)[2]

    def P(texto, estilo="body"):
        valor = limpiar(str(texto)) if texto is not None and str(texto).strip() else "Por completar"
        return Paragraph(escape(valor).replace("\n", "<br/>"), sty[estilo])

    def parrafos(texto):
        partes = (texto or "Por completar").split("\n\n")
        return [P(parte.strip()) for parte in partes if parte.strip()]

    def campo(nombre, texto):
        return [P(nombre, "h2"), *parrafos(texto)]

    def tabla(encabezados, filas, anchos=None):
        contenido = [[P(e, "th") for e in encabezados]]
        contenido += [[celda if isinstance(celda, Flowable) else P(celda, "small")
                       for celda in fila] for fila in filas]
        n = len(encabezados)
        if anchos is None:
            anchos = [ancho/n]*n
        t = Table(contenido, colWidths=anchos, repeatRows=1,
                  splitByRow=1, splitInRow=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE),
            ("LINEABOVE", (0, 0), (-1, 0), 1, NAVY),
            ("LINEBELOW", (0, 0), (-1, 0), .55, GOLD),
            ("LINEBELOW", (0, 1), (-1, -1), .25, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    # Conserva el logo proporcionado, pero permite generar un informe digno
    # incluso si el archivo SVG/PNG todavía no está disponible.
    try:
        raw_logo, nombre_logo = bytes_logo(b, "oferente")
        logo = preparar_logo(raw_logo, nombre_logo) if raw_logo else None
    except Exception as exc:
        raise ValueError(f"No se pudo interpretar el logo del oferente: {exc}") from exc
    try:
        raw_comprador, nombre_comprador = bytes_logo(b, "comprador")
        logo_comprador = preparar_logo(raw_comprador, nombre_comprador) if raw_comprador else None
    except Exception as exc:
        raise ValueError(f"No se pudo interpretar el logo del organismo comprador: {exc}") from exc

    def texto_ajustado(c, texto, x, borde_superior, anchura, altura,
                       tamano=12, negrita=False, color=INK, centrado=False):
        fuente = FUENTE_SERIF_BOLD if negrita else FUENTE_SERIF
        for tam in [tamano - .5*i for i in range(max(1, int((tamano-8)*2)+1))]:
            estilo = ParagraphStyle(
                "cubierta", fontName=fuente, fontSize=tam,
                leading=tam*1.32, textColor=color,
                alignment=1 if centrado else TA_LEFT)
            par = Paragraph(escape(limpiar(texto or "Por completar")), estilo)
            _, alto_real = par.wrap(anchura, altura)
            if alto_real <= altura:
                par.drawOn(c, x, borde_superior - alto_real)
                return alto_real
        raise ValueError("El título de la portada es demasiado largo para el área disponible.")

    def portada(c, doc):
        w, h = A4
        c.saveState()
        c.setTitle(f"Propuesta técnica y económica - {d['proceso']}")
        c.setAuthor(d["oferente"])
        c.setSubject(d["titulo"])
        c.setKeywords("propuesta técnica, propuesta económica, capacitación")
        # Cabecera de institución y regla delgada, sin recuadros promocionales.
        c.setFillColor(NAVY)
        c.setFont(FUENTE_SANS_BOLD, 8.5)
        entidad = " ".join(d["nombre_comercial"].strip().split())
        if len(entidad) > 50:
            entidad = entidad[:47] + "..."
        if logo_comprador:
            # Ambos logos, sin rótulos superiores. Se preservan sus
            # proporciones y la línea fina de separación inferior.
            if logo:
                dibujar_logo(c, logo, margen_izq, h-121, 150, 49, "")
            else:
                texto_ajustado(c, entidad.upper(), margen_izq, h-89, 220, 34,
                               tamano=9.3, negrita=True, color=NAVY)
            dibujar_logo(c, logo_comprador, w-margen_der-160, h-121, 160, 49, "")
        else:
            c.drawString(margen_izq, h-75, entidad.upper())
            if logo:
                dibujar_logo(c, logo, w-200, h-115, 140, 55, "")
        c.setStrokeColor(NAVY)
        c.setLineWidth(.9)
        c.line(margen_izq, h-127, w-margen_der, h-127)

        c.setFont(FUENTE_SANS_BOLD, 10.5)
        c.setFillColor(GOLD)
        c.drawCentredString(w/2, 651, "PROPUESTA TÉCNICA Y ECONÓMICA")
        texto_ajustado(c, d["titulo"], margen_izq+5, 630, ancho-10, 99,
                       tamano=22, negrita=True, color=NAVY, centrado=True)
        c.setFont(FUENTE_SANS, 9.2)
        c.setFillColor(MUTED)
        c.drawCentredString(w/2, 505,
                            f"{d['modalidad']}  ·  {d['proceso'] or 'Código por completar'}")

        c.setStrokeColor(LINE)
        c.line(110, 477, w-110, 477)
        c.setFillColor(MUTED)
        c.setFont(FUENTE_SANS_BOLD, 8.1)
        c.drawCentredString(w/2, 455, "DOCUMENTO PRESENTADO A")
        texto_ajustado(c, d["comprador"], 80, 440, w-160, 42,
                       tamano=13.5, negrita=True, color=NAVY, centrado=True)

        # Ficha simple, alineada como un documento académico/profesional.
        ficha = [
            ("Modalidad", "Clases virtuales en vivo"),
            ("Participantes", f"{d['cupos']} personas"),
            ("Duración", f"{total_curso:g} horas de capacitación"),
            ("Valor ofertado", pesos(total_precio) if total_precio is not None else "Por definir"),
        ]
        y = 345
        for etiqueta, valor in ficha:
            c.setFillColor(MUTED)
            c.setFont(FUENTE_SANS, 8.8)
            c.drawString(109, y, etiqueta)
            texto_ajustado(c, valor, 245, y+10, 245, 24, tamano=10,
                           negrita=etiqueta == "Valor ofertado", color=NAVY if etiqueta == "Valor ofertado" else INK)
            c.setStrokeColor(LINE)
            c.setLineWidth(.35)
            c.line(108, y-11, w-108, y-11)
            y -= 36

        c.setFillColor(MUTED)
        c.setFont(FUENTE_SANS_BOLD, 8.1)
        c.drawString(margen_izq, 163, "OFERENTE")
        texto_ajustado(c, d["oferente"], margen_izq, 153, ancho, 36,
                       tamano=11.5, negrita=True, color=NAVY)
        c.setFont(FUENTE_SERIF, 9)
        c.setFillColor(INK)
        c.drawString(margen_izq, 107, "RUT " + d["rut_oferente"])
        correo = d["correo"]
        if len(correo) < 90:
            c.drawString(margen_izq, 92, correo)
        c.setStrokeColor(NAVY)
        c.setLineWidth(.65)
        c.line(margen_izq, 72, w-margen_der, 72)
        c.setFont(FUENTE_SANS, 8)
        c.setFillColor(MUTED)
        c.drawString(margen_izq, 56, "Fecha de emisión: " + d["fecha_propuesta"])
        c.drawRightString(w-margen_der, 56,
                          "BORRADOR" if b["marcar_borrador"] else "PROPUESTA FORMAL")
        c.restoreState()

    def paginas(c, doc):
        w, h = A4
        c.saveState()
        c.setFont(FUENTE_SANS_BOLD, 7.3)
        c.setFillColor(NAVY)
        nombre = d["nombre_comercial"].upper()
        if len(nombre) > 44:
            nombre = nombre[:41] + "..."
        c.drawString(margen_izq, h-35, nombre)
        c.setFont(FUENTE_SANS, 7.2)
        c.setFillColor(MUTED)
        c.drawRightString(w-margen_der, h-35, d["proceso"][:45])
        c.setLineWidth(.72)
        c.setStrokeColor(NAVY)
        c.line(margen_izq, h-46, w-margen_der, h-46)
        c.setStrokeColor(LINE)
        c.setLineWidth(.45)
        c.line(margen_izq, 45, w-margen_der, 45)
        c.setFillColor(MUTED)
        c.setFont(FUENTE_SANS, 7.3)
        c.drawString(margen_izq, 31,
                     "Borrador · revisión pendiente" if b["marcar_borrador"]
                     else "Propuesta técnica y económica")
        # La numeración con total se agrega al finalizar la composición.
        c.restoreState()

    buffer = BytesIO()
    doc = DocumentoEditorial(
        buffer, pagesize=A4, rightMargin=margen_der, leftMargin=margen_izq,
        topMargin=68, bottomMargin=62, title=f"Propuesta técnica y económica - {d['proceso']}",
        author=d["oferente"], subject=d["titulo"],
        keywords="propuesta técnica, propuesta económica, capacitación", allowSplitting=1)
    story = [Spacer(1, 1)]
    if solo_portada:
        doc.build(story, onFirstPage=portada, onLaterPages=paginas, canvasmaker=CanvasConTotal)
        return buffer.getvalue()
    story.append(PageBreak())
    numero_seccion = 0

    def cap(titulo, clave=None, pagina_nueva=False):
        nonlocal numero_seccion
        numero_seccion += 1
        if pagina_nueva:
            story.append(PageBreak())
        else:
            story.append(CondPageBreak(155))
        p = P(f"{numero_seccion}.  {titulo}", "h1")
        p._marca_seccion = f"seccion_{numero_seccion}"
        p._titulo_seccion = f"{numero_seccion}. {titulo}"
        story.extend([p, HRFlowable(width="100%", thickness=.65, color=GOLD,
                                    spaceBefore=0, spaceAfter=11)])
        if clave:
            intro = INTRODUCCIONES.get(clave, "").format(**d)
            if intro:
                story.extend(parrafos(intro))

    cap("Presentación institucional")
    story.extend(parrafos(d["quienes"]))
    story.extend(campo("Visión institucional", d["vision"]))
    story.extend(campo("Servicio propuesto", d["que_ofrecemos"]))

    cap("Antecedentes de la contratación", "proceso")
    story.extend(campo("Servicio requerido", d["titulo"]))
    story.append(tabla(["Antecedente", "Información"], [
        ["Organismo comprador", d["comprador"] + "\nRUT " + d["rut_comprador"]],
        ["Modalidad y código", d["modalidad"] + "\n" + d["proceso"]],
        ["Categoría del servicio", d["rubro"]],
        ["Ejecución", "100 % virtual, sin asistencia presencial"],
        ["Modalidad del curso", d["modalidad_curso"]],
    ], [156, ancho-156]))
    if d["numero_oc"].strip():
        story.extend(campo("Orden de compra", d["numero_oc"]))
    fechas = [[etiqueta, d[k]] for etiqueta, k in [
        ("Publicación", "publicacion"),
        ("Cierre del primer llamado", "cierre_1"),
        ("Cierre del segundo llamado", "cierre_2")]
        if d[k].strip()]
    if fechas:
        story.append(P("Fechas del proceso", "h2"))
        story.append(tabla(["Hito", "Fecha y hora"], fechas, [212, ancho-212]))

    cap("Objetivos y participantes", "objetivos")
    story.extend(campo("Objetivo general", d["objetivo_general"]))
    story.append(P("Objetivos específicos", "h2"))
    for i, linea in enumerate(filter(str.strip, d["objetivos_especificos"].splitlines()), 1):
        story.append(P(f"{i}. {linea.strip()}", "enumeracion"))
    story.extend(campo("Participantes", f"La actividad contempla {d['cupos']} participantes. "
                       + d["participantes"]))
    story.extend(campo("Conocimientos previos", d["prerrequisitos"]))

    cap("Programa de capacitación", "programa")
    totales = horas(b)
    for jornada in dict.fromkeys(m["jornada"] for m in b["modulos"]):
        story.append(P(jornada, "h2"))
        filas = [m for m in b["modulos"] if m["jornada"] == jornada]
        modulos = tabla(["Módulo / modalidad", "Contenidos", "Horas"],
            [[m["nombre"] + "\n" + m["tipo"], m["contenido"], f"{m['horas']:g}"]
             for m in filas]
            + [["Total " + jornada.lower(), "Horas de capacitación",
                f"{sum(m['horas'] for m in filas):g}"]],
            [141, ancho-189, 48])
        modulos.setStyle(TableStyle([
            ("BACKGROUND", (0, -1), (-1, -1), PALE),
            ("LINEABOVE", (0, -1), (-1, -1), .65, NAVY),
        ]))
        story.append(modulos)
    story.append(Spacer(1, 6))
    story.append(P(f"Duración total del programa: {sum(totales.values()):g} horas de capacitación.", "h2"))

    cap("Metodología y recursos de aprendizaje", "metodologia")
    story.extend(campo("Desarrollo de las actividades", d["metodologia"]))
    story.extend(campo("Herramientas de trabajo", d["herramientas"]))
    story.extend(campo("Materiales para los participantes", d["materiales"]))

    cap("Condiciones de ejecución virtual", "logistica")
    story.extend(campo("Recinto y ubicación", d["lugar"]))
    responsable = {
        "Proveedor": "El proveedor habilitará la plataforma de videoconferencia para las clases virtuales.",
        "Comprador": "El recinto será dispuesto por el organismo comprador.",
        "Compartido": "La habilitación del recinto se coordinará entre el oferente y el organismo comprador.",
        "Por definir": "El responsable del recinto se confirmará antes de la ejecución.",
    }.get(d["quien_lugar"], d["quien_lugar"])
    story.extend(parrafos(responsable))
    story.extend(campo("Fechas de ejecución", d["periodo_ejecucion"]))
    if d["fecha_ejecucion"].strip():
        story.extend(parrafos(d["fecha_ejecucion"]))
    story.extend(campo("Equipamiento y conectividad", d["equipamiento"]))
    if d["cafeteria"].strip():
        story.extend(campo("Servicio de cafetería", d["cafeteria"]))

    cap("Equipo de relatoría y antecedentes profesionales", "relator")
    story.extend(campo("Relatoría principal y alternativa", d["perfil_docente"]))
    story.extend(parrafos(
        "La oferta contempla un relator principal (Diego Zamorano) y un alternativo de contingencia "
        "(Daniel Vargas). Diego es el profesional programado para impartir la totalidad del curso. "
        "Daniel no constituye una segunda oferta ni reemplaza libremente al titular: cualquier "
        "sustitución deberá contar con autorización previa del Servicio Médico Legal y preservar "
        "las 24 horas, los ocho módulos y el precio ofertado."))
    for rel in b["docentes"]:
        story.append(P(rel.get("rol", "Relator propuesto") + ": " + rel["nombre"], "h2"))
        story.extend(parrafos(f"RUT {rel['rut']}. {rel['titulo']}."))
        story.extend(parrafos(rel["experiencia"]))
        story.extend(parrafos(rel["disponibilidad"]))
        story.append(tabla(["Competencia o antecedente", "Estado", "Respaldo"],
            [[x["requisito"], EstadoPDF(x["estado"]), x["respaldo"]]
             for x in rel["checklist"]], [157, 102, ancho-259]))
    story.extend(campo("Documentación de respaldo", d["referencia_cv"]))

    cap("Requisitos de contratación y observaciones", "requisitos")
    story.append(tabla(["Requisito", "Estado declarado", "Respuesta de la oferta"],
        [[x["requisito"], EstadoPDF(x["estado"]), x["respaldo"]]
         for x in b["compra"]], [157, 102, ancho-259]))
    if d["requisitos_oc"].strip():
        story.extend(campo("Condiciones de la orden de compra", d["requisitos_oc"]))
    if d["observaciones"].strip():
        story.extend(campo("Observaciones", d["observaciones"]))

    cap("Evaluación, certificación e informe final", "certificacion")
    for etiqueta, clave in [
        ("Evaluación del aprendizaje", "evaluacion"),
        ("Condiciones de aprobación", "aprobacion"),
        ("Entrega de certificados y resultados", "entrega_certificados")]:
        story.extend(campo(etiqueta, d[clave]))
    story.extend(parrafos("El informe final será entregado a la " + d["destino_informe"] + "."))
    story.append(P("Contenido de los entregables", "h2"))
    tabla_entregables = tabla(["Requisito", "Estado declarado"],
        [[x["requisito"], EstadoPDF(x["estado"])] for x in b["certificacion"]],
        [ancho-132, 132])
    # Tabla compacta para evitar dejar medio folio vacío antes de los entregables.
    tabla_entregables.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tabla_entregables)

    cap("Propuesta económica", "economica")
    neto, iva, total = montos(d)
    comparacion = comparar_presupuesto(d)
    impuesto_txt = ("Exento / sin impuesto" if d["impuesto"] == "Exento / sin impuesto"
                    else f"{d['tasa']} %" if d["impuesto"] == "Con impuesto"
                    else "Por definir")
    precio = tabla(["Concepto", "Valor"], [
        ["Valor global del servicio", pesos(neto)],
        ["Tratamiento tributario", impuesto_txt],
        ["Impuesto calculado", pesos(iva) if iva is not None else "Por definir"],
        ["Total ofertado", pesos(total) if total is not None else "Por definir"],
    ], [ancho-157, 157])
    precio.setStyle(TableStyle([
        ("BACKGROUND", (0, -1), (-1, -1), PALE),
        ("LINEABOVE", (0, -1), (-1, -1), .8, NAVY),
    ]))
    story.append(precio)
    story.extend(campo("Alcance del valor ofertado", d["incluye_precio"]))

    cap("Documentación que acompaña la oferta", "documentos")
    story.extend(parrafos(d["documentacion_adjunta"]))
    cargadas = {x["categoria"] for x in b["archivos"]}
    nombres = [x["nombre"] for x in b["declarados"] if x["categoria"] not in cargadas]
    nombres += [descripcion_documento(x) for x in b["archivos"]
                if x["categoria"] != "Bases técnicas"]
    for i, nombre in enumerate(dict.fromkeys(nombres), 1):
        story.append(P(f"{i}. {nombre}"))

    # Sección de contacto siempre visible, con independencia de la opción
    # "incluir_admin". No incluye cuentas bancarias ni información sensible.
    cap("Contacto de la propuesta")
    story.append(tabla(["Antecedente", "Información"], [
        ["Nombre", d["contacto_oferta"]],
        ["Cargo", d["cargo_contacto"]],
        ["Teléfono", d["telefono"]],
        ["Correo electrónico", d["correo"]],
    ], [135, ancho-135]))
    story.extend(parrafos("Contacto designado por el oferente para consultas y coordinación relacionadas con esta propuesta."))

    if b["incluir_admin"]:
        cap("Identificación del oferente", "identificacion", pagina_nueva=True)
        story.append(P("Datos institucionales", "h2"))
        story.append(tabla(["Antecedente", "Información"],
            [["Razón social", d["oferente"]],
             ["RUT", d["rut_oferente"]],
             ["Domicilio", d["domicilio_empresa"]]], [132, ancho-132]))
        story.append(P("Representación legal", "h2"))
        story.append(tabla(["Antecedente", "Información"],
            [["Representante", d["representante"]],
             ["Cargo", d["cargo_representante"]],
             ["RUT", d["rut_representante"]]],
            [132, ancho-132]))
        if any(d[k].strip() for k in ("banco", "tipo_cuenta", "cuenta", "correo_pagos")):
            story.append(P("Antecedentes para transferencia", "h2"))
            story.append(tabla(["Antecedente", "Información"],
                [["Titular", d["oferente"]], ["RUT", d["rut_oferente"]],
                 ["Banco", d["banco"]], ["Tipo de cuenta", d["tipo_cuenta"]],
                 ["N.º de cuenta", d["cuenta"]], ["Correo", d["correo_pagos"]]],
                [132, ancho-132]))

    if b["incluir_revision"]:
        cap("Anexo: revisión documental", pagina_nueva=True)
        story.extend(parrafos(
            "Relación de antecedentes que requieren revisión antes de presentar la oferta. "
            "Esta sección es un instrumento interno de control documental."))
        for i, lista in pendientes(b, token):
            story.append(P(PASOS[i], "h2"))
            for elemento in lista:
                story.append(P("- " + elemento, "small"))

    doc.build(story, onFirstPage=portada, onLaterPages=paginas, canvasmaker=CanvasConTotal)
    return buffer.getvalue()


def firma_propuesta(b):
    """Firma del contenido visible del PDF y de sus fuentes externas.

    Evita serializar los archivos anexos, que pueden sumar decenas de MB.
    """
    datos = {k: v for k, v in b.items() if k not in {"archivos", "logos"}}
    datos["archivos"] = [
        {k: v for k, v in a.items() if k != "base64"} for a in b.get("archivos", [])
    ]
    datos["logos"] = [
        (rol, info.get("nombre", ""), hashlib.sha256(info.get("base64", "").encode()).hexdigest())
        for rol, info in sorted(b.get("logos", {}).items())
    ]
    try:
        local, _ = bytes_logo(b, "oferente")
        datos["logo_local_oferente"] = hashlib.sha256(local or b"").hexdigest()
    except Exception:
        datos["logo_local_oferente"] = "logo_no_disponible"
    serial = json.dumps(datos, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256((PDF_RENDER_VERSION + serial).encode()).hexdigest()


def main():
    import streamlit as st
    st.set_page_config(page_title="Propuesta técnica | OTEC Santa Mónica",page_icon="📄",layout="centered")
    st.title("Propuesta técnica y económica")
    if "modelo_propuesta_v6" not in st.session_state:
        # Una versión anterior puede haber dejado widgets con valores de ejemplo.
        for clave in list(st.session_state):
            if clave.startswith("q_") or clave in {"propuesta_pdf","propuesta_firma"}:
                del st.session_state[clave]
        st.session_state.modelo_propuesta_v6=nuevo()
    b=st.session_state.modelo_propuesta_v6
    # Migrar una sesión creada con el generador de un solo relator una sola vez.
    if "sml_dos_relatores_migracion_v1" not in st.session_state:
        if len(b.get("docentes", [])) == 1 and "Zamorano" in b["docentes"][0].get("nombre", ""):
            alternativo = copy.deepcopy(RELATOR_ALTERNATIVO)
            alternativo["id"] = uuid4().hex[:12]
            alternativo["checklist"] = items_check(REQ_RELATOR_ALTERNATIVO)
            for row, (estado, respaldo) in zip(alternativo["checklist"], [
                ("Respaldado", "Ingeniero Civil Industrial PUCV, según antecedentes."),
                ("Respaldado", "Diplomado de 96 horas en Data Science e IA, PUCV."),
                ("Respaldado", "Certificados de relatoría en instituciones públicas."),
                ("Declarado", "Experiencia en análisis de datos e IA, según CV.")
            ]):
                row.update(estado=estado, respaldo=respaldo)
            b["docentes"][0].setdefault("rol", "Relator principal (prioridad 1)")
            b["docentes"].append(alternativo)
            b["datos"]["perfil_docente"] = DATOS_LICITACION["perfil_docente"]
            b["datos"]["referencia_cv"] = DATOS_LICITACION["referencia_cv"]
            b["datos"]["documentacion_adjunta"] = DATOS_LICITACION["documentacion_adjunta"]
            b["declarados"] = copy.deepcopy(ADJUNTOS_DECLARADOS)
            b["datos"]["adjuntos_esperados"] = 2
        st.session_state.sml_dos_relatores_migracion_v1 = True
    # Corregir únicamente el recorte histórico exacto de 500 caracteres
    # causado por el text_input en el campo de experiencia. Respeta cualquier
    # contenido distinto que haya editado el usuario.
    if b.get("docentes"):
        recortado = RELATOR_INICIAL["experiencia"][:500]
        if b["docentes"][0].get("experiencia") == recortado:
            b["docentes"][0]["experiencia"] = RELATOR_INICIAL["experiencia"]
            clave_widget = "q_docentes_0_experiencia"
            if st.session_state.get(clave_widget) == recortado:
                st.session_state[clave_widget] = RELATOR_INICIAL["experiencia"]
    b.setdefault("logos", {}).setdefault("comprador", {"nombre":"", "base64":""})
    def leer(path):
        obj=b
        for k in path: obj=obj[k]
        return obj

    def cambiar(path,key):
        obj=b
        for k in path[:-1]: obj=obj[k]
        obj[path[-1]]=st.session_state[key]

    def widget(path,label,tipo="texto",opciones=None):
        key="q_"+"_".join(map(str,path))
        if key not in st.session_state: st.session_state[key]=leer(path)
        kw=dict(key=key,on_change=cambiar,args=(path,key))
        if tipo=="bool": return st.checkbox(label,**kw)
        if opciones is not None:
            formato={"format_func":etiqueta_estado} if opciones==ESTADOS else {}
            return st.selectbox(label,opciones,**formato,**kw)
        if tipo in {"entero","decimal"}:
            minimo=1 if path[-1]=="cantidad" else 0
            tope=100 if path[-1] in {"tasa","adjuntos_esperados"} else 10000 if path[-1] in {"horas","horas_exigidas","cupos"} else 10**12
            if tipo=="decimal": return st.number_input(label,min_value=float(minimo),max_value=float(tope),step=.5,**kw)
            return st.number_input(label,min_value=minimo,max_value=tope,step=1,**kw)
        # La experiencia profesional es una descripción extensa: nunca usar
        # text_input(max_chars=500), que recorta silenciosamente el CV.
        if tipo=="area" or path[-1]=="experiencia":
            return st.text_area(label,max_chars=12000,height=180,**kw)
        return st.text_input(label,max_chars=255 if tipo=="corto" else 500,**kw)

    def preguntas(seccion):
        fila=0
        for p,k,label,tipo,requerido in PREGUNTAS:
            if p!=seccion: continue
            opts={"modalidad":MODALIDADES,"modalidad_curso":["Presencial","Virtual","Mixta","Presencial con estudio autónomo","Otra"],
                  "responsable":["Proveedor","Comprador","Compartido","Por definir"],
                  "impuesto":["Por definir","Con impuesto","Exento / sin impuesto"]}.get(tipo)
            if tipo=="area":
                widget(["datos",k],label,tipo,opts)
                fila=0
            else:
                if fila%2==0: cols=st.columns(2)
                with cols[fila%2]: widget(["datos",k],label,tipo,opts)
                fila+=1

    def checklist(path,titulo):
        st.markdown("**"+titulo+"**")
        lista=leer(path)
        if not lista: st.caption("Sin requisitos. Puedes agregar los que correspondan a las bases.")
        for j,row in enumerate(lista):
            with st.container(border=True):
                a,c=st.columns([3,1])
                with a: widget(path+[j,"requisito"],f"Requisito {j+1}")
                with c: widget(path+[j,"estado"],f"Estado {j+1}",opciones=ESTADOS)
                widget(path+[j,"respaldo"],f"¿Qué documento o compromiso respalda el requisito {j+1}?")
                if st.button("Eliminar este requisito",key="del_"+row["id"]):
                    lista.pop(j)
                    # Las posiciones cambian: limpiar claves del bloque antes de reconstruir.
                    prefix="q_"+"_".join(map(str,path))+"_"
                    for k in list(st.session_state):
                        if k.startswith(prefix): del st.session_state[k]
                    st.rerun()
        if st.button("Agregar requisito",key="add_"+"_".join(map(str,path))):
            lista.extend(items_check(["Nuevo requisito: editar según las bases"]))
            st.rerun()

    def cargar_logo(rol,key):
        archivo=st.session_state.get(key)
        if archivo is None: return
        try:
            raw=archivo.getvalue(); preparar_logo(raw,archivo.name)
            b["logos"][rol]={"nombre":archivo.name[:200],"base64":base64.b64encode(raw).decode()}
            st.session_state["aviso_logo_"+rol]=""
        except Exception as exc: st.session_state["aviso_logo_"+rol]=str(exc)

    tab_generar, tab_detalles = st.tabs(["Generar PDF", "Detalles y edición"])

    with tab_generar:
        # Generación directa con los datos precargados o los editados en la otra pestaña.
        st.file_uploader(
            "Logo del organismo comprador (opcional)",
            type=["svg", "png", "jpg", "jpeg"],
            key=f"upload_logo_comprador_{st.session_state.get('logo_comprador_revision',0)}",
            on_change=cargar_logo,
            args=("comprador", f"upload_logo_comprador_{st.session_state.get('logo_comprador_revision',0)}"),
            help="Se incorpora exclusivamente en la portada, junto a la identificación del oferente.",
        )
        if st.session_state.get("aviso_logo_comprador"):
            st.error(st.session_state["aviso_logo_comprador"])
        if b["logos"].get("comprador", {}).get("base64"):
            st.caption("Logo seleccionado: " + b["logos"]["comprador"]["nombre"])
            if st.button("Quitar logo del comprador", type="secondary"):
                b["logos"]["comprador"] = {"nombre":"", "base64":""}
                st.session_state["aviso_logo_comprador"] = ""
                st.session_state["logo_comprador_revision"] = st.session_state.get("logo_comprador_revision",0) + 1
                st.rerun()

        firma_actual = firma_propuesta(b)
        if st.button("Generar PDF", type="primary"):
            try:
                st.session_state.propuesta_pdf = generar_pdf(b)
                st.session_state.propuesta_firma = firma_actual
                st.success("PDF generado correctamente.")
            except Exception as exc:
                st.session_state.pop("propuesta_pdf",None)
                st.session_state.pop("propuesta_firma",None)
                st.error(f"No se pudo generar el PDF: {exc}")
        if st.session_state.get("propuesta_pdf"):
            if st.session_state.get("propuesta_firma") == firma_actual:
                st.download_button(
                    "Descargar PDF", st.session_state.propuesta_pdf,
                    file_name=f"Propuesta_{slug(b['datos']['proceso'],80)}.pdf",
                    mime="application/pdf", type="primary",
                )
            else:
                st.caption("Existen cambios pendientes. Vuelve a generar el PDF para actualizarlos.")

    with tab_detalles:
        st.caption("Edita los datos, módulos, requisitos, anexos y condiciones del proceso. La generación se realiza desde la primera pestaña.")
        for seccion,nombre in enumerate(PASOS):
            with st.expander(f"{seccion+1:02d}. {nombre}",expanded=False):
                preguntas(seccion)
                if seccion==0:
                    d=b["datos"]
                    st.caption("Publicación a primer cierre: "+intervalo(d["publicacion"],d["cierre_1"]))
                    st.caption("Publicación a segundo cierre: "+intervalo(d["publicacion"],d["cierre_2"]))
                if seccion==1:
                    dd = b["datos"]
                    st.caption("Contacto: " + " · ".join(filter(None, [
                        dd["contacto_oferta"], dd["cargo_contacto"],
                        dd["telefono"], dd["correo"]])))
                if seccion==5:
                    st.markdown("**¿Qué módulos, contenidos y horas tendrá el programa?**")
                    for j,m in enumerate(b["modulos"]):
                        with st.container(border=True):
                            st.markdown(f"**Módulo {j+1}**")
                            a,c,e=st.columns([1,2,1])
                            with a: widget(["modulos",j,"jornada"],"Jornada / bloque")
                            with c: widget(["modulos",j,"nombre"],"Nombre del módulo")
                            with e: widget(["modulos",j,"horas"],"Horas de capacitación","decimal")
                            widget(["modulos",j,"contenido"],"¿Qué contenidos se abordarán?","area")
                            widget(["modulos",j,"tipo"],"Modalidad del módulo",opciones=["Presencial","Autónomo","Virtual"])
                            if st.button("Eliminar módulo",key="del_m_"+m["id"]):
                                b["modulos"].pop(j)
                                for k in list(st.session_state):
                                    if k.startswith("q_modulos_"): del st.session_state[k]
                                st.rerun()
                    if st.button("Agregar módulo"):
                        b["modulos"].append(dict(id=uuid4().hex[:12],jornada="Nueva jornada",nombre="Nuevo módulo",contenido="",horas=0.0,tipo="Presencial"))
                        st.rerun()
                    tot=horas(b); st.metric("Horas pedagógicas del programa",f"{sum(tot.values()):g}")
                    for jornada in dict.fromkeys(m["jornada"] for m in b["modulos"]):
                        h=sum(m["horas"] for m in b["modulos"] if m["jornada"]==jornada)
                        st.caption(f"Total {jornada.lower()}: {h:g} horas pedagógicas")
                    st.caption(" / ".join(f"{k}: {v:g} horas" for k,v in tot.items()))
                    if abs(sum(tot.values())-b["datos"]["horas_exigidas"])>.01:
                        st.warning("La suma del programa no coincide con las horas exigidas. Puedes generar el borrador y corregirla después.")
                if seccion==7:
                    st.caption("Relator identificado según el CV aportado. Su experiencia y competencias se describen conforme a los antecedentes disponibles.")
                    for j,rel in enumerate(b["docentes"]):
                        st.markdown(f"**Relator {j+1}**")
                        for k,label in [("rol","¿Cuál es su función en la propuesta?") , ("nombre","¿Cuál es su nombre completo?"),("rut","¿Cuál es su RUT?"),("titulo","¿Cuál es su título profesional?"),("experiencia","¿Qué experiencia efectiva declara en la temática?"),("disponibilidad","¿Cuál es su disponibilidad confirmada?")]:
                            widget(["docentes",j,k],label)
                        checklist(["docentes",j,"checklist"],f"Checklist del relator {j+1}")
                        if st.button("Eliminar relator",key="del_doc_"+rel["id"]):
                            b["docentes"].pop(j)
                            for k in list(st.session_state):
                                if k.startswith("q_docentes_"): del st.session_state[k]
                            st.rerun()
                    if st.button("Agregar otro relator"):
                        b["docentes"].append(dict(id=uuid4().hex[:12],rol="Relator adicional",nombre="",rut="",titulo="",experiencia="",disponibilidad="Por coordinar",checklist=items_check(REQ_RELATOR)))
                        st.rerun()
                if seccion==8:
                    st.caption("Las condiciones se revisan contra las bases aportadas. Si existe una orden de compra, incorpora su número, condiciones y documento en el formulario.")
                    checklist(["compra"],"Requisitos de contratación")
                if seccion==9: checklist(["certificacion"],"¿Qué incluirán los certificados y el informe final?")
                if seccion==10:
                    neto,iva,total=montos(b["datos"])
                    a,c,e=st.columns(3); a.metric("Neto + despacho",pesos(neto)); c.metric("Impuesto",pesos(iva) if iva is not None else "Por definir")
                    e.metric("Total",pesos(total) if total is not None else "Por definir")
                    st.caption("El PDF presenta el valor ofertado y el alcance del servicio.")
                    comparacion=comparar_presupuesto(b["datos"])
                    if comparacion: st.metric("Comparación con presupuesto",comparacion["porcentaje"])
                    if total is not None and total>b["datos"]["presupuesto"]>0: st.warning("La oferta supera el presupuesto estimado del comprador.")
                if seccion==11:
                    st.markdown("**Logo del oferente para la portada**")
                    contenedor_logo=st.container()
                    for rol,col in [("oferente",contenedor_logo)]:
                        with col:
                            key="upload_logo_"+rol
                            st.file_uploader("Adjuntar logo institucional (SVG, PNG o JPG)",type=["svg","png","jpg","jpeg"],key=key,on_change=cargar_logo,args=(rol,key))
                            if st.session_state.get("aviso_logo_"+rol): st.error(st.session_state["aviso_logo_"+rol])
                            try:
                                raw,n=bytes_logo(b,rol)
                                if raw:
                                    preparar_logo(raw,n)
                                    if not n.lower().endswith(".svg"):
                                        st.image(raw,width=180)
                                    st.caption(("Logo por defecto de GitHub: " if rol=="oferente" and not b["logos"][rol]["base64"] else "Logo listo: ")+n)
                                else: st.info("Logo opcional. Si no se incorpora, la portada se genera con cabecera institucional de texto.")
                            except Exception as exc: st.warning(str(exc))
                    st.caption(f"Logo opcional: {LOGO_NAME}, en la carpeta del script o en assets/, logos/ o images/. Sin logo, se utiliza cabecera institucional tipográfica.")
                    st.markdown("**Documentación adjunta: bases, anexos, CV y respaldos**")
                    st.caption("Ajusta la cantidad esperada para incluir todos los documentos. Máximo 20 MB por archivo y 100 MB en total. Los originales van en el ZIP; el PDF muestra su inventario.")
                    categoria=st.selectbox("Categoría del lote que incorporarás",CATEGORIAS_ADJUNTOS,key="categoria_lote")
                    subidos=st.file_uploader("Seleccionar archivos",type=["pdf","doc","docx","xls","xlsx","txt","png","jpg","jpeg","svg"],accept_multiple_files=True,key="uploads_documentos")
                    if st.button("Incorporar archivos al formulario",disabled=not subidos):
                        errors=[]
                        for archivo in subidos:
                            try: agregar_archivo(b,archivo.name,archivo.getvalue(),categoria)
                            except Exception as exc: errors.append(f"{archivo.name}: {exc}")
                        if errors: st.session_state.aviso_archivos="\n".join(errors)
                        st.rerun()
                    if st.session_state.get("aviso_archivos"): st.warning(st.session_state.pop("aviso_archivos"))
                    st.write(f"**{len(b['archivos'])} de {b['datos']['adjuntos_esperados']} archivos incorporados**")
                    for j,a in enumerate(b["archivos"]):
                        with st.container(border=True):
                            st.caption("Original: "+a["nombre"])
                            a.setdefault("descripcion",titulo_documento(a["categoria"]))
                            widget(["archivos",j,"descripcion"],"¿Qué nombre descriptivo debe aparecer en la propuesta?")
                            widget(["archivos",j,"categoria"],"¿Qué tipo de documento es?",opciones=CATEGORIAS_ADJUNTOS)
                            if st.button("Retirar archivo",key="del_a_"+a["id"]):
                                b["archivos"].pop(j)
                                for k in list(st.session_state):
                                    if k.startswith("q_archivos_"): del st.session_state[k]
                                st.rerun()
                if seccion==12:
                    widget(["incluir_admin"],"Incluir identificación legal y datos bancarios","bool")
                    widget(["marcar_borrador"],"Marcar el PDF como borrador","bool")
                    widget(["incluir_revision"],"Incluir hoja adicional de revisión al final del PDF","bool")
                    lista=pendientes(b)
                    if lista:
                        st.info(f"Hay {sum(len(v) for _,v in lista)} observaciones de revisión o carga. Puedes generar la propuesta; los estados se muestran de forma explícita.")
                        for i,items in lista: st.caption(PASOS[i]+": "+"; ".join(items))
                    else: st.success("Los campos requeridos y la carga documental están completos. Los estados del checklist siguen siendo declaraciones del oferente para evaluación del comprador.")
                    st.markdown("**Esqueleto reutilizable para IA**")
                    md=esqueleto_markdown(b); plantilla=esqueleto_markdown(b,True)
                    a,c=st.columns(2)
                    with a: st.download_button("Descargar preguntas y respuestas (.md)",md.encode(),file_name="Preguntas_y_respuestas.md",mime="text/markdown")
                    with c: st.download_button("Descargar esqueleto vacío para IA (.md)",plantilla.encode(),file_name="Esqueleto_propuesta_IA.md",mime="text/markdown")
                    st.text_area("Texto para copiar y completar con IA",md,height=210,disabled=True)
                    if st.session_state.get("propuesta_firma") == firma_propuesta(b):
                        st.divider()
                        st.download_button(
                            "Descargar expediente completo (.zip)",
                            exportar_zip(b, st.session_state.propuesta_pdf),
                            file_name=f"Expediente_{slug(b['datos']['proceso'],80)}.zip",
                            mime="application/zip",
                        )
        st.caption("El formulario permanece en esta sesión. Descarga el expediente antes de cerrar la aplicación.")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-pdf",type=Path,help="Generar la propuesta precargada sin iniciar Streamlit (logo opcional)")
    args,_=parser.parse_known_args()
    if args.demo_pdf:
        args.demo_pdf.write_bytes(generar_pdf(nuevo()))
        print(f"PDF generado: {args.demo_pdf.resolve()}")
    else: main()
