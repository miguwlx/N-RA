"""Pruebas de menús para HU-002 y HU-003 (lo que ve cada rol en consola)."""
import io
import unittest
from unittest.mock import patch

import main
from inventory import Inventario

REGISTRO_VALIDO = ["CAM-001", "Camiseta básica", "Camisetas", "M", "Negro", "35000", "10"]


def ejecutar(funcion, entradas, *args):
    salida = io.StringIO()
    with patch("builtins.input", side_effect=entradas), patch("sys.stdout", salida):
        funcion(*args)
    return salida.getvalue()


class PruebasMenuAdmin(unittest.TestCase):
    def setUp(self):
        self.inventario = Inventario()

    def test_registrar_prenda_desde_el_menu(self):
        texto = ejecutar(main.menu_admin, ["1"] + REGISTRO_VALIDO + ["0"], self.inventario)
        self.assertIn("Prenda registrada correctamente: CAM-001", texto)
        self.assertIn("CAM-001", self.inventario.prendas)

    def test_cero_en_el_codigo_cancela_el_registro(self):
        texto = ejecutar(main.menu_admin, ["1", "0", "0"], self.inventario)
        self.assertIn("Registro cancelado.", texto)
        self.assertNotIn("Nombre:", texto)
        self.assertEqual(self.inventario.prendas, {})

    def test_codigo_repetido_se_avisa_al_escribirlo_sin_pedir_mas_datos(self):
        self.inventario.registrar_prenda("PAN-002", "Pantalon", "Pantalones",
                                         "M", "Azul", "15000", "15")
        texto = ejecutar(main.menu_admin, ["1", "PAN-002", "0", "0"], self.inventario)
        self.assertIn("Ya existe una prenda con el código PAN-002.", texto)
        self.assertNotIn("Nombre:", texto)
        self.assertIn("Registro cancelado.", texto)
        self.assertEqual(len(self.inventario.prendas), 1)

    def test_codigo_invalido_se_vuelve_a_pedir_y_luego_registra(self):
        entradas = ["1", "XX", REGISTRO_VALIDO[0]] + REGISTRO_VALIDO[1:] + ["0"]
        texto = ejecutar(main.menu_admin, entradas, self.inventario)
        self.assertIn("no es válido", texto)
        self.assertIn("Prenda registrada correctamente: CAM-001", texto)

    def test_registro_rechazado_muestra_mensaje_y_no_cierra_el_programa(self):
        datos = REGISTRO_VALIDO[:5] + ["abc", "10"]  # precio inválido
        texto = ejecutar(main.menu_admin, ["1"] + datos + ["0"], self.inventario)
        self.assertIn("No se registró la prenda", texto)
        self.assertIn("El precio debe ser un número mayor que 0", texto)
        self.assertIn("Sesión cerrada.", texto)
        self.assertEqual(self.inventario.prendas, {})

    def test_hu003_c05_admin_consulta_el_catalogo_con_los_mismos_datos(self):
        self.inventario.registrar_prenda("CAM-001", "Camiseta básica", "Camisetas",
                                         "M", "Negro", "35000", "10")
        texto = ejecutar(main.menu_admin, ["2", "0"], self.inventario)
        for dato in ("CAM-001", "Camiseta básica", "Camisetas", "M", "Negro", "35,000.00", "10"):
            self.assertIn(dato, texto)


class PruebasMenuCliente(unittest.TestCase):
    def setUp(self):
        self.inventario = Inventario()
        self.inventario.registrar_prenda("CAM-001", "Camiseta básica", "Camisetas",
                                         "M", "Negro", "35000", "0")
        self.inventario.registrar_prenda("PAN-001", "Jean recto", "Pantalones",
                                         "L", "Azul", "80000", "3")

    def test_cliente_no_tiene_la_opcion_de_registrar_prendas(self):
        texto = ejecutar(main.menu_cliente, ["0"], "Ana", self.inventario)
        self.assertNotIn("Registrar prenda", texto)
        self.assertNotIn("Admin", texto)

    def test_cliente_ve_el_catalogo_con_las_agotadas_marcadas(self):
        texto = ejecutar(main.menu_cliente, ["1", "0"], "Ana", self.inventario)
        self.assertIn("CAM-001", texto)
        self.assertIn("PAN-001", texto)
        self.assertEqual(texto.count("AGOTADA"), 1)
        linea_camiseta = [l for l in texto.splitlines() if "CAM-001" in l][0]
        self.assertIn("AGOTADA", linea_camiseta)

    def test_cliente_filtra_por_categoria(self):
        texto = ejecutar(main.menu_cliente, ["2", "Pantalones", "0"], "Ana", self.inventario)
        self.assertIn("PAN-001", texto)
        self.assertNotIn("CAM-001", texto)

    def test_categoria_invalida_muestra_mensaje_y_el_programa_sigue(self):
        texto = ejecutar(main.menu_cliente, ["2", "Zapatos", "0"], "Ana", self.inventario)
        self.assertIn("no es válida", texto)
        self.assertIn("Sesión cerrada.", texto)

    def test_categoria_sin_prendas(self):
        texto = ejecutar(main.menu_cliente, ["2", "Vestidos", "0"], "Ana", self.inventario)
        self.assertIn("No hay prendas en la categoría Vestidos.", texto)

    def test_hu003_c04_catalogo_vacio(self):
        texto = ejecutar(main.menu_cliente, ["1", "0"], "Ana", Inventario())
        self.assertIn("No hay prendas registradas.", texto)


if __name__ == "__main__":
    unittest.main()
