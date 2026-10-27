"""Pruebas del inventario: registro, catálogo, compras, devoluciones, mantenimiento,
filtros y datos para reportes.

Cada grupo de pruebas cubre una funcionalidad, con sus casos de rechazo.
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

    def test_registro_exitoso(self):
        prenda = registrar(self.inventario)
        self.assertIn("CAM-001", self.inventario.prendas)
        self.assertEqual((prenda.codigo, prenda.nombre, prenda.categoria, prenda.talla,
                          prenda.color, prenda.precio, prenda.stock),
                         ("CAM-001", "Camiseta básica", "Camisetas", "M", "Negro", 35000.0, 10))

    def test_codigo_duplicado_se_rechaza_y_el_catalogo_no_cambia(self):
        registrar(self.inventario)
        with self.assertRaises(ErrorValidacion):
            registrar(self.inventario, nombre="Otra camiseta", precio="99999", stock="1")
        self.assertEqual(len(self.inventario.prendas), 1)
        original = self.inventario.prendas["CAM-001"]
        self.assertEqual((original.nombre, original.precio, original.stock),
                         ("Camiseta básica", 35000.0, 10))

    def test_codigo_o_nombre_vacio(self):
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
        for malo in ("CAM001", "CA-001", "CAMI-001", "CAM-01", "CAM-0001", "123-ABC",
                     "CAM_001", "CAM-00A", "CA1-001", "CAM-\u0660\u0660\u0661", "\u00dfa-001"):
            self.assertRechazada(codigo=malo)

    def test_codigo_en_minuscula_se_acepta_y_se_guarda_en_mayuscula(self):
        prenda = registrar(self.inventario, codigo="  cam-001 ")
        self.assertEqual(prenda.codigo, "CAM-001")
        self.assertEqual(list(self.inventario.prendas), ["CAM-001"])

    def test_el_mismo_codigo_con_otra_escritura_cuenta_como_duplicado(self):
        registrar(self.inventario, codigo="CAM-001")
        for escritura in ("cam-001", "Cam-001", " CAM-001 "):
            with self.assertRaises(ErrorValidacion):
                registrar(self.inventario, codigo=escritura)
        self.assertEqual(list(self.inventario.prendas), ["CAM-001"])

    def test_obtener_prenda_no_distingue_mayusculas(self):
        registrar(self.inventario, codigo="CAM-001")
        self.assertIs(self.inventario.obtener_prenda("cam-001"),
                      self.inventario.prendas["CAM-001"])

    def test_precio_invalido(self):
        for malo in ("0", "-5", "abc", "", "1e3", "nan", "inf", 0, -1, float("nan"), True):
            self.assertRechazada(precio=malo)

    def test_stock_invalido(self):
        for malo in ("-1", "abc", "2.5", "", "1_0", -3, 2.0, True):
            self.assertRechazada(stock=malo)

    def test_stock_cero_es_valido(self):
        self.assertEqual(registrar(self.inventario, stock="0").stock, 0)

    def test_categoria_talla_o_color_no_permitido(self):
        self.assertRechazada(categoria="Zapatos")
        self.assertRechazada(talla="XXL")
        self.assertRechazada(color="Fucsia")
        self.assertRechazada(categoria="")

    def test_cada_color_valido_en_cualquier_categoria(self):
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

    def test_listado_ordenado_por_codigo_con_color(self):
        registrar(self.inventario, codigo="PAN-002", categoria="Pantalones", color="Azul")
        registrar(self.inventario, codigo="CAM-001")
        registrar(self.inventario, codigo="VES-001", categoria="Vestidos", color="Rojo")
        catalogo = self.inventario.listar_catalogo()
        self.assertEqual([p.codigo for p in catalogo], ["CAM-001", "PAN-002", "VES-001"])
        self.assertEqual([p.color for p in catalogo], ["Negro", "Azul", "Rojo"])

    def test_las_prendas_agotadas_siguen_en_el_catalogo_marcadas(self):
        registrar(self.inventario, codigo="CAM-001", stock="0")
        registrar(self.inventario, codigo="CAM-002", stock="4")
        catalogo = self.inventario.listar_catalogo()
        self.assertEqual(len(catalogo), 2)
        self.assertTrue(catalogo[0].esta_agotada())
        self.assertFalse(catalogo[1].esta_agotada())

    def test_filtro_por_categoria(self):
        registrar(self.inventario, codigo="CAM-001")
        registrar(self.inventario, codigo="PAN-001", categoria="Pantalones")
        registrar(self.inventario, codigo="CAM-002")
        camisetas = self.inventario.listar_catalogo("Camisetas")
        self.assertEqual([p.codigo for p in camisetas], ["CAM-001", "CAM-002"])
        self.assertEqual(self.inventario.listar_catalogo("vestidos"), [])

    def test_categoria_fuera_de_la_lista_se_rechaza(self):
        registrar(self.inventario)
        with self.assertRaises(ErrorValidacion):
            self.inventario.listar_catalogo("Zapatos")

    def test_catalogo_vacio(self):
        self.assertEqual(self.inventario.listar_catalogo(), [])

    def test_consultar_no_modifica_el_catalogo(self):
        registrar(self.inventario, stock="0")
        antes = dict(self.inventario.prendas)
        self.inventario.listar_catalogo()
        self.inventario.listar_catalogo("Camisetas")
        self.assertEqual(self.inventario.prendas, antes)


def inventario_con_prendas():
    """CAM-001: 10 unidades a 35.000 · PAN-001: 3 unidades a 80.000 · VES-001: agotada."""
    inventario = Inventario()
    registrar(inventario, codigo="CAM-001", precio="35000", stock="10")
    registrar(inventario, codigo="PAN-001", nombre="Jean recto", categoria="Pantalones",
              precio="80000", stock="3")
    registrar(inventario, codigo="VES-001", nombre="Vestido", categoria="Vestidos", stock="0")
    return inventario


class PruebasComprar(unittest.TestCase):
    """Compra de prendas: stock, identificadores, total y precio congelado."""

    def setUp(self):
        self.inventario = inventario_con_prendas()

    def assertCompraRechazada(self, cliente="Ana", codigo="CAM-001", cantidad="2"):
        """Se rechaza con ErrorValidacion sin cambiar stock, historial ni contador."""
        stock_antes = {c: p.stock for c, p in self.inventario.prendas.items()}
        with self.assertRaises(ErrorValidacion):
            self.inventario.comprar(cliente, codigo, cantidad)
        self.assertEqual({c: p.stock for c, p in self.inventario.prendas.items()}, stock_antes)
        self.assertEqual(self.inventario.compras, {})
        self.assertEqual(self.inventario.siguiente_id_compra, 1)

    def test_compra_exitosa_baja_el_stock_exactamente_la_cantidad(self):
        compra = self.inventario.comprar("Ana", "CAM-001", "4")
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 6)
        self.assertIn(compra.id_compra, self.inventario.compras)
        self.assertEqual(compra.cantidad, 4)

    def test_identificador_unico_y_total(self):
        primera = self.inventario.comprar("Ana", "CAM-001", "2")
        segunda = self.inventario.comprar("Luis", "PAN-001", "1")
        self.assertEqual((primera.id_compra, segunda.id_compra), (1, 2))
        self.assertEqual(primera.total, 70000.0)
        self.assertEqual(segunda.total, 80000.0)
        self.assertEqual(self.inventario.siguiente_id_compra, 3)

    def test_stock_insuficiente(self):
        self.assertCompraRechazada(cantidad="11")
        self.assertCompraRechazada(codigo="PAN-001", cantidad="4")

    def test_prenda_agotada_no_se_puede_comprar(self):
        self.assertCompraRechazada(codigo="VES-001", cantidad="1")

    def test_se_puede_comprar_todo_el_stock(self):
        self.inventario.comprar("Ana", "PAN-001", "3")
        self.assertEqual(self.inventario.prendas["PAN-001"].stock, 0)
        self.assertTrue(self.inventario.prendas["PAN-001"].esta_agotada())

    def test_prenda_inexistente(self):
        self.assertCompraRechazada(codigo="ZZZ-999")
        self.assertCompraRechazada(codigo="")

    def test_cantidad_invalida(self):
        for mala in ("0", "-1", "abc", "2.5", "", "1_0", 0, -2, 1.5, True):
            self.assertCompraRechazada(cantidad=mala)

    def test_codigo_en_minuscula_tambien_sirve_para_comprar_y_mantener(self):
        compra = self.inventario.comprar("Ana", "cam-001", "2")
        self.assertEqual(compra.codigo_prenda, "CAM-001")
        self.inventario.reponer_stock("cam-001", "1")
        self.inventario.actualizar_precio("cam-001", "40000")
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 9)
        self.assertEqual(self.inventario.prendas["CAM-001"].precio, 40000.0)

    def test_compra_asociada_al_cliente(self):
        compra = self.inventario.comprar("  Ana  ", "CAM-001", "1")
        self.assertEqual(compra.cliente, "Ana")
        self.assertEqual(compra.codigo_prenda, "CAM-001")

    def test_cliente_vacio_se_rechaza(self):
        self.assertCompraRechazada(cliente="   ")

    def test_conserva_el_precio_unitario_del_momento(self):
        compra = self.inventario.comprar("Ana", "CAM-001", "2")
        self.assertEqual(compra.precio_unitario, 35000.0)
        self.inventario.actualizar_precio("CAM-001", "50000")
        self.assertEqual(compra.precio_unitario, 35000.0)
        self.assertEqual(compra.total, 70000.0)


class PruebasConsultarCompras(unittest.TestCase):
    """Consulta de compras: las de un cliente y todas (vista del Admin)."""

    def setUp(self):
        self.inventario = inventario_con_prendas()
        self.inventario.comprar("Ana", "CAM-001", "1")     # 1
        self.inventario.comprar("Luis", "CAM-001", "2")    # 2
        self.inventario.comprar("Ana", "PAN-001", "1")     # 3

    def test_solo_las_compras_del_cliente(self):
        compras = self.inventario.compras_de_cliente("Ana")
        self.assertEqual([c.id_compra for c in compras], [1, 3])
        self.assertTrue(all(c.cliente == "Ana" for c in compras))

    def test_detalle_de_la_compra(self):
        compra = self.inventario.compras_de_cliente("Ana")[0]
        self.assertEqual((compra.id_compra, compra.codigo_prenda, compra.cantidad,
                          compra.total, compra.devuelta), (1, "CAM-001", 1, 35000.0, False))

    def test_cliente_sin_compras(self):
        """Un cliente que nunca ha comprado recibe una lista vacía (no un error).

        Marta no aparece en las compras del setUp (solo Ana y Luis compraron), así que
        compras_de_cliente("Marta") debe devolver [] y el menú mostrará "Aún no tienes compras".
        """
        self.assertEqual(self.inventario.compras_de_cliente("Marta"), [])

    def test_el_nombre_se_compara_sin_importar_mayusculas(self):
        for escritura in ("ana", "ANA", "  Ana "):
            self.assertEqual([c.id_compra for c in self.inventario.compras_de_cliente(escritura)],
                             [1, 3])

    def test_nombre_vacio_se_rechaza(self):
        for vacio in ("", "   "):
            with self.assertRaises(ErrorValidacion):
                self.inventario.compras_de_cliente(vacio)

    def test_todas_ordenadas_por_identificador(self):
        todas = self.inventario.listar_todas_las_compras()
        self.assertEqual([c.id_compra for c in todas], [1, 2, 3])
        self.assertEqual({c.cliente for c in todas}, {"Ana", "Luis"})

    def test_compra_devuelta_aparece_marcada(self):
        self.inventario.devolver_compra("2")
        estados = {c.id_compra: c.devuelta for c in self.inventario.listar_todas_las_compras()}
        self.assertEqual(estados, {1: False, 2: True, 3: False})
        self.assertTrue(self.inventario.compras_de_cliente("Luis")[0].devuelta)

    def test_todas_las_compras_sin_compras(self):
        """Vista del Admin: un inventario sin ninguna compra devuelve una lista vacía.

        Usa un Inventario() nuevo (no el del setUp, que sí tiene compras) para comprobar
        que listar_todas_las_compras() funciona aunque todavía no se haya vendido nada.
        """
        self.assertEqual(Inventario().listar_todas_las_compras(), [])


class PruebasDevolverCompra(unittest.TestCase):
    """Devolución de compras: stock repuesto, repetidas e inexistentes."""

    def setUp(self):
        self.inventario = inventario_con_prendas()
        self.compra = self.inventario.comprar("Ana", "CAM-001", "4")   # stock 10 -> 6

    def assertDevolucionRechazada(self, identificador):
        stock = self.inventario.prendas["CAM-001"].stock
        with self.assertRaises(ErrorValidacion):
            self.inventario.devolver_compra(identificador)
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, stock)

    def test_devolucion_exitosa(self):
        self.inventario.devolver_compra("1")
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 10)
        self.assertTrue(self.compra.devuelta)

    def test_acepta_el_identificador_como_numero(self):
        self.inventario.devolver_compra(1)
        self.assertTrue(self.compra.devuelta)

    def test_devolucion_repetida(self):
        self.inventario.devolver_compra("1")
        self.assertDevolucionRechazada("1")
        self.assertEqual(self.inventario.prendas["CAM-001"].stock, 10)  # no se suma dos veces

    def test_compra_inexistente(self):
        self.assertDevolucionRechazada("99")
        self.assertFalse(self.compra.devuelta)

    def test_identificador_que_no_es_un_numero_valido(self):
        for malo in ("abc", "", "0", "-1", "1.5", True):
            self.assertDevolucionRechazada(malo)
        self.assertFalse(self.compra.devuelta)

    def test_la_devolucion_conserva_el_total_de_la_compra(self):
        self.inventario.actualizar_precio("CAM-001", "99999")
        self.inventario.devolver_compra("1")
        self.assertEqual(self.compra.total, 4 * 35000.0)


class PruebasActualizarPrendas(unittest.TestCase):
    """Mantenimiento: cambio de precio y reposición de stock."""

    def setUp(self):
        self.inventario = inventario_con_prendas()

    def assertSinCambios(self, funcion, *args):
        antes = [(p.precio, p.stock) for p in self.inventario.prendas.values()]
        with self.assertRaises(ErrorValidacion):
            funcion(*args)
        self.assertEqual([(p.precio, p.stock) for p in self.inventario.prendas.values()], antes)

    def test_cambio_de_precio(self):
        self.inventario.actualizar_precio("CAM-001", "42000.5")
        self.assertEqual(self.inventario.prendas["CAM-001"].precio, 42000.5)

    def test_reposicion_de_stock(self):
        self.inventario.reponer_stock("PAN-001", "7")
        self.assertEqual(self.inventario.prendas["PAN-001"].stock, 10)

    def test_reponer_una_prenda_agotada_la_deja_disponible(self):
        self.inventario.reponer_stock("VES-001", "5")
        self.assertFalse(self.inventario.prendas["VES-001"].esta_agotada())

    def test_precio_invalido_o_prenda_inexistente(self):
        for malo in ("0", "-3", "abc", "", "nan"):
            self.assertSinCambios(self.inventario.actualizar_precio, "CAM-001", malo)
        self.assertSinCambios(self.inventario.actualizar_precio, "ZZZ-999", "100")

    def test_cantidad_invalida_o_prenda_inexistente(self):
        for mala in ("0", "-3", "abc", "2.5", ""):
            self.assertSinCambios(self.inventario.reponer_stock, "CAM-001", mala)
        self.assertSinCambios(self.inventario.reponer_stock, "ZZZ-999", "5")

    def test_el_total_de_compras_anteriores_no_cambia(self):
        compra = self.inventario.comprar("Ana", "CAM-001", "2")
        total = compra.total
        self.inventario.actualizar_precio("CAM-001", "1")
        self.assertEqual(compra.total, total)
        self.assertEqual(self.inventario.listar_todas_las_compras()[0].total, total)


class PruebasFiltrarCatalogo(unittest.TestCase):
    """Filtros del catálogo por categoría, talla y color."""

    def setUp(self):
        self.inventario = Inventario()
        registrar(self.inventario, codigo="CAM-001", talla="M", color="Negro")
        registrar(self.inventario, codigo="PAN-001", nombre="Jean", categoria="Pantalones",
                  talla="L", color="Azul")
        registrar(self.inventario, codigo="CAM-002", nombre="Polo", talla="M", color="Azul")
        registrar(self.inventario, codigo="VES-001", nombre="Vestido", categoria="Vestidos",
                  talla="S", color="Negro")

    def codigos(self, **filtros):
        return [p.codigo for p in self.inventario.listar_catalogo(**filtros)]

    def test_filtro_por_talla(self):
        self.assertEqual(self.codigos(talla="M"), ["CAM-001", "CAM-002"])

    def test_filtro_por_color(self):
        self.assertEqual(self.codigos(color="Azul"), ["CAM-002", "PAN-001"])

    def test_los_filtros_se_pueden_combinar(self):
        self.assertEqual(self.codigos(talla="M", color="Azul"), ["CAM-002"])
        self.assertEqual(self.codigos(categoria="Camisetas", talla="M"), ["CAM-001", "CAM-002"])
        self.assertEqual(self.codigos(categoria="Camisetas", talla="M", color="Negro"), ["CAM-001"])

    def test_los_filtros_no_distinguen_mayusculas(self):
        self.assertEqual(self.codigos(talla="m", color="AZUL"), ["CAM-002"])

    def test_talla_o_color_fuera_de_la_lista_se_rechazan(self):
        for filtro in ({"talla": "XXL"}, {"color": "Morado"}, {"talla": ""}, {"color": "  "},
                       {"categoria": "Zapatos"}, {"talla": "M", "color": "Morado"}):
            with self.assertRaises(ErrorValidacion):
                self.inventario.listar_catalogo(**filtro)

    def test_sin_coincidencias_devuelve_lista_vacia(self):
        self.assertEqual(self.codigos(talla="XL"), [])
        self.assertEqual(self.codigos(talla="S", color="Azul"), [])

    def test_sin_filtros_devuelve_todo_y_filtrar_no_modifica_el_catalogo(self):
        antes = dict(self.inventario.prendas)
        self.assertEqual(len(self.codigos()), 4)
        self.codigos(talla="M", color="Azul")
        self.assertEqual(self.inventario.prendas, antes)

    def test_las_agotadas_tambien_aparecen_al_filtrar(self):
        registrar(self.inventario, codigo="CAM-003", talla="M", color="Rojo", stock="0")
        self.assertIn("CAM-003", self.codigos(talla="M"))


class PruebasDatosParaReportes(unittest.TestCase):
    """unidades_vendidas_por_prenda y prendas_con_poco_stock (datos de los reportes)."""

    def setUp(self):
        self.inventario = inventario_con_prendas()   # CAM-001: 10 · PAN-001: 3 · VES-001: 0

    def test_unidades_vendidas_suman_compras_y_excluyen_devueltas(self):
        self.inventario.comprar("Ana", "CAM-001", "2")
        devuelta = self.inventario.comprar("Luis", "CAM-001", "3")
        self.inventario.comprar("Ana", "PAN-001", "1")
        self.inventario.devolver_compra(devuelta.id_compra)
        self.assertEqual(self.inventario.unidades_vendidas_por_prenda(), {"CAM-001": 2, "PAN-001": 1})

    def test_sin_compras_no_hay_unidades_vendidas(self):
        self.assertEqual(self.inventario.unidades_vendidas_por_prenda(), {})

    def test_poco_stock_incluye_el_umbral_y_las_agotadas(self):
        self.assertEqual([p.codigo for p in self.inventario.prendas_con_poco_stock()],
                         ["PAN-001", "VES-001"])
        registrar(self.inventario, codigo="CAM-002", stock="5")
        registrar(self.inventario, codigo="CAM-003", stock="6")
        codigos = [p.codigo for p in self.inventario.prendas_con_poco_stock()]
        self.assertIn("CAM-002", codigos)
        self.assertNotIn("CAM-003", codigos)


if __name__ == "__main__":
    unittest.main()
