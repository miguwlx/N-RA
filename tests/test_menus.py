"""Pruebas de los menús de consola (lo que ve y puede hacer cada rol)."""
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from inventory import Inventario
from storage import Almacenamiento

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

    def test_admin_consulta_el_catalogo_con_los_mismos_datos(self):
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
        texto = ejecutar(main.menu_cliente, ["2", "Pantalones", "", "", "0"], "Ana", self.inventario)
        self.assertIn("PAN-001", texto)
        self.assertNotIn("CAM-001", texto)

    def test_categoria_invalida_muestra_mensaje_y_el_programa_sigue(self):
        texto = ejecutar(main.menu_cliente, ["2", "Zapatos", "", "", "0"], "Ana", self.inventario)
        self.assertIn("no es válida", texto)
        self.assertIn("Sesión cerrada.", texto)

    def test_categoria_sin_prendas(self):
        texto = ejecutar(main.menu_cliente, ["2", "Vestidos", "", "", "0"], "Ana", self.inventario)
        self.assertIn("Ninguna prenda cumple el filtro.", texto)

    def test_catalogo_vacio(self):
        texto = ejecutar(main.menu_cliente, ["1", "0"], "Ana", Inventario())
        self.assertIn("No hay prendas registradas.", texto)


def inventario_base():
    inventario = Inventario()
    inventario.registrar_prenda("CAM-001", "Camiseta básica", "Camisetas", "M", "Negro", "35000", "10")
    inventario.registrar_prenda("PAN-001", "Jean recto", "Pantalones", "L", "Azul", "80000", "3")
    return inventario


class PruebasMenuClienteCompras(unittest.TestCase):
    """Comprar y ver mis compras desde el menú del Cliente."""

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

    def test_el_cliente_no_ve_opciones_de_admin(self):
        texto = ejecutar(main.menu_cliente, ["0"], "Ana", self.inventario)
        for prohibida in ("Devolver", "Ver todas las compras", "Actualizar precio",
                          "Reponer stock", "Registrar prenda"):
            self.assertNotIn(prohibida, texto)
        self.assertIn("Comprar una prenda", texto)
        self.assertIn("Mis compras", texto)


class PruebasMenuAdminCompras(unittest.TestCase):
    """Ver compras, devolver, cambiar precio y reponer stock desde el menú del Admin."""

    def setUp(self):
        self.inventario = inventario_base()

    def test_ver_todas_las_compras_con_cliente_y_estado(self):
        self.inventario.comprar("Ana", "CAM-001", "1")
        self.inventario.comprar("Luis", "PAN-001", "2")
        self.inventario.devolver_compra("2")
        texto = ejecutar(main.menu_admin, ["4", "0"], self.inventario)
        for dato in ("Ana", "Luis", "CAM-001", "PAN-001", "160,000.00", "Cliente", "Devuelta"):
            self.assertIn(dato, texto)
        linea_luis = [l for l in texto.splitlines() if "Luis" in l][0]
        self.assertIn("Sí", linea_luis)

    def test_ver_compras_sin_compras(self):
        """Admin, opción 4 (Ver todas las compras) sin compras registradas.

        Entradas simuladas: "4" abre el listado y "0" cierra la sesión. Debe mostrar
        "No hay compras registradas." en lugar de una tabla vacía.
        """
        texto = ejecutar(main.menu_admin, ["4", "0"], self.inventario)
        self.assertIn("No hay compras registradas.", texto)

    def test_devolver_desde_el_menu_muestra_el_listado_primero(self):
        self.inventario.comprar("Ana", "CAM-001", "4")
        texto = ejecutar(main.menu_admin, ["5", "1", "0"], self.inventario)
        self.assertIn("Ana", texto)  # listado de compras antes de pedir el identificador
        self.assertIn("Devolución registrada: compra #1. Stock de CAM-001: 10.", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 10)

    def test_repetida_inexistente_y_cancelar(self):
        self.inventario.comprar("Ana", "CAM-001", "4")
        self.inventario.devolver_compra("1")
        texto = ejecutar(main.menu_admin, ["5", "1", "99", "abc", "0", "0"], self.inventario)
        self.assertIn("La compra 1 ya fue devuelta.", texto)
        self.assertIn("No existe una compra con el identificador 99.", texto)
        self.assertIn("El identificador de la compra debe ser un número entero", texto)
        self.assertIn("Devolución cancelada.", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 10)

    def test_devolver_sin_compras(self):
        """Admin, opción 5 (Devolver una compra) sin compras registradas.

        Entradas simuladas: "5" entra a la devolución y "0" cierra la sesión. Debe avisar
        "No hay compras registradas." y volver al menú SIN pedir el identificador,
        porque no hay ninguna compra que se pueda devolver.
        """
        texto = ejecutar(main.menu_admin, ["5", "0"], self.inventario)
        self.assertIn("No hay compras registradas.", texto)
        self.assertNotIn("Identificador de la compra a devolver", texto)

    def test_actualizar_precio(self):
        texto = ejecutar(main.menu_admin, ["6", "CAM-001", "42000", "0"], self.inventario)
        self.assertIn("Precio actualizado: CAM-001 ahora cuesta 42,000.00.", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].precio, 42000.0)

    def test_precio_invalido_no_modifica(self):
        texto = ejecutar(main.menu_admin, ["6", "CAM-001", "abc", "0"], self.inventario)
        self.assertIn("No se actualizó el precio. El precio debe ser un número mayor que 0.", texto)
        self.assertEqual(self.inventario.prendas["CAM-001"].precio, 35000.0)

    def test_reponer_stock(self):
        texto = ejecutar(main.menu_admin, ["7", "PAN-001", "5", "0"], self.inventario)
        self.assertIn("Stock repuesto: PAN-001 ahora tiene 8 unidades.", texto)
        self.assertEqual(self.inventario.prendas["PAN-001"].stock, 8)

    def test_cantidad_invalida_o_prenda_inexistente(self):
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


class PruebasFiltroEnLosMenus(unittest.TestCase):
    """El filtro por talla y color existe para ambos roles."""

    def setUp(self):
        self.inventario = inventario_base()
        self.inventario.registrar_prenda("CAM-002", "Polo", "Camisetas", "L", "Azul", "60000", "4")

    def filtrar(self, menu, entradas, *args):
        return ejecutar(menu, entradas, *args, self.inventario)

    def test_ambos_menus_ofrecen_filtrar_el_catalogo(self):
        self.assertIn("Filtrar catálogo", ejecutar(main.menu_cliente, ["0"], "Ana", self.inventario))
        self.assertIn("Filtrar catálogo", ejecutar(main.menu_admin, ["0"], self.inventario))

    def test_el_cliente_filtra_por_talla(self):
        texto = ejecutar(main.menu_cliente, ["2", "", "L", "", "0"], "Ana", self.inventario)
        self.assertIn("PAN-001", texto)
        self.assertIn("CAM-002", texto)
        self.assertNotIn("CAM-001", texto)

    def test_el_admin_filtra_por_color(self):
        texto = ejecutar(main.menu_admin, ["3", "", "", "Azul", "0"], self.inventario)
        self.assertIn("PAN-001", texto)
        self.assertIn("CAM-002", texto)
        self.assertNotIn("CAM-001", texto)

    def test_combinar_categoria_talla_y_color(self):
        texto = ejecutar(main.menu_cliente, ["2", "camisetas", "l", "azul", "0"], "Ana", self.inventario)
        self.assertIn("CAM-002", texto)
        self.assertNotIn("PAN-001", texto)

    def test_talla_o_color_no_permitido_muestra_mensaje_y_no_cierra(self):
        for entradas, esperado in ((["2", "", "XXL", "", "0"], "La talla 'XXL' no es válida"),
                                   (["2", "", "", "Morado", "0"], "El color 'Morado' no es válido")):
            texto = ejecutar(main.menu_cliente, entradas, "Ana", self.inventario)
            self.assertIn(esperado, texto)
            self.assertIn("Sesión cerrada.", texto)

    def test_sin_coincidencias(self):
        texto = ejecutar(main.menu_cliente, ["2", "", "XL", "", "0"], "Ana", self.inventario)
        self.assertIn("Ninguna prenda cumple el filtro.", texto)

    def test_sin_ningun_filtro_muestra_el_catalogo_completo(self):
        texto = ejecutar(main.menu_cliente, ["2", "", "", "", "0"], "Ana", self.inventario)
        for codigo in ("CAM-001", "CAM-002", "PAN-001"):
            self.assertIn(codigo, texto)

    def test_catalogo_vacio_sin_filtros(self):
        texto = ejecutar(main.menu_cliente, ["2", "", "", "", "0"], "Ana", Inventario())
        self.assertIn("No hay prendas registradas.", texto)


class PruebasEntradasInvalidasEnLosMenus(unittest.TestCase):
    """Ningún texto inesperado cierra el programa."""

    def setUp(self):
        self.inventario = inventario_base()
        self.inventario.comprar("Ana", "CAM-001", "1")

    def test_opcion_desconocida_en_los_tres_menus(self):
        for malas in (["99"], ["abc"], [""], ["-1"], ["1.5"], ["  "]):
            principal = ejecutar(main.ciclo_principal, malas + ["3"], self.inventario, None)
            cliente = ejecutar(main.menu_cliente, malas + ["0"], "Ana", self.inventario)
            admin = ejecutar(main.menu_admin, malas + ["0"], self.inventario)
            for texto in (principal, cliente, admin):
                self.assertIn("Opción no válida. Elige una opción del menú.", texto)

    def test_texto_donde_se_espera_un_numero_informa_y_sigue(self):
        admin = ejecutar(main.menu_admin, [
            "5", "abc", "0",                 # identificador de compra
            "6", "CAM-001", "abc",           # precio
            "7", "CAM-001", "abc",           # unidades a reponer
            "1", "NUE-001", "Camisa", "Camisetas", "M", "Negro", "abc", "5",   # precio al registrar
            "1", "NUE-001", "Camisa", "Camisetas", "M", "Negro", "100", "abc",  # stock al registrar
            "0"], self.inventario)
        cliente = ejecutar(main.menu_cliente, ["3", "CAM-001", "abc", "0"], "Ana", self.inventario)
        for texto, esperados in (
                (admin, ("El identificador de la compra debe ser un número entero",
                         "El precio debe ser un número mayor que 0",
                         "La cantidad debe ser un número entero mayor que 0",
                         "El stock debe ser un número entero mayor o igual a 0")),
                (cliente, ("La cantidad debe ser un número entero mayor que 0",))):
            for esperado in esperados:
                self.assertIn(esperado, texto)
            self.assertIn("Sesión cerrada.", texto)
        self.assertNotIn("NUE-001", self.inventario.prendas)

    def test_cerrar_la_entrada_no_deja_el_programa_con_un_error_feo(self):
        salida = io.StringIO()
        with patch("builtins.input", side_effect=["1", EOFError()]), patch("sys.stdout", salida):
            main.main(Almacenamiento(Path(tempfile.mkdtemp()) / "state.json"))
        self.assertIn("Programa terminado.", salida.getvalue())

    def test_ctrl_c_termina_de_forma_limpia(self):
        salida = io.StringIO()
        with patch("builtins.input", side_effect=KeyboardInterrupt), patch("sys.stdout", salida):
            main.main(Almacenamiento(Path(tempfile.mkdtemp()) / "state.json"))
        self.assertIn("Programa terminado.", salida.getvalue())


class PruebasControlDeAccesoCompleto(unittest.TestCase):
    """Control de acceso completo: lo que ve cada rol."""

    def setUp(self):
        self.inventario = inventario_base()

    def test_el_cliente_solo_tiene_sus_cuatro_opciones(self):
        texto = ejecutar(main.menu_cliente, ["0"], "Ana", self.inventario)
        for permitida in ("Ver catálogo", "Filtrar catálogo", "Comprar una prenda", "Mis compras"):
            self.assertIn(permitida, texto)
        for prohibida in ("Registrar", "Devolver", "Ver todas las compras", "Actualizar precio",
                          "Reponer stock", "Exportar", "reporte", "Reporte"):
            self.assertNotIn(prohibida, texto)

    def test_el_admin_tiene_todas_sus_opciones(self):
        texto = ejecutar(main.menu_admin, ["0"], self.inventario)
        for opcion in ("Registrar prenda", "Ver catálogo", "Filtrar catálogo", "Ver todas las compras",
                       "Devolver una compra", "Actualizar precio", "Reponer stock",
                       "Exportar CSV", "Ver reporte", "Cerrar sesión"):
            self.assertIn(opcion, texto)


if __name__ == "__main__":
    unittest.main()
