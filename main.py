"""NöRA - tienda de ropa (aplicación de consola).

Funciones: ingreso por rol, catálogo y filtros, compras, devoluciones, precio y
stock, guardado y carga en JSON, reporte CSV y resumen en pantalla.
"""
from product import CATEGORIAS, COLORES, TALLAS, ErrorValidacion
from reports import ReporteCSV, ReporteTexto
from storage import Almacenamiento, ErrorAlmacenamiento

# Clave de práctica del proyecto académico.
CLAVE_ADMIN = "123456"


# ---------- Reglas de ingreso por rol ----------
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


# ---------- Guardado automático ----------
def guardar_cambios(inventario, almacenamiento):
    """Guarda el estado tras una operación válida. Si falla, avisa y el programa sigue."""
    if almacenamiento is None:
        return
    try:
        almacenamiento.guardar(inventario)
    except ErrorAlmacenamiento as error:
        print(f"Advertencia: {error}")
        print("Los cambios pueden existir solo en memoria.")


# ---------- Presentación ----------
def formatear_tabla(encabezados, filas):
    """Tabla de texto con columnas del ancho justo."""
    todas = [tuple(encabezados)] + [tuple(fila) for fila in filas]
    anchos = [max(len(fila[i]) for fila in todas) for i in range(len(encabezados))]
    lineas = ["  ".join(celda.ljust(ancho) for celda, ancho in zip(fila, anchos)).rstrip()
              for fila in todas]
    lineas.insert(1, "-" * len(lineas[0]))
    return "\n".join(lineas)


def formatear_catalogo(prendas):
    """Catálogo como tabla; las prendas sin stock salen como AGOTADA."""
    filas = [
        (prenda.codigo, prenda.nombre, prenda.categoria, prenda.talla, prenda.color,
         f"{prenda.precio:,.2f}", str(prenda.stock),
         "AGOTADA" if prenda.esta_agotada() else "")
        for prenda in prendas
    ]
    return formatear_tabla(
        ("Código", "Nombre", "Categoría", "Talla", "Color", "Precio", "Stock", "Estado"), filas)


def formatear_compras(compras, inventario, con_cliente):
    """Compras como tabla. El Admin ve además la columna Cliente."""
    encabezados = ["ID"] + (["Cliente"] if con_cliente else []) + \
                  ["Prenda", "Cantidad", "Total", "Devuelta"]
    filas = []
    for compra in compras:
        prenda = inventario.prendas[compra.codigo_prenda]
        fila = [str(compra.id_compra)] + ([compra.cliente] if con_cliente else []) + [
            f"{prenda.codigo} - {prenda.nombre}", str(compra.cantidad),
            f"{compra.total:,.2f}", "Sí" if compra.devuelta else "No"]
        filas.append(fila)
    return formatear_tabla(encabezados, filas)


# ---------- Catálogo ----------
def ver_catalogo(inventario):
    """Muestra el catálogo completo, o un mensaje si no hay prendas registradas."""
    prendas = inventario.listar_catalogo()
    if not prendas:
        print("No hay prendas registradas.")
        return
    print()
    print(formatear_catalogo(prendas))


def filtrar_catalogo(inventario):
    """Filtra por categoría, talla y color; Enter omite cada filtro."""
    print("\n--- Filtrar catálogo (Enter para omitir un filtro) ---")
    print(f"Categorías: {', '.join(CATEGORIAS)}")
    categoria = input("Categoría: ").strip() or None
    print(f"Tallas: {', '.join(TALLAS)}")
    talla = input("Talla: ").strip() or None
    print(f"Colores: {', '.join(COLORES)}")
    color = input("Color: ").strip() or None
    try:
        prendas = inventario.listar_catalogo(categoria, talla, color)
    except ErrorValidacion as error:
        print(error)
        return
    if not prendas:
        if categoria is None and talla is None and color is None:
            print("No hay prendas registradas.")
        else:
            print("Ninguna prenda cumple el filtro.")
        return
    print()
    print(formatear_catalogo(prendas))


# ---------- Registro de prendas ----------
def registrar_prenda_desde_consola(inventario, almacenamiento=None):
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
    guardar_cambios(inventario, almacenamiento)


# ---------- Pedir una prenda existente (compras y mantenimiento) ----------
def pedir_prenda_existente(inventario):
    """Pide un código hasta que exista; con 0 cancela y devuelve None."""
    while True:
        codigo = input("Código de la prenda (0 para cancelar): ")
        if codigo.strip() == "0":
            print("Operación cancelada.")
            return None
        try:
            return inventario.obtener_prenda(codigo)
        except ErrorValidacion as error:
            print(error)


# ---------- Compras del Cliente ----------
def comprar_prenda(nombre, inventario, almacenamiento=None):
    """El Cliente elige una prenda y una cantidad; si la compra es válida se guarda."""
    print("\n--- Comprar una prenda ---")
    prenda = pedir_prenda_existente(inventario)
    if prenda is None:
        return
    print(f"{prenda.codigo} - {prenda.nombre} | Precio: {prenda.precio:,.2f} | Stock: {prenda.stock}")
    cantidad = input("Cantidad: ")
    try:
        compra = inventario.comprar(nombre, prenda.codigo, cantidad)
    except ErrorValidacion as error:
        print(f"No se registró la compra. {error}")
        return
    print(f"Compra registrada: #{compra.id_compra} - {prenda.nombre} x{compra.cantidad}. "
          f"Total: {compra.total:,.2f}")
    guardar_cambios(inventario, almacenamiento)


def ver_mis_compras(nombre, inventario):
    """Solo las compras hechas con el nombre del cliente que ingresó."""
    compras = inventario.compras_de_cliente(nombre)
    if not compras:
        print("Aún no tienes compras.")
        return
    print()
    print(formatear_compras(compras, inventario, con_cliente=False))


# ---------- Compras y mantenimiento del Admin ----------
def ver_todas_las_compras(inventario):
    """Todas las compras de todos los clientes, con su cliente y estado."""
    compras = inventario.listar_todas_las_compras()
    if not compras:
        print("No hay compras registradas.")
        return
    print()
    print(formatear_compras(compras, inventario, con_cliente=True))


def devolver_compra_desde_consola(inventario, almacenamiento=None):
    """Muestra todas las compras y pide el identificador a devolver (0 cancela)."""
    print("\n--- Devolver una compra ---")
    if not inventario.listar_todas_las_compras():
        print("No hay compras registradas.")
        return
    ver_todas_las_compras(inventario)
    while True:
        identificador = input("\nIdentificador de la compra a devolver (0 para cancelar): ")
        if identificador.strip() == "0":
            print("Devolución cancelada.")
            return
        try:
            compra = inventario.devolver_compra(identificador)
            break
        except ErrorValidacion as error:
            print(error)
    prenda = inventario.prendas[compra.codigo_prenda]
    print(f"Devolución registrada: compra #{compra.id_compra}. "
          f"Stock de {prenda.codigo}: {prenda.stock}.")
    guardar_cambios(inventario, almacenamiento)


def actualizar_precio_desde_consola(inventario, almacenamiento=None):
    """Cambia el precio de una prenda existente."""
    print("\n--- Actualizar precio ---")
    prenda = pedir_prenda_existente(inventario)
    if prenda is None:
        return
    print(f"{prenda.codigo} - {prenda.nombre} | Precio actual: {prenda.precio:,.2f}")
    nuevo_precio = input("Nuevo precio: ")
    try:
        inventario.actualizar_precio(prenda.codigo, nuevo_precio)
    except ErrorValidacion as error:
        print(f"No se actualizó el precio. {error}")
        return
    print(f"Precio actualizado: {prenda.codigo} ahora cuesta {prenda.precio:,.2f}.")
    guardar_cambios(inventario, almacenamiento)


def reponer_stock_desde_consola(inventario, almacenamiento=None):
    """Suma unidades al stock de una prenda existente."""
    print("\n--- Reponer stock ---")
    prenda = pedir_prenda_existente(inventario)
    if prenda is None:
        return
    print(f"{prenda.codigo} - {prenda.nombre} | Stock actual: {prenda.stock}")
    cantidad = input("Cantidad a sumar: ")
    try:
        inventario.reponer_stock(prenda.codigo, cantidad)
    except ErrorValidacion as error:
        print(f"No se repuso el stock. {error}")
        return
    print(f"Stock repuesto: {prenda.codigo} ahora tiene {prenda.stock} unidades.")
    guardar_cambios(inventario, almacenamiento)


# ---------- Reportes del Admin ----------
def exportar_csv(inventario):
    """Exporta reports/ventas.csv y muestra la ruta generada."""
    try:
        ruta = ReporteCSV().generar(inventario)
    except OSError as error:
        print(f"No se pudo exportar el reporte: {error}")
        return
    print(f"Reporte exportado en: {ruta}")


def ver_reporte(inventario):
    """Resumen en pantalla. Usa la misma operación generar() que el CSV."""
    print()
    print(ReporteTexto().generar(inventario))


# ---------- Menús ----------
def menu_cliente(nombre, inventario, almacenamiento=None):
    """Menú del Cliente. Nunca muestra opciones de Admin."""
    while True:
        print(f"\n--- Menú Cliente: {nombre} ---")
        print("1. Ver catálogo")
        print("2. Filtrar catálogo")
        print("3. Comprar una prenda")
        print("4. Mis compras")
        print("0. Cerrar sesión")
        opcion = input("Elige una opción: ").strip()
        if opcion == "1":
            ver_catalogo(inventario)
        elif opcion == "2":
            filtrar_catalogo(inventario)
        elif opcion == "3":
            comprar_prenda(nombre, inventario, almacenamiento)
        elif opcion == "4":
            ver_mis_compras(nombre, inventario)
        elif opcion == "0":
            print("Sesión cerrada.")
            return
        else:
            print("Opción no válida. Elige una opción del menú.")


def menu_admin(inventario, almacenamiento=None):
    """Menú del Admin."""
    while True:
        print("\n--- Menú Admin ---")
        print("1. Registrar prenda")
        print("2. Ver catálogo")
        print("3. Filtrar catálogo")
        print("4. Ver todas las compras")
        print("5. Devolver una compra")
        print("6. Actualizar precio")
        print("7. Reponer stock")
        print("8. Exportar CSV")
        print("9. Ver reporte")
        print("0. Cerrar sesión")
        opcion = input("Elige una opción: ").strip()
        if opcion == "1":
            registrar_prenda_desde_consola(inventario, almacenamiento)
        elif opcion == "2":
            ver_catalogo(inventario)
        elif opcion == "3":
            filtrar_catalogo(inventario)
        elif opcion == "4":
            ver_todas_las_compras(inventario)
        elif opcion == "5":
            devolver_compra_desde_consola(inventario, almacenamiento)
        elif opcion == "6":
            actualizar_precio_desde_consola(inventario, almacenamiento)
        elif opcion == "7":
            reponer_stock_desde_consola(inventario, almacenamiento)
        elif opcion == "8":
            exportar_csv(inventario)
        elif opcion == "9":
            ver_reporte(inventario)
        elif opcion == "0":
            print("Sesión cerrada.")
            return
        else:
            print("Opción no válida. Elige una opción del menú.")


def ingresar_como_cliente(inventario, almacenamiento=None):
    """Pide el nombre del Cliente; si es válido abre su menú."""
    nombre = input("Escribe tu nombre: ")
    try:
        nombre = validar_nombre_cliente(nombre)
    except ErrorValidacion as error:
        print(error)
        return
    menu_cliente(nombre, inventario, almacenamiento)


def ingresar_como_admin(inventario, almacenamiento=None):
    """Pide la clave del Admin; solo con la clave correcta abre su menú."""
    clave = input("Escribe la clave de Admin: ")
    try:
        validar_clave_admin(clave)
    except ErrorValidacion as error:
        print(error)
        return
    menu_admin(inventario, almacenamiento)


def ciclo_principal(inventario, almacenamiento):
    """Menú principal: elegir rol o salir. Se repite hasta elegir Salir."""
    while True:
        print("\n=== NöRA ===")
        print("1. Cliente")
        print("2. Admin")
        print("3. Salir")
        opcion = input("Elige una opción: ").strip()
        if opcion == "1":
            ingresar_como_cliente(inventario, almacenamiento)
        elif opcion == "2":
            ingresar_como_admin(inventario, almacenamiento)
        elif opcion == "3":
            print("Hasta pronto.")
            return
        else:
            print("Opción no válida. Elige una opción del menú.")


def main(almacenamiento=None):
    """Carga el estado guardado desde JSON y abre el menú principal.

    Un archivo dañado o inconsistente detiene la aplicación SIN sobrescribirlo
    """
    if almacenamiento is None:
        almacenamiento = Almacenamiento()
    try:
        inventario = almacenamiento.cargar()
    except ErrorAlmacenamiento as error:
        print(error)
        print("La aplicación se detuvo para proteger los datos existentes.")
        return
    try:
        ciclo_principal(inventario, almacenamiento)
    except (EOFError, KeyboardInterrupt):
        print("\nPrograma terminado.")


if __name__ == "__main__":
    main()
