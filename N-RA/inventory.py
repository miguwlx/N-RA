"""Inventario de NöRA: prendas, compras y contador de identificadores.

Regla general: validar primero y modificar después. Una operación rechazada
no cambia el stock ni el historial.
"""
from product import CATEGORIAS, ErrorValidacion, Prenda, normalizar_opcion, validar_codigo


class Inventario:
    """Guarda las prendas (por código) y las compras (por identificador)."""

    def __init__(self):
        self.prendas = {}              # código -> Prenda
        self.compras = {}              # id_compra -> Compra (orden de registro)
        # Entero autoincremental. Se guarda en el JSON (HU-008) y se recupera (HU-013);
        # no se calcula con len(compras) para que un id nunca se repita.
        self.siguiente_id_compra = 1

    # ---- Sprint 1 ----
    def validar_codigo_disponible(self, codigo):
        """HU-002: comprueba formato y que el código no exista, sin modificar nada.

        Permite avisar del problema apenas se escribe el código, antes de pedir el
        resto de los datos. Devuelve el código limpio.
        """
        codigo = validar_codigo(codigo)
        if codigo in self.prendas:
            raise ErrorValidacion(f"Ya existe una prenda con el código {codigo}.")
        return codigo

    def registrar_prenda(self, codigo, nombre, categoria, talla, color, precio, stock):
        """HU-002: valida todo, rechaza códigos duplicados y agrega la prenda al catálogo.

        Primero se valida (Prenda lanza ErrorValidacion) y solo después se modifica el
        catálogo, así un registro rechazado no cambia nada. Devuelve la Prenda creada.
        """
        prenda = Prenda(codigo, nombre, categoria, talla, color, precio, stock)
        self.validar_codigo_disponible(prenda.codigo)  # garantía final contra duplicados
        self.prendas[prenda.codigo] = prenda
        return prenda

    def listar_catalogo(self, categoria=None):
        """HU-003: todas las prendas ordenadas por código, agotadas incluidas.

        Con categoría solo devuelve las de esa categoría; una categoría fuera de la
        lista permitida lanza ErrorValidacion. (Los filtros por talla y color son HU-012.)
        """
        prendas = sorted(self.prendas.values(), key=lambda prenda: prenda.codigo)
        if categoria is not None:
            categoria = normalizar_opcion(categoria, CATEGORIAS, "La categoría", "válida")
            prendas = [prenda for prenda in prendas if prenda.categoria == categoria]
        return prendas

    # ---- Sprint 2 ----
    def comprar(self, cliente, codigo, cantidad):
        """HU-004: valida existencia, cantidad entera > 0 y stock; luego registra y descuenta."""
        raise NotImplementedError("HU-004")

    def compras_de_cliente(self, cliente):
        """HU-005: solo las compras hechas con ese nombre."""
        raise NotImplementedError("HU-005")

    def devolver_compra(self, id_compra):
        """HU-006: suma la cantidad al stock y marca la compra; rechaza si ya se devolvió."""
        raise NotImplementedError("HU-006")

    def actualizar_precio(self, codigo, nuevo_precio):
        """HU-007: precio > 0; no altera compras ya registradas."""
        raise NotImplementedError("HU-007")

    def reponer_stock(self, codigo, cantidad):
        """HU-007: suma una cantidad entera > 0 al stock."""
        raise NotImplementedError("HU-007")

    def listar_todas_las_compras(self):
        """HU-011: todas las compras de todos los clientes, ordenadas por identificador."""
        raise NotImplementedError("HU-011")

    # ---- Sprint 3 ----
    def unidades_vendidas_por_prenda(self):
        """HU-009: unidades por código, sin contar compras devueltas."""
        raise NotImplementedError("HU-009")

    def prendas_con_poco_stock(self):
        """HU-014: prendas con UMBRAL_POCO_STOCK unidades o menos (incluye agotadas)."""
        raise NotImplementedError("HU-014")

    def a_diccionario(self):
        """HU-008: prendas, compras y siguiente_id_compra como datos simples."""
        raise NotImplementedError("HU-008")

    @classmethod
    def desde_diccionario(cls, datos):
        """HU-013: reconstruye todo; rechaza la carga completa si hay incoherencias."""
        raise NotImplementedError("HU-013")
