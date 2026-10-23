import json

import pytest

from carburantes_ingesta.validacion import MAX_ESTACIONES, RespuestaInvalida, comprobar_estaciones, comprobar_resultado, leer_respuesta

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


def test_excesivas_estaciones_lanza_error():
   # Más estaciones de las normales: respuesta anómala (por ejemplo, duplicada).
    with pytest.raises(RespuestaInvalida):
        comprobar_estaciones({"ListaEESSPrecio": [{}] * (MAX_ESTACIONES + 1)}) 

def test_respuesta_que_no_es_json_lanza_error():
    # b"..." es un literal de bytes, como los que llegan del servidor.
    with pytest.raises(RespuestaInvalida):
        leer_respuesta(b"<html>Error 500</html>")


def test_respuesta_valida_devuelve_diccionario():
    # json.dumps() convierte el diccionario en texto JSON y .encode() lo pasa a bytes.
    contenido = json.dumps({"ResultadoConsulta": "OK", "ListaEESSPrecio": [{}] * 11_000}).encode()
    datos = leer_respuesta(contenido)
    assert datos["ResultadoConsulta"] == "OK"

def test_json_que_no_es_objeto_lanza_error():
    # b"[]" es JSON válido (una lista vacía), pero no es un objeto.
    with pytest.raises(RespuestaInvalida):
        leer_respuesta(b"[]")