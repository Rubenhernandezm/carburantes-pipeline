import pytest

from carburantes_ingesta.cliente import crear_sesion, descargar
from carburantes_ingesta.validacion import leer_respuesta


@pytest.mark.integracion
def test_descarga_real_del_ministerio():
    # Llama de verdad a la API: comprueba el TLS, la cabecera y que la respuesta es válida.
    contenido = descargar(crear_sesion())
    datos = leer_respuesta(contenido)
    assert datos["ResultadoConsulta"] == "OK"