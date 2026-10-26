# Costes

Límite del proyecto: 3 € al año. Coste esperado con este diseño: 1–3 € al año. Si una decisión técnica choca con el límite, gana el coste.

El primer año lo cubre Azure for Students: 88 $ de crédito sin tarjeta, que caducan el 18/11/2027. Si se acabara, la suscripción se desactiva en lugar de cobrar. Aun así lo vigilo como si fuera dinero propio, porque con pago por uso los mismos errores sí costarían. Cómo lo controlo: D-010 y D-011 en [DECISIONES.md](DECISIONES.md).

## Lo que uso

| Servicio | Uso | Coste anual estimado |
|---|---|---|
| Azure Functions, Flex Consumption (Python 3.13) | 1 ejecución diaria de unos 20 s | < 0,50 € |
| Cuenta de almacenamiento interna de la Function | Estado y despliegue de la Function | Céntimos (a medir la primera semana) |
| ADLS Gen2 (Hot, LRS) | ~0,5 GB al año (~1 GB con el backfill desde 2025) | ~0,10–0,25 € |
| Capa de consulta, opción A: Synapse serverless sobre Parquet | Consultas, dbt y Power BI | ~0,50–1 € |
| Capa de consulta, opción B: Azure SQL Database, oferta gratuita | Datos modelados, dbt y Power BI en modo Import | 0 € |
| Application Insights con límite diario | Logs de la Function | 0 € (cuota gratuita) |
| Identidad administrada | Acceso de la Function al data lake sin claves | 0 € |
| Cost Management y Azure Policy | Control de costes | 0 € |
| Power BI Desktop | Visualización (aplicación local) | 0 € |

## Lo que no uso sin justificarlo antes

| Recurso | Por qué es caro | Coste aproximado | ¿Lo bloquea la política? |
|---|---|---|---|
| Microsoft Fabric, Power BI Premium o Embedded | Se paga la capacidad por hora, se use o no | Cientos de € al mes | Sí (Fabric y Embedded) |
| Synapse dedicated SQL pool o Spark pools | Cómputo por hora | Desde ~1 € la hora | Sí |
| Azure Databricks | Cómputo y máquinas virtuales | Decenas de € al mes | Sí |
| Data Factory | Coste mínimo por ejecución | Una copia diaria ya supera el límite anual | Sí |
| Functions Premium o App Service plan | Coste fijo aunque no se ejecute nada | Decenas de € al mes | No: lo vigilo en el plan de Terraform |
| Private Endpoints, NAT Gateway, VPN, Firewall | Cobran por hora | ~7 € al mes por endpoint, NAT ~30 € | Sí |
| Synapse serverless sobre JSON sin comprimir | Cobra por datos leídos | Hasta 100 veces más que Parquet | No: lo evita el diseño (D-004) |
| Defender for Cloud | Se cobra por recurso y mes | ~10 € al mes por cuenta de almacenamiento | No: es una configuración, regla manual |
| Application Insights sin límite diario | La ingesta de logs por encima de la cuota | Variable | No: límite diario en Terraform |
| Almacenamiento GRS, Premium o versionado sin limpieza | Multiplica el coste sin aportar nada aquí | Poco, pero innecesario | No: fijo LRS y Hot en Terraform |
| Managed HSM | Coste fijo por clave | ~1 € al mes o más | Sí |
| Máquinas virtuales, IP públicas, Cosmos DB | Coste fijo por hora | Decenas de € al mes | Sí |
| Azure SQL aprovisionado (no la oferta gratuita) | Coste fijo por hora | Decenas de € al mes | No: la opción B usa el mismo tipo de recurso |
