"""Modelo de dominio de NöRA: Prenda y Compra.

Las reglas de negocio viven aquí y en inventory.py, nunca en los menús.
"""
import math
import re

# Listas cerradas definidas en HU-002
CATEGORIAS = ("Camisetas", "Pantalones", "Vestidos", "Accesorios")
TALLAS = ("XS", "S", "M", "L", "XL", "Única")
COLORES = ("Negro", "Blanco", "Gris", "Azul", "Rojo", "Verde",
           "Beige", "Rosado", "Vinotinto")

# Código por variante: 3 letras, guion y 3 números (ejemplo: CAM-001).
# POR CONFIRMAR: ¿las letras van siempre en mayúscula? Hoy se exigen en mayúscula.
PATRON_CODIGO = re.compile(r"^[A-Z]{3}-\d{3}$")

# HU-014: poco stock = 5 unidades o menos (incluye agotadas)
UMBRAL_POCO_STOCK = 5

_ENTERO = re.compile(r"^-?\d+$")
_DECIMAL = re.compile(r"^-?\d+(\.\d+)?$")


class ErrorValidacion(Exception):
    """Se lanza cuando una operación incumple una regla de negocio.

    El mensaje es el texto claro que verá la persona en consola.
    """


# ---------- Validaciones reutilizables ----------
def texto_obligatorio(valor, mensaje):
    """Devuelve el texto sin espacios sobrantes; lanza ErrorValidacion si queda vacío."""
    texto = valor.strip() if isinstance(valor, str) else ""
    if not texto:
        raise ErrorValidacion(mensaje)
    return texto


def validar_codigo(codigo):
    """Devuelve el código sin espacios sobrantes; lanza ErrorValidacion si está vacío
    o no cumple el formato de 3 letras, guion y 3 números."""
    codigo = texto_obligatorio(codigo, "El código no puede estar vacío.")
    if not PATRON_CODIGO.match(codigo):
        raise ErrorValidacion(
            f"El código '{codigo}' no es válido. Usa 3 letras, guion y 3 números (ejemplo: CAM-001).")
    return codigo


def normalizar_opcion(valor, permitidos, etiqueta, adjetivo):
    """Devuelve la opción permitida que coincide (sin distinguir mayúsculas).

    Ejemplo: "vinotinto" -> "Vinotinto". Lanza ErrorValidacion si no está en la lista.
    """
    texto = valor.strip() if isinstance(valor, str) else ""
    for permitido in permitidos:
        if texto.casefold() == permitido.casefold():
            return permitido
    raise ErrorValidacion(
        f"{etiqueta} '{texto}' no es {adjetivo}. Opciones: {', '.join(permitidos)}.")


def convertir_precio(valor):
    """Número mayor que 0 (acepta número o texto). Lanza ErrorValidacion si no lo es."""
    error = ErrorValidacion("El precio debe ser un número mayor que 0.")
    if isinstance(valor, bool):
        raise error
    if isinstance(valor, (int, float)):
        numero = float(valor)
    elif isinstance(valor, str) and _DECIMAL.match(valor.strip()):
        numero = float(valor.strip())
    else:
        raise error
    if not math.isfinite(numero) or numero <= 0:
        raise error
    return numero


def convertir_stock(valor):
    """Entero mayor o igual a 0 (acepta entero o texto). Lanza ErrorValidacion si no lo es."""
    error = ErrorValidacion("El stock debe ser un número entero mayor o igual a 0.")
    if isinstance(valor, bool):
        raise error
    if isinstance(valor, int):
        numero = valor
    elif isinstance(valor, str) and _ENTERO.match(valor.strip()):
        numero = int(valor.strip())
    else:
        raise error
    if numero < 0:
        raise error
    return numero


class Prenda:
    """Una variante vendible: una combinación de talla y color con su propio código."""

    def __init__(self, codigo, nombre, categoria, talla, color, precio, stock):
        """HU-002: valida cada dato antes de aceptarlo; lanza ErrorValidacion si algo falla."""
        self.codigo = validar_codigo(codigo)
        self.nombre = texto_obligatorio(nombre, "El nombre no puede estar vacío.")
        self.categoria = normalizar_opcion(categoria, CATEGORIAS, "La categoría", "válida")
        self.talla = normalizar_opcion(talla, TALLAS, "La talla", "válida")
        self.color = normalizar_opcion(color, COLORES, "El color", "válido")
        self.precio = convertir_precio(precio)
        self.stock = convertir_stock(stock)

    def esta_agotada(self):
        """HU-003: True si el stock es 0."""
        return self.stock == 0

    def a_diccionario(self):
        """HU-008: datos simples (para JSON) con color, precio y stock."""
        raise NotImplementedError("HU-008")

    @classmethod
    def desde_diccionario(cls, datos):
        """HU-013: reconstruye la prenda validando los datos leídos."""
        raise NotImplementedError("HU-013")


class Compra:
    """Registro de una compra: guarda el precio unitario del momento."""

    def __init__(self, id_compra, cliente, codigo_prenda, cantidad,
                 precio_unitario, devuelta=False):
        """HU-004: asocia la compra al nombre del cliente y congela el precio unitario."""
        raise NotImplementedError("HU-004")

    @property
    def total(self):
        """HU-004: precio_unitario x cantidad."""
        raise NotImplementedError("HU-004")

    def marcar_devuelta(self):
        """HU-006: marca la compra como devuelta; una compra no se devuelve dos veces."""
        raise NotImplementedError("HU-006")

    def a_diccionario(self):
        """HU-008: cliente, precio unitario, cantidad y estado de devolución."""
        raise NotImplementedError("HU-008")

    @classmethod
    def desde_diccionario(cls, datos):
        """HU-013: reconstruye la compra validando los datos leídos."""
        raise NotImplementedError("HU-013")
