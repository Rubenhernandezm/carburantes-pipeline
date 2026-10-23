import pytest

from carburantes_ingesta.validacion import RespuestaInvalida, comprobar_resultado


def test_resultado_ok_no_lanza_error():
    # Si la función no lanza nada, el test pasa.
    comprobar_resultado({"ResultadoConsulta": "OK"})


def test_resultado_distinto_de_ok_lanza_error():
    with pytest.raises(RespuestaInvalida):
        comprobar_resultado({"ResultadoConsulta": "ERROR"})

def test_diccionario_sin_resultado_consulta_lanza_error():
    with pytest.raises(RespuestaInvalida):
        comprobar_resultado({})      