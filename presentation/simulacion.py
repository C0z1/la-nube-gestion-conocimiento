"""Simulación del impacto mensual del asistente en La Nube (cifras SIMULADAS para la presentación).

Las bases salen del corpus (D61, D67, D69, D70, D64); todo lo marcado "supuesto" es una estimación
nuestra, no un dato medido. Cambia un supuesto y vuelve a correr: python presentation/simulacion.py
"""

BASE = {  # datos del corpus
    "ventas_semana": 182_400,      # D61 reporte semanal de ventas
    "pago_tarjeta": 0.34,          # D61 34 % de las ventas con tarjeta
    "horas_caida_internet": 3,     # D69 caída del jueves de 10 a 13
    "fiado_por_cobrar": 21_500,    # D70 saldo que deben los clientes
    "kg_res_semana": 60,           # D31 orden de compra de res
    "puntos_rendimiento_perdidos": 2,  # D67 rendimiento 2 puntos abajo del mes pasado
}
SUPUESTOS = {
    "dias_mes": 30, "horas_abierto": 15,             # D48: 7 am a 10 pm
    "ticket_promedio": 100,                          # pesos
    "preguntas_dia": 12, "min_por_pregunta": 3,      # preguntas a la encargada que detienen la caja
    "resuelve_asistente": 0.70,                      # parte de esas preguntas que el asistente contesta solo
    "preguntas_en_pico": 4, "abandono_por_espera": 0.25,  # clientes que se van si la fila se detiene en hora pico
    "caidas_mes": 2, "tarjeta_perdida_sin_saber": 0.40,  # ventas con tarjeta que se pierden si el cajero no sabe el cobro manual
    "recupera_cobro_manual": 0.50,                   # la terminal también puede fallar: solo la mitad se recupera
    "cobranza_extra": 0.05,                          # parte del fiado que se recupera al ver saldo y límite en la caja
    "precio_kg_res": 160, "puntos_recuperados": 1,   # de los 2 puntos de rendimiento perdidos
    "tickets_dia": 260, "venta_sugerida_tasa": 0.01, "venta_sugerida_monto": 20,  # promoción sugerida al cobrar
    "costo_hora_encargada": 70,
    "costo_mes": 600,                                # LLM opcional + 4 h de mantenimiento del corpus
}


def simular(b=BASE, s=SUPUESTOS):
    d = s["dias_mes"]
    venta_hora = b["ventas_semana"] / 7 / s["horas_abierto"]
    palancas = {  # pesos al mes
        "Fila que no se detiene": s["preguntas_en_pico"] * s["resuelve_asistente"] * s["abandono_por_espera"]
        * s["ticket_promedio"] * d,
        "Cobro con tarjeta sin internet": s["caidas_mes"] * b["horas_caida_internet"] * venta_hora * b["pago_tarjeta"]
        * s["tarjeta_perdida_sin_saber"] * s["recupera_cobro_manual"],
        "Cobranza de fiado": b["fiado_por_cobrar"] * s["cobranza_extra"],
        "Menos merma en carnicería": b["kg_res_semana"] * 4 * s["puntos_recuperados"] / 100 * s["precio_kg_res"],
        "Promoción sugerida al cobrar": s["tickets_dia"] * s["venta_sugerida_tasa"] * s["venta_sugerida_monto"] * d,
        "Tiempo de la encargada": s["preguntas_dia"] * s["min_por_pregunta"] * s["resuelve_asistente"] / 60
        * s["costo_hora_encargada"] * d,
    }
    palancas = {k: round(v, -1) for k, v in palancas.items()}
    total = sum(palancas.values())
    ventas_mes = b["ventas_semana"] / 7 * d
    return {"palancas": palancas, "total_mes": total, "ventas_mes": round(ventas_mes, -3),
            "pct_ventas": round(total / ventas_mes * 100, 1), "costo_mes": s["costo_mes"],
            "neto_mes": total - s["costo_mes"], "neto_anio": (total - s["costo_mes"]) * 12,
            "conservador_mes": round(total / 2 - s["costo_mes"], -1),
            # solo las palancas que no dependen de clientes ni de la terminal
            "sin_promo_ni_caidas": total - palancas["Promoción sugerida al cobrar"] - palancas["Cobro con tarjeta sin internet"],
            "horas_encargada_mes": round(s["preguntas_dia"] * s["min_por_pregunta"] * s["resuelve_asistente"] / 60 * d, 1)}


if __name__ == "__main__":
    r = simular()
    assert r["total_mes"] == sum(r["palancas"].values()) and r["neto_mes"] > 0
    for k, v in sorted(r["palancas"].items(), key=lambda x: -x[1]):
        print(f"{k:32s} ${v:>8,.0f}")
    print({k: v for k, v in r.items() if k != "palancas"})
