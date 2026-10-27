"""Persistencia de NöRA en JSON: guardar y cargar el inventario."""
import json
import os
from pathlib import Path

from inventory import Inventario
from product import ErrorValidacion

RUTA_ESTADO = Path(__file__).resolve().parent / "data" / "state.json"


class ErrorAlmacenamiento(Exception):
    """Falla al leer o escribir el archivo de datos."""


class Almacenamiento:
    """Lee y escribe el inventario completo en un archivo JSON."""

    def __init__(self, ruta=RUTA_ESTADO):
        self.ruta = Path(ruta)

    def guardar(self, inventario):
        """Escribe en un archivo temporal (utf-8) y luego reemplaza el archivo real.

        El reemplazo solo ocurre si la escritura terminó bien. Si algo falla se borra el
        temporal, el archivo anterior queda intacto y se lanza ErrorAlmacenamiento.
        """
        temporal = Path(str(self.ruta) + ".tmp")
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            with temporal.open("w", encoding="utf-8") as archivo:
                json.dump(inventario.a_diccionario(), archivo, ensure_ascii=False, indent=2)
                archivo.flush()
                os.fsync(archivo.fileno())
            temporal.replace(self.ruta)
        except (OSError, TypeError, ValueError) as error:
            try:
                temporal.unlink(missing_ok=True)
            except OSError:
                pass
            raise ErrorAlmacenamiento("No se pudo guardar el inventario.") from error

    def cargar(self):
        """Lee el archivo y devuelve un Inventario.

        - archivo inexistente: inventario vacío
        - JSON dañado o inconsistente: lanza ErrorAlmacenamiento sin tocar el archivo
        """
        if not self.ruta.exists():
            return Inventario()
        try:
            with self.ruta.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            return Inventario.desde_diccionario(datos)
        except (OSError, ValueError, ErrorValidacion) as error:
            raise ErrorAlmacenamiento(
                f"No se pudo cargar el inventario de forma segura: {error}") from error
