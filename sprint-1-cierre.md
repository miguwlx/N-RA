# Sprint 1 — Review y Retrospective

## Sprint Review

**Sprint Goal:** Permitir ingresar según el rol y consultar un catálogo de prendas validado.

**Historias terminadas (Done):** HU1 (#1), HU2 (#2) y HU3 (#3).

**Historias no terminadas y por qué:** Ninguna.

**Avance:** Se completaron las tres historias seleccionadas (HU1, HU2 y HU3) y se cumplieron todas las tareas planificadas: el modelo Product con sus validaciones, el Inventory para registrar y listar, los menús de Cliente y Admin y las pruebas de rechazos. El Sprint Goal se cumplió: el sistema permite ingresar según el rol y consultar un catálogo de prendas validado. No quedaron historias pendientes para el siguiente sprint. Enlaces a los Issues y Pull Requests como evidencia: [completar].

**Qué se demostró:** El incremento permite ingresar como Cliente con un nombre o como Admin con una clave, cada uno con su menú y con cierre de sesión; que el Admin registre prendas validando cada dato y rechazando los códigos duplicados; y que el Cliente y el Admin consulten el catálogo ordenado por código, con las prendas agotadas marcadas y con filtro por categoría.

**Feedback recibido:** Los comentarios sobre el incremento fueron los dos ajustes descritos arriba, validar el código repetido al escribirlo y poder cancelar el registro con 0, y la duda sobre el idioma de los nombres. Todos quedaron resueltos.

**Cambios al Product Backlog:** Los ajustes se resolvieron dentro de la historia HU2, sin necesidad de historias nuevas.

## Impedimentos y ajustes

**Impedimentos y dudas resueltas:** Quedaron en duda varias decisiones que las historias no fijaban, y todas se resolvieron antes de dar el sprint por cerrado. Los nombres del código podían ir en inglés, como en la lista de tareas (por ejemplo Inventory.add_product), o en español, y se resolvió usar español (Prenda, Inventario y registrar_prenda). Se definió que el código de la prenda tiene el formato de tres letras, un guion y tres números (por ejemplo CAM-001), que el Admin ingresa con una clave de práctica y que el identificador de cada compra será un número entero que aumenta de uno en uno.

**Ajustes:** Al probar el registro de prendas en la consola se detectó que el código repetido solo se rechazaba al final, después de escribir los siete datos, y que no existía forma de cancelar un registro a medias. Se ajustó para que el código se valide apenas se escribe (formato y duplicado) y para que escribir 0 cancele el registro.

## Sprint Retrospective

**Qué funcionó bien:** Las reglas de negocio quedaron en el modelo y en el inventario y no en los menús, lo que permitió probar los rechazos de forma automática sin escribir nada en la consola.

**Qué debemos mejorar:** Varias decisiones no estaban fijadas en las historias (idioma de los nombres, formato del código, valor de la clave y formato del identificador de compra) y se resolvieron preguntando en pleno desarrollo; además, el rechazo del código duplicado se detectó al probar en la consola y no antes.

**Mejora acordada para el Sprint 2 (una, concreta):** Dejar por escrito, antes de programar cada historia, las decisiones que el documento de historias no define.
