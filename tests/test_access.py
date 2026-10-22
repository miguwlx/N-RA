"""Pruebas de HU-001: ingreso según el rol (una por criterio de aceptación)."""
import io
import unittest
from unittest.mock import patch

import main
from inventory import Inventario
from product import ErrorValidacion


def ejecutar(funcion, entradas, *args):
    """Corre una función simulando lo que la persona escribe; devuelve lo impreso."""
    salida = io.StringIO()
    with patch("builtins.input", side_effect=entradas), patch("sys.stdout", salida):
        funcion(*args)
    return salida.getvalue()


class PruebasAcceso(unittest.TestCase):
    def test_c01_menu_principal_ofrece_cliente_admin_salir(self):
        texto = ejecutar(main.main, ["3"])
        for opcion in ("Cliente", "Admin", "Salir"):
            self.assertIn(opcion, texto)

    def test_c02_cliente_con_nombre_valido_accede_sin_opciones_admin(self):
        texto = ejecutar(main.main, ["1", "Ana", "0", "3"])
        self.assertIn("Menú Cliente: Ana", texto)
        self.assertNotIn("Menú Admin", texto)
        menu = ejecutar(main.menu_cliente, ["0"], "Ana", Inventario())
        self.assertNotIn("Admin", menu)

    def test_c03_nombre_vacio_se_rechaza_con_mensaje(self):
        for vacio in ("", "   "):
            with self.assertRaises(ErrorValidacion):
                main.validar_nombre_cliente(vacio)
        texto = ejecutar(main.main, ["1", "", "3"])
        self.assertIn("El nombre no puede estar vacío", texto)
        self.assertNotIn("Menú Cliente", texto)

    def test_c04_admin_con_clave_correcta_accede(self):
        texto = ejecutar(main.main, ["2", main.CLAVE_ADMIN, "0", "3"])
        self.assertIn("Menú Admin", texto)

    def test_c05_clave_incorrecta_se_rechaza_sin_mostrar_menu_admin(self):
        for mala in ("", "abc", main.CLAVE_ADMIN + "0"):
            with self.assertRaises(ErrorValidacion):
                main.validar_clave_admin(mala)
        texto = ejecutar(main.main, ["2", "mala", "3"])
        self.assertIn("Clave incorrecta", texto)
        self.assertNotIn("Menú Admin", texto)

    def test_c06_cerrar_sesion_vuelve_al_menu_principal(self):
        for entradas in (["1", "Ana", "0", "3"], ["2", main.CLAVE_ADMIN, "0", "3"]):
            texto = ejecutar(main.main, entradas)
            self.assertIn("Sesión cerrada.", texto)
            self.assertEqual(texto.count("=== NöRA ==="), 2)  # antes y después de cerrar sesión

    def test_opcion_desconocida_no_cierra_el_programa(self):
        texto = ejecutar(main.main, ["9", "3"])
        self.assertIn("Opción no válida", texto)
        self.assertIn("Hasta pronto.", texto)


if __name__ == "__main__":
    unittest.main()
