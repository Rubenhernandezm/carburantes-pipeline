"""Compara las fotos guardadas en raw para ver si el servicio cambia entre peticiones."""

import gzip
import hashlib
import json
from pathlib import Path

for fichero in sorted(Path("data/raw").glob("fecha=*/*.json.gz")):
    datos = json.loads(gzip.decompress(fichero.read_bytes()))
    # Huella de la lista de estaciones: si dos fotos tienen la misma, sus datos son idénticos.
    lista = json.dumps(datos["ListaEESSPrecio"], sort_keys=True).encode()
    huella = hashlib.sha256(lista).hexdigest()[:12]
    print(f"{fichero.name}  Fecha={datos['Fecha']}  estaciones={len(datos['ListaEESSPrecio'])}  huella={huella}")