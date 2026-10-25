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

    def test_codigo_en_minuscula_se_registra_en_mayuscula(self):
        datos = ["cam-001"] + REGISTRO_VALIDO[1:]
        texto = ejecutar(main.menu_admin, ["1"] + datos + ["0"], self.inventario)
        self.assertIn("Prenda registrada correctamente: CAM-001", texto)
        self.assertEqual(list(self.inventario.prendas), ["CAM-001"])

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


def inventario_base():
    inventario = Inventario()
    inventario.registrar_prenda("CAM-001", "Camiseta básica", "Camisetas", "M", "Negro", "35000", "10")
    inventario.registrar_prenda("PAN-001", "Jean recto", "Pantalones", "L", "Azul", "80000", "3")
    return inventario


class PruebasMenuClienteCompras(unittest.TestCase):
    """HU-004 y HU-005 desde el menú del Cliente."""

    def setUp(self):
        self.inventario = inventario_base()

    def test_comprar_desde_el_menu(self):
        texto = ejecutar(main.menu_cliente, ["3", "CAM-001", "2", "0"], "Ana", self.inventario)
        self.assertIn("Compra registrada: #1", texto)
        self.assertIn("70,000.00", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 8)
        self.assertEqual(self.inventario.compras[1].cliente, "Ana")

    def test_comprar_con_el_codigo_en_minuscula(self):
        texto = ejecutar(main.menu_cliente, ["3", "cam-001", "1", "0"], "Ana", self.inventario)
        self.assertIn("Compra registrada: #1", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 9)

    def test_codigo_inexistente_se_vuelve_a_pedir_y_cero_cancela(self):
        texto = ejecutar(main.menu_cliente, ["3", "ZZZ-999", "0", "0"], "Ana", self.inventario)
        self.assertIn("No existe una prenda con el código ZZZ-999.", texto)
        self.assertIn("Operación cancelada.", texto)
        self.assertNotIn("Cantidad:", texto)
        self.assertEqual(self.inventario.compras, {})

    def test_cantidad_invalida_no_cierra_el_programa_ni_cambia_nada(self):
        for mala in ("0", "-1", "abc", "2.5"):
            inventario = inventario_base()
            texto = ejecutar(main.menu_cliente, ["3", "CAM-001", mala, "0"], "Ana", inventario)
            self.assertIn("No se registró la compra. La cantidad debe ser un número entero mayor que 0.", texto)
            self.assertIn("Sesión cerrada.", texto)
            self.assertEqual((inventario.prendas["CAM-001"].stock, inventario.compras), (10, {}))

    def test_stock_insuficiente_muestra_el_motivo(self):
        texto = ejecutar(main.menu_cliente, ["3", "PAN-001", "9", "0"], "Ana", self.inventario)
        self.assertIn("Stock insuficiente de PAN-001: hay 3 unidad(es) disponible(s).", texto)
        self.assertEqual(self.inventario.prendas["PAN-001"].stock, 3)

    def test_mis_compras_muestra_solo_las_propias_con_su_detalle(self):
        self.inventario.comprar("Ana", "CAM-001", "1")
        self.inventario.comprar("Luis", "PAN-001", "2")
        self.inventario.devolver_compra("1")
        texto = ejecutar(main.menu_cliente, ["4", "0"], "Ana", self.inventario)
        for dato in ("CAM-001 - Camiseta básica", "35,000.00", "Sí", "Devuelta", "Total"):
            self.assertIn(dato, texto)
        self.assertNotIn("PAN-001", texto)
        self.assertNotIn("Luis", texto)

    def test_mis_compras_sin_compras(self):
        self.inventario.comprar("Luis", "PAN-001", "1")
        texto = ejecutar(main.menu_cliente, ["4", "0"], "Ana", self.inventario)
        self.assertIn("Aún no tienes compras.", texto)

    def test_hu006_c04_hu011_c04_el_cliente_no_ve_opciones_de_admin(self):
        texto = ejecutar(main.menu_cliente, ["0"], "Ana", self.inventario)
        for prohibida in ("Devolver", "Ver todas las compras", "Actualizar precio",
                          "Reponer stock", "Registrar prenda"):
            self.assertNotIn(prohibida, texto)
        self.assertIn("Comprar una prenda", texto)
        self.assertIn("Mis compras", texto)


class PruebasMenuAdminCompras(unittest.TestCase):
    """HU-006, HU-007 y HU-011 desde el menú del Admin."""

    def setUp(self):
        self.inventario = inventario_base()

    def test_hu011_ver_todas_las_compras_con_cliente_y_estado(self):
        self.inventario.comprar("Ana", "CAM-001", "1")
        self.inventario.comprar("Luis", "PAN-001", "2")
        self.inventario.devolver_compra("2")
        texto = ejecutar(main.menu_admin, ["4", "0"], self.inventario)
        for dato in ("Ana", "Luis", "CAM-001", "PAN-001", "160,000.00", "Cliente", "Devuelta"):
            self.assertIn(dato, texto)
        linea_luis = [l for l in texto.splitlines() if "Luis" in l][0]
        self.assertIn("Sí", linea_luis)

    def test_hu011_c03_sin_compras(self):
        texto = ejecutar(main.menu_admin, ["4", "0"], self.inventario)
        self.assertIn("No hay compras registradas.", texto)

    def test_hu006_devolver_desde_el_menu_muestra_el_listado_primero(self):
        self.inventario.comprar("Ana", "CAM-001", "4")
        texto = ejecutar(main.menu_admin, ["5", "1", "0"], self.inventario)
        self.assertIn("Ana", texto)  # listado de HU-011 antes de pedir el identificador
        self.assertIn("Devolución registrada: compra #1. Stock de CAM-001: 10.", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 10)

    def test_hu006_repetida_inexistente_y_cancelar(self):
        self.inventario.comprar("Ana", "CAM-001", "4")
        self.inventario.devolver_compra("1")
        texto = ejecutar(main.menu_admin, ["5", "1", "99", "abc", "0", "0"], self.inventario)
        self.assertIn("La compra 1 ya fue devuelta.", texto)
        self.assertIn("No existe una compra con el identificador 99.", texto)
        self.assertIn("El identificador de la compra debe ser un número entero", texto)
        self.assertIn("Devolución cancelada.", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 10)

    def test_hu006_sin_compras(self):
        texto = ejecutar(main.menu_admin, ["5", "0"], self.inventario)
        self.assertIn("No hay compras registradas.", texto)
        self.assertNotIn("Identificador de la compra a devolver", texto)

    def test_hu007_actualizar_precio(self):
        texto = ejecutar(main.menu_admin, ["6", "CAM-001", "42000", "0"], self.inventario)
        self.assertIn("Precio actualizado: CAM-001 ahora cuesta 42,000.00.", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].precio, 42000.0)

    def test_hu007_precio_invalido_no_modifica(self):
        texto = ejecutar(main.menu_admin, ["6", "CAM-001", "abc", "0"], self.inventario)
        self.assertIn("No se actualizó el precio. El precio debe ser un número mayor que 0.", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].precio, 35000.0)

    def test_hu007_reponer_stock(self):
        texto = ejecutar(main.menu_admin, ["7", "PAN-001", "5", "0"], self.inventario)
        self.assertIn("Stock repuesto: PAN-001 ahora tiene 8 unidades.", texto)
        self.assertEqual(self.inventario.prendas["PAN-001"].stock, 8)

    def test_hu007_cantidad_invalida_o_prenda_inexistente(self):
        texto = ejecutar(main.menu_admin, ["7", "PAN-001", "0", "7", "ZZZ-999", "0", "0"],
                         self.inventario)
        self.assertIn("No se repuso el stock. La cantidad debe ser un número entero mayor que 0.", texto)
        self.assertIn("No existe una prenda con el código ZZZ-999.", texto)
        self.assertEqual(self.inventario.prendas["PAN-001"].stock, 3)

    def test_flujo_completo_comprar_devolver_y_ver_el_stock(self):
        ejecutar(main.menu_cliente, ["3", "CAM-001", "10", "0"], "Ana", self.inventario)
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 0)
        ejecutar(main.menu_admin, ["5", "1", "0"], self.inventario)
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 10)


if __name__ == "__main__":
    unittest.main()
