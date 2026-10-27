"""Pruebas de guardar y cargar el inventario en JSON, con archivos temporales."""
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from inventory import Inventario
from storage import Almacenamiento, ErrorAlmacenamiento


def construir_inventario():
    """CAM-001 (vinotinto, stock 9 tras 3 compras y 1 devolución) y dos compras."""
    inventario = Inventario()
    inventario.registrar_prenda("CAM-001", "Camiseta NöRA", "Camisetas", "M", "Vinotinto", "50000", "10")
    primera = inventario.comprar("Ana", "CAM-001", "2")
    inventario.comprar("Luis", "CAM-001", "1")
    inventario.devolver_compra(primera.id_compra)
    return inventario


def ejecutar(funcion, entradas, *args):
    salida = io.StringIO()
    with patch("builtins.input", side_effect=entradas), patch("sys.stdout", salida):
        funcion(*args)
    return salida.getvalue()


class BaseConCarpeta(unittest.TestCase):
    def setUp(self):
        self.carpeta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.carpeta, ignore_errors=True)
        self.ruta = self.carpeta / "state.json"
        self.almacenamiento = Almacenamiento(self.ruta)

    def leer(self):
        return json.loads(self.ruta.read_text(encoding="utf-8"))


class PruebasGuardar(BaseConCarpeta):
    """Guardar el inventario en JSON."""

    def test_guarda_las_prendas_con_su_color(self):
        self.almacenamiento.guardar(construir_inventario())
        prenda = self.leer()["prendas"][0]
        self.assertEqual((prenda["color"], prenda["stock"], prenda["precio"]), ("Vinotinto", 9, 50000))
        self.assertEqual((prenda["categoria"], prenda["talla"]), ("Camisetas", "M"))

    def test_guarda_las_compras_con_cliente_precio_unitario_y_devolucion(self):
        self.almacenamiento.guardar(construir_inventario())
        compras = self.leer()["compras"]
        self.assertEqual([c["cliente"] for c in compras], ["Ana", "Luis"])
        self.assertEqual((compras[0]["precio_unitario"], compras[0]["cantidad"]), (50000, 2))
        self.assertTrue(compras[0]["devuelta"])
        self.assertFalse(compras[1]["devuelta"])

    def test_guarda_el_siguiente_identificador(self):
        self.almacenamiento.guardar(construir_inventario())
        self.assertEqual(self.leer()["siguiente_id_compra"], 3)

    def test_escribe_en_utf8_sin_alterar_la_o_con_dieresis(self):
        self.almacenamiento.guardar(construir_inventario())
        self.assertIn("NöRA", self.ruta.read_text(encoding="utf-8"))

    def test_crea_la_carpeta_data_si_no_existe(self):
        almacenamiento = Almacenamiento(self.carpeta / "data" / "state.json")
        almacenamiento.guardar(Inventario())
        self.assertTrue((self.carpeta / "data" / "state.json").exists())

    def test_falla_al_escribir_conserva_el_archivo_anterior(self):
        self.almacenamiento.guardar(construir_inventario())
        original = self.ruta.read_text(encoding="utf-8")
        with patch.object(Inventario, "a_diccionario", side_effect=TypeError("boom")):
            with self.assertRaises(ErrorAlmacenamiento):
                self.almacenamiento.guardar(construir_inventario())
        self.assertEqual(self.ruta.read_text(encoding="utf-8"), original)
        self.assertFalse(Path(str(self.ruta) + ".tmp").exists())

    def test_falla_si_la_carpeta_es_en_realidad_un_archivo(self):
        bloqueo = self.carpeta / "bloqueo"
        bloqueo.write_text("x", encoding="utf-8")
        with self.assertRaises(ErrorAlmacenamiento):
            Almacenamiento(bloqueo / "state.json").guardar(construir_inventario())

    def test_no_queda_archivo_temporal_tras_guardar_bien(self):
        self.almacenamiento.guardar(construir_inventario())
        self.assertFalse(Path(str(self.ruta) + ".tmp").exists())


class PruebasCargar(BaseConCarpeta):
    """Cargar el inventario desde JSON."""

    def escribir(self, datos):
        self.ruta.write_text(json.dumps(datos), encoding="utf-8")

    def datos_validos(self):
        return construir_inventario().a_diccionario()

    def assertCargaRechazada(self, datos):
        self.escribir(datos)
        contenido = self.ruta.read_text(encoding="utf-8")
        with self.assertRaises(ErrorAlmacenamiento):
            self.almacenamiento.cargar()
        self.assertEqual(self.ruta.read_text(encoding="utf-8"), contenido)  # no se toca

    def test_archivo_valido_recupera_prendas_y_compras(self):
        self.almacenamiento.guardar(construir_inventario())
        recuperado = self.almacenamiento.cargar()
        self.assertEqual(recuperado.prendas["CAM-001"].color, "Vinotinto")
        self.assertEqual(recuperado.prendas["CAM-001"].stock, 9)
        compras = recuperado.listar_todas_las_compras()
        self.assertEqual([c.cliente for c in compras], ["Ana", "Luis"])

    def test_archivo_inexistente_inicia_vacio(self):
        recuperado = Almacenamiento(self.carpeta / "no_existe.json").cargar()
        self.assertEqual((recuperado.prendas, recuperado.compras, recuperado.siguiente_id_compra),
                         ({}, {}, 1))

    def test_json_danado_se_rechaza_y_no_se_sobrescribe(self):
        self.ruta.write_text("{invalido", encoding="utf-8")
        with self.assertRaises(ErrorAlmacenamiento):
            self.almacenamiento.cargar()
        self.assertEqual(self.ruta.read_text(encoding="utf-8"), "{invalido")

    def test_archivo_vacio_o_con_bytes_ilegibles(self):
        self.ruta.write_text("", encoding="utf-8")
        with self.assertRaises(ErrorAlmacenamiento):
            self.almacenamiento.cargar()
        self.ruta.write_bytes(b"\xff\xfe\x00\x01")
        with self.assertRaises(ErrorAlmacenamiento):
            self.almacenamiento.cargar()

    def test_compra_de_una_prenda_inexistente_rechaza_toda_la_carga(self):
        datos = self.datos_validos()
        datos["compras"][0]["codigo_prenda"] = "ZZZ-999"
        self.assertCargaRechazada(datos)

    def test_una_compra_nueva_tras_reiniciar_no_repite_identificador(self):
        self.almacenamiento.guardar(construir_inventario())
        recuperado = self.almacenamiento.cargar()
        nueva = recuperado.comprar("Sofía", "CAM-001", "1")
        self.assertEqual(nueva.id_compra, 3)
        self.assertEqual(list(recuperado.compras), [1, 2, 3])

    def test_conserva_precio_unitario_y_estado_de_devolucion(self):
        inventario = Inventario()
        inventario.registrar_prenda("CAM-001", "Camiseta", "Camisetas", "M", "Negro", "50000", "10")
        compra = inventario.comprar("Ana", "CAM-001", "2")
        inventario.devolver_compra(compra.id_compra)
        inventario.actualizar_precio("CAM-001", "80000")
        self.almacenamiento.guardar(inventario)
        recuperado = self.almacenamiento.cargar()
        recuperada = recuperado.listar_todas_las_compras()[0]
        self.assertEqual((recuperada.precio_unitario, recuperada.devuelta), (50000, True))
        self.assertEqual(recuperado.prendas["CAM-001"].precio, 80000)
        self.assertEqual(recuperada.total, 100000)

    def test_siguiente_identificador_incoherente_se_rechaza(self):
        datos = self.datos_validos()
        datos["siguiente_id_compra"] = 1
        self.assertCargaRechazada(datos)

    def test_siguiente_identificador_invalido(self):
        for malo in (0, -1, "3", 2.5, None, True):
            datos = self.datos_validos()
            datos["siguiente_id_compra"] = malo
            self.assertCargaRechazada(datos)

    def test_identificadores_de_compra_repetidos(self):
        datos = self.datos_validos()
        datos["compras"][1]["id_compra"] = datos["compras"][0]["id_compra"]
        self.assertCargaRechazada(datos)

    def test_codigos_de_prenda_repetidos(self):
        datos = self.datos_validos()
        datos["prendas"].append(dict(datos["prendas"][0]))
        self.assertCargaRechazada(datos)

    def test_prenda_con_datos_invalidos_rechaza_toda_la_carga(self):
        for campo, valor in (("stock", -1), ("stock", "3"), ("precio", 0), ("precio", True),
                             ("color", "Fucsia"), ("talla", "XXL"), ("categoria", "Zapatos"),
                             ("codigo", "P001"), ("nombre", ""), ("stock", None)):
            datos = self.datos_validos()
            datos["prendas"][0][campo] = valor
            self.assertCargaRechazada(datos)

    def test_compra_con_datos_invalidos_rechaza_toda_la_carga(self):
        for campo, valor in (("cantidad", 0), ("cantidad", "2"), ("precio_unitario", -5),
                             ("devuelta", "false"), ("devuelta", 0), ("cliente", " "),
                             ("id_compra", 0), ("id_compra", "1")):
            datos = self.datos_validos()
            datos["compras"][0][campo] = valor
            self.assertCargaRechazada(datos)

    def test_faltan_campos_o_la_estructura_es_incorrecta(self):
        for datos in ([], "texto", 5, None, {}, {"prendas": [], "compras": []},
                      {"prendas": {}, "compras": [], "siguiente_id_compra": 1},
                      {"prendas": [1], "compras": [], "siguiente_id_compra": 1},
                      {"prendas": [], "compras": ["x"], "siguiente_id_compra": 1}):
            self.assertCargaRechazada(datos)
        datos = self.datos_validos()
        del datos["prendas"][0]["color"]
        self.assertCargaRechazada(datos)

    def test_guardar_y_cargar_dan_el_mismo_estado(self):
        original = construir_inventario()
        self.almacenamiento.guardar(original)
        self.assertEqual(self.almacenamiento.cargar().a_diccionario(), original.a_diccionario())


class PruebasGuardadoAutomaticoEnLosMenus(BaseConCarpeta):
    """Guardado automático: tras cada operación válida los cambios quedan en el archivo."""

    def setUp(self):
        super().setUp()
        self.inventario = Inventario()
        self.registro = ["CAM-001", "Camiseta", "Camisetas", "M", "Negro", "35000", "10"]

    def test_registrar_prenda_guarda(self):
        ejecutar(main.menu_admin, ["1"] + self.registro + ["0"], self.inventario, self.almacenamiento)
        self.assertEqual([p["codigo"] for p in self.leer()["prendas"]], ["CAM-001"])

    def test_comprar_devolver_precio_y_stock_guardan(self):
        self.inventario.registrar_prenda(*self.registro)
        ejecutar(main.menu_cliente, ["3", "CAM-001", "4", "0"], "Ana", self.inventario, self.almacenamiento)
        datos = self.leer()
        self.assertEqual((datos["prendas"][0]["stock"], len(datos["compras"])), (6, 1))
        ejecutar(main.menu_admin, ["5", "1", "0"], self.inventario, self.almacenamiento)
        self.assertTrue(self.leer()["compras"][0]["devuelta"])
        ejecutar(main.menu_admin, ["6", "CAM-001", "42000", "0"], self.inventario, self.almacenamiento)
        self.assertEqual(self.leer()["prendas"][0]["precio"], 42000)
        ejecutar(main.menu_admin, ["7", "CAM-001", "5", "0"], self.inventario, self.almacenamiento)
        self.assertEqual(self.leer()["prendas"][0]["stock"], 15)

    def test_una_operacion_rechazada_no_guarda_nada(self):
        self.inventario.registrar_prenda(*self.registro)
        ejecutar(main.menu_cliente, ["3", "CAM-001", "99", "0"], "Ana", self.inventario, self.almacenamiento)
        ejecutar(main.menu_admin, ["6", "CAM-001", "abc", "7", "CAM-001", "0", "0"],
                 self.inventario, self.almacenamiento)
        self.assertFalse(self.ruta.exists())

    def test_si_falla_el_guardado_avisa_y_el_programa_sigue(self):
        with patch.object(Almacenamiento, "guardar", side_effect=ErrorAlmacenamiento("No se pudo guardar el inventario.")):
            texto = ejecutar(main.menu_admin, ["1"] + self.registro + ["0"],
                             self.inventario, self.almacenamiento)
        self.assertIn("Prenda registrada correctamente", texto)
        self.assertIn("Advertencia: No se pudo guardar el inventario.", texto)
        self.assertIn("Los cambios pueden existir solo en memoria.", texto)
        self.assertIn("Sesión cerrada.", texto)

    def test_sin_almacenamiento_no_se_escribe_nada(self):
        ejecutar(main.menu_admin, ["1"] + self.registro + ["0"], self.inventario)
        self.assertFalse(self.ruta.exists())


class PruebasReinicioDeLaAplicacion(BaseConCarpeta):
    """Carga de punta a punta: cerrar y volver a abrir main()."""

    def test_los_datos_siguen_ahi_tras_reiniciar(self):
        registro = ["CAM-001", "Camiseta", "Camisetas", "M", "Negro", "35000", "10"]
        ejecutar(main.main, ["2", main.CLAVE_ADMIN, "1"] + registro + ["0", "1", "Ana", "3", "CAM-001", "2", "0", "3"],
                 self.almacenamiento)
        texto = ejecutar(main.main, ["1", "Ana", "1", "4", "0", "3"], Almacenamiento(self.ruta))
        self.assertIn("CAM-001", texto)
        self.assertIn("70,000.00", texto)
        self.assertIn("8", texto)  # stock tras la compra de 2

    def test_el_identificador_de_compra_continua_tras_reiniciar(self):
        registro = ["CAM-001", "Camiseta", "Camisetas", "M", "Negro", "35000", "10"]
        ejecutar(main.main, ["2", main.CLAVE_ADMIN, "1"] + registro + ["0", "1", "Ana", "3", "CAM-001", "1", "0", "3"],
                 self.almacenamiento)
        texto = ejecutar(main.main, ["1", "Luis", "3", "CAM-001", "1", "0", "3"], Almacenamiento(self.ruta))
        self.assertIn("Compra registrada: #2", texto)

    def test_archivo_danado_detiene_la_aplicacion_sin_sobrescribirlo(self):
        self.ruta.write_text("{invalido", encoding="utf-8")
        texto = ejecutar(main.main, [], self.almacenamiento)  # no pide ninguna entrada
        self.assertIn("No se pudo cargar el inventario de forma segura", texto)
        self.assertIn("La aplicación se detuvo para proteger los datos existentes.", texto)
        self.assertNotIn("=== NöRA ===", texto)
        self.assertEqual(self.ruta.read_text(encoding="utf-8"), "{invalido")

    def test_primer_uso_sin_archivo_arranca_vacio(self):
        texto = ejecutar(main.main, ["1", "Ana", "1", "0", "3"], self.almacenamiento)
        self.assertIn("No hay prendas registradas.", texto)


if __name__ == "__main__":
    unittest.main()
