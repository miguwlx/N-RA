"""Reportes de NöRA con herencia y polimorfismo (HU-009 y HU-014)."""
from abc import ABC, abstractmethod


class Reporte(ABC):
    """Clase base: el menú invoca generar() sin conocer el tipo de reporte."""

    @abstractmethod
    def generar(self, inventario):
        """Produce el reporte a partir del inventario."""


class ReporteCSV(Reporte):
    """HU-009: reports/ventas.csv con código, nombre, categoría, talla, color,
    precio, stock y unidades vendidas (sin compras devueltas).
    Crea la carpeta reports si no existe y devuelve la ruta generada."""

    def generar(self, inventario):
        raise NotImplementedError("HU-009")


class ReporteTexto(Reporte):
    """HU-014: resumen en pantalla con total vendido en dinero, número de compras
    (sin devueltas) y prendas con poco stock."""

    def generar(self, inventario):
        raise NotImplementedError("HU-014")
