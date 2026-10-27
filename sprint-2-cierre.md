# Sprint 2 — Review y Retrospective

## Sprint Review

**Sprint Goal:** Registrar compras y devoluciones sin perder la coherencia del stock, con el historial visible para el Cliente y el Admin.

**Historias terminadas (Done):** HU4 (#4), HU11 (#11), HU5 (#5), HU6 (#6) y HU7 (#7).

**Historias no terminadas y por qué:** Ninguna.

**Avance:** Se completaron las cinco historias seleccionadas (HU4, HU11, HU5, HU6 y HU7) y se cumplieron todas las tareas planificadas. El Sprint Goal se cumplió: se registran compras y devoluciones sin perder la coherencia del stock, y el historial es visible para el Cliente (sus compras) y para el Admin (todas). Ninguna historia pasó al Sprint 3. Enlaces a los Issues y Pull Requests como evidencia: [completar].

**Qué se demostró:** El incremento permite que el Cliente compre una prenda indicando la cantidad, con validación de existencia, cantidad y stock, precio unitario guardado y stock descontado, y que consulte solo sus compras; y que el Admin vea todas las compras con su identificador y estado, registre la devolución de una compra una sola vez reintegrando el stock, cambie el precio y reponga el stock sin alterar el total de las compras anteriores.

**Feedback recibido:** Los comentarios sobre el incremento fueron los ajustes descritos arriba: nombres en español, formato del código, decimales, cancelar con 0, Mis compras sin distinguir mayúsculas y código en minúscula. Todos quedaron resueltos.

**Cambios al Product Backlog:** Los ajustes se resolvieron dentro de las historias existentes, sin necesidad de historias nuevas.

## Impedimentos y ajustes

**Impedimentos y dudas resueltas:** Al contrastar el código con la guía paso a paso del sprint aparecieron diferencias que quedaron en duda y se resolvieron. La guía usaba nombres en inglés (Sale, sell, ValueError) y códigos como P001; se confirmó mantener los nombres en español y el formato de tres letras, guion y tres números. También se confirmó que los precios se muestran con decimales y que escribir 0 cancela las operaciones que piden un código o un identificador. Surgió además la duda de si el Cliente debía poder devolver compras; se confirmó que no, porque la historia HU-006 reserva la devolución al Admin y el Cliente solo se identifica con su nombre.

**Ajustes:** Mejora de la Retrospective del Sprint 1 que se aplicó: se dejaron por escrito las decisiones que las historias no fijaban (idioma de los nombres, formato del código, decimales y cancelar con 0) antes de cerrar el sprint. Se ajustó Mis compras para que compare el nombre sin distinguir mayúsculas (ana y Ana son la misma persona) y rechace el nombre vacío, como indica la guía. Se ajustó el código de la prenda para aceptarse en minúscula y guardarse siempre en mayúscula (cam-001 queda como CAM-001), de modo que un mismo código no puede registrarse dos veces con distinta escritura y funciona igual al registrar, comprar, actualizar el precio y reponer el stock.

## Sprint Retrospective

**Qué funcionó bien:** Validar todo antes de modificar nada hizo que ninguna operación rechazada alterara el stock ni el historial, y el sprint se apoyó en las validaciones y los menús construidos en el Sprint 1.

**Qué debemos mejorar:** Las diferencias entre la guía y el código se encontraron al revisar el sprint ya construido y no mientras se programaba.

**Mejora acordada para el Sprint 3 (una, concreta):** Contrastar cada historia con la guía del sprint antes de entregarla.
