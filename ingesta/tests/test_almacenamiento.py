import gzip
from datetime import datetime

from carburantes_ingesta.almacenamiento import guardar_raw, ruta_raw

MOMENTO = datetime(2026, 10, 19, 12, 49, 44)


def test_ruta_raw_particiona_por_fecha():
    assert ruta_raw(MOMENTO).as_posix() == "fecha=2026-10-19/precios_20261019T124944.json.gz"


def test_guardar_raw_conserva_los_bytes_originales(tmp_path):
    # tmp_path: carpeta temporal que pytest crea para cada test.
    contenido = b'{"ResultadoConsulta": "OK"}'
    destino = guardar_raw(contenido, tmp_path, MOMENTO)
    assert gzip.decompress(destino.read_bytes()) == contenido