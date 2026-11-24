# Discurso — Asistente de La Nube (≈10 minutos)

Diapositivas: https://claude.ai/artifact/6t6j8niso1rLXymJKEiCZg · Un bloque por diapositiva. *Cursivas* = lo que haces, no lo que dices.
Ritmo: unas 130 palabras por minuto. La demo en vivo (diapositiva 4) es opcional; si falta tiempo, lee la diapositiva.
Las cifras de dinero son **simuladas** (`presentation/simulacion.py`); dilo siempre así. Las métricas de calidad son **medidas** (`evaluate.py`).

---

## 1 · Portada (0:00 – 0:35)

Buenas tardes. Hoy no les vengo a presentar solo un proyecto escolar: les vengo a presentar una herramienta que una tienda de verdad necesita.

La Nube es un mini súper de barrio con dos cajas y una carnicería. Todo lo que sabe el negocio —cómo hacer el corte, cómo cobrar si se cae el internet, quién nos debe, cuánto rinde la carne— vive en la cabeza de dos personas. El Asistente de La Nube pone ese conocimiento en la caja, donde nacen las preguntas. Les voy a mostrar el problema, la solución funcionando, cuánto dinero puede generar y cómo la llevamos al negocio.

## 2 · El problema (0:35 – 1:35)

En un mini súper la encargada contesta las mismas preguntas todos los días: cómo hago el corte, cómo le cobro fiado a este cliente, qué hago si se cae el internet. Estimamos unas doce preguntas al día, de tres minutos cada una: más de media hora de caja detenida diaria.

Y eso no es solo tiempo. En la hora pico, de seis a ocho de la noche, una fila detenida es un cliente que deja la canasta y se va. Además hay dinero parado: los propios reportes de la tienda dicen que los clientes deben veintiún mil quinientos pesos de fiado, con tres cuentas atrasadas más de treinta días. Y el conocimiento se pierde: el rendimiento de la carne bajó dos puntos en un mes, y cuando alguien renuncia, lo que sabía se va con esa persona.

## 3 · La solución (1:35 – 2:20)

La solución es una sola aplicación web, en español, pensada para usarse en la caja.

**Preguntar:** el cajero escribe como habla y el asistente contesta con los documentos de la tienda, citando la fuente. Si le preguntas algo que no es de la tienda, dice que no lo encontró: no inventa, y eso es lo que la hace confiable. **Buscar** entiende el significado, no solo las palabras. **Te puede interesar** recomienda lo siguiente que vas a necesitar. Y **Clasificar** archiva solo cada documento nuevo. Detrás hay un mapa de conocimiento que amplía la ontología de la Fase I.

## 4 · Ejemplo real 1: el cajero pregunta (2:20 – 3:15)

Estas son salidas reales de la app. Un cajero termina su turno y pregunta cómo hacer el corte. Respuesta: F8, opción 5, con la fuente, el manual D04. Nadie tuvo que llamar a la encargada.

Segundo caso, el que cuesta dinero: se cae el internet y el cliente quiere pagar con tarjeta. Si el cajero no sabe qué hacer, la venta se pierde. El asistente le dice: cobro manual, cobra en la terminal y escribe el número de autorización. Venta salvada.

Tercer caso: le pido una receta de pastel y me dice que no lo encontró. Prefiere decir "no sé" antes que inventar.

*Demo opcional: en la pestaña Preguntar, toca el botón "¿Qué tecla presiono para vender a crédito?" y luego "🧪 Receta de pastel de chocolate".*

## 5 · Ejemplo real 2: la encargada y el dueño (3:15 – 4:05)

La encargada quiere saber quién está cancelando muchos tickets y lo escribe tal cual. Ningún documento tiene esas palabras, pero el sistema entiende el significado y trae primero el reporte de cancelaciones y auditoría. Las cancelaciones son una de las fugas de dinero más comunes en una tienda.

El dueño busca "quién nos debe dinero" y abre la política de crédito. En ese momento la barra de recomendaciones le pone enfrente el reporte de cobranza, los saldos de cada cliente y los pagos a cuenta. En tres clics pasó de una duda a una lista de quién debe, cuánto y desde cuándo. Ahí empieza la cobranza, y ahí empieza el dinero.

## 6 · Ejemplo real 3: el conocimiento se ordena solo (4:05 – 4:45)

Cuando llega un documento nuevo, como un faltante de 120 pesos en la caja 2, el clasificador lo archiva como Reporte; una recepción de 30 cajas de refresco queda como Inventario. Por eso la base de conocimiento no se desordena con el tiempo.

A la derecha está el mapa de conocimiento de la app: puntos para documentos, rombos para temas y, en gris, las clases de nuestra ontología de la Fase I. El modelo conceptual del curso se volvió algo que se puede explorar.

## 7 · Cómo funciona (4:45 – 5:25)

Tres capas. Las fuentes: 102 documentos en español —los procedimientos vienen de los manuales reales del punto de venta— y la ontología de la Fase I, ampliada a 560 tripletas. El motor: combina palabras exactas, para cosas como F6 o CFDI, con significado, usando un modelo multilingüe que corre sin tarjeta gráfica; encima están el clasificador, el recomendador y un chatbot que solo responde con lo que encontró. Y la app web, publicada gratis, que también puede correr en el servidor de la tienda. Todo se mide contra respuestas que etiqueté a mano.

## 8 · Resultados medidos (5:25 – 6:15)

¿Funciona de verdad? En 17 de 18 preguntas la respuesta trae el dato correcto, la fuente correcta siempre aparece entre las tres primeras y rechazó todas las preguntas fuera de tema. En búsqueda, cuando la gente pregunta con sus palabras, el primer resultado correcto pasó de 0.52 con la búsqueda de la Fase I a 0.72. El clasificador acierta 82 por ciento de las veces, y las recomendaciones son ocho veces mejores que el azar.

[Completar: en la prueba de usabilidad con N personas el puntaje SUS fue __; arriba de 68 es mejor que el promedio.]

## 9 · Simulación: cómo genera más ventas (6:15 – 7:40)

Ahora, lo que le importa al dueño: ¿cuánto dinero deja? Hicimos una simulación con datos de los reportes de la tienda —182 mil pesos de ventas a la semana, 21 mil de fiado, la caída de internet, el rendimiento de la carne— y con supuestos explícitos que están en el repositorio.

Hay seis palancas. La más grande es la fila: si el asistente resuelve el 70 por ciento de las dudas en la hora pico, menos clientes se van; unos 2,100 pesos al mes. La promoción sugerida al cobrar: si solo uno de cada cien clientes agrega 20 pesos, son 1,560. La cobranza: ver saldo y límite en la caja recupera un 5 por ciento del fiado, unos mil pesos. Después vienen el tiempo de la encargada, el cobro con tarjeta cuando se cae el internet y la merma de carnicería.

Total: unos 6,700 pesos al mes, menos del uno por ciento de las ventas, contra un costo de 600. Son unos 73 mil pesos netos al año. Y lo importante: aunque solo se cumpla la mitad, sigue dejando 2,760 al mes; solo la cobranza de fiado ya paga el costo. Son cifras simuladas, y por eso proponemos validarlas con un piloto.

## 10 · Cómo lo llevamos al negocio (7:40 – 8:45)

Cuatro pasos, y cada uno se tiene que pagar antes de pasar al siguiente.

Uno, el primer mes: un piloto en la caja 1, con el asistente en una tablet. Medimos preguntas resueltas sin la encargada, clientes que dejan la fila y fiado cobrado; así los supuestos se vuelven datos. Dos: lo metemos dentro del punto de venta; una tecla abre el asistente, y al cobrar fiado con F6 aparecen saldo, límite y días de atraso. Tres, vender más en cada ticket: al cobrar, sugiere la promoción o el complemento. Ya sabemos que funciona: el 2 por 1 en bebidas subió el ticket 12 por ciento porque la gente se llevó botanas. Y si algo se agota, propone un sustituto en vez de perder la venta. Cuatro: clientes que regresan, con recordatorios de fiado y ofertas por WhatsApp a quienes ya tienen puntos de lealtad.

## 11 · Impacto en la gestión del conocimiento (8:45 – 9:25)

Más allá del dinero, este es el corazón del curso. En capacitación, el cajero nuevo aprende preguntando en la caja. En recuperación, la respuesta llega en segundos con su fuente. En reutilización, lo que aprendimos de una caída o de una merma alta ya no se olvida, porque los documentos relacionados aparecen juntos. Y en decisiones, el dueño tiene crédito, merma, cancelaciones y proveedores a la mano. El cambio de fondo: el conocimiento tácito de dos personas se vuelve explícito y se queda aunque alguien se vaya.

## 12 · Lo que proponemos (9:25 – 10:10)

Lo que proponemos es concreto: un piloto de treinta días en la caja 1. ¿Por qué ahora? Porque ya funciona, está publicada, en español y medida. Porque cuesta casi nada: corre sin tarjeta gráfica y puede vivir en el servidor de la tienda. Y porque es confiable: si algo no está en los documentos, lo dice.

¿Cómo sabremos que funcionó? Si resuelve al menos el 70 por ciento de las dudas sin la encargada, si se cobra más fiado que el mes anterior, si el ticket sube cuando hay sugerencia y si los usuarios le dan 68 o más en la escala de usabilidad.

El conocimiento de la tienda ya existe; este asistente lo pone a trabajar en la caja, donde se vende. Muchas gracias. La app está en https://la-nube-gestion-conocimiento-oh27aiwzetkmeuk37gfncd.streamlit.app para que la prueben ahora mismo.

---

## Preguntas probables

- **¿De dónde salen los $6,700?** De `presentation/simulacion.py`: las bases vienen de los reportes de la tienda (D61, D67, D69, D70) y cada supuesto está escrito ahí (70 % de dudas resueltas, 25 % de abandono en hora pico, 1 % de clientes que aceptan una sugerencia…). Por eso proponemos el piloto: para cambiar supuestos por datos.
- **¿Y si los supuestos están inflados?** Con la mitad del efecto sigue dejando $2,760 al mes, y solo la cobranza de fiado ($1,080) ya cubre el costo de $600.
- **¿Por qué no usar ChatGPT?** Contestaría con internet, no con los procedimientos de la tienda, y puede inventar. Este sistema solo responde con los documentos y los cita; un modelo de lenguaje se puede conectar, pero solo redacta lo que la búsqueda encontró.
- **¿Cómo midieron la precisión?** Clasificación: validación cruzada de 5 particiones sobre 102 documentos. Búsqueda: 26 consultas con los documentos relevantes marcados a mano (P@3, R@5, MRR). Chatbot: 18 preguntas con respuesta conocida.
- **¿Los datos son reales?** Los procedimientos salen de los manuales reales del punto de venta, anonimizados. Las cifras de ventas y algunos reportes son ilustrativos.
- **¿Qué falla todavía?** Algunas frases coloquiales: "¿cuánto vendimos ayer?" responde que no lo encontró, y "precio del bitcoin" contesta con la política de precios. Lo vamos a mejorar con las preguntas reales del piloto.
