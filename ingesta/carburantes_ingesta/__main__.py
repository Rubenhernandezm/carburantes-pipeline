"""Lanza la ingesta en local: python -m carburantes_ingesta (desde la carpeta ingesta/)."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from carburantes_ingesta.cliente import crear_sesion
from carburantes_ingesta.ingesta import ejecutar

# Raíz del repositorio calculada desde este fichero, para que los datos vayan siempre
# a la misma carpeta, se lance desde donde se lance. El .gitignore la excluye (/data/).
RAIZ_REPO = Path(__file__).resolve().parents[2]
DIRECTORIO_RAW = RAIZ_REPO / "data" / "raw"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Hora en UTC: es la que usará la Function en Azure, así local y nube nombran igual los ficheros.
ejecutar(crear_sesion(), DIRECTORIO_RAW, datetime.now(timezone.utc))