"""Modelo de dominio de NöRA: Prenda y Compra.

Las reglas de negocio viven aquí y en inventory.py.
"""
import math
import re

# Listas cerradas de opciones permitidas para las prendas
CATEGORIAS = ("Camisetas", "Pantalones", "Vestidos", "Accesorios")
TALLAS = ("XS", "S", "M", "L", "XL", "Única")
COLORES = ("Negro", "Blanco", "Gris", "Azul", "Rojo", "Verde",
           "Beige", "Rosado", "Vinotinto")

# Código por variante: 3 letras, guion y 3 números (ejemplo: CAM-001).
# Se acepta en minúscula ("cam-001") y se guarda siempre en mayúscula ("CAM-001"),
# así un mismo código no puede quedar registrado dos veces con distinta escritura.
PATRON_CODIGO = re.compile(r"^[A-Za-z]{3}-[0-9]{3}$")

# Umbral de poco stock: 5 unidades o menos (incluye agotadas)
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
    """Devuelve el código limpio y en mayúscula ("  cam-001 " -> "CAM-001").

    Lanza ErrorValidacion si está vacío o no cumple 3 letras, guion y 3 números.
    """
    codigo = texto_obligatorio(codigo, "El código no puede estar vacío.")
    if not PATRON_CODIGO.match(codigo):
        raise ErrorValidacion(
            f"El código '{codigo}' no es válido. Usa 3 letras, guion y 3 números (ejemplo: CAM-001).")
    return codigo.upper()


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


def _convertir_entero(valor, minimo, error):
    """Entero >= minimo (acepta entero o texto sin decimales); si no, lanza `error`."""
    if isinstance(valor, bool):
        raise error
    if isinstance(valor, int):
        numero = valor
    elif isinstance(valor, str) and _ENTERO.match(valor.strip()):
        numero = int(valor.strip())
    else:
        raise error
    if numero < minimo:
        raise error
    return numero


def convertir_stock(valor):
    """Stock de una prenda: entero mayor o igual a 0."""
    return _convertir_entero(
        valor, 0, ErrorValidacion("El stock debe ser un número entero mayor o igual a 0."))


def convertir_cantidad(valor):
    """Entero mayor que 0: unidades de una compra o de una reposición de stock."""
    return _convertir_entero(
        valor, 1, ErrorValidacion("La cantidad debe ser un número entero mayor que 0."))


def convertir_id_compra(valor):
    """Identificador de compra: entero mayor que 0."""
    return _convertir_entero(
        valor, 1,
        ErrorValidacion("El identificador de la compra debe ser un número entero mayor que 0."))


def exigir_tipo(valor, tipos, nombre):
    """El dato leído del archivo debe tener exactamente uno de los tipos esperados.

    Se compara con type() para que True no pase por número y "5" no pase por entero.
    """
    if type(valor) not in tipos:
        raise ErrorValidacion(f"El dato '{nombre}' del archivo no es válido.")
    return valor


class Prenda:
    """Una variante vendible: una combinación de talla y color con su propio código."""

    def __init__(self, codigo, nombre, categoria, talla, color, precio, stock):
        """Valida cada dato antes de aceptarlo; lanza ErrorValidacion si algo falla."""
        self.codigo = validar_codigo(codigo)
        self.nombre = texto_obligatorio(nombre, "El nombre no puede estar vacío.")
        self.categoria = normalizar_opcion(categoria, CATEGORIAS, "La categoría", "válida")
        self.talla = normalizar_opcion(talla, TALLAS, "La talla", "válida")
        self.color = normalizar_opcion(color, COLORES, "El color", "válido")
        self.precio = convertir_precio(precio)
        self.stock = convertir_stock(stock)

    def esta_agotada(self):
        """True si el stock es 0 (se muestra como AGOTADA)."""
        return self.stock == 0

    def a_diccionario(self):
        """Datos simples (para JSON) con color, precio y stock."""
        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "talla": self.talla,
            "color": self.color,
            "precio": self.precio,
            "stock": self.stock,
        }

    @classmethod
    def desde_diccionario(cls, datos):
        """Reconstruye la prenda reutilizando el constructor (y sus validaciones)."""
        if not isinstance(datos, dict):
            raise ErrorValidacion("Una prenda del archivo no es correspondiente.")
        return cls(
            exigir_tipo(datos.get("codigo"), (str,), "codigo"),
            exigir_tipo(datos.get("nombre"), (str,), "nombre"),
            exigir_tipo(datos.get("categoria"), (str,), "categoria"),
            exigir_tipo(datos.get("talla"), (str,), "talla"),
            exigir_tipo(datos.get("color"), (str,), "color"),
            exigir_tipo(datos.get("precio"), (int, float), "precio"),
            exigir_tipo(datos.get("stock"), (int,), "stock"),
        )


class Compra:
    """Registro de una compra: guarda el precio unitario del momento."""

    def __init__(self, id_compra, cliente, codigo_prenda, cantidad,
                 precio_unitario, devuelta=False):
        """Asocia la compra al nombre del cliente y congela el precio unitario."""
        self.id_compra = convertir_id_compra(id_compra)
        self.cliente = texto_obligatorio(cliente, "El nombre del cliente no puede estar vacío.")
        self.codigo_prenda = validar_codigo(codigo_prenda)
        self.cantidad = convertir_cantidad(cantidad)
        self.precio_unitario = convertir_precio(precio_unitario)
        self.devuelta = bool(devuelta)

    @property
    def total(self):
        """precio_unitario x cantidad (no cambia si luego cambia el precio de la prenda)."""
        return self.precio_unitario * self.cantidad

    def marcar_devuelta(self):
        """Marca la compra como devuelta; una compra no se devuelve dos veces."""
        if self.devuelta:
            raise ErrorValidacion(f"La compra {self.id_compra} ya fue devuelta.")
        self.devuelta = True

    def a_diccionario(self):
        """Datos simples (para JSON): cliente, precio unitario, cantidad y estado de devolución."""
        return {
            "id_compra": self.id_compra,
            "cliente": self.cliente,
            "codigo_prenda": self.codigo_prenda,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "devuelta": self.devuelta,
        }

    @classmethod
    def desde_diccionario(cls, datos):
        """Reconstruye la compra reutilizando el constructor (y sus validaciones)."""
        if not isinstance(datos, dict):
            raise ErrorValidacion("Una compra del archivo no es un objeto.")
        return cls(
            exigir_tipo(datos.get("id_compra"), (int,), "id_compra"),
            exigir_tipo(datos.get("cliente"), (str,), "cliente"),
            exigir_tipo(datos.get("codigo_prenda"), (str,), "codigo_prenda"),
            exigir_tipo(datos.get("cantidad"), (int,), "cantidad"),
            exigir_tipo(datos.get("precio_unitario"), (int, float), "precio_unitario"),
            exigir_tipo(datos.get("devuelta"), (bool,), "devuelta"),
        )
