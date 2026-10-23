"""Validaciones de la respuesta del Ministerio (D-014)."""


class RespuestaInvalida(Exception):
    """La respuesta no se puede usar: no se guarda y la ejecución falla."""


def comprobar_resultado(datos: dict) -> None:
    """Lanza RespuestaInvalida si ResultadoConsulta no es "OK"."""
    # .get() devuelve None si falta la clave: así una respuesta sin ese campo
    # también acaba en RespuestaInvalida, y no en un KeyError genérico.
    resultado = datos.get("ResultadoConsulta")
    if resultado != "OK":
        raise RespuestaInvalida(f"ResultadoConsulta = {resultado!r}")

