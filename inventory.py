"Inventario de NöRA: prendas, compras y contador de identificadores."
from product import (CATEGORIAS, Compra, ErrorValidacion, Prenda, convertir_cantidad,
                     convertir_id_compra, convertir_precio, normalizar_opcion,
                     texto_obligatorio, validar_codigo)


class Inventario:
    "Guarda las prendas (por código) y las compras (por identificador)."

    def __init__(self):
        self.prendas = {}              
        self.compras = {}             
        self.siguiente_id_compra = 1

  
    def obtener_prenda(self, codigo):
        """Devuelve la prenda con ese código (sin importar mayúsculas); lanza ErrorValidacion si no existe."""
        codigo = codigo.strip().upper() if isinstance(codigo, str) else ""
        if not codigo:
            raise ErrorValidacion("El código no puede estar vacío.")
        prenda = self.prendas.get(codigo)
        if prenda is None:
            raise ErrorValidacion(f"No existe una prenda con el código {codigo}.")
        return prenda

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
        self.validar_codigo_disponible(prenda.codigo)  
        self.prendas[prenda.codigo] = prenda
        return prenda

    def listar_catalogo(self, categoria=None):
        """Todas las prendas ordenadas por código, agotadas incluidas.

        Con categoría solo devuelve las de esa categoría; una categoría fuera de la
        lista permitida lanza ErrorValidacion. (Los filtros por talla y color son HU-012.)
        """
        prendas = sorted(self.prendas.values(), key=lambda prenda: prenda.codigo)
        if categoria is not None:
            categoria = normalizar_opcion(categoria, CATEGORIAS, "La categoría", "válida")
            prendas = [prenda for prenda in prendas if prenda.categoria == categoria]
        return prendas

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

    def compras_de_cliente(self, cliente):
        """Solo las compras de ese cliente, por identificador.

        Compara sin importar mayúsculas ("ana" y "Ana" son la misma persona) y rechaza
        el nombre vacío. Reutiliza listar_todas_las_compras(), por eso sale ordenado.
        """
        cliente = texto_obligatorio(cliente, "El nombre del cliente no puede estar vacío.")
        nombre = cliente.casefold()
        return [compra for compra in self.listar_todas_las_compras()
                if compra.cliente.casefold() == nombre]

    def listar_todas_las_compras(self):
        "Todas las compras de todos los clientes, ordenadas por identificador."
        return sorted(self.compras.values(), key=lambda compra: compra.id_compra)

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

    def actualizar_precio(self, codigo, nuevo_precio):
        "precio > 0; no altera compras ya registradas (guardan su precio unitario)."
        prenda = self.obtener_prenda(codigo)
        prenda.precio = convertir_precio(nuevo_precio)
        return prenda

    def reponer_stock(self, codigo, cantidad):
        "suma una cantidad entera > 0 al stock."
        prenda = self.obtener_prenda(codigo)
        prenda.stock += convertir_cantidad(cantidad)
        return prenda
