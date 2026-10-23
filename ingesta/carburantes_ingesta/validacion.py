"""Validaciones de la respuesta del Ministerio (D-014)."""

import json

class RespuestaInvalida(Exception):
    """La respuesta no se puede usar: no se guarda y la ejecución falla."""


def comprobar_resultado(datos: dict) -> None:
    """Lanza RespuestaInvalida si ResultadoConsulta no es "OK"."""
    # .get() devuelve None si falta la clave: así una respuesta sin ese campo
    # también acaba en RespuestaInvalida, y no en un KeyError genérico.
    resultado = datos.get("ResultadoConsulta")
    if resultado != "OK":
        raise RespuestaInvalida(f"ResultadoConsulta = {resultado!r}")

# Rango de D-014: unos ±12 % sobre las 11.433 estaciones del 19/10/2026.
# Fuera de él, lo más probable es una respuesta truncada o incompleta.
MIN_ESTACIONES = 10_000
MAX_ESTACIONES = 13_000


def comprobar_estaciones(datos: dict) -> None:
    """Lanza RespuestaInvalida si la lista de estaciones falta, está vacía o tiene un tamaño anómalo."""
    estaciones = datos.get("ListaEESSPrecio")
    # None (falta la clave) y [] (lista vacía) cuentan los dos como "falso".
    if not estaciones:
        raise RespuestaInvalida("Falta ListaEESSPrecio o está vacía")
    n = len(estaciones)
    if not MIN_ESTACIONES <= n <= MAX_ESTACIONES:
        raise RespuestaInvalida(f"Número de estaciones fuera de rango: {n}")

def leer_respuesta(contenido: bytes) -> dict:
    """Convierte los bytes de la respuesta en diccionario y aplica las validaciones bloqueantes."""
    try:
        datos = json.loads(contenido)
    except json.JSONDecodeError as error:
        # Sin JSON no hay nada que guardar: suele ser una página de error del servidor.
        raise RespuestaInvalida(f"La respuesta no es JSON: {error}") from error
    # Un JSON válido puede ser una lista o un número; sin un objeto, .get() fallaría.
    if not isinstance(datos, dict):
        raise RespuestaInvalida("La respuesta no es un objeto JSON")
    comprobar_resultado(datos)
    comprobar_estaciones(datos)
    return datos

