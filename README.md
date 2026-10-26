# Pipeline de precios de carburantes en Azure

Pipeline de datos que ingiere cada día los precios de las ~11.400 gasolineras de España desde el servicio público del Ministerio, construye un histórico propio en un data lake de Azure, lo modela con dbt y lo analiza en Power BI.

> En construcción. Fase actual: repositorio y estructura.

## Arquitectura prevista

```
Azure Function (Python, temporizador diario)
   → ADLS Gen2   raw: JSON comprimido · curated: Parquet particionado
   → Capa SQL    Synapse serverless o Azure SQL Database (a decidir)
   → dbt         staging, dimensiones (SCD 2), hechos
   → Power BI
```

Toda la infraestructura se define con Terraform.

## Control de costes

Objetivo: menos de 3 € al año. El control se hace por capas:
- **Prevenir:** políticas de Azure con efecto Deny (una sola región y 15 tipos de recurso de coste fijo bloqueados).
- **Limitar:** límites por servicio y formatos baratos de consultar.
- **Detectar:** presupuesto mensual y alertas de anomalías.

El detalle está en [docs/DECISIONES.md](docs/DECISIONES.md).

## Estructura del repositorio

```
ingesta/          Azure Function de ingesta y sus tests (fases 4-5)
infra/
  politicas/      Asignaciones de Azure Policy
  terraform/      Infraestructura como código (fase 5)
dbt/              Modelado de datos (fase 7)
notebooks/        Exploración inicial de los datos
docs/             Decisiones de diseño y diccionario de datos
```

## Estado

- [x] Exploración de los datos
- [x] Suscripción de Azure y protecciones de coste
- [x] Repositorio
- [x] Script de ingesta con validaciones y tests
- [ ] Infraestructura con Terraform
- [ ] Zona curated y capa de consulta SQL
- [ ] Modelado con dbt
- [ ] CI/CD con GitHub Actions
- [ ] Análisis en Power BI

## Fuente de datos

Precios de carburantes en estaciones de servicio terrestres, del Ministerio para la Transición Ecológica y el Reto Demográfico (Geoportal de gasolineras). Datos públicos, sin clave de acceso.
