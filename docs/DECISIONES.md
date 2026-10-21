# Decisiones del proyecto

Registro de las decisiones técnicas del pipeline en formato ADR (Architecture Decision Record): qué problema había, qué decidí, qué descarté y qué consecuencias tiene. Las reglas de coste están en [COSTES.md](COSTES.md) y la descripción de los datos en [ESQUEMA_DATOS.md](ESQUEMA_DATOS.md).

---

## D-001 · Fuente de datos: precios de carburantes del Ministerio

Estado: aceptada

### Contexto
Quería un dataset real, público y que se actualizara solo, para que tuviera sentido construir un pipeline. Los típicos de portfolio (Kaggle, taxis de Nueva York) son estáticos y están muy vistos.

### Decisión
Uso el servicio REST de precios de carburantes del Ministerio para la Transición Ecológica. Se actualiza a diario, es gratuito, no necesita clave y cubre unas 11.400 gasolineras. Además enlaza con un proyecto anterior mío de costes de flota.

### Alternativas descartadas
- Datasets estáticos de Kaggle o el de taxis de Nueva York: no se actualizan, así que no hay histórico que construir.

### Consecuencias
El valor del proyecto está en el histórico que voy acumulando. Si la ingesta falla un día, ese día se pierde, salvo que el servicio tenga un endpoint histórico (pendiente de comprobar).

---

## D-002 · Nube: Azure

Estado: aceptada

### Contexto
Necesitaba una nube en la que montar el pipeline sin riesgo de factura y que me sirviera para el mercado laboral al que apunto.

### Decisión
Lo hago en Azure con una suscripción Azure for Students. Tiene 88 $ de crédito sin tarjeta hasta el 18/11/2027 y, si se acaba, la suscripción se desactiva en lugar de cobrar, así que el primer año no puedo tener factura. Además, Azure aparece mucho en las ofertas de datos en España y encaja con SQL Server y Power BI.

### Alternativas descartadas
- AWS: el plan gratuito cierra la cuenta a los 6 meses, con los datos dentro, y el de pago pide tarjeta.
- GCP: aparece menos en las ofertas que me interesan.

### Consecuencias
El crédito caduca y solo se renueva mientras sea estudiante, y la suscripción depende de mi cuenta de la universidad. Por eso toda la infraestructura irá en Terraform: así puedo recrearla en otra suscripción en minutos.

---

## D-003 · Serverless en lugar de un servidor

Estado: aceptada

### Contexto
El pipeline se ejecuta una vez al día durante unos segundos.

### Decisión
Una Azure Function con disparador temporizado (Python 3.13, plan Flex Consumption) que escribe en ADLS Gen2. Encima va una capa de consulta SQL que decidiré en la fase 6, dbt y Power BI. Con serverless solo pago lo que se ejecuta: calculo 1–3 € al año, frente a 50–60 € de un VPS encendido todo el día. Elijo Flex Consumption porque el plan Consumption de Linux se retira en septiembre de 2028 y Microsoft recomienda Flex para aplicaciones nuevas. Comprobé que en Spain Central admite Python 3.13, la misma versión que uso en local.

### Alternativas descartadas
- VPS o máquina virtual con cron: más caro a este volumen, y hay que mantener el servidor.
- Data Factory para la ingesta: sus copias tienen un coste mínimo por ejecución que, a diario, supera mi límite anual.

### Consecuencias
Si la cuenta de almacenamiento interna de la Function saliera cara, tengo un plan B: ejecutar la ingesta como workflow programado de GitHub Actions. Con mucho volumen o carga constante, un servidor podría salir más a cuenta.

---

## D-004 · JSON crudo comprimido y Parquet particionado

Estado: aceptada

### Contexto
El JSON de un día ocupa unos 14 MB y la mayoría de los 23 campos de precio vienen vacíos. Synapse serverless cobra por datos leídos.

### Decisión
Guardo dos copias. En raw, el JSON tal cual llega, comprimido con gzip (1–2 MB al día): es la copia de seguridad para poder reprocesar. En curated, Parquet en formato largo (una fila por estación, carburante y día: unas 42.000 filas y menos de 0,5 MB al día), particionado por fecha. Consultar Parquet particionado cuesta del orden de 100 veces menos que consultar el JSON.

### Alternativas descartadas
- Guardar solo el JSON: caro de consultar.
- Parquet en formato ancho, con una columna por carburante: casi todas las celdas serían nulas.

### Consecuencias
La transformación de raw a curated es un paso más que mantener, pero puedo rehacer curated desde raw siempre que quiera.

---

## D-005 · Esquemas como código

Estado: aceptada

### Contexto
Sea cual sea la capa de consulta, hay que definir las tablas y vistas sobre los datos.

### Decisión
Las defino en SQL versionado en el repositorio (más adelante, con dbt), y la infraestructura con Terraform. Conozco el esquema y es estable, así que declararlo en código es gratis, reproducible y queda en el historial.

### Alternativas descartadas
- Spark pools de Synapse o Data Factory para transformar y catalogar: cobran por hora.

### Consecuencias
Si la fuente cambia un campo, tengo que actualizar el esquema yo; no hay nada que lo descubra solo.

---

## D-006 · Explorar los datos en local antes de tocar la nube

Estado: aceptada

### Contexto
Sin conocer el dato, cualquier diseño de esquema o estimación de coste habría sido inventada.

### Decisión
Primero descargué y exploré el JSON en local con Python y JupyterLab; la infraestructura viene después. No cuesta nada y me permitió encontrar los problemas de calidad antes de construir la tubería.

### Alternativas descartadas
- Diseñar el pipeline primero e ir descubriendo los datos sobre la marcha.

### Consecuencias
La exploración no depende de la nube, así que sigue valiendo aunque cambie la infraestructura. Lo que encontré está en ESQUEMA_DATOS.md.

---

## D-007 · Conexión TLS con el servidor del Ministerio

Estado: aceptada

### Contexto
Python no podía descargar los datos: el servidor cortaba la conexión en el handshake TLS. El navegador y curl sí funcionaban.

### Decisión
Probé cambiando una cosa cada vez (red, User-Agent, versión de TLS) y vi que el servidor solo acepta cifrados RSA, que Python no ofrece por defecto. Monté un adaptador de requests solo para ese host, con TLS 1.2, los cifrados modernos primero y los RSA después. La verificación del certificado sigue activa.

### Alternativas descartadas
- verify=False: quita la verificación del certificado.
- SECLEVEL=1: funcionaba, pero relaja más de lo necesario.
- Descargar con curl: la ingesta va en una Function de Python, así que tiene que funcionar en Python.

### Consecuencias
Los datos son públicos y no viajan credenciales, así que el riesgo es bajo. El cambio no afecta a ninguna otra conexión, y si el servidor se actualiza se usarán los cifrados modernos sin tocar nada.

---

## D-008 · Coordenadas erróneas

Estado: aceptada

### Contexto
Al validar las coordenadas contra los rangos de España, 27 estaciones quedaban fuera. 22 eran de Ceuta y Melilla (válidas: me faltaba su rango), 4 tenían (0, 0) y una, en Tui, tenía la latitud y la longitud intercambiadas.

### Decisión
Uso tres rangos válidos: península y Baleares (lat 36 a 44, lon −9,5 a 4,5), Canarias (lat 27,5 a 29,5, lon −18,5 a −13) y Ceuta y Melilla (lat 35 a 36, lon −5,5 a −2,8). Los (0, 0) pasan a nulo con el flag coord_ausente. Si al intercambiar latitud y longitud la estación cae en rango, la corrijo y la marco con coord_corregida. El resto de casos fuera de rango pasan a nulo con coord_invalida. Nunca borro estaciones, y el dato original queda siempre en raw.

### Alternativas descartadas
- Borrar las estaciones afectadas: perdería sus precios, que son correctos.
- Dejar los (0, 0): aparecerían en el mar frente a África.
- Geocodificar la dirección: dependencia externa y coste para 4 casos.

### Consecuencias
Solo corrijo lo inequívoco y todo lo tocado queda marcado, así que el dato sigue siendo auditable. La lección: count decía que no faltaba ninguna coordenada, pero cuatro venían como (0, 0). Un valor ausente puede llegar disfrazado de cero.

---

## D-009 · Región: Spain Central

Estado: aceptada

### Contexto
Quería una sola región para todo el proyecto. Pensaba en Spain Central, West Europe o North Europe, pero Azure for Students trae una política que solo permite 5 regiones, distintas para cada estudiante. En mi suscripción son Germany West Central, Norway East, Spain Central, Italy North y Switzerland North.

### Decisión
Spain Central. Comprobé con la CLI que tiene todo lo que necesito: Flex Consumption con Python 3.10–3.14, Synapse y Azure SQL. Además es la elección natural para datos españoles, y en precio la diferencia entre regiones es de céntimos al año.

### Alternativas descartadas
- West Europe y North Europe: no están permitidas en mi suscripción.
- Germany West Central: tiene lo mismo, pero no aporta nada. La dejo como plan B.
- Norway East, Italy North y Switzerland North: sin ventajas.

### Consecuencias
La fijé con una política propia (D-011) para que no se pueda crear nada en otra región.

---

## D-010 · Control de costes por capas

Estado: aceptada

### Contexto
La documentación de Cost Management dice que Azure for Students no está soportado, pero Education Hub recomienda crear presupuestos. Las dos fuentes se contradecían, y el presupuesto era una de mis protecciones del primer día.

### Decisión
Lo comprobé en lugar de fiarme de ninguna: el presupuesto, sus alertas y la regla de anomalías se crean sin errores, y el análisis de costes funciona. Aun así, no dejo el control de costes en una sola pieza. Lo monto en tres capas: prevenir (políticas, D-011), limitar (crédito sin tarjeta, límites por servicio y formatos baratos) y detectar (presupuesto de 1 € al mes, alerta de anomalías y revisión semanal del crédito).

### Alternativas descartadas
- Fiarme de la documentación y no crear presupuesto: me quedaría sin aviso temprano.
- Fiarme solo del presupuesto: avisa cuando el gasto ya ha ocurrido, pero no lo evita.

### Consecuencias
En la fase 5 tengo que comprobar que el presupuesto mide el consumo real y que llegan los correos. A partir del segundo año, con pago por uso, los presupuestos pasan a ser la protección principal, así que me interesa tenerlos ya funcionando y entendidos.

---

## D-011 · Políticas de Azure contra los recursos caros

Estado: aceptada

### Contexto
Las alertas solo avisan, y cuando el gasto ya ha ocurrido. El error más caro sería crear sin querer un recurso con coste fijo por hora: un asistente del portal que añade extras, un tutorial copiado o una errata en Terraform.

### Decisión
Asigné dos políticas con efecto Deny a toda la suscripción. solo-spain-central solo permite crear recursos en esa región. lista-roja-costes bloquea 15 tipos de recurso caros: máquinas virtuales y conjuntos de escalado, Databricks, Data Factory, pools dedicated y Spark de Synapse, Fabric, Power BI Embedded, NAT Gateway, Private Endpoints, IP públicas, gateways de VPN, Azure Firewall, Cosmos DB y Managed HSM.

### Alternativas descartadas
- Solo documentar la lista roja: depende de que me acuerde.
- La política Exclude Usage Costs Resources: bloquea categorías enteras e impediría el propio proyecto.

### Consecuencias
Azure aplica la lista roja aunque me equivoque, y es gratis y reversible. Pero no garantiza gastar 0 €: no cubre el coste por uso de lo que sí está permitido. Tampoco bloqueo los planes de App Service (los necesita la Function), ni los workspaces de Synapse ni los servidores SQL (son las opciones de la fase 6); esos riesgos los vigilo en el plan de Terraform. Aprendí dos cosas: el portal solo lista los tipos de los proveedores registrados, por eso asigné la lista roja con la CLI; y Azure exige MFA para crear o modificar recursos desde la CLI, Terraform o la API.

---

## D-012 · Repositorio: monorrepo por herramienta

Estado: aceptada

### Contexto
El proyecto mezcla Python, Terraform, políticas, dbt y documentación, y el repositorio es público.

### Decisión
Un único repositorio con una carpeta por herramienta: ingesta/, infra/, dbt/, notebooks/ y docs/. Las piezas cambian juntas (un campo nuevo toca la ingesta, dbt y la documentación), así que van en el mismo commit, y cada workflow de CI se lanza solo cuando cambia su carpeta. Nunca versiono secretos, el estado de Terraform (guarda claves en texto plano), los datos ni lo que se puede regenerar. En el .gitignore excluyo por ubicación y no por extensión, porque un JSON puede ser un fichero de parámetros y un CSV un seed de dbt.

### Alternativas descartadas
- Un repositorio por componente: más sobrecarga para un proyecto de una persona.
- Ignorar *.json o *.csv: excluiría ficheros que son código.
- Crear ya todas las carpetas con .gitkeep: el repositorio mostraría carpetas vacías durante meses.

### Consecuencias
Un secreto subido sigue en el historial aunque lo borre, así que lo prevengo antes del commit: .gitignore, revisión con git status --untracked-files=all y el push protection de GitHub como última red. El .gitattributes normaliza los finales de línea a LF, porque la Function y la CI corren en Linux.

---

## D-013 · Paquete de ingesta: layout plano y dependencias separadas

Estado: aceptada

### Contexto
La ingesta se va a ejecutar en local, en la CI y en una Azure Function. Necesito poder testearla sin red y que la Function cargue solo lo imprescindible.

### Decisión
Un paquete carburantes_ingesta/ con layout plano dentro de ingesta/, junto a function_app.py, con un módulo por responsabilidad: descarga, validación, almacenamiento y orquestación. La lógica no toca la red ni el disco directamente: la sesión HTTP, el destino y la fecha se pasan como parámetros, y en los tests los sustituyo. Las dependencias van separadas: requirements.txt solo con lo que necesita la Function y con versiones exactas, y requirements-dev.txt con eso más pytest. Pandas y JupyterLab se quedan en notebooks/.

### Alternativas descartadas
- Layout src/: es el estándar para librerías que se instalan con pip, pero aquí obligaría a instalar el paquete en la Function sin aportar nada.
- Un único requirements.txt, o generarlo con pip freeze: metería pandas y JupyterLab en la Function.

### Consecuencias
El mismo código se ejecuta en local, en la CI y en Azure. Con layout plano tuve que añadir pythonpath = ["."] a la configuración de pytest, porque pytest no añade la carpeta actual al sys.path (python -m pytest sí).

---

## D-014 · Validaciones de la ingesta en dos niveles

Estado: aceptada

### Contexto
Había previsto validar en la ingesta todos los precios y comparar el número de estaciones con el del día anterior. Pero un solo precio mal entre 42.000 me haría perder el día entero, y comparar con el día anterior obliga a la ingesta a leer el fichero previo.

### Decisión
Separo dos niveles. Si la respuesta es inutilizable (no es JSON, ResultadoConsulta no es OK, la lista de estaciones falta o está vacía, o hay menos de 10.000 o más de 13.000 estaciones), no guardo nada y la ejecución falla con un error propio. Si es utilizable pero tiene datos raros (IDEESS duplicados, precios que no se pueden convertir o fuera de rango), la guardo en raw y registro un aviso. Esos datos se tratan en curated, en la fase 6, igual que la comparación con el día anterior.

### Alternativas descartadas
- Rechazar el día si algo falla: perdería histórico por un solo dato.
- No validar: guardaría respuestas de error o truncadas sin enterarme.
- Comparar ya con el día anterior: añade estado a la ingesta cuando aún no hay histórico.

### Consecuencias
Un fallo de la ingesta significa algo concreto y merece una alerta. El rango de 10.000 a 13.000 (unos ±12 % sobre las 11.433 estaciones actuales) habrá que revisarlo si el número de estaciones cambia mucho.
