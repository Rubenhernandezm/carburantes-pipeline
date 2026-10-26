import gzip
import json
from datetime import datetime

import pytest

from carburantes_ingesta.ingesta import ejecutar
from carburantes_ingesta.validacion import RespuestaInvalida

MOMENTO = datetime(2026, 10, 19, 12, 49, 44)


class RespuestaFalsa:
    """Imita lo que descargar() usa de una respuesta real: .content y .raise_for_status()."""

    def __init__(self, contenido: bytes):
        self.content = contenido

    def raise_for_status(self):
        pass


class SesionFalsa:
    """Imita la sesión HTTP: en lugar de ir a internet, devuelve siempre los mismos bytes."""

    def __init__(self, contenido: bytes):
        self.contenido = contenido

    def get(self, url, timeout):
        return RespuestaFalsa(self.contenido)


def test_respuesta_valida_se_guarda_en_raw(tmp_path):
    contenido = json.dumps({"ResultadoConsulta": "OK", "ListaEESSPrecio": [{}] * 11_000}).encode()
    destino = ejecutar(SesionFalsa(contenido), tmp_path, MOMENTO)
    assert gzip.decompress(destino.read_bytes()) == contenido


def test_respuesta_invalida_no_guarda_nada(tmp_path):
    contenido = json.dumps({"ResultadoConsulta": "ERROR"}).encode()
    with pytest.raises(RespuestaInvalida):
        ejecutar(SesionFalsa(contenido), tmp_path, MOMENTO)
    # La carpeta sigue vacía: una respuesta rota nunca llega a raw.
    assert list(tmp_path.iterdir()) == []