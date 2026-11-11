#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# REPORTE_PDF.py - PROPUESTA OTEC SANTA MONICA - VERSION 4
#
# PROCESO PRECARGADO:
# Compra Agil 1057545-246-COT26 / Servicio de Salud Los Rios, RUT 61.607.500-4.
# Curso de Aplicacion de IA y Analisis de Datos para la Gestion de Personas.
# 20 participantes; 20 horas pedagogicas: 16 presenciales y 4 autonomas.
# Valdivia; segunda quincena de noviembre de 2026. Dias y recinto se coordinan
# despues de adjudicar. Oferta acordada: $2.300.000 CLP, EXENTA DE IVA.
#
# INSTALACION Y USO:
# 1. Python 3.10 o superior.
# 2. Instalar: python -m pip install -r requirements.txt
#    Dependencias: streamlit, reportlab, svglib, pillow, defusedxml.
# 3. Guardar OTEC_Santa_Monica_Opcion_1.svg junto a este archivo en GitHub.
#    Se admiten SVG vectoriales y SVG con PNG/JPEG incrustados en base64.
# 4. Ejecutar: python -m streamlit run REPORTE_PDF.py
# 5. Revisar las preguntas, los modulos y los checklists; cargar los adjuntos.
# 6. Pulsar Generar reporte PDF y luego Descargar propuesta PDF.
#    El ZIP conserva el PDF y los originales cargados bajo el nombre/codigo.
#
# COMO ADAPTAR A OTRA LICITACION CON O SIN AYUDA DE IA:
# A. Reemplazar DATOS_LICITACION con los antecedentes del nuevo proceso.
# B. Revisar MODULOS y sus horas; deben coincidir con las nuevas bases.
# C. Adaptar REQ_COMPRA, REQ_RELATOR, REQ_CERT y sus estados iniciales en nuevo().
# D. Editar RELATOR_INICIAL y ADJUNTOS_DECLARADOS; no trasladar evidencia de otro
#    proceso como si acreditara automaticamente requisitos nuevos.
# E. PREGUNTAS define los campos del formulario. generar_pdf() define la
#    estructura y el diseno; CATEGORIAS_ADJUNTOS define las cargas permitidas.
# F. Descargar el esqueleto Markdown vacio o las preguntas y respuestas para
#    completarlos con IA. Revisar la informacion antes de copiarla al codigo.
# G. Este proceso omite vigencia, equivalencia de horas en minutos, horarios
#    exactos y logo del comprador. No reincorporarlos salvo que otra base los
#    requiera. Las herramientas se describen por funcion, sin marcas.
# H. Mantener separados los domicilios y telefonos de empresa/representante.
#    El correo de la representante no se solicita ni se imprime.
#
# ALCANCE DEL DOCUMENTO:
# - Genera la propuesta detallada, no una orden de compra ni una adjudicacion.
# - La oferta contiene el precio final, no costos internos ni margen comercial.
# - La experiencia del relator se declara segun el CV, sin afirmar cinco anos.
# - Computadores de participantes: aportados por ellos o por el comprador.
# - Los adjuntos declarados se distinguen de los archivos realmente cargados.
# - El ANEXO N.1 oficial se carga completado y firmado; este programa no altera
#   ni reproduce su formato original y no genera firmas de terceros.
# - No consulta Mercado Publico ni evalua automaticamente la admisibilidad.
# - Formulario completo, sin bloqueos y sin guardado de progreso. Se trabaja
#   en la sesion abierta; al recargar el navegador se reinician las respuestas.
#
# PRUEBA LOCAL SIN INTERFAZ:
# python REPORTE_PDF.py --demo-pdf propuesta.pdf
# Se necesita el logo local o cargarlo previamente desde la interfaz.
# ============================================================================
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
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    CondPageBreak,
)

BASE_DIR = Path(__file__).resolve().parent
LOGO_NAME = "OTEC_Santa_Monica_Opcion_1.svg"
PDF_RENDER_VERSION = "v4-propuesta-los-rios-2300000-exenta"
NAVY, GOLD = colors.HexColor("#153445"), colors.HexColor("#B78D45")
INK, MUTED = colors.HexColor("#243F4D"), colors.HexColor("#5B707D")
PALE, LINE = colors.HexColor("#F0F4F5"), colors.HexColor("#DBE3E7")
MAX_LOGO = 5 * 1024 * 1024
MAX_FILE = 20 * 1024 * 1024
MAX_ZIP = 200 * 1024 * 1024
FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("OTEC", str(FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("OTEC-Bold", str(FONT_DIR / "VeraBd.ttf")))
pdfmetrics.registerFontFamily("OTEC", normal="OTEC", bold="OTEC-Bold")

PASOS = ["Proceso y comprador", "Identificación del oferente", "Quiénes somos y visión",
         "Objetivos", "Participantes", "Contenidos y horas", "Lugar y ejecución",
         "Relator y respaldos", "Requisitos de compra", "Certificación",
         "Oferta económica", "Logo y documentación adjunta", "Revisión y PDF"]
ESTADOS = ["Por verificar", "Comprometido", "Declarado", "Respaldado", "A evaluación del comprador", "Cumple", "No cumple", "No aplica"]
CATEGORIAS_ADJUNTOS = ["Anexo Nº 1", "Bases técnicas", "CV y respaldos relator", "CV relator", "Respaldo relator", "Propuesta / otro"]
ADJUNTOS_DECLARADOS = [
    {"nombre":"ANEXO Nº 1 - IDENTIFICACION DEL OFERENTE", "categoria":"Anexo Nº 1"},
    {"nombre":"CV Daniel Vargas H Compilado IA(4).pdf", "categoria":"CV y respaldos relator"},
]
RELATOR_INICIAL = {
    "nombre":"Daniel Cristóbal Vargas Herrera", "rut":"20.522.550-1",
    "titulo":"Ingeniero Civil Industrial (título declarado en el CV)",
    "experiencia":"Experiencia declarada relacionada con IA y análisis de datos desde junio de 2022: aproximadamente 4 años y 5 meses a noviembre de 2026. Relatoría en IA generativa desde febrero de 2024: aproximadamente 2 años y 9 meses. Se informa la trayectoria efectiva para evaluación del organismo comprador.",
    "disponibilidad":"Confirmada para las dos jornadas presenciales en Valdivia, en fechas a coordinar después de la adjudicación.",
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
 (0,"publicacion","¿Cuándo se publicó el proceso? Fecha y hora.","texto",False),
 (0,"cierre_1","¿Cuándo cierra el primer llamado? Fecha y hora.","texto",True),
 (0,"cierre_2","¿Cuándo cierra el segundo llamado, si corresponde?","texto",False),
 (0,"plazo_ficha","¿Qué plazo de entrega indica la ficha?","texto",False),
 (0,"alerta_plazo","¿Hay plazos contradictorios o aspectos que aclarar?","area",False),
 (0,"presupuesto","¿Cuál es el presupuesto estimado en CLP?","entero",True),
 (0,"tipo_presupuesto","¿Qué tipo de presupuesto indica la ficha?","texto",False),
 (0,"contacto_comprador","¿Quién coordina por parte del comprador?","texto",False),
 (1,"oferente","¿Cuál es la razón social del oferente?","texto",True),
 (1,"nombre_comercial","¿Cuál es el nombre comercial?","texto",True),
 (1,"rut_oferente","¿Cuál es el RUT de la empresa?","texto",True),
 (1,"domicilio_empresa","¿Cuál es el domicilio de la empresa?","area",True),
 (1,"contacto_oferta","¿Quién es el contacto de la licitación por parte del oferente?","texto",False),
 (1,"telefono","¿Cuál es el teléfono del contacto de la licitación?","texto",True),
 (1,"correo","¿Cuál es el correo del contacto de la licitación?","texto",True),
 (1,"representante","¿Quién es la representante legal?","texto",True),
 (1,"rut_representante","¿Cuál es el RUT de la representante?","texto",True),
 (1,"cargo_representante","¿Cuál es su cargo?","texto",False),
 (1,"domicilio_representante","¿Cuál es el domicilio de la representante?","texto",False),
 (1,"telefono_representante","¿Cuál es el teléfono de la representante legal?","texto",False),
 (1,"personeria","¿Qué notaría, fecha y repertorio identifica la personería?","area",False),
 (1,"banco","¿Cuál es el banco de la empresa?","texto",False),
 (1,"tipo_cuenta","¿Cuál es el tipo de cuenta?","texto",False),
 (1,"cuenta","¿Cuál es el número de cuenta?","texto",False),
 (1,"correo_pagos","¿Cuál es el correo para pagos?","texto",False),
 (1,"codigo_sence","¿Qué código SENCE se ha informado?","texto",False),
 (2,"quienes","¿Quiénes somos y cuál es nuestra propuesta de valor?","area",True),
 (2,"vision","¿Cuál es nuestra visión institucional?","area",True),
 (2,"que_ofrecemos","¿Qué servicio integral ofrecemos para este proceso?","area",True),
 (3,"objetivo_general","¿Qué resultado busca lograr la actividad? Objetivo general.","area",True),
 (3,"objetivos_especificos","¿Qué resultados específicos se esperan? Uno por línea.","area",True),
 (4,"participantes","¿A qué universo de participantes está dirigida?","area",True),
 (4,"cupos","¿Cuántos cupos o participantes contempla?","entero",True),
 (4,"prerrequisitos","¿Qué conocimientos previos necesitan?","area",False),
 (4,"modalidad_curso","¿Cómo se desarrollará la actividad?","modalidad_curso",True),
 (5,"horas_exigidas","¿Cuántas horas pedagógicas exigen las bases?","decimal",True),
 (5,"metodologia","¿Cómo enseñaremos y acompañaremos el aprendizaje?","area",True),
 (5,"herramientas","¿Qué funciones deben cumplir las herramientas, sin comprometer marcas?","area",True),
 (6,"region","¿En qué región se ejecuta?","texto",True),
 (6,"comuna","¿En qué comuna o ciudad se ejecuta?","texto",True),
 (6,"lugar","¿Cuál es el recinto o dirección de ejecución?","texto",True),
 (6,"quien_lugar","¿Quién dispone el lugar?","responsable",True),
 (6,"periodo_ejecucion","¿Qué período de ejecución señalan las bases?","texto",True),
 (6,"fecha_ejecucion","¿Cómo se coordinarán las fechas de ejecución?","area",False),
 (6,"equipamiento","¿Qué equipamiento y conectividad se requiere y quién lo aporta?","area",True),
 (6,"cafeteria","¿Qué servicio de cafetería se contempla?","area",False),
 (6,"materiales","¿Qué materiales se entregarán?","area",True),
 (7,"perfil_docente","¿Qué perfil y experiencia exige la licitación al docente?","area",True),
 (7,"referencia_cv","¿Dónde se presenta el CV y sus respaldos?","area",True),
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
REQ_COMPRA = ["Programa del curso con módulos o temario", "Currículum del o los docentes",
              "Material para ejecutar el curso", "Experiencia docente de al menos 5 años en la temática",
              "Lugar y equipamiento necesario", "Servicio de cafetería para participantes",
              "Certificación de los participantes"]
REQ_RELATOR = ["Título en Informática, Control de Gestión o carrera afín",
               "Experiencia comprobable de al menos 5 años en la temática",
               "Aplicación práctica de IA generativa y formulación de prompts",
               "Análisis y visualización de datos; planillas, indicadores y reportes",
               "Optimización de procesos administrativos",
               "Protección de datos y uso responsable de IA"]
REQ_CERT = ["Certificado individual para cada participante", "Fecha de inicio y término en el certificado",
            "Nota obtenida en el certificado", "Cantidad de horas en el certificado",
            "Informe final a la Unidad de Capacitación", "Nombre completo y RUT en el informe",
            "Nota final en escala de 1 a 7", "Fechas y horas pedagógicas en el informe"]
MODULOS = [
 ("Día 1", "Introducción a la IA", "Conceptos, IA generativa, posibilidades, limitaciones y aplicaciones laborales.", 1.5, "Presencial"),
 ("Día 1", "Uso práctico de IA generativa", "Prompts, redacción y revisión, síntesis, organización de información y elaboración de informes.", 3, "Presencial"),
 ("Día 1", "IA en gestión de personas", "Casos de uso en las distintas áreas de la subdirección.", 2, "Presencial"),
 ("Día 1", "Uso responsable y seguro", "Protección de datos, confidencialidad, anonimización, sesgos, errores y validación humana.", 1.5, "Presencial"),
 ("Día 2", "Fundamentos de análisis de datos", "Calidad de bases, filtros, ordenamiento, fórmulas, tablas dinámicas e indicadores.", 3, "Presencial"),
 ("Día 2", "Visualización y comunicación", "Gráficos, indicadores, patrones, tendencias y reportes básicos.", 2, "Presencial"),
 ("Día 2", "Integración de IA y datos", "Interpretación de información, conclusiones e informes con casos prácticos de gestión de personas.", 3, "Presencial"),
 ("Estudio autónomo", "Revisión de IA generativa", "Conceptos, aplicaciones, instrucciones y uso responsable de IA.", 1, "Autónomo"),
 ("Estudio autónomo", "Aplicación a gestión de personas", "Ejercicios de IA para tareas habituales de gestión de personas.", 1, "Autónomo"),
 ("Estudio autónomo", "Revisión de análisis de datos", "Material práctico de organización, análisis y visualización mediante planillas de cálculo.", 1, "Autónomo"),
 ("Estudio autónomo", "Ejercicio integrador", "Caso simulado de gestión de personas que vincula IA y análisis de datos.", 1, "Autónomo"),
]


def hoy():
    try:
        return datetime.now(ZoneInfo("America/Santiago")).strftime("%d-%m-%Y")
    except Exception:
        return datetime.now().strftime("%d-%m-%Y")


DATOS_LICITACION = {'proceso': '1057545-246-COT26',
 'modalidad': 'Compra Ágil',
 'titulo': 'Curso de Aplicación de Inteligencia Artificial y Análisis de Datos para la Gestión de Personas',
 'comprador': 'SERVICIO DE SALUD LOS RÍOS',
 'rut_comprador': '61.607.500-4',
 'rubro': 'Formación, capacitación y entrenamiento de personal',
 'id_item': '42161387',
 'publicacion': '09-11-2026 08:41:58',
 'cierre_1': '11-11-2026 09:01:00',
 'cierre_2': '13-11-2026 09:20:01',
 'plazo_ficha': '1 día',
 'alerta_plazo': 'Aclarar a qué corresponde el plazo de entrega de 1 día de la ficha: las bases técnicas '
                 'contemplan 2 jornadas presenciales y 4 horas de estudio autónomo.',
 'presupuesto': 2400000,
 'tipo_presupuesto': 'Disponible',
 'contacto_comprador': 'POR CONFIRMAR - Unidad de Capacitación',
 'oferente': 'CENTRO DE CAPACITACION SANTA MONICA LIMITADA',
 'nombre_comercial': 'OTEC Santa Mónica',
 'rut_oferente': '76.176.857-3',
 'domicilio_empresa': 'Isabel La Católica 4394, oficina 517, piso 5, bloque B, Las Condes, Santiago de '
                      'Chile, Región Metropolitana',
 'contacto_oferta': 'ebrun',
 'telefono': '+56 9 6359 6523',
 'correo': 'ebrun@otecsantamonica.com',
 'representante': 'María Carmen Urrutia Peña',
 'rut_representante': '11.518.133-5',
 'cargo_representante': 'Representante legal',
 'domicilio_representante': 'La Concepción 793, Quillota, Región de Valparaíso',
 'telefono_representante': '+56 9 5807 5021',
 'personeria': 'Antecedente por confirmar con escritura y vigencia: notaria Lidia María Chahuán Issa, La '
               'Calera; escritura de 10-03-2026, repertorio 625-2026.',
 'banco': 'BancoEstado',
 'tipo_cuenta': 'Chequera electrónica',
 'cuenta': '29170792066',
 'correo_pagos': 'ebrun@otecsantamonica.com',
 'codigo_sence': 'C8828904 (dato informado; verificar respaldo)',
 'quienes': 'Centro de Capacitación Santa Mónica Ltda., OTEC Santa Mónica, orienta su actividad al '
            'desarrollo de competencias laborales y técnicas mediante programas de capacitación adaptados a '
            'las necesidades de cada organización. Nuestra propuesta combina contenidos pertinentes, '
            'ejercicios prácticos y evaluación del aprendizaje, buscando que las personas puedan aplicar lo '
            'aprendido en sus funciones y elaborar productos útiles para su trabajo.',
 'vision': 'Ser una OTEC reconocida por ofrecer capacitación pertinente y práctica, que contribuya al '
           'desarrollo de las personas y a la mejora del trabajo en las organizaciones. Aspiramos a acercar '
           'el conocimiento y las nuevas herramientas a participantes con distintos niveles de experiencia, '
           'promoviendo el aprendizaje continuo, el pensamiento crítico y la aplicación responsable de lo '
           'aprendido.',
 'objetivo_general': 'Desarrollar conocimientos y habilidades prácticas para utilizar herramientas de '
                     'Inteligencia Artificial y análisis de datos en apoyo a los procesos de gestión, '
                     'procesamiento de información y elaboración de productos de trabajo de la Subdirección '
                     'de Gestión y Desarrollo de las Personas, promoviendo un uso responsable, crítico y '
                     'seguro.',
 'objetivos_especificos': 'Comprender conceptos, posibilidades, limitaciones y aplicaciones de IA en gestión '
                          'de personas.\n'
                          'Aplicar IA generativa a redacción, síntesis, organización y sistematización de '
                          'información.\n'
                          'Formular instrucciones, evaluar resultados y utilizarlos de manera crítica.\n'
                          'Organizar, explorar e interpretar información con herramientas habituales de '
                          'análisis de datos.\n'
                          'Aplicar análisis y visualización para elaborar indicadores, reportes y productos '
                          'de gestión.\n'
                          'Reconocer precauciones de protección de datos, confidencialidad y validación '
                          'humana.',
 'participantes': 'Funcionarios y funcionarias de la Subdirección de Gestión y Desarrollo de las Personas: '
                  'Departamento de Gestión de las Personas; Departamento de Formación, Capacitación y '
                  'Educación Continua; y Departamento de Desarrollo Organizacional, Calidad de Vida y Salud '
                  'Ocupacional.',
 'cupos': 20,
 'prerrequisitos': 'No se requieren conocimientos previos avanzados en IA, programación o análisis de datos. '
                   'Se contemplan distintos niveles de familiaridad con herramientas digitales.',
 'modalidad_curso': 'Presencial con estudio autónomo',
 'horas_exigidas': 20.0,
 'metodologia': 'El curso se desarrollará mediante una progresión de lo general a lo específico, '
                'considerando los distintos niveles de experiencia de los participantes. Se iniciará con la '
                'comprensión de los conceptos, posibilidades y limitaciones de la IA, avanzando hacia '
                'ejercicios guiados y aplicaciones concretas en gestión de personas. Se combinarán '
                'demostraciones, práctica acompañada, análisis de casos y un ejercicio integrador con '
                'información simulada. La protección de datos, la confidencialidad, la evaluación crítica y '
                'la validación humana se trabajarán transversalmente.',
 'region': 'Región de Los Ríos',
 'comuna': 'Valdivia',
 'lugar': 'OTEC Santa Mónica gestionará el arriendo de un recinto en la ciudad de Valdivia, adecuado para la '
          'capacitación presencial de 20 participantes. La selección y confirmación del lugar se realizará '
          'después de la adjudicación, en coordinación con el organismo comprador, asegurando condiciones '
          'apropiadas de capacidad, comodidad y funcionamiento.',
 'quien_lugar': 'Proveedor',
 'periodo_ejecucion': 'Segunda quincena de noviembre de 2026; 2 jornadas presenciales.',
 'fecha_ejecucion': 'Las fechas de las dos jornadas se coordinarán con el organismo comprador una vez '
                    'adjudicado el servicio, dentro de la segunda quincena de noviembre de 2026.',
 'equipamiento': 'La OTEC gestionará un espacio adecuado y su equipamiento de sala para desarrollar las '
                 'actividades de capacitación. Cada participante deberá disponer de un computador, propio o '
                 'proporcionado por el organismo comprador. La provisión de computadores para participantes '
                 'no está incluida en el servicio de la OTEC; esta distribución de responsabilidades se '
                 'presenta expresamente para evaluación del comprador.',
 'cafeteria': 'Servicio para 20 participantes durante las dos jornadas presenciales, con dos pausas por '
              'jornada, coordinadas con la programación de la actividad. Cada servicio incluirá café, té o '
              'infusiones, agua o jugo, un mini sándwich y una porción de fruta o bocado dulce por '
              'participante. Comprende utensilios, montaje, atención, reposición de bebidas y retiro. Las '
              'necesidades alimentarias especiales deberán informarse previamente para coordinar las '
              'alternativas correspondientes.',
 'materiales': 'Cada participante recibirá acceso a un kit digital: manual y presentaciones en PDF; guía de '
               'instrucciones para IA; cuaderno de ejercicios; bases de datos simuladas; planillas de '
               'análisis; plantillas de gráficos e informes; y ficha de uso responsable de IA. Se entregará '
               'una guía breve impresa para las actividades presenciales. El estudio autónomo contará con '
               'guía, archivos de trabajo, caso integrador y criterios de evaluación, alineados con sus '
               'cuatro horas pedagógicas. Los ejercicios utilizarán información ficticia.',
 'perfil_docente': 'Titulado en Informática, Control de Gestión o carrera afín; experiencia comprobable de '
                   'al menos 5 años en IA generativa, análisis y visualización de datos y optimización de '
                   'procesos administrativos. Dominio de prompts, planillas, indicadores, reportes, '
                   'protección de datos y uso responsable de IA.',
 'referencia_cv': 'Se adjunta el currículum de Daniel Cristóbal Vargas Herrera junto con sus antecedentes de '
                  'competencias y certificaciones en la documentación que acompaña la propuesta. El '
                  'inventario distingue esta declaración de los archivos efectivamente incorporados a la '
                  'sesión y al ZIP.',
 'evaluacion': 'Se aplicará un diagnóstico inicial sin nota, ejercicios guiados con retroalimentación '
               'durante el curso y una evaluación final mediante un caso integrador individual. El '
               'participante trabajará con una base simulada, elaborará un indicador o gráfico y preparará '
               'un informe breve apoyado por IA, revisando exactitud y uso responsable de la información. La '
               'evaluación final se expresará en escala de 1 a 7.',
 'aprobacion': 'Se propone una nota mínima de aprobación de 4,0 y una asistencia mínima del 75 %. Estos '
               'criterios son parte de la propuesta de la OTEC y no se presentan como umbrales fijados en '
               'las bases. El certificado y el informe registrarán la calificación y el resultado de cada '
               'participante.',
 'entrega_certificados': 'Entrega digital de certificados individuales e informe final en PDF, más una '
                         'planilla de resultados en formato editable, dentro de cinco días hábiles '
                         'posteriores a la finalización del curso. Los certificados incluirán nombre y RUT, '
                         'curso, fechas de inicio y término, nota obtenida, cantidad de horas pedagógicas e '
                         'identificación de la OTEC. Se contemplan como firmantes la representante legal y '
                         'el relator, mediante las firmas que efectivamente correspondan al emitirlos.',
 'destino_informe': 'Unidad de Capacitación de la Dirección del Servicio de Salud Los Ríos',
 'cantidad': 1,
 'valor_unitario': 2300000,
 'despacho': 0,
 'impuesto': 'Exento / sin impuesto',
 'tasa': 19,
 'incluye_precio': 'Precio global de $2.300.000, exento de IVA, para los 20 participantes. Comprende '
                   'relatoría, preparación y materiales, recinto y equipamiento de sala, cafetería, '
                   'evaluación, certificación e informe final, conforme a las condiciones descritas. Los '
                   'computadores de los participantes serán aportados por ellos o por el organismo '
                   'comprador.',
 'detalle': 'Curso de IA y análisis de datos para 20 participantes: 20 horas pedagógicas (16 presenciales y '
            '4 autónomas). Incluye relatoría, materiales, recinto, cafetería, evaluación, certificados e '
            'informe final. Valor global exento: $2.300.000.',
 'adjuntos_esperados': 2,
 'adjuntos_solicitados': 'ANEXO Nº 1_ COMPRAS AGILES.docx\n'
                         'BASES TECNICAS CURSO APLICACION IA Y ANALISIS DE DATOS.pdf',
 'fecha_propuesta': '',
 'que_ofrecemos': 'La coordinación y ejecución integral del Curso de Aplicación de Inteligencia Artificial y '
                  'Análisis de Datos para la Gestión de Personas, dirigido a 20 funcionarios y funcionarias '
                  'del Servicio de Salud Los Ríos. El servicio comprende 20 horas pedagógicas: 16 '
                  'presenciales en dos jornadas en Valdivia y 4 de estudio autónomo. Incluye programa, '
                  'relatoría, materiales, recinto, equipamiento de sala, cafetería, evaluación, '
                  'certificación e informe final, conforme al alcance de esta propuesta.',
 'herramientas': 'Se utilizarán herramientas de IA generativa, planillas de cálculo y recursos de '
                 'visualización pertinentes a los objetivos y contenidos solicitados, seleccionados según su '
                 'accesibilidad, disponibilidad y compatibilidad con las condiciones institucionales. Su '
                 'aplicación avanzará desde instrucciones, redacción y síntesis hasta organización de datos, '
                 'filtros, fórmulas básicas, tablas dinámicas, indicadores, gráficos y elaboración de '
                 'informes. La propuesta no compromete marcas específicas.',
 'documentacion_adjunta': 'Se adjunta el Anexo Nº 1: Identificación del Oferente, junto con el currículum y '
                          'los antecedentes de competencias y certificaciones del relator. La propuesta '
                          'incorpora un checklist de los requisitos de las bases, con el compromiso de '
                          'ejecución, los antecedentes disponibles y las observaciones correspondientes. El '
                          'Anexo Nº 1 debe conservar su texto y formato oficial y presentarse completado y '
                          'firmado.'}


def datos_licitacion():
    d=copy.deepcopy(DATOS_LICITACION)
    d["fecha_propuesta"]=d["fecha_propuesta"] or hoy()
    return d



def items_check(textos):
    return [{"id": uuid4().hex[:12], "requisito": s, "estado": "Por verificar", "respaldo": ""} for s in textos]


def nuevo(ejemplo_activo=True):
    d=datos_licitacion()
    if not ejemplo_activo:
        for seccion,k,_,tipo,_ in PREGUNTAS:
            if seccion==1: continue
            if tipo in {"entero","decimal"}: d[k]=0.0 if tipo=="decimal" else 0
            elif k not in {"modalidad","modalidad_curso","quien_lugar","impuesto"}: d[k]=""
        d.update(cantidad=1,tasa=19,fecha_propuesta=hoy())
    modulos=[{"id":uuid4().hex[:12],"jornada":a,"nombre":n,"contenido":c,"horas":float(h),"tipo":t}
             for a,n,c,h,t in MODULOS] if ejemplo_activo else []
    rel=copy.deepcopy(RELATOR_INICIAL)
    rel.update(id=uuid4().hex[:12],checklist=items_check(REQ_RELATOR))
    for row in rel["checklist"]:
        req=row["requisito"]
        if "5 años" in req:
            row.update(estado="A evaluación del comprador",respaldo=rel["experiencia"])
        elif "Título" in req:
            row.update(estado="Declarado",respaldo="Ingeniero Civil Industrial, según CV. Afinidad del perfil a evaluar por el comprador.")
        elif "Análisis" in req:
            row.update(estado="Declarado",respaldo="CV, diplomado en Data Science e IA y antecedentes en herramientas de productividad; el comprador evalúa su suficiencia.")
        else:
            row.update(estado="Respaldado",respaldo="Antecedentes de relatoría, competencias y certificaciones incluidos en el compilado del CV.")
    compra=items_check(REQ_COMPRA)
    for row in compra:
        if "5 años" in row["requisito"]:
            row.update(estado="A evaluación del comprador",respaldo=rel["experiencia"])
        elif "Lugar" in row["requisito"]:
            row.update(estado="Comprometido",respaldo="Recinto arrendado por la OTEC tras adjudicar; computadores aportados por participantes o comprador, según condiciones de esta propuesta.")
        elif "Currículum" in row["requisito"]:
            row.update(estado="Declarado",respaldo="CV y competencias/certificaciones declarados como documentación adjunta.")
        else:
            row.update(estado="Comprometido",respaldo="Prestación descrita en el programa y alcance de la presente propuesta.")
    certificacion=items_check(REQ_CERT)
    for row in certificacion:
        row.update(estado="Comprometido",respaldo="Certificados e informe final dentro de cinco días hábiles posteriores al término del curso.")
    return {"version":4,"datos":d,"modulos":modulos,"docentes":[rel],"compra":compra,
            "certificacion":certificacion,"logos":{"oferente":{"nombre":"","base64":""}},
            "archivos":[],"declarados":copy.deepcopy(ADJUNTOS_DECLARADOS),
            "marcar_borrador":False,"incluir_revision":False,"incluir_admin":True}


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
    item=b["logos"][rol]
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
    if b.get("version")!=4: raise ValueError("Versión de formulario no compatible.")
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
    for rol in ["oferente"]:
        item=b.get("logos",{}).get(rol,{})
        if not isinstance(item.get("nombre"),str) or len(item["nombre"])>200 or not isinstance(item.get("base64"),str) or len(item["base64"])>7000000:
            raise ValueError("Logo inválido.")
        if item["base64"]: preparar_logo(base64.b64decode(item["base64"],validate=True),item["nombre"])
    for a in b["archivos"]:
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
                if not raw: r.append(f"Cargar logo del {rol}.")
                else: preparar_logo(raw,nombre)
            except Exception as e: r.append(f"Revisar logo {rol}: {e}")
        count=len(disponibles(b,token)) if token else len(b["archivos"])
        if "Anexo Nº 1" not in {a["categoria"] for a in b["archivos"]}:
            r.append("Anexo Nº 1 declarado: cargar su original completado y firmado para incorporarlo al ZIP.")
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
    for i,nombre in enumerate(PASOS[:-1]):
        out += [f"## {i+1}. {nombre}",""]
        for p,k,pregunta,t,req in PREGUNTAS:
            if p==i:
                out += [f"### {pregunta}", "[COMPLETAR]" if solo_estructura else str(d[k] or "[PENDIENTE]"), ""]
        if i==5:
            out += ["### Módulos: jornada / nombre / contenidos / horas pedagógicas / modalidad",""]
            out += ["[AGREGAR MÓDULOS]"] if solo_estructura else [f"- {m['jornada']} | {m['nombre']} | {m['contenido']} | {m['horas']:g} h | {m['tipo']}" for m in b["modulos"]]
        if i==7:
            for doc in b["docentes"]:
                out += ["### Relator: nombre / RUT / título / experiencia / disponibilidad", "[COMPLETAR]" if solo_estructura else f"{doc['nombre']} | {doc['rut']} | {doc['titulo']} | {doc['experiencia']} | {doc['disponibilidad']}"]
                out += [f"- [ ] {x['requisito']}" if solo_estructura else f"- {x['requisito']}: {x['estado']}. Respaldo: {x['respaldo'] or '[PENDIENTE]'}" for x in doc["checklist"]]
        if i in {8,9}:
            out += [f"- [ ] {x['requisito']}" if solo_estructura else f"- {x['requisito']}: {x['estado']}. Respaldo: {x['respaldo'] or '[PENDIENTE]'}" for x in b["compra" if i==8 else "certificacion"]]
        if i==11 and not solo_estructura:
            out += [f"- Documento declarado: {a['nombre']} | Categoría: {a['categoria']}" for a in b["declarados"]]
            out += [f"- Archivo: {a['nombre']} | Categoría: {a['categoria']}" for a in b["archivos"]]
        out += [""]
    return "\n".join(out)


def estilos_pdf():
    return {
        "body":ParagraphStyle("body",fontName="OTEC",fontSize=10,leading=14,textColor=INK,spaceAfter=8),
        "small":ParagraphStyle("small",fontName="OTEC",fontSize=8,leading=10.5,textColor=INK,spaceAfter=2),
        "h1":ParagraphStyle("h1",fontName="OTEC-Bold",fontSize=20,leading=25,textColor=NAVY,spaceAfter=16,keepWithNext=True),
        "h2":ParagraphStyle("h2",fontName="OTEC-Bold",fontSize=11,leading=15,textColor=NAVY,spaceBefore=10,spaceAfter=6,keepWithNext=True),
        "th":ParagraphStyle("th",fontName="OTEC-Bold",fontSize=8,leading=11,textColor=colors.white),
        "note":ParagraphStyle("note",fontName="OTEC",fontSize=9,leading=13,textColor=MUTED,spaceAfter=9),
    }


def generar_pdf(b,token=None,solo_portada=False):
    b=validar(b); d=b["datos"]; sty=estilos_pdf(); ancho=A4[0]-96
    def P(t,style="body"):
        return Paragraph(escape(limpiar(t or "Por completar")).replace("\n","<br/>"),sty[style])
    def tabla(headers,rows,widths=None):
        data=[[P(x,"th") for x in headers]]+[[P(x,"small") for x in row] for row in rows]
        t=Table(data,colWidths=widths or [ancho/len(headers)]*len(headers),repeatRows=1,splitByRow=1,splitInRow=1,hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,PALE]),("LEFTPADDING",(0,0),(-1,-1),9),
            ("RIGHTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LINEBELOW",(0,0),(-1,0),1,GOLD),("LINEBELOW",(0,1),(-1,-1),.3,LINE)]))
        return t
    def campo(label,text): return [P(label,"h2"),P(text)]
    logos={}; problemas_logo=[]
    for rol in ["oferente"]:
        try:
            raw,nombre=bytes_logo(b,rol); logos[rol]=preparar_logo(raw,nombre) if raw else None
        except Exception as e:
            if rol=="oferente":
                raise ValueError(f"No se pudo leer el logo del oferente {LOGO_NAME}: {e}") from e
            logos[rol]=None; problemas_logo.append(f"Logo {rol}: {e}")
    if logos["oferente"] is None:
        raise ValueError(f"No se encontró {LOGO_NAME}. Debe estar junto a REPORTE_PDF.py en el repositorio; también puedes cargarlo en la sección Logos.")
    trabajo=b["marcar_borrador"]

    def caja(c,t,x,y,w,h,fs=12,bold=False,color=INK):
        for size in [fs-.5*i for i in range(int((fs-7)*2)+1)]:
            st=ParagraphStyle("cover",fontName="OTEC-Bold" if bold else "OTEC",fontSize=size,leading=size*1.2,textColor=color)
            par=Paragraph(escape(limpiar(t or "Por completar")),st); _,hh=par.wrap(w,h)
            if hh<=h: par.drawOn(c,x,y+h-hh); return
        raise ValueError("Texto demasiado largo en la portada; reduce el título o el campo.")

    def portada(c,doc):
        w,h=A4; c.saveState()
        c.setFillColor(NAVY); c.rect(0,0,14,h,fill=1,stroke=0)
        c.setFillColor(GOLD); c.rect(48,h-48,w-96,3,fill=1,stroke=0)
        dibujar_logo(c,logos["oferente"],148,682,300,102,"LOGO OTEC")
        caja(c,"PROPUESTA TÉCNICA Y ECONÓMICA",48,644,499,17,10,True,color=GOLD)
        caja(c,d["titulo"],48,512,499,119,27,True,color=NAVY)
        caja(c,f"{d['modalidad']} | {d['proceso'] or 'Código por completar'}",48,478,499,28,12,True,color=GOLD)
        c.setFillColor(PALE); c.roundRect(48,347,499,111,8,fill=1,stroke=0)
        caja(c,"ORGANISMO COMPRADOR",62,427,470,15,8,True,color=MUTED)
        caja(c,d["comprador"],62,389,470,33,15,True,color=NAVY)
        caja(c,f"RUT {d['rut_comprador']} | {d['comuna']}, {d['region']}",62,357,470,28,9)
        for x,label,value in [(48,"PARTICIPANTES",str(d["cupos"]) if d["cupos"] else "Por definir"),
                (222,"HORAS PEDAGÓGICAS",f"{sum(horas(b).values()):g}"),
                (396,"OFERTA GLOBAL",pesos(montos(d)[2]) if montos(d)[2] is not None else "Por definir")]:
            caja(c,label,x,313,151,15,7.5,True,color=MUTED); caja(c,value,x,277,151,31,15,True,color=NAVY)
        caja(c,d["periodo_ejecucion"],48,229,499,35,11)
        caja(c,d["nombre_comercial"],48,183,499,32,18,True,color=NAVY)
        caja(c,d["oferente"]+" | RUT "+d["rut_oferente"],48,150,499,28,9)
        caja(c,"Contacto licitación: "+d["correo"]+" | "+d["telefono"],48,125,499,20,9)
        caja(c,"Emisión: "+d["fecha_propuesta"],48,91,499,20,9,color=MUTED)
        c.setStrokeColor(GOLD); c.line(48,72,547,72)
        caja(c,"BORRADOR DE TRABAJO" if trabajo else "PROPUESTA TÉCNICA Y ECONÓMICA",48,44,499,20,7.5,True,color=MUTED)
        c.restoreState()

    def paginas(c,doc):
        c.saveState(); w,h=A4
        c.setFont("OTEC-Bold",8); c.setFillColor(NAVY); c.drawString(48,h-36,"OTEC Santa Mónica")
        c.setFont("OTEC",7.5); c.setFillColor(MUTED); c.drawRightString(w-48,h-36,d["proceso"][:60])
        c.setStrokeColor(GOLD); c.line(48,h-45,w-48,h-45)
        c.setStrokeColor(LINE); c.line(48,43,w-48,43)
        c.setFont("OTEC",7); c.drawString(48,29,"Borrador de propuesta" if trabajo else "Propuesta técnica y económica")
        c.drawRightString(w-48,29,f"Página {doc.page}"); c.restoreState()

    out=BytesIO(); doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=48,leftMargin=48,
        topMargin=66,bottomMargin=56,title=f"Propuesta {d['proceso']}",author=d["oferente"],allowSplitting=1)
    story=[Spacer(1,1)]
    if solo_portada:
        doc.build(story,onFirstPage=portada,onLaterPages=paginas); return out.getvalue()
    story.append(PageBreak())
    def cap(t): story.extend([CondPageBreak(100),P(t,"h1")])
    cap("01 / Presentación institucional")
    story.extend(campo("Quiénes somos",d["quienes"])); story.extend(campo("Nuestra visión",d["vision"]))
    story.extend(campo("Qué ofrecemos",d["que_ofrecemos"]))
    story.append(PageBreak()); cap("02 / Antecedentes del proceso")
    story.append(tabla(["Antecedente","Información"],[
        ["Comprador",d["comprador"]+" / "+d["rut_comprador"]],["Modalidad y código",d["modalidad"]+" / "+d["proceso"]],
        ["Rubro e ítem",d["rubro"]+" / "+d["id_item"]],["Presupuesto",pesos(d["presupuesto"])+" / "+d["tipo_presupuesto"]],
        ["Publicación",d["publicacion"]],["Cierre primer llamado",d["cierre_1"]],["Cierre segundo llamado",d["cierre_2"]],
        ["Publicación a primer cierre",intervalo(d["publicacion"],d["cierre_1"])],
        ["Publicación a segundo cierre",intervalo(d["publicacion"],d["cierre_2"])],
    ],[163,ancho-163]))
    if d["alerta_plazo"]: story.extend(campo("Aspecto por aclarar",d["alerta_plazo"]))
    story.append(PageBreak()); cap("03 / Objetivos y participantes")
    story.extend(campo("Objetivo general",d["objetivo_general"]))
    story.append(P("Objetivos específicos","h2"))
    for i,linea in enumerate(d["objetivos_especificos"].splitlines(),1):
        if linea.strip(): story.append(P(f"{i}. {linea.strip()}"))
    story.extend(campo("Universo de participantes",d["participantes"]))
    story.append(tabla(["Cupos","Modalidad"],[[str(d["cupos"]),d["modalidad_curso"]]],[80,ancho-80]))
    story.extend(campo("Conocimientos previos",d["prerrequisitos"]))
    story.append(PageBreak()); cap("04 / Programa y distribución horaria")
    tot=horas(b)
    story.append(P(f"Duración exigida: {d['horas_exigidas']:g} horas pedagógicas. Programa propuesto: {sum(tot.values()):g} horas. "+" / ".join(f"{k}: {v:g} h" for k,v in tot.items())))
    for jornada in dict.fromkeys(m["jornada"] for m in b["modulos"]):
        story.append(P(jornada,"h2")); filas=[m for m in b["modulos"] if m["jornada"]==jornada]
        story.append(tabla(["Módulo / modalidad","Contenidos","Horas"],[[m["nombre"]+"\n"+m["tipo"],m["contenido"],f"{m['horas']:g}"] for m in filas],[148,ancho-196,48]))
    story.append(PageBreak()); cap("04 / Metodología y herramientas")
    story.extend(campo("Metodología de trabajo",d["metodologia"]))
    story.extend(campo("Aplicación de herramientas",d["herramientas"]))
    story.append(PageBreak()); cap("05 / Lugar, fechas y logística")
    story.append(tabla(["Aspecto","Propuesta / requisito"],[["Región y comuna",d["region"]+" / "+d["comuna"]],
        ["Lugar",d["lugar"]],["Responsable de disponer el lugar",d["quien_lugar"]],
        ["Período requerido",d["periodo_ejecucion"]],["Coordinación de fechas",d["fecha_ejecucion"]],
        ["Plazo indicado en ficha",d["plazo_ficha"]]],[158,ancho-158]))
    for label,k in [("Equipamiento y conectividad","equipamiento"),("Materiales de trabajo","materiales"),("Cafetería","cafeteria")]: story.extend(campo(label,d[k]))
    story.append(PageBreak()); cap("06 / Equipo relator y documentación")
    story.extend(campo("Perfil requerido",d["perfil_docente"]))
    for i,rel in enumerate(b["docentes"],1):
        story.append(P(f"Relator {i}: {rel['nombre']}","h2"))
        story.append(tabla(["Antecedente","Información"],[["RUT",rel["rut"]],["Título",rel["titulo"]],["Experiencia declarada",rel["experiencia"]],["Disponibilidad",rel["disponibilidad"]]],[100,ancho-100]))
        story.append(Spacer(1,8))
        story.append(tabla(["Requisito","Estado","Respaldo / observación"],[[x["requisito"],x["estado"],x["respaldo"] or "Por adjuntar / verificar"] for x in rel["checklist"]],[190,108,ancho-298]))
    story.extend(campo("Referencia al CV y respaldos",d["referencia_cv"]))
    archivos=disponibles(b,token) if token else b["archivos"]
    story.append(PageBreak()); cap("07 / Checklist de requisitos de compra")
    story.append(P("Matriz editable de cumplimiento. Cada estado debe sustentarse en los antecedentes de la propuesta; cargar un archivo no verifica automáticamente su contenido.","note"))
    story.append(tabla(["Requisito","Estado","Evidencia / compromiso"],[[x["requisito"],x["estado"],x["respaldo"] or "Por completar"] for x in b["compra"]],[190,108,ancho-298]))
    story.append(PageBreak()); cap("08 / Evaluación y certificación")
    for label,k in [("Evaluación del aprendizaje","evaluacion"),("Condiciones de aprobación","aprobacion"),("Entrega de certificados e informe","entrega_certificados"),("Destinatario del informe final","destino_informe")]: story.extend(campo(label,d[k]))
    story.append(P("Checklist de certificación","h2"))
    story.append(tabla(["Requisito","Estado","Evidencia / compromiso"],[[x["requisito"],x["estado"],x["respaldo"] or "Por completar"] for x in b["certificacion"]],[190,108,ancho-298]))
    story.append(PageBreak()); cap("09 / Propuesta económica")
    neto,iva,total=montos(d)
    story.append(tabla(["Concepto","Valor"],[["Cantidad global",str(d["cantidad"])],["Valor unitario neto",pesos(d["valor_unitario"])],
        ["Despacho neto",pesos(d["despacho"])],["Neto + despacho",pesos(neto)],["Tratamiento de impuesto",d["impuesto"]],
        ["Impuesto",pesos(iva) if iva is not None else "Por definir"],["TOTAL OFERTADO",pesos(total) if total is not None else "Por definir"],
        ["Presupuesto estimado del comprador",pesos(d["presupuesto"])]],[245,ancho-245]))
    story.extend(campo("Alcance del precio",d["incluye_precio"])); story.extend(campo("Detalle breve de cotización",d["detalle"]))
    story.append(PageBreak()); cap("10 / Documentación adjunta")
    story.extend(campo("Documentos que acompañan la oferta",d["documentacion_adjunta"]))
    story.extend(campo("Documentos de referencia del proceso",d["adjuntos_solicitados"]))
    filas=[]; categorias_cargadas={x["categoria"] for x in archivos}
    for item in b["declarados"]:
        if item["categoria"] not in categorias_cargadas:
            filas.append([item["nombre"],item["categoria"],"Declarado; presentación por separado"])
    filas += [[a["nombre"],a["categoria"],"Cargado en esta sesión / ZIP"] for a in archivos]
    story.append(tabla(["Documento","Categoría","Estado"],filas or [["Sin documentos declarados","Por completar","Pendiente"]],[225,118,ancho-343]))
    story.append(P("El ZIP descargable contiene el PDF de la propuesta y solo los originales efectivamente cargados. La declaración de un adjunto no incorpora sus bytes al ZIP.","note"))
    if b["incluir_admin"]:
        story.append(PageBreak()); cap("11 / Identificación administrativa")
        story.append(P("Datos informativos para identificar al oferente. Esta sección no sustituye el Anexo Nº 1 oficial, que debe conservarse en su formato original, completado y firmado.","note"))
        story.append(tabla(["Empresa","Información"],[["Razón social",d["oferente"]],["RUT",d["rut_oferente"]],["Domicilio",d["domicilio_empresa"]],
            ["Contacto de la licitación",d["contacto_oferta"]+" / "+d["telefono"]+" / "+d["correo"]],["Código SENCE informado",d["codigo_sence"]]],[135,ancho-135]))
        story.append(P("Representante legal","h2"))
        story.append(tabla(["Antecedente","Información"],[["Nombre",d["representante"]],["RUT",d["rut_representante"]],["Cargo",d["cargo_representante"]],
            ["Domicilio",d["domicilio_representante"]],["Teléfono",d["telefono_representante"]],["Personería",d["personeria"]]],[135,ancho-135]))
        story.append(P("Datos bancarios","h2"))
        story.append(tabla(["Antecedente","Información"],[["Titular",d["oferente"]],["RUT titular",d["rut_oferente"]],["Banco",d["banco"]],
            ["Tipo de cuenta",d["tipo_cuenta"]],["Número de cuenta",d["cuenta"]],["Correo pagos",d["correo_pagos"]]],[135,ancho-135]))
    if b["incluir_revision"]:
        story.append(PageBreak()); cap("Control de revisión solicitado")
        story.append(P("Hoja de apoyo opcional. Los estados del checklist distinguen compromisos, declaraciones y antecedentes sujetos a evaluación del comprador.","note"))
        for i,lista in pendientes(b,token):
            story.append(P(PASOS[i],"h2"))
            for item in lista: story.append(P("- "+item,"small"))
        for item in problemas_logo: story.append(P(item,"small"))
    doc.build(story,onFirstPage=portada,onLaterPages=paginas)
    return out.getvalue()


def main():
    import streamlit as st
    st.set_page_config(page_title="OTEC Santa Mónica | Propuestas",page_icon="📄",layout="wide")
    st.title("Constructor de propuestas · OTEC Santa Mónica")
    st.caption("Formulario completo por preguntas. Edita las respuestas, revisa los requisitos y genera una propuesta PDF profesional.")
    st.info("Propuesta precargada: Compra Ágil 1057545-246-COT26, 20 participantes y 20 horas pedagógicas. Oferta global: $2.300.000, exenta de IVA. Revisa y adapta todas las respuestas para el proceso que vayas a ofertar.")
    if "modelo_propuesta_v4" not in st.session_state:
        # Una versión anterior puede haber dejado widgets con valores de ejemplo.
        for clave in list(st.session_state):
            if clave.startswith("q_") or clave in {"propuesta_pdf","propuesta_firma"}:
                del st.session_state[clave]
        st.session_state.modelo_propuesta_v4=nuevo()
    b=st.session_state.modelo_propuesta_v4
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
        if opciones is not None: return st.selectbox(label,opciones,**kw)
        if tipo in {"entero","decimal"}:
            minimo=1 if path[-1]=="cantidad" else 0
            tope=100 if path[-1] in {"tasa","adjuntos_esperados"} else 10000 if path[-1] in {"horas","horas_exigidas","cupos"} else 10**12
            if tipo=="decimal": return st.number_input(label,min_value=float(minimo),max_value=float(tope),step=.5,**kw)
            return st.number_input(label,min_value=minimo,max_value=tope,step=1,**kw)
        if tipo=="area": return st.text_area(label,max_chars=12000,height=130,**kw)
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

    for seccion,nombre in enumerate(PASOS):
        with st.expander(f"{seccion+1:02d}. {nombre}",expanded=seccion in {0,12}):
            preguntas(seccion)
            if seccion==0:
                d=b["datos"]
                st.caption("Publicación a primer cierre: "+intervalo(d["publicacion"],d["cierre_1"]))
                st.caption("Publicación a segundo cierre: "+intervalo(d["publicacion"],d["cierre_2"]))
            if seccion==1:
                st.caption("Empresa: Las Condes. Representante legal: Quillota, teléfono +56 9 5807 5021. Contacto de licitación: ebrun, +56 9 6359 6523, ebrun@otecsantamonica.com. No se incluye correo de la representante legal.")
            if seccion==5:
                st.markdown("**¿Qué módulos, contenidos y horas tendrá el programa?**")
                for j,m in enumerate(b["modulos"]):
                    with st.container(border=True):
                        st.markdown(f"**Módulo {j+1}**")
                        a,c,e=st.columns([1,2,1])
                        with a: widget(["modulos",j,"jornada"],"Jornada / bloque")
                        with c: widget(["modulos",j,"nombre"],"Nombre del módulo")
                        with e: widget(["modulos",j,"horas"],"Horas pedagógicas","decimal")
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
                st.caption(" / ".join(f"{k}: {v:g} horas" for k,v in tot.items()))
                if abs(sum(tot.values())-b["datos"]["horas_exigidas"])>.01:
                    st.warning("La suma del programa no coincide con las horas exigidas. Puedes generar el borrador y corregirla después.")
            if seccion==7:
                st.caption("Relator identificado según el CV aportado. Se informa la experiencia efectiva; el requisito de cinco años queda expresamente a evaluación del comprador.")
                for j,rel in enumerate(b["docentes"]):
                    st.markdown(f"**Relator {j+1}**")
                    for k,label in [("nombre","¿Cuál es su nombre completo?"),("rut","¿Cuál es su RUT?"),("titulo","¿Cuál es su título profesional?"),("experiencia","¿Qué experiencia efectiva declara en la temática?"),("disponibilidad","¿Cuál es su disponibilidad confirmada?")]:
                        widget(["docentes",j,k],label)
                    checklist(["docentes",j,"checklist"],f"Checklist del relator {j+1}")
                    if st.button("Eliminar relator",key="del_doc_"+rel["id"]):
                        b["docentes"].pop(j)
                        for k in list(st.session_state):
                            if k.startswith("q_docentes_"): del st.session_state[k]
                        st.rerun()
                if st.button("Agregar otro relator"):
                    b["docentes"].append(dict(id=uuid4().hex[:12],nombre="",rut="",titulo="",experiencia="",disponibilidad="Por coordinar",checklist=items_check(REQ_RELATOR)))
                    st.rerun()
            if seccion==8: checklist(["compra"],"¿Cómo cumpliremos cada requisito obligatorio de compra?")
            if seccion==9: checklist(["certificacion"],"¿Qué incluirán los certificados y el informe final?")
            if seccion==10:
                neto,iva,total=montos(b["datos"])
                a,c,e=st.columns(3); a.metric("Neto + despacho",pesos(neto)); c.metric("Impuesto",pesos(iva) if iva is not None else "Por definir")
                e.metric("Total",pesos(total) if total is not None else "Por definir")
                st.caption("Oferta acordada: $2.300.000 exenta de IVA. Este apartado muestra únicamente el precio ofertado; no contiene costos internos ni margen comercial.")
                if total is not None and total>b["datos"]["presupuesto"]>0: st.warning("La oferta supera el presupuesto estimado del comprador.")
            if seccion==11:
                st.markdown("**Logo institucional de la OTEC**")
                contenedor_logo=st.container()
                for rol,col in [("oferente",contenedor_logo)]:
                    with col:
                        key="upload_logo_"+rol
                        st.file_uploader("Logo del "+rol,type=["svg","png","jpg","jpeg"],key=key,on_change=cargar_logo,args=(rol,key))
                        if st.session_state.get("aviso_logo_"+rol): st.error(st.session_state["aviso_logo_"+rol])
                        try:
                            raw,n=bytes_logo(b,rol)
                            if raw:
                                preparar_logo(raw,n)
                                st.image(raw.decode("utf-8") if n.lower().endswith(".svg") else raw,width=210)
                                st.caption(("Logo por defecto de GitHub: " if rol=="oferente" and not b["logos"][rol]["base64"] else "Logo listo: ")+n)
                            else: st.info("Carga el logo de la OTEC o guarda OTEC_Santa_Monica_Opcion_1.svg junto al archivo .py para generar el PDF.")
                        except Exception as exc: st.warning(str(exc))
                st.caption(f"Logo OTEC automático: {LOGO_NAME}, en la carpeta del script o en assets/, logos/ o images/ del repositorio GitHub. La portada utiliza únicamente el logo de la OTEC.")
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
                        st.write(a["nombre"])
                        widget(["archivos",j,"categoria"],"¿Qué tipo de documento es?",opciones=CATEGORIAS_ADJUNTOS)
                        if st.button("Retirar archivo",key="del_a_"+a["id"]):
                            b["archivos"].pop(j)
                            for k in list(st.session_state):
                                if k.startswith("q_archivos_"): del st.session_state[k]
                            st.rerun()
            if seccion==12:
                widget(["incluir_admin"],"Incluir anexo administrativo: representante legal y datos bancarios","bool")
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
                fuentes=[]
                for rol in ["oferente"]:
                    try:
                        raw,_=bytes_logo(b,rol); fuentes.append(hashlib.sha256(raw or b"").hexdigest())
                    except Exception: fuentes.append("logo_no_valido")
                firma=hashlib.sha256((PDF_RENDER_VERSION+json.dumps(b,sort_keys=True,ensure_ascii=False)+"".join(fuentes)).encode()).hexdigest()
                st.divider()
                if st.button("Generar reporte PDF",type="primary"):
                    try:
                        with st.spinner("Preparando propuesta PDF..."):
                            st.session_state.propuesta_pdf=generar_pdf(b)
                            st.session_state.propuesta_firma=firma
                        st.success("Reporte generado. Descárgalo a continuación.")
                    except Exception as exc: st.error(f"No se pudo generar el reporte: {exc}")
                if st.session_state.get("propuesta_firma")==firma:
                    codigo=slug(b["datos"]["proceso"],80)
                    st.download_button("Descargar propuesta PDF",st.session_state.propuesta_pdf,file_name=f"Propuesta_{codigo}.pdf",mime="application/pdf",type="primary")
                    st.download_button("Descargar PDF y adjuntos (.zip)",exportar_zip(b,st.session_state.propuesta_pdf),file_name=f"Expediente_{codigo}.zip",mime="application/zip")
                elif st.session_state.get("propuesta_pdf"):
                    st.info("Las respuestas cambiaron. Genera el reporte nuevamente para descargar la versión actualizada.")
    st.caption("Formulario sin guardado de progreso: conserva abierta esta sesión mientras editas y descarga los documentos que necesites.")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-pdf",type=Path,help="Generar la propuesta precargada sin iniciar Streamlit")
    args,_=parser.parse_known_args()
    if args.demo_pdf:
        args.demo_pdf.write_bytes(generar_pdf(nuevo()))
        print(f"PDF generado: {args.demo_pdf.resolve()}")
    else: main()
