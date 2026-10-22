"""Pruebas del inventario: HU-002 (registrar prendas) y HU-003 (consultar catálogo).

Se agrega un grupo de pruebas por historia, con sus rechazos.
"""
import unittest

from inventory import Inventario
from product import CATEGORIAS, COLORES, ErrorValidacion

DATOS = dict(codigo="CAM-001", nombre="Camiseta básica", categoria="Camisetas",
             talla="M", color="Negro", precio="35000", stock="10")


def registrar(inventario, **cambios):
    datos = {**DATOS, **cambios}
    return inventario.registrar_prenda(**datos)


class PruebasEstadoInicial(unittest.TestCase):
    def test_inventario_nuevo_esta_vacio_y_ids_empiezan_en_1(self):
        inventario = Inventario()
        self.assertEqual(inventario.prendas, {})
        self.assertEqual(inventario.compras, {})
        self.assertEqual(inventario.siguiente_id_compra, 1)


class PruebasRegistrarPrenda(unittest.TestCase):
    def setUp(self):
        self.inventario = Inventario()

    def assertRechazada(self, **cambios):
        """La prenda se rechaza con ErrorValidacion y el catálogo no cambia."""
        with self.assertRaises(ErrorValidacion):
            registrar(self.inventario, **cambios)
        self.assertEqual(self.inventario.prendas, {})

    def test_c01_registro_exitoso(self):
        prenda = registrar(self.inventario)
        self.assertIn("CAM-001", self.inventario.prendas)
        self.assertEqual((prenda.codigo, prenda.nombre, prenda.categoria, prenda.talla,
                          prenda.color, prenda.precio, prenda.stock),
                         ("CAM-001", "Camiseta básica", "Camisetas", "M", "Negro", 35000.0, 10))

    def test_c02_codigo_duplicado_se_rechaza_y_el_catalogo_no_cambia(self):
        registrar(self.inventario)
        with self.assertRaises(ErrorValidacion):
            registrar(self.inventario, nombre="Otra camiseta", precio="99999", stock="1")
        self.assertEqual(len(self.inventario.prendas), 1)
        original = self.inventario.prendas["CAM-001"]
        self.assertEqual((original.nombre, original.precio, original.stock),
                         ("Camiseta básica", 35000.0, 10))

    def test_c03_codigo_o_nombre_vacio(self):
        for vacio in ("", "   "):
            self.assertRechazada(codigo=vacio)
            self.assertRechazada(nombre=vacio)

    def test_validar_codigo_disponible(self):
        self.assertEqual(self.inventario.validar_codigo_disponible(" CAM-001 "), "CAM-001")
        registrar(self.inventario)
        for malo in ("CAM-001", "", "cam-001", "CAM001"):
            with self.assertRaises(ErrorValidacion):
                self.inventario.validar_codigo_disponible(malo)
        self.assertEqual(len(self.inventario.prendas), 1)

    def test_codigo_con_formato_invalido(self):
        for malo in ("CAM001", "CA-001", "CAMI-001", "CAM-01", "CAM-0001", "123-ABC", "cam-001"):
            self.assertRechazada(codigo=malo)

    def test_c04_precio_invalido(self):
        for malo in ("0", "-5", "abc", "", "1e3", "nan", "inf", 0, -1, float("nan"), True):
            self.assertRechazada(precio=malo)

    def test_c05_stock_invalido(self):
        for malo in ("-1", "abc", "2.5", "", "1_0", -3, 2.0, True):
            self.assertRechazada(stock=malo)

    def test_stock_cero_es_valido(self):
        self.assertEqual(registrar(self.inventario, stock="0").stock, 0)

    def test_c06_categoria_talla_o_color_no_permitido(self):
        self.assertRechazada(categoria="Zapatos")
        self.assertRechazada(talla="XXL")
        self.assertRechazada(color="Fucsia")
        self.assertRechazada(categoria="")

    def test_c07_cada_color_valido_en_cualquier_categoria(self):
        numero = 1
        for categoria in CATEGORIAS:
            for color in COLORES:
                registrar(self.inventario, codigo=f"ABC-{numero:03d}",
                          categoria=categoria, color=color)
                numero += 1
        self.assertEqual(len(self.inventario.prendas), len(CATEGORIAS) * len(COLORES))
        vinotinto = registrar(self.inventario, codigo="VIN-001", categoria="Vestidos",
                              color="Vinotinto")
        self.assertEqual(vinotinto.color, "Vinotinto")

    def test_listas_cerradas_aceptan_mayusculas_distintas(self):
        prenda = registrar(self.inventario, categoria=" camisetas ", talla="única",
                           color="VINOTINTO")
        self.assertEqual((prenda.categoria, prenda.talla, prenda.color),
                         ("Camisetas", "Única", "Vinotinto"))


class PruebasConsultarCatalogo(unittest.TestCase):
    def setUp(self):
        self.inventario = Inventario()

    def test_c01_listado_ordenado_por_codigo_con_color(self):
        registrar(self.inventario, codigo="PAN-002", categoria="Pantalones", color="Azul")
        registrar(self.inventario, codigo="CAM-001")
        registrar(self.inventario, codigo="VES-001", categoria="Vestidos", color="Rojo")
        catalogo = self.inventario.listar_catalogo()
        self.assertEqual([p.codigo for p in catalogo], ["CAM-001", "PAN-002", "VES-001"])
        self.assertEqual([p.color for p in catalogo], ["Negro", "Azul", "Rojo"])

    def test_c02_las_prendas_agotadas_siguen_en_el_catalogo_marcadas(self):
        registrar(self.inventario, codigo="CAM-001", stock="0")
        registrar(self.inventario, codigo="CAM-002", stock="4")
        catalogo = self.inventario.listar_catalogo()
        self.assertEqual(len(catalogo), 2)
        self.assertTrue(catalogo[0].esta_agotada())
        self.assertFalse(catalogo[1].esta_agotada())

    def test_c03_filtro_por_categoria(self):
        registrar(self.inventario, codigo="CAM-001")
        registrar(self.inventario, codigo="PAN-001", categoria="Pantalones")
        registrar(self.inventario, codigo="CAM-002")
        camisetas = self.inventario.listar_catalogo("Camisetas")
        self.assertEqual([p.codigo for p in camisetas], ["CAM-001", "CAM-002"])
        self.assertEqual(self.inventario.listar_catalogo("vestidos"), [])

    def test_c03_categoria_fuera_de_la_lista_se_rechaza(self):
        registrar(self.inventario)
        with self.assertRaises(ErrorValidacion):
            self.inventario.listar_catalogo("Zapatos")

    def test_c04_catalogo_vacio(self):
        self.assertEqual(self.inventario.listar_catalogo(), [])

    def test_consultar_no_modifica_el_catalogo(self):
        registrar(self.inventario, stock="0")
        antes = dict(self.inventario.prendas)
        self.inventario.listar_catalogo()
        self.inventario.listar_catalogo("Camisetas")
        self.assertEqual(self.inventario.prendas, antes)


if __name__ == "__main__":
    unittest.main()
