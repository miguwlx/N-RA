"""Inventario de NöRA: prendas, compras y contador de identificadores.

"""
from product import (CATEGORIAS, COLORES, TALLAS, UMBRAL_POCO_STOCK, Compra, ErrorValidacion,
                     Prenda, convertir_cantidad, convertir_id_compra, convertir_precio,
                     normalizar_opcion, texto_obligatorio, validar_codigo)


class Inventario:
    """Guarda las prendas (por código) y las compras (por identificador)."""

    def __init__(self):
        self.prendas = {}              # código -> Prenda
        self.compras = {}              # id_compra -> Compra
        # Entero autoincremental. Se guarda en el JSON y se recupera al cargarlo;
        # no se calcula con len(compras) para que un id nunca se repita.
        self.siguiente_id_compra = 1

    # ---- Búsqueda ----
    def obtener_prenda(self, codigo):
        """Devuelve la prenda con ese código (sin importar mayúsculas); lanza ErrorValidacion si no existe."""
        codigo = codigo.strip().upper() if isinstance(codigo, str) else ""
        if not codigo:
            raise ErrorValidacion("El código no puede estar vacío.")
        prenda = self.prendas.get(codigo)
        if prenda is None:
            raise ErrorValidacion(f"No existe una prenda con el código {codigo}.")
        return prenda

    # ---- Registro de prendas ----
    def validar_codigo_disponible(self, codigo):
        """Comprueba formato y que el código no exista, sin modificar nada.

        Permite avisar del problema apenas se escribe el código, antes de pedir el
        resto de los datos. Devuelve el código limpio.
        """
        codigo = validar_codigo(codigo)
        if codigo in self.prendas:
            raise ErrorValidacion(f"Ya existe una prenda con el código {codigo}.")
        return codigo

    def registrar_prenda(self, codigo, nombre, categoria, talla, color, precio, stock):
        """Valida todo, rechaza códigos duplicados y agrega la prenda al catálogo.

        Primero se valida (Prenda lanza ErrorValidacion) y solo después se modifica el
        catálogo, así un registro rechazado no cambia nada. Devuelve la Prenda creada.
        """
        prenda = Prenda(codigo, nombre, categoria, talla, color, precio, stock)
        self.validar_codigo_disponible(prenda.codigo)  # garantía final contra duplicados
        self.prendas[prenda.codigo] = prenda
        return prenda

    # ---- Consulta y filtros del catálogo ----
    def listar_catalogo(self, categoria=None, talla=None, color=None):
        """Prendas ordenadas por código, agotadas incluidas.

        Los filtros son opcionales y se combinan. Cada uno se valida contra su lista
        permitida antes de filtrar (sin distinguir mayúsculas); un valor fuera de la
        lista lanza ErrorValidacion. None significa "sin filtro".
        """
        if categoria is not None:
            categoria = normalizar_opcion(categoria, CATEGORIAS, "La categoría", "válida")
        if talla is not None:
            talla = normalizar_opcion(talla, TALLAS, "La talla", "válida")
        if color is not None:
            color = normalizar_opcion(color, COLORES, "El color", "válido")
        prendas = sorted(self.prendas.values(), key=lambda prenda: prenda.codigo)
        if categoria is not None:
            prendas = [prenda for prenda in prendas if prenda.categoria == categoria]
        if talla is not None:
            prendas = [prenda for prenda in prendas if prenda.talla == talla]
        if color is not None:
            prendas = [prenda for prenda in prendas if prenda.color == color]
        return prendas

    # ---- Compra de una prenda ----
    def comprar(self, cliente, codigo, cantidad):
        """Valida existencia, cantidad entera > 0 y stock; luego registra y descuenta.

        Orden: se valida todo primero (prenda, cantidad, stock). Solo si todo es válido
        se crea la compra con el precio unitario de ESE momento, se descuenta el stock,
        se guarda la compra y se avanza el contador. Devuelve la Compra.
        """
        cliente = texto_obligatorio(cliente, "El nombre del cliente no puede estar vacío.")
        prenda = self.obtener_prenda(codigo)
        cantidad = convertir_cantidad(cantidad)
        if cantidad > prenda.stock:
            raise ErrorValidacion(
                f"Stock insuficiente de {prenda.codigo}: hay {prenda.stock} unidad(es) disponible(s).")
        compra = Compra(self.siguiente_id_compra, cliente, prenda.codigo, cantidad, prenda.precio)
        prenda.stock -= cantidad
        self.compras[compra.id_compra] = compra
        self.siguiente_id_compra += 1
        return compra

    # ---- Consulta de compras (por cliente y generales) ----
    def compras_de_cliente(self, cliente):
        """Solo las compras de ese cliente, ordenadas por identificador.

        Compara sin importar mayúsculas ("ana" y "Ana" son la misma persona) y rechaza
        el nombre vacío. Reutiliza listar_todas_las_compras(), por eso sale ordenado.
        """
        cliente = texto_obligatorio(cliente, "El nombre del cliente no puede estar vacío.")
        nombre = cliente.casefold()
        return [compra for compra in self.listar_todas_las_compras()
                if compra.cliente.casefold() == nombre]

    def listar_todas_las_compras(self):
        """Todas las compras de todos los clientes, ordenadas por identificador."""
        return sorted(self.compras.values(), key=lambda compra: compra.id_compra)

    # ---- Devolución de una compra ----
    def devolver_compra(self, id_compra):
        """Suma la cantidad al stock y marca la compra; rechaza si ya se devolvió.

        Se valida identificador, existencia y estado antes de tocar el stock o la compra.
        """
        id_compra = convertir_id_compra(id_compra)
        compra = self.compras.get(id_compra)
        if compra is None:
            raise ErrorValidacion(f"No existe una compra con el identificador {id_compra}.")
        if compra.devuelta:
            raise ErrorValidacion(f"La compra {id_compra} ya fue devuelta.")
        prenda = self.prendas[compra.codigo_prenda]
        compra.marcar_devuelta()
        prenda.stock += compra.cantidad
        return compra

    # ---- Mantenimiento del catálogo (precio y stock) ----
    def actualizar_precio(self, codigo, nuevo_precio):
        """Cambia el precio (> 0); no altera compras ya registradas (guardan su precio unitario)."""
        prenda = self.obtener_prenda(codigo)
        prenda.precio = convertir_precio(nuevo_precio)
        return prenda

    def reponer_stock(self, codigo, cantidad):
        """Suma una cantidad entera > 0 al stock."""
        prenda = self.obtener_prenda(codigo)
        prenda.stock += convertir_cantidad(cantidad)
        return prenda

    # ---- Datos para los reportes ----
    def unidades_vendidas_por_prenda(self):
        """Unidades vendidas por código, sin contar compras devueltas.

        Es el único lugar donde se calcula: el CSV y el resumen en pantalla lo comparten,
        por eso sus cifras siempre coinciden.
        """
        vendidas = {}
        for compra in self.compras.values():
            if not compra.devuelta:
                vendidas[compra.codigo_prenda] = vendidas.get(compra.codigo_prenda, 0) + compra.cantidad
        return vendidas

    def prendas_con_poco_stock(self):
        """Prendas con UMBRAL_POCO_STOCK unidades o menos (incluye agotadas), por código."""
        return [prenda for prenda in self.listar_catalogo() if prenda.stock <= UMBRAL_POCO_STOCK]

    # ---- Persistencia: convertir a datos simples y reconstruir ----
    def a_diccionario(self):
        """Prendas, compras y siguiente_id_compra como datos simples (para JSON)."""
        return {
            "siguiente_id_compra": self.siguiente_id_compra,
            "prendas": [prenda.a_diccionario() for prenda in self.listar_catalogo()],
            "compras": [compra.a_diccionario() for compra in self.listar_todas_las_compras()],
        }

    @classmethod
    def desde_diccionario(cls, datos):
        
        if not isinstance(datos, dict):
            raise ErrorValidacion("Los datos del inventario deben ser un objeto.")
        prendas = datos.get("prendas")
        compras = datos.get("compras")
        siguiente = datos.get("siguiente_id_compra")
        if not isinstance(prendas, list) or not isinstance(compras, list):
            raise ErrorValidacion("Las prendas y las compras deben ser listas.")
        if type(siguiente) is not int or siguiente <= 0:
            raise ErrorValidacion("El siguiente identificador de compra no es válido.")
        inventario = cls()
        for entrada in prendas:
            prenda = Prenda.desde_diccionario(entrada)
            if prenda.codigo in inventario.prendas:
                raise ErrorValidacion(f"El código {prenda.codigo} aparece repetido en el archivo.")
            inventario.prendas[prenda.codigo] = prenda
        for entrada in compras:
            compra = Compra.desde_diccionario(entrada)
            if compra.id_compra in inventario.compras:
                raise ErrorValidacion(f"El identificador de compra {compra.id_compra} está repetido.")
            if compra.codigo_prenda not in inventario.prendas:
                raise ErrorValidacion(
                    f"La compra {compra.id_compra} referencia una prenda inexistente.")
            inventario.compras[compra.id_compra] = compra
        if inventario.compras and siguiente <= max(inventario.compras):
            raise ErrorValidacion("El siguiente identificador de compra no es coherente.")
        inventario.siguiente_id_compra = siguiente
        return inventario
