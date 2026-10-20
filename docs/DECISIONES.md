# Registro de decisiones — Pipeline de precios de carburantes en Azure

Este documento recoge las decisiones técnicas del proyecto: qué se decidió, por qué y qué alternativas se descartaron.

Formato de cada decisión:
- **Contexto:** qué problema había.
- **Decisión:** qué se eligió.
- **Por qué:** los motivos, con números cuando los hay.
- **Alternativas descartadas:** y por qué no.

---

## Reglas de coste (se revisan antes de crear cualquier recurso)

Límite absoluto del proyecto: **3 € al año**. Coste esperado con este diseño: **~1–3 €/año**. Si una decisión técnica choca con el límite, gana el coste.

**Primer año:** suscripción **Azure for Students**, **sin tarjeta**. El portal muestra **88 $ de crédito** (la documentación de Microsoft habla de 100 $), que **caducan el 18/11/2027**. Si el crédito se agotara o caducara, la suscripción se desactiva en lugar de cobrar, así que el coste real del primer año es **0 €**. Aun así, se vigila como si fuera dinero propio, porque con pago por uso los mismos errores sí costarían.

**Defensa en profundidad (D-010):** prevenir (políticas, D-011) → limitar (crédito sin tarjeta, límites por servicio, formatos baratos) → detectar (presupuesto, anomalías, revisión semanal).

### Protecciones (día 1, antes de crear nada)
- [x] **Nunca añadir una tarjeta a la suscripción de estudiante.** Es lo que quita el límite de gasto. No pulsar nunca "Actualizar ahora", "Upgrade" ni "Quitar límite de gasto".
- [x] Suscripción **Azure for Students** activa, sin tarjeta. Crédito: 88 $. Caduca: **18/11/2027**.
- [x] MFA en la cuenta (Authenticator y un método de respaldo). Para **crear, modificar o borrar** desde la CLI o Terraform, la sesión tiene que haberse iniciado con MFA (ver D-011, lecciones).
- [x] **Una sola región: Spain Central**, impuesta por la política `solo-spain-central` (D-009, D-011).
- [ ] **Un único grupo de recursos** para todo el proyecto. Lo crea Terraform en la fase 5.
- [x] Presupuesto en **Cost Management** (`presupuesto-mensual-1usd`): **1 €/mes** (la suscripción factura en EUR), ámbito de suscripción, alertas al 25 %, 50 % y 100 % real y al 100 % previsto, a dos correos (el universitario y uno personal). Caduca el 31/12/2036. Se crea sin problemas en Azure for Students (D-010). **Pendiente de la fase 5:** comprobar que mide el consumo real.
- [x] **Alerta de anomalías** de Cost Management: diaria por grupo de recursos, al correo personal, vigente hasta el **19/10/2027** (renovar, ver el plan de fin del crédito).
- [x] **Políticas de Azure con efecto Deny:** `solo-spain-central` y `lista-roja-costes` (D-011).
- [ ] Filtro en el correo para que `azure-noreply@microsoft.com` no vaya nunca a spam.
- [ ] Cuando exista Synapse: **límites de datos procesados** (diario, semanal y mensual) al valor más bajo permitido.
- [ ] Cuando exista Application Insights: **límite diario de ingesta**, muestreo y retención de 30 días.
- [x] **No activar planes de Defender for Cloud** aunque el portal lo sugiera (verificado: "Azure Defender no está habilitado"). No pulsar "Actualizar cobertura". La política no lo cubre porque no es un recurso: es una regla manual.
- [ ] Revisión semanal del crédito restante (Education Hub) y del análisis de costes.

### Lista roja: nunca sin justificarlo antes
Costes aproximados, para dar el orden de magnitud. La última columna indica si la política `lista-roja-costes` (D-011) lo impide automáticamente.

| Recurso / práctica | Por qué es peligroso | Coste aproximado | ¿Bloqueado por política? |
|---|---|---|---|
| Microsoft Fabric (capacidad F) / Power BI Premium / Power BI Embedded | Se cobra la capacidad por hora, se use o no | Cientos de €/mes | Sí (Fabric y Embedded) |
| Synapse **dedicated** SQL pool o **Spark** pools | Cobran por hora de cómputo | Desde ~1 €/hora | Sí |
| Azure Databricks | Cómputo (DBU) + máquinas virtuales | Decenas de €/mes | Sí |
| Data Factory: actividades de copia y data flows | Se cobra por DIU-hora con mínimo por ejecución | Una copia diaria ya supera el límite anual | Sí (todo Data Factory) |
| Functions **Premium** o **App Service plan** | Coste fijo mensual aunque no se ejecute nada | Decenas de €/mes | **No**: Flex Consumption usa el mismo tipo de recurso. Se vigila en el `plan` de Terraform |
| Private Endpoints, NAT Gateway, VPN, Azure Firewall | Cobran por hora | ~7 €/mes por endpoint; NAT ~30 €/mes | Sí |
| Consultar con Synapse serverless JSON sin comprimir ni particionar | Se cobra por datos procesados | Hasta 100× más que Parquet | No (es coste por uso): se evita con el diseño (D-004) y los límites de Synapse |
| Defender for Cloud (Storage, etc.) | Se cobra por recurso y mes | ~10 €/mes por cuenta de almacenamiento | No (es una configuración): regla manual |
| Application Insights sin límite diario | Se cobra la ingesta por encima de la cuota gratuita | Variable, puede dispararse | No: límite diario en Terraform (fase 5) |
| Almacenamiento GRS / RA-GRS, nivel Premium, versionado sin reglas de limpieza | Multiplica el coste sin aportar nada aquí | Poco, pero innecesario | No: se fija LRS/Hot en Terraform |
| Claves gestionadas por el cliente (Key Vault HSM) | Coste fijo por clave | ~1 €/mes o más | Sí (Managed HSM) |
| Máquinas virtuales, IP públicas, Cosmos DB | Coste fijo por hora | Decenas de €/mes | Sí |
| Azure SQL aprovisionado (no la oferta gratuita) | Coste fijo por hora | Decenas de €/mes | No: la opción B de la fase 6 usa el mismo tipo de recurso |

### Lista verde: lo que se usa y por qué es barato
| Servicio | Uso | Coste anual estimado |
|---|---|---|
| Azure Functions (**Flex Consumption**, Python 3.13, disparador temporizado) | 1 ejecución diaria de ~20 s | < 0,50 € |
| Cuenta de almacenamiento interna de la Function | Estado y despliegue de la Function | Céntimos, **a medir la primera semana** |
| ADLS Gen2 (nivel Hot, redundancia LRS) | ~1–1,5 GB al cabo de un año | ~0,30 € |
| Capa de consulta, opción A: Synapse **serverless** SQL sobre Parquet particionado | Consultas de desarrollo, dbt y Power BI | ~0,50–1 € |
| Capa de consulta, opción B: **Azure SQL Database, oferta gratuita** (100.000 vCore-s y 32 GB al mes) con pausa automática al llegar al límite | Datos modelados, dbt y Power BI en modo Import | 0 € |
| Application Insights / Log Analytics con límite diario | Logs de la Function | 0 € (dentro de la cuota gratuita) |
| Identidad administrada (Managed Identity) | Acceso de la Function al data lake sin claves | 0 € |
| Cost Management (presupuestos, alertas, anomalías) y Azure Policy | Control de costes | 0 € |
| Power BI Desktop | Visualización (aplicación local, no es un recurso de Azure) | 0 € |

---

## D-001 · Fuente de datos: precios de carburantes del Ministerio
- **Contexto:** hacía falta un dataset real, público, que se actualice solo y que no esté sobreexplotado en portfolios.
- **Decisión:** servicio REST de precios de carburantes de las gasolineras de España (Ministerio para la Transición Ecológica / Geoportal de gasolineras).
- **Por qué:** se actualiza a diario, es gratuito y sin clave de API, cubre ~11.400 estaciones y permite construir un histórico propio. Además conecta con un proyecto anterior de costes de flota.
- **Alternativas descartadas:** datasets estáticos de Kaggle o el de taxis de Nueva York (no se actualizan y están muy vistos).

## D-002 · Cloud: Azure (revisada: inicialmente AWS)
- **Contexto:** el proyecto se planteó primero en AWS, pero antes de crear ninguna infraestructura se reconsideró la elección.
- **Decisión:** Azure, con una suscripción **Azure for Students**.
- **Por qué:**
  - **Riesgo de factura nulo el primer año:** crédito de 88 $ (caduca el 18/11/2027) sin tarjeta; si se agotara, la suscripción se desactiva en lugar de cobrar.
  - **Muy presente en las ofertas de datos en España**, sobre todo en grandes empresas y consultoras.
  - **Coherencia con el ecosistema Microsoft** (SQL Server, Power BI).
  - **No se pierde trabajo:** la exploración de los datos no depende de la nube.
- **Alternativas descartadas:**
  - AWS: su plan gratuito cierra la cuenta a los 6 meses (con pérdida de los datos) y el plan de pago requiere tarjeta.
  - GCP: menos presente en las ofertas del mercado objetivo.
- **Limitaciones:**
  - El crédito caduca y solo se renueva mientras se mantenga la condición de estudiante. Ver el **plan de fin del crédito**, más abajo.
  - La suscripción depende de la cuenta universitaria. En el peor caso, el proyecto queda en el repositorio y se puede recrear con Terraform en otra suscripción.

## D-003 · Arquitectura serverless en lugar de un servidor
- **Contexto:** el pipeline se ejecuta una vez al día unos segundos.
- **Decisión:** Azure Function con disparador temporizado (Python, plan **Flex Consumption**) → ADLS Gen2 (raw y curated) → capa de consulta SQL → dbt → Power BI. La capa de consulta (Synapse serverless o Azure SQL Database con oferta gratuita) se decide en la fase 6; las dos cuestan prácticamente cero.
- **Por qué:** con serverless solo se paga lo que se ejecuta. Coste estimado ~1–3 €/año frente a ~50–60 €/año de un VPS con cron y Postgres, que cobra 24 h al día aunque esté parado. Se elige **Flex Consumption** porque el plan Consumption en Linux (necesario para Python) se retira en septiembre de 2028 y Microsoft recomienda Flex para aplicaciones nuevas. **Confirmado en Spain Central:** Flex Consumption admite Python 3.10–3.14; se usa **3.13** (la misma versión que en local, con soporte hasta el 31/10/2029).
- **Alternativas descartadas:**
  - VPS o máquina virtual con cron: más caro a este volumen y hay que mantener el servidor.
  - Data Factory para la ingesta: sus actividades de copia cobran por ejecución con un mínimo que, a diario, supera el límite anual.
- **Plan B:** si la cuenta de almacenamiento interna de la Function resultara cara, la ingesta puede ejecutarse como workflow programado de GitHub Actions (gratuito en repos públicos) escribiendo en ADLS.
- **Cuándo cambiaría la decisión:** con mucho volumen o carga constante, un servidor o un warehouse dedicado puede salir más a cuenta.

### Equivalencias AWS ↔ Azure
| Función | AWS | Azure |
|---|---|---|
| Cómputo serverless | Lambda | Azure Functions |
| Programación | EventBridge Scheduler | Disparador temporizado de la Function |
| Data lake | S3 | ADLS Gen2 |
| Consultas SQL sobre ficheros | Athena + Glue Data Catalog | Synapse serverless SQL |
| Base de datos SQL serverless | Aurora Serverless | Azure SQL Database serverless |
| Identidad y permisos | IAM roles | Entra ID + RBAC + identidad administrada |
| Logs y monitorización | CloudWatch | Application Insights / Azure Monitor |
| Control de costes | AWS Budgets / Cost Anomaly Detection | Cost Management (presupuestos y alertas de anomalías) |
| Reglas preventivas sobre lo que se puede crear | Service Control Policies (SCP) | Azure Policy |

## D-004 · Formatos: JSON crudo comprimido + Parquet particionado en formato largo
- **Contexto:** el JSON de un día ocupa ~14 MB, y la mayoría de los 23 campos de precio vienen vacíos. Synapse serverless cobra por datos procesados.
- **Decisión:**
  - Contenedor **raw** en ADLS: el JSON tal cual llega, comprimido con gzip (~1–2 MB/día). Es la copia de seguridad para poder reprocesar.
  - Contenedor **curated**: Parquet en formato largo (una fila por estación, carburante y día; ~42.000 filas/día, ~0,3–0,5 MB), particionado por fecha.
- **Por qué:** pasar de ~14 MB a <0,5 MB por día. Consultar Parquet particionado cuesta del orden de **100 veces menos** que consultar el JSON sin comprimir. El formato largo elimina los cientos de miles de campos vacíos.
- **Alternativas descartadas:** guardar solo el JSON (caro de consultar); formato ancho con 23 columnas de precio (casi todas nulas).

## D-005 · Esquemas como código, sin servicios de cómputo por hora
- **Contexto:** sea cual sea la capa de consulta, hay que describir las tablas: vistas o tablas externas sobre los Parquet si es Synapse serverless, o tablas y vistas si es Azure SQL Database.
- **Decisión:** definir esquemas, tablas y vistas en **SQL versionado en el repositorio** (más adelante, generado con dbt). La infraestructura, con Terraform. Sin Data Factory, sin Spark pools y sin servicios de catalogación de pago.
- **Por qué:** el esquema es conocido y estable; definirlo en código es gratis, reproducible y queda versionado. Los servicios que descubren esquemas o transforman con clústeres cobran por hora.
- **Alternativas descartadas:** Spark pools de Synapse o Data Factory para transformar y catalogar (coste por hora, incompatible con el límite).

## D-006 · Metodología: explorar los datos en local antes de tocar la nube
- **Contexto:** sin conocer el dato, cualquier diseño de esquema o estimación de coste es inventada.
- **Decisión:** primero se descarga y explora el JSON en local con Python; después se crea la infraestructura.
- **Por qué:** coste cero, y permite detectar problemas de calidad antes de construir la tubería. Además, resultó independiente de la nube: el cambio de AWS a Azure no invalidó nada de la exploración.

## D-007 · Conexión TLS adaptada al servidor del Ministerio
- **Contexto:** Python no podía descargar los datos: el servidor cortaba la conexión durante el saludo TLS (`ConnectionResetError 10054`), mientras que el navegador y el curl de Windows sí funcionaban.
- **Diagnóstico:** se descartó la red (el navegador funcionaba), la cabecera `User-Agent` (no cambiaba nada) y la versión de TLS (TLS 1.2 con cifrados por defecto también fallaba). Probando una variable cada vez, se vio que el servidor **solo acepta cifrados con intercambio de claves RSA**, que Python no ofrece por defecto por carecer de *forward secrecy*.
- **Decisión:** un adaptador de `requests` montado **solo para ese servidor**, con TLS 1.2 y una lista explícita de cifrados: primero los modernos (ECDHE) y después los RSA que acepta el servidor. La verificación del certificado se mantiene.
- **Por qué es aceptable:** los datos son públicos y no viajan credenciales; el certificado sigue verificándose, así que la autenticidad e integridad están garantizadas; el cambio no afecta a ninguna otra conexión; y si el servidor se actualiza, se usarán automáticamente los cifrados modernos.
- **Alternativas descartadas:**
  - `verify=False`: desactiva la verificación del certificado; inaceptable.
  - `SECLEVEL=1`: también funcionaba, pero relaja más cosas de las necesarias.
  - Descargar con curl en lugar de Python: la ingesta irá en una Azure Function con Python, así que tiene que funcionar en Python.

## D-008 · Tratamiento de coordenadas erróneas
- **Contexto:** al validar las coordenadas contra los rangos geográficos de España, 27 estaciones quedaban fuera. Al revisarlas: 22 eran de Ceuta y Melilla (válidas, faltaba su rango), 4 tenían `(0, 0)` y 1 (Tui, Pontevedra) tenía latitud y longitud intercambiadas.
- **Decisión:**
  - Tres rangos válidos: península y Baleares (lat 36–44, lon -9,5–4,5), Canarias (lat 27,5–29,5, lon -18,5–-13), Ceuta y Melilla (lat 35–36, lon -5,5–-2,8).
  - `(0, 0)` → nulo + flag `coord_ausente`.
  - Fuera de rango que, al intercambiar latitud y longitud, cae en rango → se corrige + flag `coord_corregida`.
  - Resto fuera de rango → nulo + flag `coord_invalida`.
  - El dato original se conserva siempre en raw; la estación y sus precios nunca se descartan.
- **Por qué:** los errores son pocos (5 de 11.433, un 0,04 %) pero rompen mapas y cálculos de distancia. Corregir solo cuando la corrección es inequívoca, y marcar siempre lo que se ha tocado, mantiene el dato auditable.
- **Alternativas descartadas:**
  - Borrar las estaciones afectadas: se perderían sus precios, que son correctos.
  - Dejar los `(0, 0)`: aparecerían en el océano frente a África y distorsionarían cualquier cálculo geográfico.
  - Intentar geocodificar la dirección: añade dependencia externa y coste para 4 casos.
- **Lección:** `count` decía que no faltaba ninguna coordenada, pero 4 venían como `(0, 0)`. **Un valor ausente puede llegar disfrazado de cero.**

## D-009 · Región: Spain Central
- **Contexto:** había que fijar una única región para todo el proyecto. Las candidatas iniciales eran Spain Central, West Europe y North Europe. Al activar la suscripción se descubrió que Azure for Students trae una política de Microsoft (`sys.regionrestriction`, "Allowed resource deployment regions") que solo permite 5 regiones, distintas para cada estudiante. En esta suscripción: `germanywestcentral`, `norwayeast`, `spaincentral`, `italynorth` y `switzerlandnorth`. **West Europe y North Europe no están permitidas.**
- **Decisión:** **Spain Central** (`spaincentral`). Alternativa si algún servicio fallara: **Germany West Central**.
- **Por qué:**
  - **Permitida** por la política de la suscripción.
  - **Tiene todas las piezas críticas**, comprobado con la CLI: Flex Consumption con Python 3.10–3.14 (`az functionapp list-flexconsumption-locations` y `list-flexconsumption-runtimes`), workspaces de Synapse (`az provider show --namespace Microsoft.Synapse`) y Azure SQL. Las dos opciones de la fase 6 siguen abiertas.
  - **Cercanía:** los datos y su fuente son españoles. Para una ingesta diaria la latencia no importa, pero es la elección natural.
  - **El precio no discrimina:** con ~1,5 GB, la diferencia entre regiones es de céntimos al año.
- **Alternativas descartadas:**
  - West Europe y North Europe: no permitidas en la suscripción de estudiante.
  - Germany West Central: tiene los mismos servicios, pero no aporta nada frente a Spain Central. Queda como plan B.
  - Norway East, Italy North, Switzerland North: sin ventajas.
- **Cómo se garantiza:** con la política `solo-spain-central` (D-011), que reduce las 5 regiones permitidas a 1.

## D-010 · Control de costes en Azure for Students: comprobar en lugar de suponer, y por capas
- **Contexto:** la documentación de Cost Management incluye Azure for Students (`MS-AZR-0170P`) en la tabla de ofertas **no soportadas**, y un moderador de Microsoft lo confirmó en 2020 y en 2023. Pero la página de Education Hub recomienda crear presupuestos. La información se contradecía, y el presupuesto era una de las protecciones del día 1.
- **Decisión:**
  1. **Comprobarlo en la práctica** antes de fiarse de cualquiera de las dos fuentes.
  2. **No depender de una sola protección:** montar la protección en tres capas.
     - **Prevenir:** políticas que impiden crear recursos caros o fuera de la región (D-011).
     - **Limitar:** el crédito sin tarjeta como tope duro, límites por servicio (App Insights, Synapse) y formatos baratos (D-004).
     - **Detectar:** presupuesto de 1 €/mes, alerta de anomalías y revisión semanal del crédito en Education Hub.
- **Resultado de la comprobación (20/10/2026):**
  - El presupuesto se crea sin errores, con sus 4 alertas y dos destinatarios.
  - Análisis de costes abre las vistas ("No se ha notificado ningún costo durante este período") sin ningún aviso de oferta no soportada, y el panel de velocidad de gasto de la suscripción muestra 0,00.
  - La regla de anomalías se crea sin errores.
  - **Queda por comprobar en la fase 5:** que mide el consumo real y que los correos llegan. Hasta que haya recursos no hay consumo con el que probarlo.
- **Detalles de configuración:**
  - **Ámbito de suscripción**, no de grupo de recursos: así avisa también de un recurso creado por error fuera del grupo.
  - **1 €/mes:** la suscripción factura en euros. El nombre `presupuesto-mensual-1usd` es anterior a saberlo y no se puede cambiar.
  - **Avisos a un correo personal además del universitario**, por si la cuenta universitaria se desactiva.
- **Por qué:**
  - Durante el primer año, el tope real es el crédito sin tarjeta; el presupuesto es un aviso temprano.
  - Con pago por uso (segundo año), los presupuestos sí están soportados oficialmente y pasan a ser la protección principal. Conviene tenerlos funcionando y entendidos desde ya.
  - Un presupuesto solo avisa cuando el gasto ya ha ocurrido (se evalúa cada ~24 h); por eso hacen falta también las capas de prevenir y limitar.
- **Alternativas descartadas:**
  - Fiarse de la documentación y renunciar al presupuesto: habría dejado sin aviso temprano algo que sí funciona.
  - Fiarse del presupuesto como única protección: no evita el gasto, solo lo notifica.

## D-011 · Políticas de Azure: la lista roja y la región como código
- **Contexto:** el presupuesto y las alertas solo **avisan**, y lo hacen cuando el gasto ya ha ocurrido. El error más caro posible es crear sin querer un recurso con coste fijo por hora (un asistente del portal que añade extras, un tutorial copiado, una errata en Terraform).
- **Decisión:** dos asignaciones de Azure Policy a nivel de suscripción, con efecto **Deny**:
  - `solo-spain-central`: definición integrada *Allowed locations* (`e56962a6-4747-49cd-b67b-bf8b01975c4c`), con `spaincentral` como única región. Se creó en el portal, que le asignó como nombre interno el identificador `d2d47a34e2da53deb832e047`.
  - `lista-roja-costes`: definición integrada *Not allowed resource types* (`6c112d4e-5bc7-47ae-a041-ea2d9dccd749`), con 15 tipos de recurso de la lista roja. Los parámetros están en `infra/politicas/lista-roja.parameters.json`. Se creó con la CLI.
  - Cada una tiene un mensaje de no cumplimiento que remite a este documento.
- **Tipos bloqueados:** máquinas virtuales y conjuntos de escalado, Databricks, Data Factory, pools dedicated y Spark de Synapse, capacidades de Fabric y Power BI Embedded, NAT Gateway, Private Endpoints, IP públicas, gateways de VPN, Azure Firewall, Cosmos DB y Managed HSM.
- **Lo que no se bloquea a propósito:**
  - `Microsoft.Web/serverFarms`: la Function de Flex Consumption lo necesita. El riesgo de un plan Premium o App Service se vigila en el `plan` de Terraform.
  - `Microsoft.Synapse/workspaces` y `Microsoft.Sql/servers`: son las dos opciones de la fase 6.
  - Defender for Cloud: es una configuración de la suscripción, no un recurso; queda como regla manual.
- **Por qué:** convierte la lista roja de un documento que hay que recordar en una regla que Azure aplica aunque haya un error humano. Es gratis y reversible.
- **Limitación:** **no garantiza gastar 0 €.** No cubre los costes por uso de los servicios permitidos (consultas de Synapse, ingesta de logs, transacciones de almacenamiento). Eso lo cubren las capas de limitar y detectar (D-010).
- **Verificación:** con `az policy assignment show` se comprobó que los parámetros son los esperados y que el modo es `Default` (aplica y bloquea). La primera prueba de denegación real será en la fase 5.
- **Lecciones:**
  - El selector de tipos del portal solo muestra los tipos de los **proveedores de recursos registrados**. En una suscripción nueva, el desplegable sale vacío, pero la política funciona igual. Por eso la lista roja se asignó con la CLI y un fichero de parámetros.
  - Desde octubre de 2025, Azure exige **MFA para crear, modificar o borrar** desde la CLI, Terraform o la API (fase 2 de la MFA obligatoria); leer no lo requiere. Si `az login` reutiliza una sesión sin MFA, las escrituras fallan con `RequestDisallowedByAzure`. La solución es iniciar sesión forzando la MFA:
    ```powershell
    az logout
    az login --tenant "<ID_DEL_TENANT>" --scope "https://management.core.windows.net//.default" --claims-challenge "eyJhY2Nlc3NfdG9rZW4iOnsiYWNycyI6eyJlc3NlbnRpYWwiOnRydWUsInZhbHVlcyI6WyJwMSJdfX19"
    ```
  - Con `--params` de la CLI, un fichero se indica con `@` delante, y en PowerShell entre comillas: `--params "@fichero.json"`.
- **Alternativas descartadas:**
  - Solo documentar la lista roja: depende de acordarse.
  - La definición *Exclude Usage Costs Resources*: bloquea categorías enteras (cómputo, almacenamiento…) e impediría el propio proyecto.

## D-012 · Repositorio: monorrepo organizado por herramienta, y qué no se versiona
- **Contexto:** el proyecto combina código Python (ingesta), Terraform y políticas (infraestructura), dbt (modelado) y documentación. El repositorio es público.
- **Decisión:**
  - **Un único repositorio** con una carpeta por herramienta: `ingesta/`, `infra/` (`politicas/` y `terraform/`), `dbt/`, `notebooks/` y `docs/`.
  - `ingesta/` es la raíz de la Function: la lógica vive en un paquete Python testeable en local y `function_app.py` solo la llama.
  - Las carpetas se crean cuando tienen contenido (Git no versiona carpetas vacías); la estructura prevista se documenta en el README.
  - **Nunca se versionan:** secretos (`.env`, `local.settings.json`, `profiles.yml`, `*.tfvars`, certificados), el **estado y los planes de Terraform** (`*.tfstate`, `*.tfplan`), los datos (`/data/`, `*.parquet`, `*.duckdb`) y todo lo regenerable (`.venv/`, `.terraform/`, `target/`, checkpoints de Jupyter).
  - **Sí se versionan:** `.terraform.lock.hcl` (fija las versiones de los proveedores) y plantillas sin valores (`.env.example`, `terraform.tfvars.example`).
  - `.gitattributes` normaliza los finales de línea a LF (la Function y la CI corren en Linux).
  - Los commits usan el correo *noreply* de GitHub.
- **Por qué:**
  - Las piezas cambian juntas: un campo nuevo en la fuente toca la ingesta, dbt y la documentación en el mismo commit.
  - Separar por herramienta permite que cada workflow de CI se lance solo cuando cambia su carpeta (filtros `paths:`) y que el paquete de despliegue de la Function no incluya Terraform ni dbt.
  - El historial de Git es permanente: un secreto subido y borrado después sigue accesible, y la única solución es rotarlo. Por eso se previene antes del commit, en capas: `.gitignore`, revisión con `git status --untracked-files=all` y `git check-ignore -v`, y el *push protection* de GitHub como última red.
  - El estado de Terraform guarda en texto plano las claves y cadenas de conexión de los recursos.
  - Los identificadores (tenant, suscripción) no son secretos, pero en la documentación pública se sustituyen por marcadores.
- **Alternativas descartadas:**
  - Un repositorio por componente: más sobrecarga sin ventaja para un proyecto de una persona.
  - Ignorar por extensión (`*.json`, `*.csv`): excluiría los parámetros de las políticas y los seeds de dbt, que son código. Se ignora por ubicación (`/data/`) y solo por extensión los formatos que nunca son código.
  - Crear ya todas las carpetas con `.gitkeep`: el repositorio mostraría carpetas vacías durante meses.

---

## Plan de fin del crédito (segundo año)
- **Fechas clave:** el crédito caduca el **18/11/2027** y solo se renueva mientras se mantenga la condición de estudiante. Si se agotan los 88 $ antes, pasa lo mismo, aunque con ~1–3 €/año no ocurrirá.
- **Qué ocurre al caducar:** los recursos quedan inaccesibles y hay **90 días** para pasar a pago por uso; después se pierden.
- **Desde ya (sin coste):**
  - Toda la infraestructura en Terraform, para poder recrearla en cualquier suscripción en minutos.
  - Avisos de costes también a un correo personal.
- **Septiembre de 2027 — decidir:**
  - **A. Pago por uso (~1–3 €/año).** Hay que añadir una tarjeta, lo que elimina el tope duro. Antes de hacerlo deben estar funcionando los presupuestos (oficialmente soportados con pago por uso) y las políticas. Si la cuenta universitaria ya no existe, sería una suscripción nueva: `terraform apply` y subir el histórico exportado.
  - **B. Apagarlo.** Exportar los datos y hacer `terraform destroy`. El proyecto se mantiene como repositorio, documentación, Power BI en modo Import y capturas.
  - **C. Plan B de D-003** (ingesta con GitHub Actions y otro almacenamiento gratuito).
- **Octubre de 2027 — en cualquier caso:**
  - **Exportar raw y curated** a local (menos de 1 GB por año) con `az storage blob download-batch`, **antes** del 18/11/2027.
  - **Renovar la regla de anomalías**, que vence el 19/10/2027.

---

## Observaciones sobre los datos (para tratar en la transformación)
- Sin cabecera `Accept: application/json`, el servicio responde en **XML** (con nombres de campo codificados, p. ej. `_x0025__x0020_BioEtanol` = `% BioEtanol`). Indicio de un servicio .NET.
- La fecha de la cabecera coincide casi con la hora de la petición: puede que el servicio genere la foto en cada consulta en lugar de publicar una vez al día. Pendiente de confirmar.
- Precios y coordenadas vienen como **texto con coma decimal** (`"1,459"`), no como números: el JSON los manda entre comillas.
- Los precios que no existen vienen como **cadena vacía `""`**, no como nulo. Transformación: `""` → nulo, coma → punto, texto → número.
- Exploración del 19/10/2026: **11.433 estaciones**, 41 columnas, sin `IDEESS` duplicados (sirve como clave de estación).
- Cobertura por carburante: gasóleo A 98,2 %, gasolina 95 E5 95,2 %, gasóleo Premium 51,4 %, gasolina 98 E5 47,9 %, AdBlue 25,7 %, gasóleo B 19,8 %, diésel renovable 14,2 %. Amoniaco y metanol: 0 estaciones; hidrógeno: 2.
- Media de **~3,7 carburantes por estación** → ~42.000 filas/día en formato largo (confirma D-004).
- El **gasóleo B es agrícola** (otra fiscalidad, no apto para carretera): no se puede mezclar con el gasóleo A en medias. Hace falta clasificar los carburantes por uso.
- Gasóleo A (19/10/2026): 11.222 precios, de 1,499 a 2,299 €/l, media 1,888 €/l, sin valores absurdos. Nivel de precios pendiente de contrastar con una fuente independiente.
- **Fiscalidad territorial:** Melilla, Las Palmas, Ceuta y Santa Cruz de Tenerife son las zonas más baratas (10–25 cts/l por debajo de la península). Solo suman ~515 estaciones, así que no explican por sí solas la dispersión de precios (hipótesis pendiente: low-cost frente a grandes marcas). → La dimensión de estaciones necesita una **zona fiscal** (península y Baleares / Canarias / Ceuta y Melilla).
- **Los nombres de provincia no sirven como clave** (`VALENCIA / VALÈNCIA`, `PALMAS (LAS)`): se usará `IDProvincia` como clave y el nombre solo como etiqueta.
- **Los códigos se mantienen como texto** aunque parezcan números (`IDProvincia` = `"02"`, `C.P.` = `"02250"`): convertirlos a número perdería los ceros a la izquierda.
- **`Rótulo` es texto libre:** 3.565 rótulos distintos para 11.433 estaciones. Los 30 rótulos más frecuentes (~7.000 estaciones) están limpios; en la cola aparecen marca + nombre de estación (`BP HOSTAL DE LA SELVA`, `GALP/3CAMINOS-VALENCIA`), razones sociales (`COMBUSTIBLES CALAHORRA S.L.`), cooperativas y low-cost que se declaran en el nombre. → En la transformación: clasificar rótulo → marca → grupo → tipo de operador (gran petrolera / low-cost / hipermercado / independiente) con reglas de palabra completa y una tabla de correspondencias (seed de dbt), midiendo el % de cobertura.
- **MOEVE y CEPSA** conviven por el cambio de marca en curso: ejemplo real de cambio de atributo que justifica la **SCD tipo 2** en la dimensión de estaciones. Marca ≠ grupo (CAMPSA y PETRONOR pertenecen a Repsol).
- Pregunta de análisis pendiente: ¿explican las low-cost la dispersión de precios dentro de la península?
- `Tipo Venta` = `P` (venta al público) en todas las estaciones; `Margen` = lado de la carretera (D/I/N); `Remisión` = quién comunica el precio (OM/dm, pendiente de confirmar en la documentación).

## Decisiones pendientes
| Pendiente | Fase |
|---|---|
| Si el servicio genera la foto en cada petición, y hora de ejecución diaria de la ingesta | 4 · Script de ingesta |
| Si hay endpoint histórico por fecha para hacer backfill | 4 · Script de ingesta |
| Nivel de precios: contrastar con una fuente independiente (Boletín Petrolero de la UE o prensa) | 4 · Script de ingesta |
| Separar las dependencias de desarrollo (pandas, JupyterLab) de las de la Function (`ingesta/requirements.txt`, solo lo imprescindible) | 4 · Script de ingesta |
| Memoria mínima de instancia de Flex Consumption (afecta al coste). Python 3.13 ya confirmado en Spain Central (D-009) | 5 · Infraestructura con Terraform |
| Medir la primera semana el coste real de la cuenta de almacenamiento interna de la Function; si es alto, aplicar el plan B (GitHub Actions) | 5 · Infraestructura con Terraform |
| **Comprobar que Cost Management mide el consumo real** (comparar Análisis de costes con Education Hub la primera semana) y que llegan los correos de alerta (D-010) | 5 · Infraestructura con Terraform |
| Iniciar sesión con MFA en la CLI antes de `terraform apply` (ver D-011, lecciones) | 5 · Infraestructura con Terraform |
| Pasar las dos políticas a Terraform (importar las asignaciones existentes o recrearlas con nombre legible) y comprobar que rechazan un recurso fuera de la región o de la lista roja | 5 · Infraestructura con Terraform |
| **Dónde guardar el estado de Terraform:** en local o en un backend remoto en Azure Storage (coste y protección del fichero). Nunca en el repositorio (D-012) | 5 · Infraestructura con Terraform |
| Añadir `.funcignore` para que los tests y ficheros de desarrollo no entren en el paquete de la Function | 5 · Infraestructura con Terraform |
| **Capa de consulta:** Synapse serverless sobre Parquet o Azure SQL Database con oferta gratuita (ambas disponibles en Spain Central; comprobar compatibilidad con la suscripción de estudiante y el consumo de vCore-segundos) | 6 · Zona curated |
| Si se elige Synapse: límites mínimos permitidos en su control de costes, y comprobar que el bloqueo de `Microsoft.Synapse/workspaces/sqlPools` no impide crear el workspace serverless | 6 · Zona curated |
| Adaptador de dbt según la capa elegida: `dbt-sqlserver` (Azure SQL), `dbt-synapse` (comprobar soporte de serverless) o `dbt-duckdb` sobre los Parquet de ADLS | 7 · Modelado con dbt |
| Significado exacto de `Remisión` (OM / dm): confirmar en la documentación del Geoportal | 7 · Modelado con dbt |
| Reglas concretas de clasificación de rótulos y lista de marcas | 7 · Modelado con dbt |
| Si el fichero `.pbix` de Power BI se versiona (en modo Import lleva los datos dentro) | 9 · Power BI |
| Plan de fin del crédito: decidir entre A, B o C, exportar los datos y renovar la regla de anomalías | Septiembre–octubre de 2027 |
