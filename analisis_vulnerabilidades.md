# Análisis de Vulnerabilidades — Organización Apache (Maven)

**Curso:** Ciberseguridad (ICC610) — 2026  
**Organización analizada:** Apache Software Foundation  
**Ecosistema de referencia:** Apache Maven  
**Repositorios analizados:** `apache/airflow`, `apache/allura`, `apache/tvm`  
**Fecha de análisis:** 2026-04-28  
**Herramientas utilizadas:** Syft (SBOM), Grype (CVEs), CodeQL (análisis estático), revisión manual de workflows de GitHub Actions

---

## Justificación de la elección

La organización seleccionada es **Apache Software Foundation**, cuyo ecosistema de distribución de artefactos —**Apache Maven**— fue protagonista de un incidente de seguridad documentado en 2025 relacionado con la distribución de artefactos maliciosos en repositorios proxy (GitHub Security Blog, 2025). Esta elección permite conectar directamente los hallazgos del pipeline con un caso de referencia concreto, evaluando si los proyectos activos de la organización presentan condiciones que los harían susceptibles a ataques similares.

Los tres repositorios seleccionados —**Airflow**, **Allura** y **TVM**— representan proyectos de alta relevancia y uso amplio dentro del ecosistema Apache: Airflow es uno de los orquestadores de flujos de trabajo más utilizados en la industria de datos, TVM es un compilador de modelos de aprendizaje profundo con adopción significativa en el ámbito de la IA, y Allura es una plataforma de forja de software de código abierto.

---

## Parte I — Dimensión Cuantitativa

### 1. Inventario de Dependencias (SBOM)

El análisis de la lista de materiales de software (SBOM) generada con **Syft** arrojó los siguientes totales:

| Métrica | Valor |
|---|---|
| Total de dependencias detectadas | 5,624 |
| Paquetes únicos | 2,476 |
| Promedio de dependencias por repositorio | 1,875 |

#### Distribución por tipo de paquete

| Tipo | Cantidad | Porcentaje |
|---|---|---|
| npm | 4,174 | 74.2 % |
| python | 1,181 | 21.0 % |
| github-action | 169 | 3.0 % |
| go-module | 48 | 0.9 % |
| github-action-workflow | 33 | 0.6 % |
| Otros | < 20 | < 0.3 % |

#### Dependencias por repositorio

| Repositorio | Dependencias |
|---|---|
| apache/airflow | 5,423 |
| apache/allura | 128 |
| apache/tvm | 73 |

La asimetría es marcada: **airflow** concentra el 96.4 % del total de dependencias, lo que refleja su complejidad como plataforma de orquestación que integra conectores, proveedores de nube y herramientas de UI web.

#### Licencias registradas en el SBOM

| Licencia | Cantidad | Porcentaje |
|---|---|---|
| Sin licencia especificada | 5,614 | 99.8 % |
| Apache License 2.0 | 8 | 0.1 % |
| 0BSD / Apache-2.0 | 2 | < 0.1 % |

La ausencia casi total de metadatos de licencia en el SBOM es una observación relevante desde el punto de vista de la trazabilidad de la cadena de suministro.

---

### 2. Vulnerabilidades detectadas (Grype)

El escaneo con **Grype** identificó **52 CVEs** distribuidos entre dos de los tres repositorios. `apache/allura` no registró vulnerabilidades en esta ejecución.

#### Distribución por severidad (total)

| Severidad | Cantidad | Porcentaje |
|---|---|---|
| Critical | 2 | 3.8 % |
| High | 19 | 36.5 % |
| Medium | 27 | 51.9 % |
| Low | 4 | 7.7 % |
| **Total** | **52** | **100 %** |

#### Distribución por repositorio y severidad

| Repositorio | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|
| apache/tvm | 0 | 12 | 20 | 4 | **36** |
| apache/airflow | 2 | 7 | 7 | 0 | **16** |
| apache/allura | 0 | 0 | 0 | 0 | **0** |

#### Estado de remediación disponible

| Estado | Cantidad | Porcentaje |
|---|---|---|
| Con versión corregida disponible | 49 | 94.2 % |
| Sin corrección disponible | 3 | 5.8 % |

El 94.2 % de las vulnerabilidades tienen una versión corregida publicada, lo que indica que el problema no es la ausencia de soluciones sino el **retraso en la actualización de dependencias**.

#### Paquetes más vulnerables (Top 10)

| Paquete | Versión actual | Critical | High | Medium | Low | Total CVEs |
|---|---|---|---|---|---|---|
| cryptography | 41.0.6 | 0 | 3 | 2 | 1 | **6** |
| litellm | 1.82.6 | 2 | 4 | 0 | 0 | **6** |
| urllib3 | 1.26.18 | 0 | 3 | 2 | 0 | **5** |
| pip | 22.1.1 | 0 | 0 | 3 | 1 | **4** |
| requests | 2.27.1 | 0 | 0 | 4 | 0 | **4** |
| certifi | 2022.5.18.1 | 0 | 1 | 1 | 1 | **3** |
| setuptools | 62.3.2 | 0 | 3 | 0 | 0 | **3** |
| virtualenv | 20.14.1 | 0 | 1 | 1 | 0 | **2** |
| postcss (varias versiones) | múltiple | 0 | 1 | 1 | 0 | **2–3** |
| picomatch | 4.0.3 | 0 | 1 | 1 | 0 | **2** |

#### Versiones de remediación recomendadas (paquetes críticos/high)

| Paquete | Versión vulnerable | Versión(es) corregida(s) |
|---|---|---|
| litellm | 1.82.6 | 1.83.0 / 1.83.7 |
| cryptography | 41.0.6 | 42.0.0, 42.0.4, 43.0.1, 46.0.5 |
| urllib3 | 1.26.18 | 1.26.19, 2.5.0, 2.6.3 |
| setuptools | 62.3.2 | 65.5.1, 70.0.0, 78.1.1 |
| virtualenv | 20.14.1 | 20.26.6 |

---

### 3. Análisis estático de código (CodeQL)

El análisis con **CodeQL 2.25.1** procesó código Python, JavaScript, Java, C++ y C# en los repositorios compatibles, produciendo **27 hallazgos** sobre **20 archivos afectados**.

#### Distribución por nivel de severidad (CodeQL)

| Nivel | Cantidad | Porcentaje |
|---|---|---|
| error (problema de seguridad) | 13 | 48.1 % |
| warning (advertencia) | 14 | 51.9 % |
| **Total** | **27** | **100 %** |

**Reglas únicas activadas:** 7

#### Tipos de hallazgos más frecuentes

| Tipo de hallazgo | Nivel | Instancias |
|---|---|---|
| Sanitización incompleta de URL (substring) | warning | 8 |
| Uso de algoritmo de hash criptográfico débil | warning | 4 |
| Almacenamiento en texto claro de información sensible | error | 2 |
| Registro en texto claro de información sensible | error | 2 |
| XSS / patrones de inyección en plantillas | error | ~3 |
| Assert con efectos secundarios | warning | ~2 |

---

### 4. Configuraciones de CI/CD (GitHub Actions)

La revisión de los workflows de GitHub Actions detectó **57 hallazgos** en total.

#### Distribución por severidad (CI/CD)

| Severidad | Cantidad | Porcentaje |
|---|---|---|
| High | 1 | 1.8 % |
| Medium | 56 | 98.2 % |
| **Total** | **57** | **100 %** |

#### Distribución por repositorio

| Repositorio | High | Medium | Total |
|---|---|---|---|
| apache/airflow | 0 | 45 | **45** |
| apache/tvm | 1 | 10 | **11** |
| apache/allura | 0 | 1 | **1** |

#### Tipos de problemas detectados en CI/CD

| Tipo | Nivel | Instancias |
|---|---|---|
| Secreto expuesto como variable de entorno en `run` | Medium | 43 |
| Permiso `contents: write` en workflows | Medium | 12 |
| Acción referenciada por tag y no por SHA completo | Medium | 1 |
| Trigger `pull_request_target` con escritura al repo | High | 1 |

**Acciones sin pin de SHA (supply chain risk):** 4 instancias detectadas en `allura/codeql.yml`

---

### 5. Resumen ejecutivo cuantitativo

| Indicador | Valor |
|---|---|
| Repositorios analizados | 3 |
| Total dependencias en SBOM | 5,624 |
| Total CVEs detectados | 52 |
| CVEs Críticos + Altos | 21 (40.4 %) |
| CVEs con corrección disponible | 49 (94.2 %) |
| Hallazgos CodeQL (nivel error) | 13 |
| Hallazgos CodeQL totales | 27 |
| Problemas en CI/CD | 57 |
| Acciones sin pin SHA | 4 |
| **Estado de riesgo general** | 🔴 **ALTO** |

---

## Parte II — Dimensión Cualitativa

### 6. Interpretación de los resultados

#### 6.1 Patrón de acumulación de deuda de actualización

El hallazgo más llamativo desde una perspectiva cualitativa no es la presencia de vulnerabilidades críticas —solo 2 de 52— sino que el **94.2 % de los CVEs detectados tienen una solución publicada y disponible**. Esto revela un patrón sistémico de **deuda de actualización**: las vulnerabilidades no persisten por falta de parches, sino porque los proyectos no incorporan las versiones corregidas de sus dependencias a un ritmo adecuado.

Este fenómeno es especialmente visible en paquetes como `urllib3` (versión 1.26.18 frente a la 2.6.3 disponible), `certifi` (2022.5.18.1) y `setuptools` (62.3.2). Las versiones afectadas datan en algunos casos de 2022, lo que sugiere que los entornos de producción pueden estar operando con configuraciones de años de antigüedad sin revisión activa de dependencias.

Apache Foundation, como organización, prioriza históricamente la **estabilidad** sobre la actualización continua. Este es un comportamiento estructural del ecosistema de software de código abierto maduro: proyectos de larga trayectoria como Airflow gestionan matrices de compatibilidad muy amplias que desincentivan actualizaciones frecuentes de dependencias indirectas.

#### 6.2 Concentración del riesgo en Airflow y TVM

La distribución desigual de vulnerabilidades entre repositorios es significativa: `airflow` y `tvm` concentran el 100 % de los CVEs, mientras que `allura` no registra ninguno. Esto no implica necesariamente que `allura` sea más seguro, sino que su superficie de dependencias es mucho menor (128 paquetes frente a 5,423 de `airflow`).

La complejidad de `airflow` —con más de 5,400 dependencias detectadas, principalmente npm— lo convierte en el repositorio con mayor **superficie de ataque transitiva**. Esta complejidad es un multiplicador de riesgo: cada dependencia transitiva representa un punto de entrada potencial para ataques de cadena de suministro.

El caso de `litellm` en `airflow` es particularmente ilustrativo: es el único paquete con vulnerabilidades **críticas** (2 CVEs), y se trata de una biblioteca para interacción con modelos de lenguaje grande (LLMs), un tipo de dependencia que ha crecido rápidamente en popularidad reciente y que puede no estar sujeta al mismo nivel de escrutinio de seguridad que bibliotecas más maduras.

#### 6.3 Hallazgos de CodeQL: problemas de código con consecuencias reales

Los 13 hallazgos a nivel `error` en CodeQL no deben minimizarse por encontrarse parcialmente en código de pruebas o ejemplos. Las instancias de **almacenamiento y registro en texto claro de información sensible** (contraseñas, credenciales) son indicativos de prácticas de desarrollo que, si se replican en rutas de producción, pueden ser explotadas directamente.

El patrón de **sanitización incompleta de URLs** —detectado en 8 instancias— es especialmente relevante en el contexto del caso de referencia `tj-actions/changed-files` (2025): un workflow comprometido con URLs no validadas puede ser utilizado como vector para redirigir descargas o exfiltrar información.

El uso de **algoritmos de hash débiles** para contraseñas refuerza la hipótesis de que existen zonas del código que no han sido revisadas con criterios de seguridad modernos, posiblemente porque la atención de las revisiones se concentra en funcionalidades nuevas y no en componentes heredados.

#### 6.4 CI/CD: la superficie más expuesta del ecosistema

Los 57 problemas detectados en configuraciones de GitHub Actions representan la dimensión de mayor riesgo ecosistémico, por dos razones:

**Primero**, el uso de `pull_request_target` con permisos de escritura al repositorio (detectado en `tvm`) es exactamente el vector descrito en los casos de referencia de GitHub Actions (2024–2026). Este patrón permite que el código de un pull request externo —potencialmente malicioso— sea ejecutado con los permisos del repositorio original, lo que puede derivar en exfiltración de secretos o modificación del repositorio.

**Segundo**, los 43 casos de secretos expuestos como variables de entorno en pasos `run` son un patrón que, aunque clasificado como Medium en severidad individual, tiene un impacto acumulado alto. En un repositorio de alta actividad como `airflow`, los logs de CI/CD son públicos por defecto, lo que significa que cualquier filtración de secretos en los outputs de los pasos es inmediatamente visible para actores externos.

#### 6.5 Cadena de suministro: el riesgo latente de las acciones sin pin de SHA

Las 4 acciones de GitHub sin pin de SHA detectadas en `allura/codeql.yml` representan un vector de ataque directo relacionado con el incidente **Shai-Hulud (2025)**, que comprometió más de 19,000 repositorios mediante paquetes modificados. Cuando una acción se referencia por tag (`@v4`) en lugar de por hash SHA completo, el mantenedor de la acción puede modificar su código sin que el repositorio consumidor perciba ningún cambio en su configuración. Esto convierte a cada acción sin pin en un punto de confianza implícita y potencialmente no verificada.

---

### 7. Identificación de patrones y posibles causas

#### Patrón 1 — Velocidad de actualización vs. estabilidad de la plataforma

Los proyectos Apache analizados exhiben un patrón común en ecosistemas maduros de código abierto: las actualizaciones de dependencias se realizan de forma reactiva (ante reportes de CVEs críticos) más que de forma proactiva. Las versiones afectadas de `urllib3`, `certifi` y `pip` con fechas de 2022 confirman que partes del árbol de dependencias no se revisan activamente.

**Causa probable:** Airflow y TVM gestionan matrices de compatibilidad muy amplias (múltiples versiones de Python, múltiples proveedores de nube). Actualizar una dependencia como `cryptography` puede romper la compatibilidad con otros componentes, lo que desincentiva actualizaciones frecuentes sin un proceso de validación exhaustivo.

#### Patrón 2 — Complejidad como multiplicador de riesgo

La concentración del 96 % de las dependencias en un único repositorio (`airflow`) y la presencia de 74 % de paquetes npm en un proyecto predominantemente Python sugieren que la superficie de ataque no está siendo gestionada conscientemente. La inclusión masiva de dependencias npm en un proyecto de orquestación de datos probablemente responde a la integración de interfaces web (dashboards), pero genera una superficie transitiva significativa.

**Causa probable:** El crecimiento orgánico de las funcionalidades —en particular la interfaz web de Airflow— incorporó dependencias frontend que no están sujetas al mismo ciclo de revisión de seguridad que el núcleo del proyecto.

#### Patrón 3 — Configuraciones de CI/CD heredadas

La presencia de 12 workflows con `contents: write` y 43 instancias de secretos en variables de entorno sugiere que las configuraciones de CI/CD se han acumulado sin una revisión periódica de privilegios. Este es un patrón documentado en la literatura de seguridad de DevOps: los workflows se crean para resolver un problema inmediato y rara vez se revisan en términos de principio de mínimo privilegio una vez que funcionan.

**Causa probable:** En proyectos de alta contribución como `airflow` (con cientos de colaboradores), la gestión centralizada de la seguridad de los workflows es difícil de escalar. La responsabilidad recae en revisores individuales que pueden no tener el contexto de seguridad necesario para identificar configuraciones riesgosas.

#### Patrón 4 — Prácticas locales vs. condiciones del ecosistema

Es importante distinguir entre problemas que son **propios de las prácticas de desarrollo** de estos proyectos y problemas que **reflejan condiciones más amplias del ecosistema**:

- **Prácticas locales:** el almacenamiento en texto claro de credenciales en CodeQL y los algoritmos de hash débiles son indicativos de prácticas de desarrollo específicas que pueden mejorarse con revisiones de código y herramientas de análisis estático integradas en el pipeline.

- **Condiciones del ecosistema:** la acumulación de dependencias desactualizadas, las acciones sin pin de SHA y los permisos excesivos en workflows son problemas que afectan a la gran mayoría de los proyectos de código abierto en GitHub y responden a la estructura del ecosistema, no a las decisiones individuales de los desarrolladores.

---

### 8. Relación con los casos de referencia

| Caso de referencia | Año | Conexión con los hallazgos |
|---|---|---|
| **Apache Maven — Artefactos maliciosos en repos proxy** | 2025 | Las 52 dependencias con CVEs y las 4 acciones sin pin de SHA crean condiciones análogas: dependencias desactualizadas amplían la ventana de ataque para distribución de artefactos manipulados. |
| **tj-actions/changed-files — Exposición de secretos** | 2025 | El trigger `pull_request_target` detectado en `tvm` y los 43 secretos en variables de entorno reproducen exactamente el vector de ataque documentado en este caso. |
| **GitHub Actions (ecosistema) — Configuración insegura** | 2024–2026 | Los 12 workflows con `contents: write` son el patrón central estudiado en la literatura de seguridad de GitHub Actions (arXiv:2601.14455). |
| **Shai-Hulud campaign — Compromiso masivo de repositorios** | 2025 | Las 4 acciones sin pin de SHA en `allura/codeql.yml` son el vector de entrada documentado en esta campaña, que comprometió más de 19,000 repositorios. |

---

### 9. Riesgos amplios del ecosistema

#### Riesgo 1 — Ventana de explotación por deuda de actualización

El intervalo entre la publicación de un CVE y su remediación efectiva en producción es la ventana de explotación. Con el 94.2 % de los CVEs ya corregidos en versiones publicadas pero aún presentes en los repositorios analizados, la pregunta no es si las vulnerabilidades pueden explotarse, sino durante cuánto tiempo han sido explotables.

#### Riesgo 2 — Escalabilidad del riesgo de CI/CD

Airflow, con 45 problemas en CI/CD, es un proyecto de alta actividad con cientos de contribuidores activos. Un workflow con `contents: write` o secretos mal gestionados no solo afecta a los mantenedores del proyecto, sino potencialmente a los miles de organizaciones que utilizan Airflow como infraestructura crítica de datos. El riesgo se escala con el tamaño de la base de usuarios.

#### Riesgo 3 — Confianza implícita en la cadena de suministro

La combinación de dependencias desactualizadas, acciones sin pin de SHA y ausencia de verificación de integridad (checksums SBOM) crea un modelo de **confianza implícita** en toda la cadena de suministro del software. Este modelo es exactamente el que fue explotado en el incidente de Apache Maven (2025) y en la campaña Shai-Hulud.

---

### 10. Recomendaciones derivadas del análisis

1. **Actualizar dependencias con CVEs corregidos:** priorizar `litellm`, `cryptography`, `urllib3`, `setuptools` y `virtualenv`, donde existen versiones corregidas publicadas.
2. **Fijar acciones de GitHub por SHA completo:** reemplazar referencias por tag (`@v4`) con el hash SHA de la versión correspondiente.
3. **Aplicar principio de mínimo privilegio en workflows:** eliminar `contents: write` de workflows que no lo requieran de forma explícita.
4. **Migrar secretos a gestores seguros:** reemplazar variables de entorno en pasos `run` por referencias a secretos de GitHub Actions u otros sistemas de gestión de secretos.
5. **Integrar análisis estático de seguridad en el pipeline:** los 13 hallazgos a nivel `error` de CodeQL deben bloquearse en CI/CD antes de que el código llegue a producción.
6. **Firmar el SBOM generado:** implementar verificación de integridad del inventario de software como medida de detección temprana de compromiso en la cadena de suministro.

---

*Análisis generado con base en los resultados del pipeline `00_pipeline_completo.ipynb`. Herramientas: Syft v1.x, Grype v0.x, CodeQL 2.25.1.*
