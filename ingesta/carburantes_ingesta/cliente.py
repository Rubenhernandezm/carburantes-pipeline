"""Descarga de la respuesta del Ministerio (D-007)."""

import ssl

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/"

# D-007: el servidor solo acepta cifrados con intercambio de claves RSA.
# Los modernos (ECDHE) van primero para que se usen en cuanto el servidor los admita.
CIFRADOS = "ECDHE+AESGCM:ECDHE+CHACHA20:AES256-GCM-SHA384:AES128-GCM-SHA256"

# (conectar, leer) en segundos: la respuesta pesa ~14 MB y el servidor no es rápido.
TIMEOUT = (10, 120)


class AdaptadorTLS(HTTPAdapter):
    """Conexión con TLS 1.2 como mínimo y los cifrados que exige el servidor."""

    def init_poolmanager(self, *args, **kwargs):
        # create_default_context() mantiene la verificación del certificado.
        contexto = ssl.create_default_context()
        contexto.minimum_version = ssl.TLSVersion.TLSv1_2
        contexto.set_ciphers(CIFRADOS)
        kwargs["ssl_context"] = contexto
        return super().init_poolmanager(*args, **kwargs)


def crear_sesion() -> requests.Session:
    """Sesión HTTP con el adaptador TLS y los reintentos, solo para el servidor del Ministerio."""
    # Hasta 3 reintentos ante errores temporales del servidor, con espera creciente entre ellos.
    # Solo GET: repetir una petición de lectura no tiene efectos secundarios.
    reintentos = Retry(total=3, backoff_factor=5, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
    sesion = requests.Session()
    sesion.mount("https://sedeaplicaciones.minetur.gob.es/", AdaptadorTLS(max_retries=reintentos))
    sesion.headers["Accept"] = "application/json"  # sin esta cabecera, el servidor responde en XML
    return sesion


def descargar(sesion: requests.Session) -> bytes:
    """Descarga la respuesta y devuelve los bytes tal cual llegan, para guardarlos en raw."""
    respuesta = sesion.get(URL, timeout=TIMEOUT)
    respuesta.raise_for_status()  # error HTTP (404, 500…) → excepción, no unos bytes de error
    return respuesta.content