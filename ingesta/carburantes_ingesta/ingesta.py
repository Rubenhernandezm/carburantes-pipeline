"""Orquestación de la ingesta: descargar, validar y guardar (D-013, D-014)."""

import logging
from datetime import datetime
from pathlib import Path

import requests

from carburantes_ingesta.almacenamiento import guardar_raw
from carburantes_ingesta.cliente import descargar
from carburantes_ingesta.validacion import leer_respuesta

log = logging.getLogger(__name__)


def ejecutar(sesion: requests.Session, directorio: Path, momento: datetime) -> Path:
    """Descarga la respuesta, la valida y guarda los bytes originales en raw."""
    contenido = descargar(sesion)
    # Si la respuesta no sirve, lanza RespuestaInvalida y no se llega a guardar nada.
    datos = leer_respuesta(contenido)
    # Se guardan los bytes originales, no el diccionario: raw es la copia fiel.
    destino = guardar_raw(contenido, directorio, momento)
    log.info("Guardadas %d estaciones en %s", len(datos["ListaEESSPrecio"]), destino)
    return destino