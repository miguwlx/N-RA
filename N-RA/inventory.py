"""Inventario de NöRA: guarda las prendas del catálogo.

Regla general: validar primero y modificar después. Una operación rechazada
no cambia el catálogo.
"""
from product import CATEGORIAS, ErrorValidacion, Prenda, normalizar_opcion, validar_codigo


class Inventario:
    """Guarda las prendas por código."""

    def __init__(self):
        self.prendas = {}            

    
    def validar_codigo_disponible(self, codigo):
        """HU-002: comprueba formato y que el código no exista, sin modificar nada.

        Permite avisar del problema apenas se escribe el código, antes de pedir el
        resto de los datos. Devuelve el código limpio (en mayúscula).
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
        self.validar_codigo_disponible(prenda.codigo)  
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
