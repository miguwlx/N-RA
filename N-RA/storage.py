"""Persistencia de NöRA en JSON (HU-008 guardar, HU-013 cargar)."""

RUTA_ESTADO = "data/state.json"


class ErrorAlmacenamiento(Exception):
    """Falla al leer o escribir el archivo de datos."""


class Almacenamiento:
    def __init__(self, ruta=RUTA_ESTADO):
        self.ruta = ruta

    def guardar(self, inventario):
        """HU-008: escribe en un archivo temporal (utf-8) y luego reemplaza el archivo real.

        Si la escritura falla, informa el error y deja intacto el archivo anterior.
        """
        raise NotImplementedError("HU-008")

    def cargar(self):
        """HU-013: devuelve un Inventario.

        - archivo inexistente: inventario vacío
        - JSON dañado o inconsistente: lanza ErrorAlmacenamiento sin sobrescribir nada
        """
        raise NotImplementedError("HU-013")
