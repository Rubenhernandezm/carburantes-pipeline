"""Guardado de la respuesta en la zona raw (D-004)."""

import gzip
from datetime import datetime
from pathlib import Path


def ruta_raw(momento: datetime) -> Path:
    """Ruta relativa del fichero raw: una carpeta por día y la hora en el nombre."""
    return Path(f"fecha={momento:%Y-%m-%d}") / f"precios_{momento:%Y%m%dT%H%M%S}.json.gz"


def guardar_raw(contenido: bytes, directorio: Path, momento: datetime) -> Path:
    """Comprime los bytes tal cual llegaron y los guarda en el directorio raw."""
    destino = directorio / ruta_raw(momento)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0: el mismo contenido produce siempre el mismo .gz (útil en los tests).
    destino.write_bytes(gzip.compress(contenido, mtime=0))
    return destino