# Estructura de los datos — Precios de carburantes (Ministerio)

Resultado de la fase de exploración (19/10/2026), con las validaciones de la ingesta revisadas en la fase 4 (21/10/2026, D-014). Describe la fuente, sus campos, los problemas de calidad detectados y la propuesta preliminar de modelo. La propuesta de modelo se cerrará en la fase de modelado con dbt.

---

## 1. La fuente

| Aspecto | Detalle |
|---|---|
| Servicio | Servicio REST de precios de carburantes (Ministerio para la Transición Ecológica / Geoportal de gasolineras) |
| Endpoint | `https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/` |
| Autenticación | Ninguna (datos públicos) |
| Formato | JSON con la cabecera `Accept: application/json`; sin ella devuelve XML, con los nombres de campo codificados (`_x0025__x0020_BioEtanol` = `% BioEtanol`) |
| Conexión | Requiere TLS 1.2 con cifrados RSA (ver D-007) |
| Tamaño | ~14 MB por respuesta, en una sola línea |
| Volumen | 11.433 estaciones, 41 campos por estación |

### Estructura de la respuesta

```json
{
  "Fecha": "19/10/2026 12:49:44",
  "ListaEESSPrecio": [ { ...una estación... }, ... ],
  "Nota": "...",
  "ResultadoConsulta": "OK"
}
```

- `Fecha`: fecha y hora de la foto, en formato `dd/mm/aaaa hh:mm:ss`. Parece coincidir con la hora de la petición (pendiente de confirmar).
- `ResultadoConsulta`: estado de la consulta. La ingesta debe comprobar que vale `OK` antes de guardar.
- `ListaEESSPrecio`: lista de estaciones.

---

## 2. Diccionario de campos

Todos los valores llegan como **texto**, también los numéricos. Los valores ausentes llegan como **cadena vacía `""`**.

### Identificación

| Campo | Ejemplo | Tipo destino | Notas |
|---|---|---|---|
| `IDEESS` | `"4375"` | texto | Identificador único de estación. Sin duplicados. Clave natural. |
| `Rótulo` | `"REPSOL"` | texto | **Texto libre**: 3.565 valores distintos. Requiere clasificación (ver §3). |

### Ubicación

| Campo | Ejemplo | Tipo destino | Notas |
|---|---|---|---|
| `Dirección` | `"AVENIDA CASTILLA LA MANCHA, 26"` | texto | |
| `C.P.` | `"02250"` | **texto** | Ceros a la izquierda: no convertir a número. |
| `Localidad` | `"ABENGIBRE"` | texto | |
| `Municipio` | `"Abengibre"` | texto | |
| `IDMunicipio` | `"52"` | texto | |
| `Provincia` | `"ALBACETE"` | texto | Nombres con variantes bilingües (`VALENCIA / VALÈNCIA`) y formatos raros (`PALMAS (LAS)`): solo como etiqueta. |
| `IDProvincia` | `"02"` | **texto** | Clave de provincia. Ceros a la izquierda. |
| `IDCCAA` | `"07"` | **texto** | Clave de comunidad autónoma. |
| `Latitud` | `"39,211417"` | decimal | Coma decimal. Ver tratamiento en D-008. |
| `Longitud (WGS84)` | `"-1,539167"` | decimal | Coma decimal. Ver tratamiento en D-008. |
| `Margen` | `"D"` | texto | Lado de la carretera: D (derecho), I (izquierdo), N (no aplica). |

### Atributos de la estación

| Campo | Ejemplo | Tipo destino | Notas |
|---|---|---|---|
| `Horario` | `"L-D: 07:00-22:00"` | texto | Texto libre. **No explorado todavía.** |
| `Tipo Venta` | `"P"` | texto | P (público) / R (restringido). Hoy todas son P. |
| `Remisión` | `"dm"` | texto | Quién comunica el precio (OM / dm). Significado pendiente de confirmar. |
| `% BioEtanol` | `"0,0"` | decimal | Porcentaje de bioetanol. **No explorado todavía.** |
| `% Éster metílico` | `"0,0"` | decimal | Porcentaje de biodiésel. **No explorado todavía.** |

### Precios (23 campos, €/litro salvo indicación)

Todos con el nombre `Precio <carburante>`, coma decimal y `""` cuando la estación no lo vende.

| Carburante | % estaciones que lo venden | Clasificación preliminar por uso |
|---|---|---|
| Gasoleo A | 98,2 % | Gasóleo automoción |
| Gasolina 95 E5 | 95,2 % | Gasolina |
| Gasoleo Premium | 51,4 % | Gasóleo automoción |
| Gasolina 98 E5 | 47,9 % | Gasolina |
| Adblue | 25,7 % | Aditivo |
| Gasoleo B | 19,8 % | **Gasóleo agrícola** (otra fiscalidad, no mezclar con A) |
| Diésel Renovable | 14,2 % | Gasóleo automoción |
| Gasolina 95 E5 Premium | 9,7 % | Gasolina |
| Gases licuados del petróleo | 8,7 % | Gas |
| Gas Natural Comprimido | 0,8 % | Gas |
| Gas Natural Licuado | 0,5 % | Gas |
| Biogas Natural Licuado | 0,4 % | Gas |
| Biogas Natural Comprimido | 0,4 % | Gas |
| Gasolina Renovable | 0,3 % | Gasolina |
| Biodiesel | 0,2 % | Gasóleo automoción |
| Gasolina 95 E10 | 0,2 % | Gasolina |
| Gasolina 98 E10 | 0,1 % | Gasolina |
| Hidrogeno | 2 estaciones | Otros |
| Gasolina 95 E85 | ~0 % | Gasolina |
| Gasolina 95 E25 | ~0 % | Gasolina |
| Bioetanol | ~0 % | Gasolina |
| Amoniaco | 0 % | Otros |
| Metanol | 0 % | Otros |

Media de **~3,7 carburantes por estación**. Las unidades de los gases (por litro o por kg) están **pendientes de confirmar**.

---

## 3. Problemas de calidad detectados

| # | Problema | Alcance | Tratamiento previsto |
|---|---|---|---|
| 1 | Números como texto con coma decimal | Precios, coordenadas, porcentajes | `""` → nulo, coma → punto, texto → número. Fallar si algo no se puede convertir (nada de `errors="coerce"`). |
| 2 | Ausentes como `""` en lugar de nulo | Todos los campos | Convertir a nulo. |
| 3 | Coordenadas `(0, 0)` | 4 estaciones | Nulo + flag `coord_ausente` (D-008). |
| 4 | Latitud y longitud intercambiadas | 1 estación (Tui) | Corregir + flag `coord_corregida` (D-008). |
| 5 | `Rótulo` en texto libre | 3.565 valores distintos | Los 30 más frecuentes (~7.000 estaciones) están limpios; en la cola hay marca + nombre de estación (`BP HOSTAL DE LA SELVA`, `GALP/3CAMINOS-VALENCIA`), razones sociales (`COMBUSTIBLES CALAHORRA S.L.`), cooperativas y low-cost. Clasificar rótulo → marca → grupo → tipo de operador (gran petrolera / low-cost / hipermercado / independiente) con reglas de palabra completa y una tabla de correspondencias (seed de dbt). Medir cobertura. |
| 6 | Cambio de marca en curso (CEPSA → MOEVE) | Cientos de estaciones | Dimensión de estaciones SCD tipo 2. Ojo: marca ≠ grupo (CAMPSA y PETRONOR son de Repsol). |
| 7 | Nombres de provincia inconsistentes | Varias provincias | Usar `IDProvincia` como clave. |
| 8 | Códigos con ceros a la izquierda | `C.P.`, `IDProvincia`, `IDCCAA` | Mantener como texto. |

### Validaciones (D-014)

**En la ingesta, cada día**, en dos niveles:

- **Bloqueantes:** no se guarda nada y la ejecución falla.
  - La respuesta no es JSON.
  - `ResultadoConsulta` es distinto de `OK`.
  - Falta `ListaEESSPrecio` o está vacía.
  - El número de estaciones está fuera de 10.000–13.000.
- **Avisos:** se guarda el raw y se registra un warning.
  - `IDEESS` duplicados.
  - Precios no convertibles a número o fuera de un rango razonable.

**En curated (fase 6):** conversión de precios (problema 1), tratamiento de `IDEESS` duplicados y comparación del número de estaciones con el día anterior (aviso si varía más de ±10 %).

---

## 4. Hallazgos para el análisis

- **Fiscalidad territorial:** Melilla, Las Palmas, Ceuta y Santa Cruz de Tenerife son las zonas más baratas (10–25 cts/l menos que la península), pero solo suman ~515 estaciones. Hace falta una **zona fiscal**: península y Baleares / Canarias / Ceuta y Melilla.
- **Gasóleo A (19/10/2026):** 11.222 precios, de 1,499 a 2,299 €/l, media 1,888 €/l, sin valores absurdos. Nivel pendiente de contrastar con una fuente externa.
- **Dispersión dentro de la península:** la fiscalidad no la explica por sí sola. Hipótesis: low-cost frente a grandes marcas.

---

## 5. Propuesta preliminar de modelo

Se cerrará en la fase de modelado. Grano de la tabla de hechos: **una fila por estación, carburante y día**.

```
                 ┌──────────────┐
                 │  dim_fecha   │
                 └──────┬───────┘
                        │
┌──────────────┐  ┌─────┴─────────────┐  ┌───────────────┐
│ dim_estacion │──┤ fct_precio_diario ├──│ dim_carburante│
│   (SCD 2)    │  └───────────────────┘  └───────────────┘
└──────────────┘
```

- **`fct_precio_diario`:** fecha, IDEESS, carburante, precio. ~42.000 filas/día.
- **`dim_estacion` (SCD tipo 2):** IDEESS, rótulo, marca, grupo, tipo de operador, dirección, municipio, provincia, comunidad, zona fiscal, coordenadas, flags de coordenadas, margen, horario. Con fechas de validez para registrar cambios de rótulo.
- **`dim_carburante`:** nombre, categoría por uso (gasóleo automoción, gasóleo agrícola, gasolina, gas, aditivo, otros), unidad.
- **`dim_fecha`:** calendario estándar (día de la semana, mes, festivo…).

---

## 6. Pendiente de explorar
| Pendiente | Fase |
|---|---|
| Si el servicio genera la foto en cada petición o se publica a una hora fija | 4 · Script de ingesta |
| Formatos de `Horario` | 6 · Zona curated |
| `% BioEtanol` y `% Éster metílico` | 6 · Zona curated |
| Unidades de los precios de gas e hidrógeno (€/litro o €/kg) | 6 · Zona curated |
