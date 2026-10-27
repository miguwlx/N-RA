"""Pruebas de los reportes: CSV de ventas y resumen en pantalla."""
import csv
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from inventory import Inventario
from reports import Reporte, ReporteCSV, ReporteTexto


def ejecutar(funcion, entradas, *args):
    salida = io.StringIO()
    with patch("builtins.input", side_effect=entradas), patch("sys.stdout", salida):
        funcion(*args)
    return salida.getvalue()


class BaseConInventario(unittest.TestCase):
    def setUp(self):
        self.carpeta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.carpeta, ignore_errors=True)
        self.inventario = Inventario()
        self.inventario.registrar_prenda("CAM-001", "Camiseta", "Camisetas", "M", "Negro", "50000", "10")
        self.inventario.registrar_prenda("PAN-001", "Jean", "Pantalones", "L", "Azul", "90000", "5")
        self.inventario.registrar_prenda("ACC-001", "Gorra", "Accesorios", "Única", "Blanco", "25000", "0")
        self.inventario.registrar_prenda("VES-001", "Vestido", "Vestidos", "S", "Rojo", "30000", "6")


class PruebasReporteCSV(BaseConInventario):
    """Reporte CSV de ventas."""

    def filas(self, ruta):
        with Path(ruta).open(encoding="utf-8", newline="") as archivo:
            return list(csv.DictReader(archivo))

    def generar(self):
        return ReporteCSV(self.carpeta / "ventas.csv").generar(self.inventario)

    def test_columnas_y_valores(self):
        self.inventario.comprar("Ana", "CAM-001", "3")
        filas = self.filas(self.generar())
        self.assertEqual(list(filas[0].keys()), ["codigo", "nombre", "categoria", "talla", "color",
                                                 "precio", "stock", "unidades_vendidas"])
        camiseta = [f for f in filas if f["codigo"] == "CAM-001"][0]
        self.assertEqual((camiseta["nombre"], camiseta["categoria"], camiseta["talla"], camiseta["color"]),
                         ("Camiseta", "Camisetas", "M", "Negro"))
        self.assertEqual((camiseta["stock"], camiseta["unidades_vendidas"]), ("7", "3"))
        jean = [f for f in filas if f["codigo"] == "PAN-001"][0]
        self.assertEqual(jean["unidades_vendidas"], "0")

    def test_filas_ordenadas_por_codigo_e_incluye_las_agotadas(self):
        codigos = [f["codigo"] for f in self.filas(self.generar())]
        self.assertEqual(codigos, ["ACC-001", "CAM-001", "PAN-001", "VES-001"])

    def test_las_compras_devueltas_no_cuentan(self):
        compra = self.inventario.comprar("Ana", "CAM-001", "3")
        self.inventario.comprar("Luis", "CAM-001", "2")
        self.inventario.devolver_compra(compra.id_compra)
        camiseta = [f for f in self.filas(self.generar()) if f["codigo"] == "CAM-001"][0]
        self.assertEqual((camiseta["unidades_vendidas"], camiseta["stock"]), ("2", "8"))

    def test_las_unidades_de_varias_compras_se_suman(self):
        self.inventario.comprar("Ana", "CAM-001", "3")
        self.inventario.comprar("Luis", "CAM-001", "2")
        camiseta = [f for f in self.filas(self.generar()) if f["codigo"] == "CAM-001"][0]
        self.assertEqual(camiseta["unidades_vendidas"], "5")

    def test_crea_la_carpeta_y_devuelve_la_ruta(self):
        ruta = self.carpeta / "reports" / "ventas.csv"
        self.assertFalse(ruta.parent.exists())
        resultado = ReporteCSV(ruta).generar(self.inventario)
        self.assertTrue(ruta.exists())
        self.assertEqual(resultado, ruta)

    def test_hereda_de_la_clase_base(self):
        self.assertTrue(issubclass(ReporteCSV, Reporte))
        with self.assertRaises(TypeError):
            Reporte()  # la base es abstracta: no se usa directamente

    def test_conserva_los_caracteres_especiales(self):
        self.inventario.registrar_prenda("CAM-002", "Camisa NöRA", "Camisetas", "S", "Rojo", "70000", "4")
        nombres = [f["nombre"] for f in self.filas(self.generar())]
        self.assertIn("Camisa NöRA", nombres)

    def test_inventario_vacio_genera_solo_el_encabezado(self):
        ruta = ReporteCSV(self.carpeta / "vacio.csv").generar(Inventario())
        self.assertEqual(self.filas(ruta), [])
        self.assertTrue(Path(ruta).read_text(encoding="utf-8").startswith("codigo,"))


class PruebasReporteTexto(BaseConInventario):
    """Resumen de ventas en pantalla."""

    def texto(self):
        return ReporteTexto().generar(self.inventario)

    def test_total_en_dinero_y_numero_de_compras(self):
        self.inventario.comprar("Ana", "CAM-001", "2")
        self.inventario.comprar("Luis", "VES-001", "1")
        texto = self.texto()
        self.assertIn("Total vendido: 130,000.00", texto)
        self.assertIn("Número de compras: 2", texto)
        self.assertIn("Unidades vendidas: 3", texto)

    def test_las_compras_devueltas_no_cuentan_ni_en_dinero_ni_en_numero(self):
        devuelta = self.inventario.comprar("Ana", "CAM-001", "2")
        self.inventario.comprar("Luis", "VES-001", "1")
        self.inventario.devolver_compra(devuelta.id_compra)
        texto = self.texto()
        self.assertIn("Total vendido: 30,000.00", texto)
        self.assertIn("Número de compras: 1", texto)
        self.assertIn("Unidades vendidas: 1", texto)

    def test_poco_stock_incluye_cinco_y_cero_pero_no_seis(self):
        texto = self.texto()
        self.assertIn("PAN-001 | Jean | L | Azul | stock: 5", texto)
        self.assertIn("ACC-001 | Gorra | Única | Blanco | stock: 0", texto)
        self.assertNotIn("VES-001", texto)   # stock 6
        self.assertNotIn("CAM-001", texto)   # stock 10
        self.assertIn("(5 unidades o menos): 2", texto)

    def test_una_compra_puede_dejar_una_prenda_con_poco_stock(self):
        self.inventario.comprar("Ana", "CAM-001", "5")  # 10 -> 5
        self.assertIn("CAM-001 | Camiseta | M | Negro | stock: 5", self.texto())

    def test_sin_ventas_muestra_ceros_sin_errores(self):
        texto = self.texto()
        self.assertIn("Total vendido: 0.00", texto)
        self.assertIn("Número de compras: 0", texto)
        self.assertIn("Unidades vendidas: 0", texto)

    def test_inventario_vacio_no_falla(self):
        texto = ReporteTexto().generar(Inventario())
        self.assertIn("Número de compras: 0", texto)
        self.assertIn("poco stock (5 unidades o menos): 0", texto)

    def test_las_unidades_coinciden_con_el_csv(self):
        self.inventario.comprar("Ana", "CAM-001", "2")
        devuelta = self.inventario.comprar("Luis", "VES-001", "1")
        self.inventario.comprar("Marta", "PAN-001", "3")
        self.inventario.devolver_compra(devuelta.id_compra)
        ruta = ReporteCSV(self.carpeta / "ventas.csv").generar(self.inventario)
        with Path(ruta).open(encoding="utf-8", newline="") as archivo:
            unidades_csv = sum(int(f["unidades_vendidas"]) for f in csv.DictReader(archivo))
        linea = [l for l in self.texto().splitlines() if l.startswith("Unidades vendidas:")][0]
        self.assertEqual(int(linea.split(":")[1]), unidades_csv)
        self.assertEqual(unidades_csv, 5)

    def test_hereda_de_la_clase_base_y_comparte_la_operacion_generar(self):
        self.assertTrue(issubclass(ReporteTexto, Reporte))
        self.inventario.comprar("Ana", "CAM-001", "1")
        for reporte in (ReporteCSV(self.carpeta / "ventas.csv"), ReporteTexto()):
            resultado = reporte.generar(self.inventario)  # misma operación, distinto resultado
            self.assertTrue(isinstance(resultado, (Path, str)))


class PruebasMenusDeReportes(BaseConInventario):
    """Exportar CSV y ver el resumen desde el menú del Admin."""

    def test_admin_exporta_el_csv_y_ve_la_ruta(self):
        ruta = self.carpeta / "reports" / "ventas.csv"
        with patch.object(main, "ReporteCSV", lambda: ReporteCSV(ruta)):
            texto = ejecutar(main.menu_admin, ["8", "0"], self.inventario)
        self.assertIn(f"Reporte exportado en: {ruta}", texto)
        self.assertTrue(ruta.exists())

    def test_si_no_se_puede_escribir_el_csv_avisa_y_no_cierra_el_programa(self):
        ocupada = self.carpeta / "ventas.csv"
        ocupada.mkdir()   # una carpeta ocupa el nombre del archivo
        with patch.object(main, "ReporteCSV", lambda: ReporteCSV(ocupada)):
            texto = ejecutar(main.menu_admin, ["8", "0"], self.inventario)
        self.assertIn("No se pudo exportar el reporte", texto)
        self.assertIn("Sesión cerrada.", texto)

    def test_admin_ve_el_resumen_en_pantalla(self):
        self.inventario.comprar("Ana", "CAM-001", "2")
        texto = ejecutar(main.menu_admin, ["9", "0"], self.inventario)
        self.assertIn("Total vendido: 100,000.00", texto)
        self.assertIn("Número de compras: 1", texto)

    def test_el_cliente_no_tiene_exportar_ni_reporte(self):
        texto = ejecutar(main.menu_cliente, ["0"], "Ana", self.inventario)
        for prohibida in ("Exportar", "CSV", "reporte", "Reporte"):
            self.assertNotIn(prohibida, texto)

    def test_el_cliente_no_puede_ejecutar_las_opciones_8_y_9(self):
        texto = ejecutar(main.menu_cliente, ["8", "9", "0"], "Ana", self.inventario)
        self.assertEqual(texto.count("Opción no válida"), 2)
        self.assertNotIn("Total vendido", texto)


if __name__ == "__main__":
    unittest.main()
