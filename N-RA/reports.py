"""Reportes de NöRA con herencia y polimorfismo: CSV de ventas y resumen en pantalla."""
import csv
from abc import ABC, abstractmethod
from pathlib import Path

from product import UMBRAL_POCO_STOCK

RUTA_CSV = Path(__file__).resolve().parent / "reports" / "ventas.csv"


class Reporte(ABC):
    """Clase base: el menú invoca generar() sin conocer el tipo de reporte."""

    @abstractmethod
    def generar(self, inventario):
        """Produce el reporte a partir del inventario."""


class ReporteCSV(Reporte):
    """Reporte reports/ventas.csv con código, nombre, categoría, talla, color,
    precio, stock y unidades vendidas (sin compras devueltas).
    Crea la carpeta reports si no existe y devuelve la ruta generada."""

    COLUMNAS = ["codigo", "nombre", "categoria", "talla", "color",
                "precio", "stock", "unidades_vendidas"]

    def __init__(self, ruta=RUTA_CSV):
        # La ruta se puede cambiar (por ejemplo, en las pruebas usan una carpeta temporal).
        self.ruta = Path(ruta)

    def generar(self, inventario):
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        vendidas = inventario.unidades_vendidas_por_prenda()
        # newline="" evita líneas en blanco extra en Windows; utf-8 conserva la ö de NöRA.
        with self.ruta.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=self.COLUMNAS)
            escritor.writeheader()
            for prenda in inventario.listar_catalogo():
                escritor.writerow({
                    "codigo": prenda.codigo,
                    "nombre": prenda.nombre,
                    "categoria": prenda.categoria,
                    "talla": prenda.talla,
                    "color": prenda.color,
                    "precio": prenda.precio,
                    "stock": prenda.stock,
                    "unidades_vendidas": vendidas.get(prenda.codigo, 0),
                })
        return self.ruta


class ReporteTexto(Reporte):
    """Resumen en pantalla con total vendido en dinero, número de compras
    (sin devueltas), unidades vendidas y prendas con poco stock."""

    def generar(self, inventario):
        # Las compras devueltas no cuentan ni en dinero ni en número de compras.
        activas = [compra for compra in inventario.listar_todas_las_compras()
                   if not compra.devuelta]
        total = sum(compra.total for compra in activas)
        unidades = sum(inventario.unidades_vendidas_por_prenda().values())
        poco_stock = inventario.prendas_con_poco_stock()
        lineas = [
            "=== Resumen de ventas ===",
            f"Total vendido: {total:,.2f}",
            f"Número de compras: {len(activas)}",
            f"Unidades vendidas: {unidades}",
            "",
            f"Prendas con poco stock ({UMBRAL_POCO_STOCK} unidades o menos): {len(poco_stock)}",
        ]
        for prenda in poco_stock:
            lineas.append(f"  {prenda.codigo} | {prenda.nombre} | {prenda.talla} | "
                          f"{prenda.color} | stock: {prenda.stock}")
        return "\n".join(lineas)
