"""NöRA - tienda de ropa (aplicación de consola).

Implementado: HU-001 (ingreso por rol), HU-002 (registrar prendas), HU-003 (consultar catálogo).
"""
from inventory import Inventario
from product import CATEGORIAS, COLORES, TALLAS, ErrorValidacion

# Clave de práctica del proyecto académico; no es una clave real.
CLAVE_ADMIN = "123456"


# ---------- Reglas de ingreso (HU-001) ----------
def validar_nombre_cliente(nombre):
    """Devuelve el nombre sin espacios sobrantes; rechaza el nombre vacío."""
    nombre = (nombre or "").strip()
    if not nombre:
        raise ErrorValidacion("El nombre no puede estar vacío.")
    return nombre


def validar_clave_admin(clave):
    """Rechaza cualquier clave distinta a la del Admin."""
    if clave != CLAVE_ADMIN:
        raise ErrorValidacion("Clave incorrecta.")


# ---------- Presentación del catálogo (HU-003) ----------
def formatear_catalogo(prendas):
    """Devuelve el catálogo como tabla de texto; las prendas sin stock salen como AGOTADA."""
    encabezados = ("Código", "Nombre", "Categoría", "Talla", "Color", "Precio", "Stock", "Estado")
    filas = [
        (prenda.codigo, prenda.nombre, prenda.categoria, prenda.talla, prenda.color,
         f"{prenda.precio:,.2f}", str(prenda.stock),
         "AGOTADA" if prenda.esta_agotada() else "")
        for prenda in prendas
    ]
    anchos = [max(len(fila[i]) for fila in [encabezados] + filas) for i in range(len(encabezados))]
    lineas = ["  ".join(celda.ljust(ancho) for celda, ancho in zip(fila, anchos)).rstrip()
              for fila in [encabezados] + filas]
    lineas.insert(1, "-" * len(lineas[0]))
    return "\n".join(lineas)


def ver_catalogo(inventario):
    """Muestra el catálogo completo, o un mensaje si no hay prendas registradas."""
    prendas = inventario.listar_catalogo()
    if not prendas:
        print("No hay prendas registradas.")
        return
    print()
    print(formatear_catalogo(prendas))


def filtrar_catalogo(inventario):
    """Pide una categoría y muestra solo las prendas de esa categoría."""
    print(f"Categorías: {', '.join(CATEGORIAS)}")
    categoria = input("Categoría a consultar: ")
    try:
        prendas = inventario.listar_catalogo(categoria)
    except ErrorValidacion as error:
        print(error)
        return
    if not prendas:
        print(f"No hay prendas en la categoría {categoria.strip()}.")
        return
    print()
    print(formatear_catalogo(prendas))


# ---------- Registro de prendas (HU-002) ----------
def registrar_prenda_desde_consola(inventario):
    """Captura los datos de la prenda y deja que el inventario los valide."""
    print("\n--- Registrar prenda ---")
    while True:
        codigo = input("Código (3 letras, guion y 3 números, ejemplo CAM-001; 0 para cancelar): ")
        if codigo.strip() == "0":
            print("Registro cancelado.")
            return
        try:
            codigo = inventario.validar_codigo_disponible(codigo)
            break
        except ErrorValidacion as error:
            print(error)
    nombre = input("Nombre: ")
    print(f"Categorías: {', '.join(CATEGORIAS)}")
    categoria = input("Categoría: ")
    print(f"Tallas: {', '.join(TALLAS)}")
    talla = input("Talla: ")
    print(f"Colores: {', '.join(COLORES)}")
    color = input("Color: ")
    precio = input("Precio: ")
    stock = input("Stock: ")
    try:
        prenda = inventario.registrar_prenda(codigo, nombre, categoria, talla, color, precio, stock)
    except ErrorValidacion as error:
        print(f"No se registró la prenda. {error}")
        return
    print(f"Prenda registrada correctamente: {prenda.codigo} - {prenda.nombre}.")


# ---------- Menús ----------
def menu_cliente(nombre, inventario):
    """Menú del Cliente. Nunca muestra opciones de Admin."""
    while True:
        print(f"\n--- Menú Cliente: {nombre} ---")
        print("1. Ver catálogo")
        print("2. Filtrar catálogo por categoría")
        # Aquí se agregarán: HU-012 Filtrar por talla y color,
        # HU-004 Comprar una prenda, HU-005 Mis compras.
        print("0. Cerrar sesión")
        opcion = input("Elige una opción: ").strip()
        if opcion == "1":
            ver_catalogo(inventario)
        elif opcion == "2":
            filtrar_catalogo(inventario)
        elif opcion == "0":
            print("Sesión cerrada.")
            return
        else:
            print("Opción no válida. Intenta de nuevo.")


def menu_admin(inventario):
    """Menú del Admin."""
    while True:
        print("\n--- Menú Admin ---")
        print("1. Registrar prenda")
        print("2. Ver catálogo")
        print("3. Filtrar catálogo por categoría")
        # Aquí se agregarán: HU-012 Filtrar por talla y color,
        # HU-007 Actualizar precio y reponer stock, HU-011 Ver todas las compras,
        # HU-006 Devolver una compra, HU-009 Exportar CSV, HU-014 Ver reporte.
        print("0. Cerrar sesión")
        opcion = input("Elige una opción: ").strip()
        if opcion == "1":
            registrar_prenda_desde_consola(inventario)
        elif opcion == "2":
            ver_catalogo(inventario)
        elif opcion == "3":
            filtrar_catalogo(inventario)
        elif opcion == "0":
            print("Sesión cerrada.")
            return
        else:
            print("Opción no válida. Intenta de nuevo.")


def ingresar_como_cliente(inventario):
    nombre = input("Escribe tu nombre: ")
    try:
        nombre = validar_nombre_cliente(nombre)
    except ErrorValidacion as error:
        print(error)
        return
    menu_cliente(nombre, inventario)


def ingresar_como_admin(inventario):
    clave = input("Escribe la clave de Admin: ")
    try:
        validar_clave_admin(clave)
    except ErrorValidacion as error:
        print(error)
        return
    menu_admin(inventario)


def main():
    # HU-013: aquí se cargará el estado guardado; por ahora inicia vacío.
    inventario = Inventario()
    while True:
        print("\n=== NöRA ===")
        print("1. Cliente")
        print("2. Admin")
        print("3. Salir")
        opcion = input("Elige una opción: ").strip()
        if opcion == "1":
            ingresar_como_cliente(inventario)
        elif opcion == "2":
            ingresar_como_admin(inventario)
        elif opcion == "3":
            print("Hasta pronto.")
            return
        else:
            print("Opción no válida. Intenta de nuevo.")


if __name__ == "__main__":
    main()
