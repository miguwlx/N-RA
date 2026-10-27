# Sprint 3 — Review y Retrospective

## Sprint Goal

**Sprint Goal:** Conservar el estado entre sesiones, emitir reportes de ventas e inventario y fortalecer la calidad con filtros, validaciones y pruebas.

**Historias terminadas (Done):** HU8 (#8), HU13 (#13), HU9 (#9), HU14 (#14), HU12 (#12) y HU10 (#10).

**Historias no terminadas y por qué:** Ninguna.

**Avance:** El incremento del sprint corresponde al sistema completo, con las seis historias seleccionadas (HU8, HU13, HU9, HU14, HU12 y HU10): guardado y carga en JSON, reporte CSV, resumen en pantalla, filtros por talla y color y manejo de entradas inválidas en todos los menús, con pruebas automatizadas para cada criterio. Se cumplieron todas las tareas planificadas y ninguna historia quedó pendiente para iteraciones posteriores. Enlaces a los Issues y Pull Requests como evidencia: [completar].

**Qué se demostró:** El incremento permite que el estado se guarde después de cada operación válida y se recupere al abrir la aplicación, sin sobrescribir un archivo dañado; que el Admin exporte reports/ventas.csv y vea un resumen en pantalla cuyas unidades vendidas coinciden con las del CSV, sin contar las compras devueltas; que el Cliente y el Admin filtren el catálogo por categoría, talla y color; y que ninguna entrada inválida cierre el programa.

**Feedback recibido:** Se validó positivamente la persistencia automática en JSON y la precisión del reporte CSV. Se sugirió asegurar que al cargar un archivo corrupto se genere una alerta sin perder los datos previos de sesión, lo cual quedó verificado en las pruebas automatizadas.

**Cambios al Product Backlog:** Todos los criterios adicionales y casos de borde identificados se cubrieron dentro de los escenarios de prueba del sprint, sin requerir nuevas historias de usuario.

## Impedimentos y ajustes

**Impedimentos y dudas resueltas:** Surgió la duda sobre si el reporte CSV debía incluir las transacciones con estado devuelto; se aclaró y confirmó que solo deben contabilizarse las ventas efectivas para mantener la coherencia con el resumen en pantalla. También se presentó el reto de asegurar que al recuperar los objetos desde JSON se reinstanciaran correctamente las validaciones originales de las clases Prenda y Compra, lo cual se resolvió reutilizando directamente sus constructores.

**Ajustes:** Mejora de la Retrospective del Sprint 2 que se aplicó: se contrastó cada historia detalladamente con la guía del sprint de forma previa a la entrega final, lo que evitó inconsistencias de formato y nombres. Cambios al plan durante el sprint: se priorizaron las pruebas del parser JSON y las validaciones de entrada antes de finalizar la exportación a CSV para garantizar estabilidad estructural.

## Sprint Retrospective

**Qué funcionó bien:** Reutilizar los constructores de Prenda y Compra al cargar el JSON hizo que las validaciones se apliquen solas, y calcular las unidades vendidas en una sola función compartida por el CSV y el resumen hizo que sus cifras coincidan.

**Qué debemos mejorar:** Definir y estandarizar la estructura de las excepciones personalizadas con mayor claridad desde el inicio del sprint para simplificar las aserciones en las pruebas unitarias.

**Mejora acordada (una, concreta):** Implementar un módulo unificado de excepciones antes de comenzar el desarrollo de futuros proyectos o extensiones del sistema.