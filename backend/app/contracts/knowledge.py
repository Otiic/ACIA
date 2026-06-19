"""Base de conocimiento legal para enriquecer el analisis de contratos.

En vez de mandar las leyes completas a Gemini (la LCT sola son ~41k tokens),
destilamos cada ley en un CHECKLIST compacto de puntos a verificar, y cada
modelo de contrato en su lista de CLAUSULAS ESPERADAS (para detectar faltantes).

El analisis ya clasifica el tipo de contrato, asi que el match
tipo -> referencia es un simple diccionario: no hace falta busqueda vectorial.

Estos textos son auditables y editables a mano. Si una ley cambia, se edita
aca y el analisis se actualiza sin tocar codigo.

Fuentes:
- alquiler   -> CCyC arts. 1187-1226 + reformas DNU 70/2023.
- compraventa-> Codigo Civil (Velez), arts. 1323-1433. (Ver nota de vigencia.)
- trabajo    -> Ley de Contrato de Trabajo N° 20.744 (texto ordenado).
"""

# ============================================================
# CHECKLISTS LEGALES (que debe verificar la IA contra la ley)
# ============================================================

_LEY_ALQUILER = """LEY APLICABLE: Locacion de inmueble — Codigo Civil y Comercial (CCyC) arts. 1187-1226, con reformas del DNU 70/2023.

Puntos a verificar:
- Forma: el contrato de inmueble debe ser por escrito, igual sus prorrogas y modificaciones (art. 1188).
- Plazo: si no se pacta, vivienda permanente = 2 años; otros destinos = 3 años (art. 1198). Maximo legal: 20 años habitacional / 50 años otros destinos (art. 1197).
- Precio y moneda: puede pactarse en pesos o moneda extranjera libremente; el locatario no puede exigir pagar en otra moneda (art. 1199).
- Ajuste del canon: valido cualquier indice (publico o privado) en la misma moneda pactada (art. 1199).
- Periodicidad de pago: libre, pero NO inferior a mensual (art. 1196).
- Deposito/garantia: monto, moneda y forma de devolucion se pactan libremente (art. 1196).
- Destino: el locatario debe respetar el destino acordado y no puede variarlo (arts. 1194, 1205).
- Expensas y cargas: el locatario paga solo expensas ordinarias/habituales y cargas de SU destino; NO paga expensas extraordinarias ni cargas que graven la cosa (art. 1209).
- Reparaciones: el locador conserva la cosa y hace reparaciones no imputables al locatario (art. 1201). Urgentes: el locatario puede hacerlas a cargo del locador tras 24 hs de notificacion; no urgentes, tras intimacion de minimo 10 dias.
- Resolucion por el locatario: puede resolver si el locador no conserva la cosa apta o falla la garantia de eviccion/vicios (art. 1220).
- Resolucion por el locador: cambio de destino, abandono/falta de conservacion, falta de pago de 2 periodos consecutivos, o causa fijada en el contrato (art. 1219).
- Resolucion anticipada por el locatario: en cualquier momento pagando el 10% del saldo del canon futuro (art. 1221).
- Desalojo por falta de pago (vivienda): exige intimacion previa fehaciente con plazo NO menor a 10 dias corridos (art. 1222).
- Fianza: cesa automaticamente al vencer el plazo; requiere consentimiento expreso del fiador para renovar/prorrogar (art. 1225).

Clausulas NULAS o abusivas a marcar:
- Impedir el ingreso de una persona incapaz o con capacidad restringida bajo guarda del locatario (art. 1195) -> NULA.
- Poner expensas extraordinarias o cargas que graven la cosa a cargo del locatario -> contrario al art. 1209.
- Periodicidad de pago menor a mensual -> contrario al art. 1196.
- Extender automaticamente la fianza a renovaciones/prorrogas -> NULA (art. 1225).
- Penalidad por rescision anticipada mayor al 10% del saldo futuro -> contrario al art. 1221."""

_LEY_COMPRAVENTA = """LEY APLICABLE: Compraventa — Codigo Civil (arts. 1323-1433).
NOTA: estas normas son del Codigo Civil de Velez; desde 2015 rige el CCyC (Ley 26.994). Usar como guia general.

Puntos a verificar:
- Definicion: una parte transfiere la propiedad de una cosa y la otra paga un precio cierto en dinero (art. 1323).
- Elementos esenciales: cosa determinada o determinable + precio cierto. Si falta un requisito esencial, no es compraventa aunque las partes lo llamen asi (arts. 1326, 1333).
- Precio cierto: fijado por las partes, por un tercero designado, o por referencia a otra cosa cierta (art. 1349). Si queda al arbitrio de UNA sola parte -> contrato NULO (art. 1355).
- Pago mixto (parte dinero, parte cosa): es permuta si la cosa vale mas; venta en caso contrario (art. 1356).
- Cosa: pueden venderse cosas presentes o futuras no prohibidas (art. 1327). La cosa ajena no puede venderse; hacerlo genera daños si el comprador la ignoraba (art. 1329).
- Inmueble por superficie: si se vende por medida y la diferencia real supera 1/20 (5%), el comprador puede dejar sin efecto el contrato (arts. 1345-1346).
- Obligaciones del vendedor: conservar la cosa hasta entregarla (art. 1408); entregarla libre de posesion y con accesorios (art. 1409); responder por eviccion y vicios redhibitorios (art. 1414).
- Obligaciones del comprador: pagar el precio en lugar y tiempo convenidos (art. 1424); recibir la cosa (art. 1427). Puede rehusar el pago si el vendedor no entrega exactamente lo pactado (art. 1426) o suspenderlo ante riesgo de reivindicacion salvo afianzamiento (art. 1425).
- Gravamenes: conviene que el vendedor declare que la cosa no tiene embargo, medida cautelar ni gravamen.

Clausulas prohibidas o a marcar:
- Precio librado al arbitrio de una sola parte -> NULO (art. 1355).
- Falta de determinacion de la cosa o del precio -> no hay compraventa.
- Venta de cosa ajena sin declararlo (art. 1329).
- Pacto de retroventa o pacto comisorio sobre cosa MUEBLE -> prohibidos (arts. 1374, 1380).
- Clausula de no enajenar a persona alguna (generica) -> prohibida; solo valida respecto de persona determinada (art. 1364).
- Omitir la declaracion de gravamenes/embargos sobre el bien."""

_LEY_TRABAJO = """LEY APLICABLE: Contrato de Trabajo — Ley N° 20.744 (LCT).

Principios y nulidades:
- Irrenunciabilidad: es NULA toda clausula que suprima o reduzca derechos de la ley, estatutos o convenios colectivos (arts. 12, 13). Las clausulas en perjuicio del trabajador se sustituyen de pleno derecho por la norma imperativa.
- Condiciones menos favorables que la ley o el CCT -> NULAS (art. 7).
- En caso de duda prevalece la norma e interpretacion mas favorable al trabajador (art. 9).
- Fraude laboral: es NULO el contrato que simule una relacion no laboral (ej. disfrazar dependencia como locacion de servicios o monotributo) (art. 14).
- No discriminacion por sexo, raza, nacionalidad, religion, ideas politicas, gremiales o edad (art. 18).

Puntos a verificar:
- Remuneracion: no puede ser inferior al Salario Minimo Vital y Movil ni al minimo del CCT aplicable; se paga en los plazos legales (art. 82).
- SAC (aguinaldo): sueldo anual complementario, pagadero en 2 cuotas (junio y diciembre).
- Deducciones/retenciones sobre el salario: limitadas por ley; no pueden vaciar la remuneracion.
- Jornada: limite general de 8 horas diarias / 48 semanales (Ley 11.544). Las horas extra se pagan con recargo (50% dias comunes; 100% sabado despues de las 13, domingos y feriados).
- Vacaciones (art. 150): 14 dias corridos (antiguedad hasta 5 años), 21 dias (mas de 5 y hasta 10), 28 dias (mas de 10 y hasta 20), 35 dias (mas de 20). No son compensables en dinero salvo extincion.
- Licencias especiales pagas: enfermedad, maternidad, nacimiento, matrimonio, examen, fallecimiento de familiar.
- Proteccion de la maternidad y la mujer: estabilidad y prohibicion de despido por embarazo o matrimonio.
- Preaviso (art. 252): trabajador 1 mes; empleador 1 mes (hasta 5 años de antiguedad), 2 meses (hasta 10), 3 meses (mas de 10). Su omision genera indemnizacion sustitutiva (art. 253).
- Indemnizacion por despido sin causa (art. 245/266): 1 mes de la mejor remuneracion mensual, normal y habitual por cada año de servicio o fraccion mayor a 3 meses; minimo 2 meses.
- Despido con justa causa: debe comunicarse por escrito expresando la causa (art. 264).
- Periodo de prueba: la relacion por tiempo indeterminado tiene un periodo de prueba inicial limitado por ley (clasico: 3 meses); no puede extenderse mas alla del tope legal.
- Registracion: la relacion debe estar registrada; el trabajo no registrado ("en negro") es sancionable.

Clausulas a marcar como invalidas o riesgosas:
- Renunciar a indemnizacion, vacaciones, SAC, preaviso o cualquier derecho legal -> NULA (irrenunciabilidad).
- Remuneracion por debajo del SMVM o del CCT aplicable.
- Jornada mayor a 8 h/48 h sin pago de horas extra.
- Encuadrar como "locacion de servicios"/monotributista una relacion de dependencia -> fraude (art. 14).
- Permitir el despido sin preaviso ni indemnizacion.
- Clausulas discriminatorias.
- Periodo de prueba mayor al tope legal.
- Facultad de modificar unilateralmente condiciones esenciales del contrato (ius variandi abusivo, art. 71)."""


# ============================================================
# CLAUSULAS ESPERADAS POR MODELO (para detectar faltantes)
# ============================================================

_MODELO_ALQUILER = """CLAUSULAS ESPERADAS en un contrato de locacion de vivienda (modelo de referencia):
1. Identificacion de las partes (LOCADOR y LOCATARIO: nombre, DNI, domicilio, correo).
2. Objeto y destino del inmueble (ej. vivienda familiar).
3. Plazo (fecha de inicio y de vencimiento).
4. Precio (canon) y mecanismo de actualizacion/ajuste.
5. Fecha y lugar de pago (datos bancarios; emision de factura).
6. Intereses por mora.
7. Prohibiciones / intransferibilidad (cesion y sublocacion).
8. Garantia (tipo de garantia elegida).
9. Impuestos, servicios y expensas (que paga cada parte).
10. Deposito en garantia (monto).
11. Estado del inmueble e inventario.
12. Clausula de incumplimiento.
13. Falta de pago como causal de rescision (2 meses consecutivos).
14. Primer mes y entrega de llaves al inicio.
15. Entrega de llaves al vencimiento.
16. Resolucion anticipada (10% del saldo futuro, art. 1221 CCyC).
17. Domicilios de las partes (incluido domicilio electronico).
18. Jurisdiccion y competencia."""

_MODELO_COMPRAVENTA = """CLAUSULAS ESPERADAS en un contrato de compraventa de bien mueble (modelo de referencia):
1. Identificacion de las partes (VENDEDOR y COMPRADOR: nombre, DNI/CUIT, domicilio).
2. Objeto: detalle del bien (marca, modelo, N° de serie, etc.).
3. Precio y forma de pago (monto, medio: transferencia/cheque, datos de cuenta).
4. Declaracion de que el bien esta libre de gravamenes, embargos o medidas cautelares.
5. Constitucion de domicilios para notificaciones.
6. Jurisdiccion / competencia ante controversias.
7. Cantidad de ejemplares y firma con aclaracion de las partes.
8. (Opcional) Certificacion de firmas."""

_MODELO_TRABAJO = """CLAUSULAS ESPERADAS en un contrato de trabajo (modelo de referencia):
1. Identificacion de las partes (EMPLEADOR y TRABAJADOR: nombre, DNI).
2. Antecedentes y cargo a desempeñar.
3. Objeto del contrato.
4. Jornada y horario de trabajo.
5. Remuneracion (monto y forma de pago).
6. Plazo del contrato (indefinido o a plazo).
7. Lugar de trabajo.
8. Obligaciones de las partes (remision a la LCT).
9. Legislacion aplicable (Ley de Contrato de Trabajo).
10. Jurisdiccion y competencia.
11. Suscripcion (ejemplares y firma)."""


# ============================================================
# MAPA tipo -> referencia y helper de armado
# ============================================================

_KNOWLEDGE = {
    "alquiler": {"ley": _LEY_ALQUILER, "modelo": _MODELO_ALQUILER},
    "compraventa": {"ley": _LEY_COMPRAVENTA, "modelo": _MODELO_COMPRAVENTA},
    "trabajo": {"ley": _LEY_TRABAJO, "modelo": _MODELO_TRABAJO},
}


def build_reference_block(contract_type: str | None) -> str | None:
    """Arma el bloque de referencia legal + modelo para inyectar en el prompt.

    Devuelve None si el tipo no tiene referencia (ej. otro_contrato), en cuyo
    caso el analisis corre sin material de apoyo.
    """
    entry = _KNOWLEDGE.get(contract_type or "")
    if entry is None:
        return None

    return (
        "MATERIAL DE REFERENCIA (usalo para fundamentar el analisis):\n\n"
        f"=== MARCO LEGAL ===\n{entry['ley']}\n\n"
        f"=== {entry['modelo']}"
    )
