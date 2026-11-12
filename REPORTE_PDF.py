# VERSION: 10.0 - La Pintana / precio comercial fijado / IVA exento informado
# CURSO: Programa de Capacitación y Adopción Organizacional de Inteligencia Artificial
# CÓDIGO: 2273-984-COT26 | MODALIDAD: Compra Ágil | 28 participantes | 20 horas cronológicas
# ORGANISMO: I. Municipalidad de La Pintana | Presupuesto: $5.040.000 IVA incluido
# PRECIO PROPUESTO: $4.390.000 CLP TOTAL, exento de IVA segun oferente; costo interno estimado $3.370.000
# FECHA: 12-11-2026 America/Santiago
# Origen: generador editorial OTEC Santa Mónica, ajustado a bases técnicas aportadas.
# AVISO: Las más de 2.500 personas capacitadas en IA NO están acreditadas en la documentación revisada.
# Los certificados de Marcelo respaldan relatorías, pero no el número de asistentes por actividad.
# Exención de IVA informada por el oferente. El precio es propuesto, no reemplaza la verificacion de requisitos excluyentes.
# El recinto será proporcionado en La Pintana según bases; no se ha contratado un salón concreto.
# Uso: python -m pip install -r requirements.txt
#      python -m streamlit run Generador_Propuesta_La_Pintana_2273-984-COT26_FINAL.py
# Prueba: python Generador_Propuesta_La_Pintana_2273-984-COT26_FINAL.py --demo-pdf Propuesta_La_Pintana_FINAL.pdf

# -*- coding: utf-8 -*-
#
# INSTRUCCIONES DE USO
# 1. Instalar dependencias: python -m pip install -r requirements.txt
# 2. Ejecutar: python -m streamlit run Generador_Propuesta_La_Pintana_2273-984-COT26_FINAL.py
# 3. Precio precargado definitivo para esta propuesta comercial: $4.390.000 exento de IVA.
#    El recinto lo aporta el oferente en La Pintana; fechas dentro de noviembre según bases.
# 4. Adjuntar CV, diplomas, constancias y respaldos institucionales en la sección de anexos.
# 5. Revisar la matriz de requisitos mínimos. No se acreditan 2.501 personas con las OC disponibles.
# 6. Usar «Generar PDF» y luego descargar el expediente ZIP. Incluye SOLO los archivos cargados.
# 7. Sin sesión persistente: descargar el expediente antes de cerrar Streamlit.
# 8. Demo sin Streamlit: python Generador_Propuesta_La_Pintana_2273-984-COT26_FINAL.py --demo-pdf Propuesta_La_Pintana_FINAL.pdf
# El logo del oferente es opcional; si no se encuentra se usa una portada tipográfica.
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
PDF_RENDER_VERSION = "v10.0-la-pintana-4390000-20261112"
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
CATEGORIAS_ADJUNTOS = ["Bases técnicas", "CV y respaldos relator", "CV relator", "Respaldo relator",
                        "Experiencia OTEC IA", "Certificado participantes", "Encuestas de satisfacción",
                        "Propuesta / otro", "Orden de compra"]
ADJUNTOS_DECLARADOS = []  # El PDF lista únicamente los documentos cargados realmente.

RELATOR_INICIAL = {
    'rol':'Relator principal', 'nombre':'Luis Marcelo Ortiz Contreras',
    'rut':'9.052.506-9',
    'titulo':'Profesor de Matemática y Licenciado en Educación, Universidad de Concepción (1987); Máster en Tecnologías para la Educación y el Conocimiento, UNED/Universidad de Concepción (estudios 2006-2008).',
    'experiencia': (
        'Profesor de Matemática con amplia experiencia docente y de formación en tecnologías para la educación. '
        'Su CV identifica actividades específicas de relatoría y formación en Inteligencia Artificial entre 2023 y 2026, '
        'incluyendo presentaciones en Tarapacá (octubre de 2023) y Atacama (diciembre de 2023), '
        'y talleres o capacitaciones durante 2024, 2025 y 2026. '
        'Constancias disponibles respaldan actividades vinculadas con MINEDUC / Programa Inglés Abre Puertas '
        '(dos talleres de IA en 2025), Servicio de Registro Civil e Identificación (generación de contenidos con IA) '
        'y establecimientos educacionales. El CV menciona IA generativa en planificación, evaluación y gestión administrativa. '
        'Como experiencia tecnológica, declara trabajo en British Council (2024-2025) y PNUD (2023) '
        'con administración de Moodle, reportes y seguimiento de datos. '
        'El período mínimo exigido de tres años en desarrollo, implementación o liderazgo de proyectos profesionales de '
        'IA o análisis de datos se encuentra pendiente de acreditación específica; la actividad docente por sí sola no lo sustituye.'),
    'disponibilidad':'Relator propuesto para la ejecución presencial del programa en La Pintana durante noviembre de 2026; calendario y disponibilidad sujetos a coordinación y confirmación con la contraparte.'
}


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
REQ_COMPRA = [
    'Programa presencial teórico-práctico de 20 horas cronológicas para 28 Apoyos Familiares Integrales',
    'Cobertura íntegra de los 10 módulos de las especificaciones técnicas',
    'Diagnóstico inicial antes de la primera clase para los 28 participantes',
    'Dos sesiones de mentoría durante el mes siguiente al cierre',
    'Recinto en La Pintana, computador, proyector, telón y coffee break a cargo del oferente',
    'Informe final con evaluación individual, carpeta fotográfica y certificados del 100% de profesionales',
    'Capacitación de IA para al menos 5 instituciones distintas en los últimos 3 años (9.1)',
    'Más de 2.500 personas realmente capacitadas en IA en los últimos 3 años (9.1)',
    'Al menos una capacitación en IA a institución pública o municipio en los últimos 3 años (9.1)',
    'Cotización electrónica y anexo económico exactamente coincidentes',
    'Plazo de ejecución expresamente informado y cotización por la totalidad del servicio',
]
REQ_RELATOR = [
    'Título universitario de profesor/a o pedagogo/a',
    'Experiencia docente mínima de 5 años posterior al título',
    'Formación certificada en ciencia de datos, análisis de datos, ML o IA',
    'Experiencia mínima de 3 años como relator/a de IA o IA Generativa',
    'Experiencia profesional mínima de 3 años en desarrollo, implementación o liderazgo de proyectos de IA o datos',
    'Enseñanza de IA Generativa aplicada a tareas administrativas',
    'Experiencia de IA con organismos públicos, municipios, programas sociales, educación o salud',
    'Certificación de competencias laborales en IA y/o participación en comunidad especializada (criterio de puntaje)',
    'Resultados de satisfacción en capacitaciones anteriores (criterio de puntaje)',
]
REQ_CERT = [
    'Evaluación diagnóstica de los 28 participantes antes de la primera clase',
    'Evaluación final individual de aplicación de IA en el trabajo de AFI',
    'Dos mentorías durante el mes posterior al programa',
    'Informe final con resultados de evaluación por participante',
    'Carpeta de registro fotográfico de la capacitación',
    'Certificación individual del 100% de los 28 profesionales, según exigencia contractual',
    'Protección y anonimización de datos personales y familiares durante todos los ejercicios',
]
MODULOS = [
    ('Bloque I: Fundamentos y uso responsable', 'Módulo 1. Fundamentos de Inteligencia Artificial',
     'Conceptos de IA, alcance y limitaciones, ejemplos en el acompañamiento familiar; diferencias entre IA generativa y automatización. Actividad: identificar tareas repetitivas del equipo.', 2, 'Presencial'),
    ('Bloque I: Fundamentos y uso responsable', 'Módulo 2. Uso avanzado de asistentes conversacionales multipropósito',
     'Ingeniería de prompts, contexto, verificación, iteración y revisión humana. Taller: borradores de correos, minutas y resúmenes con datos ficticios.', 2, 'Presencial'),
    ('Bloque I: Fundamentos y uso responsable', 'Módulo 3. Riesgos, ética y buenas prácticas',
     'Privacidad, datos personales y sensibles, sesgos, alucinaciones, consentimiento y validación humana. Prohibición de ingresar datos identificables de familias a herramientas no autorizadas.', 2, 'Presencial'),
    ('Bloque II: Herramientas aplicadas', 'Módulo 4. Herramientas de IA I',
     'Producción y revisión de documentos: fichas, comunicaciones, minutas, informes y síntesis de antecedentes con datos simulados.', 2, 'Presencial'),
    ('Bloque II: Herramientas aplicadas', 'Módulo 5. Herramientas de IA II',
     'Organización de información y calendarización: planificación de visitas, priorización y seguimiento de tareas con validaciones y herramientas autorizadas.', 2, 'Presencial'),
    ('Bloque II: Herramientas aplicadas', 'Módulo 6. Herramientas de IA III',
     'Reportabilidad, análisis básico de datos, clasificación de registros anonimizados y elaboración de apoyos visuales para la coordinación institucional.', 2, 'Presencial'),
    ('Bloque III: Productividad e implementación', 'Módulo 7. Machine Learning, Deep Learning e IA Generativa',
     'Explicación accesible de ML, DL e IA generativa aplicada a productividad y atención ciudadana. Ejercicios de detección de patrones y límites de inferencia.', 2, 'Presencial'),
    ('Bloque III: Productividad e implementación', 'Módulo 8. Identificación e implementación de casos de uso',
     'Priorización de casos por beneficio, factibilidad y riesgo. Diseño de un caso de uso aplicable a planificación de visitas, reportabilidad o redes de apoyo.', 2, 'Presencial'),
    ('Bloque III: Productividad e implementación', 'Módulo 9. Taller de institucionalización de asistentes de IA',
     'Prototipos de instrucciones, plantillas y protocolos de uso de asistentes institucionales, con control de acceso, supervisión humana y continuidad operacional.', 2, 'Presencial'),
    ('Bloque IV: Transferencia', 'Módulo 10. Actividad integradora final',
     'Caso práctico grupal con datos ficticios: planificación, documentación y seguimiento de intervención familiar; demostración, evaluación y plan de adopción responsable.', 2, 'Presencial'),
]


def hoy():
    try:
        return datetime.now(ZoneInfo("America/Santiago")).strftime("%d-%m-%Y")
    except Exception:
        return datetime.now().strftime("%d-%m-%Y")


DATOS_LICITACION = {'proceso': '2273-984-COT26',
 'modalidad': 'Compra Ágil',
 'titulo': 'Programa de Capacitación y Adopción Organizacional de Inteligencia Artificial para Apoyos '
           'Familiares Integrales',
 'comprador': 'I. MUNICIPALIDAD DE LA PINTANA',
 'rut_comprador': '69.253.800-5',
 'rubro': 'Capacitación presencial y adopción de IA generativa para equipos de intervención familiar y gestión '
          'municipal',
 'id_item': '',
 'numero_oc': '',
 'requisitos_oc': '',
 'publicacion': '',
 'cierre_1': '12-11-2026 17:20:00',
 'cierre_2': '',
 'plazo_ficha': 'Ejecución de 20 horas cronológicas en noviembre de 2026, más dos mentorías en el mes '
                'siguiente',
 'presupuesto': 5040000,
 'tipo_presupuesto': 'Presupuesto máximo disponible: $5.040.000, IVA incluido',
 'contacto_comprador': 'Contraparte técnica Programa Familias de la Municipalidad de La Pintana',
 'oferente': 'CENTRO DE CAPACITACION SANTA MONICA LIMITADA',
 'nombre_comercial': 'CENTRO DE CAPACITACION SANTA MONICA',
 'rut_oferente': '76.176.857-3',
 'domicilio_empresa': 'Isabel La Católica 4394, oficina 517, piso 5, Las Condes, Santiago, Región '
                      'Metropolitana',
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
 'quienes': 'Centro de Capacitación Santa Mónica Limitada es un organismo dedicado al fortalecimiento de '
            'competencias laborales y tecnológicas de organizaciones públicas y privadas. Su oferta combina '
            'prácticas aplicadas, seguimiento y evaluación. Cuenta con antecedentes de contratación de '
            'capacitación en IA para municipalidades y organismos públicos, respaldados por órdenes de compra '
            'y facturas que se detallarán en la matriz institucional. El número total de participantes '
            'capacitados en IA debe sustentarse con registros de ejecución y no se presume por el valor de las '
            'órdenes.',
 'vision': 'Acompañar a equipos profesionales no técnicos en una adopción útil, responsable y verificable de '
           'la inteligencia artificial, protegiendo la privacidad de las personas y mejorando la calidad del '
           'servicio público.',
 'que_ofrecemos': 'Programa presencial teórico-práctico de 20 horas cronológicas para 28 Apoyos Familiares '
                  'Integrales de La Pintana, distribuidas en diez módulos; diagnóstico inicial previo, dos '
                  'mentorías de seguimiento durante el mes posterior, lugar de ejecución en la comuna, '
                  'equipamiento audiovisual, coffee break, evaluación final, informe, registro fotográfico y '
                  'certificados individuales.',
 'objetivo_general': 'Fortalecer las capacidades del equipo del Programa Familias para utilizar de forma '
                     'práctica, segura y sostenida herramientas de Inteligencia Artificial que permitan '
                     'ordenar, calendarizar y visualizar el avance de visitas familiares, gestionar cargas de '
                     'trabajo, apoyar reportabilidad y mejorar la coordinación institucional, sin exponer '
                     'datos personales.',
 'objetivos_especificos': 'Explicar fundamentos de IA, ML, DL e IA generativa de forma accesible.\n'
                          'Emplear asistentes de IA para elaborar y revisar comunicaciones, documentos y '
                          'reportes.\n'
                          'Planificar y hacer seguimiento de visitas y actividades con herramientas '
                          'apropiadas.\n'
                          'Aplicar criterios de privacidad, ética, trazabilidad y validación humana.\n'
                          'Diseñar un caso de uso y un protocolo básico de adopción para el Programa '
                          'Familias.\n'
                          'Evaluar aprendizajes y acompañar la transferencia al puesto de trabajo mediante '
                          'mentorías.',
 'participantes': '28 Apoyos Familiares Integrales (AFI) del Programa Familias, con funciones de intervención '
                  'y acompañamiento a familias en situación de vulnerabilidad.',
 'cupos': 28,
 'prerrequisitos': 'Conocimientos básicos de computador y manejo de documentos; no se requiere formación '
                   'previa en programación ni inteligencia artificial.',
 'modalidad_curso': 'Presencial',
 'horas_exigidas': 20.0,
 'metodologia': 'Aprendizaje participativo de aplicación inmediata. Diagnóstico de competencias antes de la '
                'primera clase para los 28 participantes; explicación breve, demostración, trabajo por '
                'parejas, ejercicios con información ficticia o anonimizada, puesta en común y evaluación por '
                'caso práctico. Los participantes construirán plantillas, instrucciones (prompts) y rutinas de '
                'revisión humana para apoyar visitas y reportabilidad; nunca se cargarán datos identificables '
                'de familias en sistemas no autorizados. Se realizarán dos mentorías durante el mes siguiente '
                'al cierre de las 20 horas presenciales, incluidas en el valor global y no descontadas del '
                'total lectivo exigido.',
 'herramientas': 'Asistentes de IA generativa y herramientas de productividad autorizados por la contraparte. '
                 'Demostraciones de generación documental, síntesis, tabulación, planificación y reportes. Los '
                 'recursos específicos se seleccionarán según licencias y políticas de la Municipalidad; no se '
                 'exigirán cuentas personales ni se subirán antecedentes sensibles.',
 'region': 'Región Metropolitana',
 'comuna': 'La Pintana',
 'lugar': 'Recinto apto para capacitación presencial dentro de la comuna de La Pintana, proporcionado por OTEC '
          'Santa Mónica; dirección exacta por confirmar con la contraparte antes de contratar.',
 'quien_lugar': 'Proveedor',
 'periodo_ejecucion': 'Las 20 horas cronológicas se desarrollarán durante noviembre de 2026, en calendario '
                      'coordinado con la Municipalidad. Antes de la primera clase se aplicará diagnóstico; '
                      'durante diciembre de 2026 se realizarán dos mentorías de acompañamiento.',
 'fecha_ejecucion': 'Calendario ofrecido: cinco jornadas presenciales de 4 horas cronológicas cada una en noviembre de 2026. '
                    'Las fechas y el recinto provisto por la OTEC se coordinarán con la contraparte, respetando el '
                    'plazo de ejecución comprometido. Dos mentorías durante el mes siguiente al cierre.',
 'equipamiento': 'OTEC Santa Mónica proporcionará recinto, computador de apoyo del relator, proyector y telón '
                 'para presentaciones, además de conectividad adecuada a la actividad. Se coordinará acceso de '
                 'participantes a equipos y herramientas autorizadas.',
 'cafeteria': 'Coffee break a cargo del oferente: café, té, agua saborizada y productos tales como mini '
              'sándwiches y galletas, coordinando requerimientos alimentarios con la contraparte.',
 'materiales': 'Presentaciones, guías de prompts, fichas de casos de uso, rúbricas, plantillas de '
               'reportabilidad, ejercicios con datos ficticios, pautas de seguridad y documentos digitales de '
               'apoyo.',
 'perfil_docente': 'Relator principal: Luis Marcelo Ortiz Contreras, Profesor de Matemática y Licenciado en '
                   'Educación, Universidad de Concepción, con experiencia docente extensa y trayectoria '
                   'declarada de actividades de capacitación y relatorías en IA desde 2023. La acreditación '
                   'completa de tres años de proyectos profesionales de IA o datos requiere respaldo '
                   'documental específico; no se presenta como acreditada automáticamente.',
 'referencia_cv': 'Se acompaña CV de Luis Marcelo Ortiz, título de profesor y grado, diploma de máster, '
                  'constancias de relatorías de IA y formación especializada declarada en el CV. La '
                  'verificación del perfil se realiza con la matriz de cumplimiento incluida en la propuesta.',
 'observaciones': 'La experiencia personal del relator y la experiencia contractual de Santa Mónica se '
                  'presentan por separado. No se declara como acreditado el mínimo de más de 2.500 '
                  'participantes de IA: el expediente revisado acredita contrataciones y cupos previstos, pero '
                  'no dispone de nóminas o certificados de ejecución que permitan totalizar 2.501 personas '
                  'efectivamente capacitadas. La aceptación de la experiencia personal del relator como '
                  'experiencia del oferente corresponde exclusivamente a la evaluación del comprador. El '
                  'precio global propuesto $4.390.000, exento de IVA según información proporcionada por el oferente.',
 'evaluacion': 'Diagnóstico inicial previo para establecer línea base; actividades prácticas observadas en '
               'cada módulo; evaluación final individual mediante caso de acompañamiento familiar con datos '
               'simulados y pauta de logro que considere pertinencia, seguridad, calidad del producto y '
               'verificación humana.',
 'aprobacion': 'Se propone evaluación de adquisición de competencias y acciones de apoyo para facilitar que el '
               '100% de profesionales reciba certificación al cierre; la certificación se sujetará a criterios '
               'y evidencias de participación acordados con la contraparte, sin declarar aprobaciones '
               'anticipadas.',
 'entrega_certificados': 'Informe final con resultados individuales, registro de actividades, carpeta '
                         'fotográfica y certificados nominativos con curso, fecha y duración, conforme al 100% '
                         'de certificación requerido por la entidad; entrega a la contraparte al término de la '
                         'capacitación, complementada con acta de mentorías posteriores.',
 'destino_informe': 'contraparte técnica del Programa Familias de la Municipalidad de La Pintana',
 'cantidad': 1,
 'valor_unitario': 4390000,
 'despacho': 0,
 'impuesto': 'Exento / sin impuesto',
 'tasa': 0,
 'incluye_precio': 'Precio total y global propuesto: $4.390.000 exento de IVA. Comprende 20 horas cronológicas presenciales para 28 personas; incluye '
                   'diagnóstico inicial, diez módulos, relatoría de Marcelo Ortiz, salón en La Pintana, '
                   'equipamiento audiovisual, coffee break, materiales, dos mentorías el mes siguiente, '
                   'evaluaciones, informe final, registros fotográficos y 28 certificaciones. Cinco jornadas presenciales de cuatro horas y dos mentorías posteriores de noventa minutos cada una, adicionales a las veinte horas. No se cobrará suplemento por los entregables previstos.',
 'detalle': 'Capacitación presencial IA para 28 AFI, 20 horas cronológicas y 10 módulos. Diagnóstico, recinto '
            'y coffee break, 2 mentorías, evaluación, informe y certificación. Precio total $4.390.000 exento de IVA.',
 'adjuntos_esperados': 15,
 'adjuntos_solicitados': '01 Cotización económica coincidente con portal\n'
                         '02 Propuesta técnica y cronograma\n'
                         '03 CV de Marcelo Ortiz\n'
                         '04 Título, grado y máster\n'
                         '05 Formación certificada en IA\n'
                         '06 Constancias de relatorías\n'
                         '07 Matriz OTEC de cursos IA con respaldos\n'
                         '08 Declaración jurada de experiencia y participantes con evidencia\n'
                         '09 Encuestas de satisfacción y recomendaciones\n'
                         '10 Plan logístico, evaluación, mentorías y entregables',
 'documentacion_adjunta': 'Se incluye una carpeta de respaldos con CV, títulos, diploma de máster y constancias del relator; órdenes '
                          'de compra y facturas de cursos IA de Santa Mónica; matriz institucional con '
                          'institución, fecha, datos disponibles de participantes y respaldo; declaración '
                          'jurada simple y resultados de satisfacción únicamente si se aportan efectivamente. No se atribuye '
                          'acreditación a documentos aún no incorporados.',
 'fecha_propuesta': '12-11-2026'}

INTRODUCCIONES = {'proceso': 'Esta propuesta responde a la Compra Ágil {proceso}, convocada por {comprador}, para la adopción '
            'organizacional de IA de los equipos de Apoyo Familiar Integral.',
 'objetivos': 'El servicio apunta a ordenar el seguimiento de las visitas, la gestión documental y la '
              'coordinación de actividades del Programa Familias mediante IA responsable y prácticas '
              'verificables.',
 'programa': 'Se ofrecen 20 horas cronológicas presenciales en diez módulos de dos horas. El diagnóstico '
             'previo y dos mentorías del mes siguiente complementan la formación.',
 'metodologia': 'Talleres aplicados a tareas reales de AFI, usando únicamente datos ficticios o anonimizados, '
                'verificación humana y herramientas autorizadas.',
 'logistica': 'El oferente propone impartir las 20 horas presenciales en un recinto de la comuna de La Pintana '
              'durante noviembre de 2026, con equipamiento y coffee break a su cargo.',
 'relator': 'Se propone como relator principal a Luis Marcelo Ortiz Contreras, Profesor de Matemática de la '
            'Universidad de Concepción, con actividades de relatoría de IA declaradas desde 2023 y constancias '
            'que respaldan capacitaciones en organismos públicos. Su experiencia en proyectos de IA o datos y '
            'los antecedentes de experiencia institucional se someten a evaluación documental.',
 'requisitos': 'La matriz siguiente distingue compromisos de la oferta, respaldo documental del relator y '
               'requisitos mínimos de experiencia del oferente; los campos pendientes no se presentan como '
               'acreditados.',
 'certificacion': 'Se realizará diagnóstico, evaluación final, dos mentorías de transferencia y entrega de '
                  'informe, carpeta fotográfica y certificaciones a los 28 profesionales conforme a las bases.',
 'economica': 'El precio global incluye recinto, equipamiento, colaciones, 20 horas, diagnóstico, mentorías, '
              'evaluación, informes y certificados para 28 participantes.',
 'documentos': 'El siguiente listado corresponde únicamente a documentos efectivamente incorporados al expediente. '
               'Los documentos no presentes no se consideran adjuntos ni acreditados.',
 'identificacion': 'Los datos institucionales corresponden a Santa Mónica según antecedentes aportados.'}

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
            if k in {'oferente','nombre_comercial','rut_oferente','domicilio_empresa','contacto_oferta',
                     'cargo_contacto','telefono','correo','representante','rut_representante','cargo_representante'}:
                continue
            if tipo in {'entero','decimal'}:
                d[k] = 0.0 if tipo == 'decimal' else 0
            elif k not in {'modalidad','modalidad_curso','quien_lugar','impuesto'}:
                d[k] = ''
        d.update(cantidad=1,tasa=19,fecha_propuesta=hoy())
    rows=[{'id':uuid4().hex[:12],'jornada':j,'nombre':n,'contenido':c,'horas':float(h),'tipo':t}
          for j,n,c,h,t in MODULOS] if ejemplo_activo else []
    rel=copy.deepcopy(RELATOR_INICIAL)
    rel['id']=uuid4().hex[:12]
    rel['checklist']=items_check(REQ_RELATOR)
    soportes_rel=[
        ('Respaldado','Título profesional Universidad de Concepción; archivo de título y grado.'),
        ('Respaldado','CV y trayectoria docente universitaria desde 2004; verificar certificados de vínculo si se solicitan.'),
        ('Declarado','CV indica diplomado de IA 2023 y cursos de ChatGPT 2024; adjuntar certificado específico del programa.'),
        ('Declarado','CV refiere relatorías de IA desde agosto/octubre de 2023; constancias recibidas respaldan actividades posteriores.'),
        ('Por verificar','CV describe análisis de datos y reportabilidad en British Council/PNUD; no documenta por sí solo 3 años de proyectos profesionales específicos de IA o datos.'),
        ('Respaldado','CV y constancias de IA aplicada a gestión docente/administrativa; MINEDUC, Registro Civil y Academia Politécnica Militar.'),
        ('Respaldado','Constancias de MINEDUC/Programa Inglés Abre Puertas, Registro Civil y actividades públicas.'),
        ('Por verificar','No se acreditó una certificación de competencias laborales en IA ni membresía gremial o en red especializada con la documentación revisada.'),
        ('Por verificar','Solicitar informes o resultados cuantificados de encuestas de satisfacción en cursos anteriores.'),
    ]
    for row,(estado,respaldo) in zip(rel['checklist'],soportes_rel):
        row.update(estado=estado,respaldo=respaldo)
    compra=items_check(REQ_COMPRA)
    soportes_compra=[
        ('Comprometido','Programa propuesto: 20 horas cronológicas presenciales, 28 AFI y ejercicios aplicados.'),
        ('Comprometido','Diez módulos coincidentes con la secuencia de las especificaciones técnicas.'),
        ('Comprometido','Instrumento diagnóstico aplicado antes de la primera clase a los 28 participantes.'),
        ('Comprometido','Dos mentorías de acompañamiento el mes siguiente al cierre; adicionales a 20 horas.'),
        ('Comprometido','El proveedor se obliga a aportar recinto en la comuna, audiovisual y coffee break.'),
        ('Comprometido','Informe, evaluaciones, fotografías y certificación individual conforme a bases.'),
        ('Declarado','Se identificaron contrataciones de IA con varias entidades públicas y municipales. Incorporar matriz con OC/facturas, fechas, duración y asistentes.'),
        ('Por verificar','No constan registros de 2.501 asistentes a capacitación de IA; las OC contienen cupos y no listas de participantes efectivos.'),
        ('Respaldado','OC 2446-1884-AG25: Municipalidad de Coquimbo, capacitación de IA para Mujeres Jefas de Hogar (20 cupos previstos); complementar asistencia.'),
        ('Comprometido','Revisar que monto en formulario de Mercado Público y PDF adjunto sea exactamente el mismo.'),
        ('Comprometido','20 horas en noviembre 2026 y 2 mentorías en diciembre; servicio completo, precio global.'),
    ]
    for row,(estado,respaldo) in zip(compra,soportes_compra):
        row.update(estado=estado,respaldo=respaldo)
    cert=items_check(REQ_CERT)
    soportes_cert=[
        'Diagnóstico inicial individual antes del comienzo de los módulos.',
        'Evaluación integradora con caso de AFI, datos ficticios y rúbrica individual.',
        'Dos mentorías durante diciembre de 2026 para resolver dudas y apoyar adopción.',
        'Informe individual con resultados, aprendizaje y recomendaciones.',
        'Carpeta de fotografías de sesiones, resguardando consentimientos.',
        'Certificados nominativos para los 28 profesionales conforme a exigencias del comprador.',
        'Casos anonimizados, acceso autorizado y revisión humana permanente.',
    ]
    for row,respaldo in zip(cert,soportes_cert):
        row.update(estado='Comprometido',respaldo=respaldo)
    return {'version':6,'datos':d,'modulos':rows,'docentes':[rel],
            'compra':compra,'certificacion':cert,
            'logos':{'oferente':{'nombre':'','base64':''},'comprador':{'nombre':'','base64':''}},
            'archivos':[],'declarados':copy.deepcopy(ADJUNTOS_DECLARADOS),
            'marcar_borrador':False,'incluir_revision':False,'incluir_admin':False}


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
    if paso==10 and int(d["valor_unitario"])<=0:
        r.append("PRECIO PENDIENTE: no presentar al portal sin definir el valor total y hacerlo coincidir con el PDF.")
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
    if total is None or presupuesto<=0 or int(d["valor_unitario"])<=0: return None
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
    if int(d["valor_unitario"])<=0:
        b["marcar_borrador"] = True
    sty = estilos_pdf()
    margen_izq, margen_der = 61, 57
    ancho = A4[0] - margen_izq - margen_der
    total_curso = sum(horas(b).values())
    total_precio = montos(d)[2] if int(d["valor_unitario"]) > 0 else None

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
            ("Modalidad", d["modalidad_curso"]),
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
        ["Organismo comprador", d["comprador"] + ("\nRUT " + d["rut_comprador"] if d["rut_comprador"].strip() else "")],
        ["Modalidad y código", d["modalidad"] + "\n" + d["proceso"]],
        ["Categoría del servicio", d["rubro"]],
        ["Ejecución", d["periodo_ejecucion"]],
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

    cap("Lugar y condiciones de ejecución presencial", "logistica")
    story.extend(campo("Recinto y ubicación", d["lugar"]))
    responsable = {
        "Proveedor": "El proveedor suministrará el recinto presencial dentro de La Pintana y el equipamiento para el curso.",
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
    story.extend(campo("Relatoría principal", d["perfil_docente"]))
    story.extend(parrafos(
        "La propuesta contempla un relator principal: Luis Marcelo Ortiz Contreras. "
        "Su trayectoria de capacitaciones de IA está declarada desde 2023 y se acompaña evidencia "
        "disponible de relatorías. Los requisitos de experiencia profesional en proyectos de IA/datos "
        "y el total de personas capacitadas por el oferente se mantienen expresamente sujetos a verificación."))
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
    precio_confirmado = int(d["valor_unitario"]) > 0
    impuesto_txt = ("Exento / sin impuesto" if d["impuesto"] == "Exento / sin impuesto"
                    else f"{d['tasa']} %" if d["impuesto"] == "Con impuesto"
                    else "Por definir")
    precio = tabla(["Concepto", "Valor"], [
        ["Valor global del servicio", pesos(neto) if precio_confirmado else "Pendiente de revisar costos"],
        ["Tratamiento tributario", impuesto_txt],
        ["Impuesto calculado", pesos(iva) if iva is not None else "Por definir"],
        ["Total ofertado", pesos(total) if total is not None and precio_confirmado else "PENDIENTE DE DEFINIR"],
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




def cargar_anexos_distribuidos(b):
    """Carga al formulario las copias originales incluidas en Anexos/.

    Si se ejecuta solo el .py, se podrá cargar desde la interfaz; nunca
    simula adjuntos que no existen.
    """
    carpeta = BASE_DIR / "Anexos"
    archivos = sorted(p for p in carpeta.glob("*.pdf") if p.is_file()) if carpeta.exists() else []
    if not archivos:
        return 0
    b["datos"]["adjuntos_esperados"] = len(archivos)
    n=0
    for ruta in archivos:
        nombre = ruta.name
        categoria = ("CV y respaldos relator" if nombre.startswith(("03_", "04", "06_"))
                     else "Experiencia OTEC IA" if nombre.startswith("07_FEX")
                     else "Certificado participantes" if nombre.startswith("07_Matriz")
                     else "Propuesta / otro")
        if agregar_archivo(b, nombre, ruta.read_bytes(), categoria):
            b["archivos"][-1]["descripcion"] = nombre.removesuffix(".pdf").replace("_", " ")
            n+=1
    return n

def main():
    import streamlit as st
    st.set_page_config(page_title="Propuesta técnica | OTEC Santa Mónica",page_icon="📄",layout="centered")
    st.title("Propuesta técnica y económica")
    if "modelo_propuesta_pintana_v10" not in st.session_state:
        # Una versión anterior puede haber dejado widgets con valores de ejemplo.
        for clave in list(st.session_state):
            if clave.startswith("q_") or clave in {"propuesta_pdf","propuesta_firma"}:
                del st.session_state[clave]
        b_inicial=nuevo()
        cargar_anexos_distribuidos(b_inicial)
        st.session_state.modelo_propuesta_pintana_v10=b_inicial
    b=st.session_state.modelo_propuesta_pintana_v10
    # Aplicación dedicada a la compra de La Pintana, precargada con un único relator.
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

    st.warning("Requisito 9.1 pendiente: no se acreditan más de 2.500 personas capacitadas en IA. "
               "La experiencia de las 2.501 personas no está respaldada; esta propuesta comercial no supone admisibilidad. "
               "Se requiere evidencia verificable de requisitos 8.1 y 9.1.")
    st.caption("Precio comercial fijado: $4.390.000 (exento de IVA según oferente). "
               "La OTEC asume proveer el recinto en la comuna; el calendario se coordina con la Municipalidad.")
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
            if int(b["datos"]["valor_unitario"])<=0:
                b["marcar_borrador"] = True
            try:
                st.session_state.propuesta_pdf = generar_pdf(b)
                st.session_state.propuesta_firma = firma_actual
                st.success("PDF generado. Verifica requisitos mínimos antes de presentar la oferta.")
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
                    tot=horas(b); st.metric("Horas cronológicas del programa",f"{sum(tot.values()):g}")
                    for jornada in dict.fromkeys(m["jornada"] for m in b["modulos"]):
                        h=sum(m["horas"] for m in b["modulos"] if m["jornada"]==jornada)
                        st.caption(f"Total {jornada.lower()}: {h:g} horas cronológicas")
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
                    precio_listo=int(b["datos"]["valor_unitario"])>0
                    a,c,e=st.columns(3)
                    a.metric("Neto + despacho",pesos(neto) if precio_listo else "PENDIENTE")
                    c.metric("Impuesto", "Exento ($0)" if b["datos"]["impuesto"]=="Exento / sin impuesto" else (pesos(iva) if iva is not None else "Por definir"))
                    e.metric("Total ofertado",pesos(total) if total is not None and precio_listo else "PENDIENTE")
                    if not precio_listo:
                        st.warning("Aún no hay precio definitivo: el PDF se generará solo como BORRADOR. No usar $0 para cotizar en Mercado Público.")
                    st.caption("Precio global propuesto: $4.390.000 exento; 20 horas, recinto, 5 coffee breaks, 2 mentorías y entregables.")
                    with st.expander("Control de costos internos (no se incorpora al PDF)"):
                        st.caption("Presupuesto interno estimado, NO son cotizaciones de proveedores. Reemplazar al contratar.")
                        conceptos=[("relatoria", "Relatoría 20 horas"), ("recinto", "Arriendo de recinto y servicios"),
                                   ("cafe", "Coffee break para 28 personas"), ("equipos", "Proyector, computador, telón y conectividad"),
                                   ("traslados", "Traslados y logística"), ("materiales", "Materiales, evaluaciones y certificados"),
                                   ("mentorias", "Dos mentorías posteriores"), ("administracion", "Coordinación e informes"),
                                   ("contingencia", "Contingencia y otros costos")]
                        costos_estimados={"relatoria":1250000,"recinto":600000,"cafe":580000,"equipos":90000,
                                          "traslados":100000,"materiales":80000,"mentorias":180000,
                                          "administracion":260000,"contingencia":230000}
                        costos=[]
                        for clave,rotulo in conceptos:
                            costos.append(st.number_input(rotulo, min_value=0, max_value=10000000, value=costos_estimados[clave],
                                                         step=10000, key="costo_pintana_"+clave))
                        costo_total=sum(costos)
                        margen=st.number_input("Margen deseado sobre precio final (%)",min_value=0.0,max_value=70.0,
                                                value=23.0,step=1.0,key="margen_pintana")
                        sugerido=round(costo_total/(1-margen/100)) if costo_total and margen<100 else 0
                        st.metric("Costo interno total",pesos(costo_total))
                        st.metric("Precio orientativo exento de IVA",pesos(sugerido) if sugerido else "Pendiente de ingresar costos")
                        st.caption("Esta cifra es solo una referencia comercial. Para ofertar, copia el precio final en 'Valor unitario' del servicio y confirma que no exceda el presupuesto.")
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
                    if int(b["datos"]["valor_unitario"])<=0:
                        b["marcar_borrador"]=True
                        st.warning("Precio pendiente: la propuesta debe permanecer como borrador hasta definir el valor ofertado.")
                    else:
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
        b=nuevo()
        cargar_anexos_distribuidos(b)
        args.demo_pdf.write_bytes(generar_pdf(b))
        print(f"PDF generado: {args.demo_pdf.resolve()}")
    else: main()
