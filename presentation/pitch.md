# Pitch de venta — Asistente de La Nube (≈5 minutos)

Diapositivas: https://claude.ai/artifact/UFj7KZSCB3CufySLwCfVFr · Un bloque por diapositiva. *Cursivas* = lo que haces.
Público: el dueño de un mini súper. Tono: directo, de tú, sin tecnicismos. Las cifras de dinero son **simuladas** (`presentation/simulacion.py`); las de calidad son **medidas** (`evaluate.py`).

---

## 1 · El gancho (0:00 – 0:25)

*Pausa antes de hablar. Mira al público.*

¿Cuánto dinero pierdes cada vez que tu cajero no sabe algo? No sabe cómo cobrar con tarjeta cuando se cae el internet, no sabe si este cliente todavía tiene crédito, no sabe cómo hacer el corte. Cada duda detiene la caja. Y la caja es el único lugar de la tienda donde entra dinero.

## 2 · El dolor (0:25 – 1:00)

La encargada contesta unas doce dudas al día, siempre las mismas. Son más de media hora de caja detenida, y en la hora pico una fila detenida es un cliente que deja la canasta y se va. Mientras tanto hay veintiún mil quinientos pesos de fiado sin cobrar, con tres cuentas atrasadas más de un mes; eso lo dice tu propio reporte. Y el día que la encargada renuncia, todo lo que sabía se va con ella.

## 3 · La solución (1:00 – 1:30)

Tu cajero pregunta y el asistente contesta con tus propios manuales, reportes y políticas. Eso se traduce en tres cosas: **vende más**, porque la fila no se detiene; **cobra más**, porque quién te debe, cuánto y desde cuándo está a tres clics; y **entrena solo**, porque el cajero nuevo aprende preguntando en la caja.

## 4 · Así se ve (1:30 – 2:15)

Estas respuestas son reales. Se cae el internet y el cliente quiere pagar con tarjeta: cobro manual, cobra en la terminal y escribe la autorización. Venta salvada, y te dice de qué manual lo sacó. Fin de turno: F8, opción 5. Y si le preguntas una receta de pastel, te dice que no lo encontró. No inventa, y por eso le puedes creer.

*Si hay tiempo: abre la app, pestaña Preguntar, toca "¿Qué hago si se cae el internet?" y luego "🧪 Receta de pastel de chocolate".*

## 5 · Cuánto dinero deja (2:15 – 3:05)

Simulamos seis palancas con los reportes de la tienda. La fila que no se detiene: unos 2,100 pesos al mes. La promoción sugerida al cobrar: si uno de cada cien clientes agrega veinte pesos, 1,560. La cobranza de fiado: mil pesos. Más el tiempo de la encargada, el cobro sin internet y la merma.

Total: unos **6,700 pesos al mes, 73 mil netos al año**. Y aunque solo funcione la mitad, sigue dejando dinero: la cobranza de fiado sola ya paga el servicio.

## 6 · Por qué confiar (3:05 – 3:35)

Lo probamos antes de pedirte un peso. En 17 de 18 preguntas trae el dato correcto. Rechazó las tres preguntas fuera de tema. Encuentra la respuesta 38 % mejor que buscar por palabras. Y no compras nada: corre sin tarjeta gráfica, en la nube o en el servidor de tu tienda, y tus datos se quedan contigo.

## 7 · La oferta (3:35 – 4:10)

Treinta días en tu caja 1, **sin costo**. Cargamos tus documentos, lo instalamos en una tablet junto a la caja y cada semana te damos tres números: dudas resueltas, fila y fiado cobrado. Después, **600 pesos al mes**, todo incluido: menos de lo que recupera la cobranza. Y el riesgo es nuestro: si en 30 días no resuelve siete de cada diez dudas sin la encargada, no pagas nada.

## 8 · Y después (4:10 – 4:40)

Esto crece contigo. Luego lo metemos dentro de tu punto de venta, con saldo y límite del cliente al cobrar fiado. Después, más venta por ticket: sugiere la promoción al cobrar; tu 2×1 ya subió el ticket 12 %. Y al final, clientes que regresan, con recordatorios y ofertas por WhatsApp. Cada paso se paga antes del siguiente.

## 9 · El cierre (4:40 – 5:00)

Así que la pregunta es una sola: **¿empezamos el lunes en tu caja 1?** Lo que sabe tu tienda ya existe; pongámoslo a trabajar donde se vende. La app está en el enlace: pruébenla ahora mismo e intenten hacerla fallar. Gracias.

---

## Objeciones y respuestas

- **"Mis cajeros no van a usar una app."** Escriben como hablan y tocan botones de ejemplo; en la prueba no necesitas explicarles nada. Y si no la usan, el piloto lo muestra y no pagas.
- **"¿Y si se equivoca?"** Siempre dice de qué documento sacó la respuesta, y si no lo sabe, lo dice. En las pruebas acertó 17 de 18.
- **"¿De dónde salen los 6,700 pesos?"** De tus reportes (ventas, fiado, rendimiento, caída de internet) más supuestos escritos uno por uno en `presentation/simulacion.py`. Por eso el piloto: cambia supuestos por datos.
- **"¿Qué pasa con mis datos?"** Puede correr en el servidor que ya tienes en la tienda; nada tiene que salir de ahí.
- **"¿Por qué no uso ChatGPT?"** ChatGPT no conoce tus procedimientos y puede inventar. Este solo responde con tus documentos y los cita.
- **"$600 es caro."** Es menos de lo que la simulación dice que recupera solo la cobranza de fiado, y el primer mes no cuesta nada.
