import pytest

from carburantes_ingesta.validacion import RespuestaInvalida, comprobar_resultado, comprobar_estaciones


def test_resultado_ok_no_lanza_error():
    # Si la función no lanza nada, el test pasa.
    comprobar_resultado({"ResultadoConsulta": "OK"})


def test_resultado_distinto_de_ok_lanza_error():
    with pytest.raises(RespuestaInvalida):
        comprobar_resultado({"ResultadoConsulta": "ERROR"})

def test_diccionario_sin_resultado_consulta_lanza_error():
    with pytest.raises(RespuestaInvalida):
        comprobar_resultado({}) 

def test_lista_de_estaciones_normal_no_lanza_error():
    # [{}] * 11_000 crea una lista de 11.000 elementos: basta para contar.
    comprobar_estaciones({"ListaEESSPrecio": [{}] * 11_000})


def test_lista_de_estaciones_vacia_lanza_error():
    with pytest.raises(RespuestaInvalida):
        comprobar_estaciones({"ListaEESSPrecio": []})


def test_sin_lista_de_estaciones_lanza_error():
    with pytest.raises(RespuestaInvalida):
        comprobar_estaciones({})


def test_pocas_estaciones_lanza_error():
    # 500 estaciones: probable respuesta truncada.
    with pytest.raises(RespuestaInvalida):
        comprobar_estaciones({"ListaEESSPrecio": [{}] * 500})    

from carburantes_ingesta.validacion import MAX_ESTACIONES

def test_excesivas_estaciones_lanza_error():
   # Más estaciones de las normales: respuesta anómala (por ejemplo, duplicada).
    with pytest.raises(RespuestaInvalida):
        comprobar_estaciones({"ListaEESSPrecio": [{}] * (MAX_ESTACIONES + 1)}) 