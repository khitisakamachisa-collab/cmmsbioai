**EQUIPOS**

1.- falta: imagen ruta --> Ruta local donde se almacena una imagen del equipo.

2.- modificar : sus estados y evaluar si su significado puede ser adicionado como ayuda, en una ventana de ayuda a futuro.

\- Operativo/En servicio: Funciona correctamente, disponible

\- En mantenimiento: Detenido activamente para trabajo

\- En reparación: Falla activa siendo reparada

\- Fuera de servicio: Intencionalmente inactivo (no por falla)

\- En espera/Standby: Funcional pero no activo (reserva)

\- En calibración: Detenido específicamente para calibrar

\- En inspección/diagnóstico: Evaluándose para identificar problema

\- Con repuesto pendiente: Detenido esperando pieza crítica

\- Bloqueado/Seguridad (LOTO): Bloqueado por seguridad

\- En almacén/Sin instalar: Disponible pero no instalado

\- En almacén de repuestos: Dado de baja, usado como fuente de partes

\- Retirado/Dado de baja: Retirado permanentemente

\- En transporte: En movimiento entre ubicaciones

\- En préstamo/Externos: Fuera de instalación (proveedor/préstamo)

\- En certificación/Validación: En proceso de certificación regulatoria

\- En modificación/Mejora: Detenido para transformaciones mayores

\- Condición crítica/Alerta: Opera con anomalías detectadas

\- Degradado: Opera pero con capacidad reducida

\- En monitoreo: Con sensores IoT activos (predictivo)


**ORDEN DE TRABAJO OT**
1.- en +NUEVA ORDEN, asi como ESTADO Y PRIORIDAD tienen sus menus de seleccion, generar un menu de seleccion para TITULO
solo los nombres no la explicacion que podria servir para mas adelante un menu de ayuda.

\- Correctivo: Reparación de falla inesperada

\- Preventivo: Mantenimiento programado por tiempo/uso

\- Predictivo: Intervención basada en condición/monitoreo

\- Calibración: Ajuste de precisión de instrumentos

\- Inspección: Revisión visual o funcional sin intervención

\- Actualización: Upgrade de firmware/software/hardware

\- Diagnóstico: Evaluación de falla sin reparación aún

\- Prueba/Validación: Verificación post-mantenimiento

\- Limpieza: Mantenimiento de limpieza general

\- Cambio de repuesto: Sustitución de componente

\- Grasa/Lubricación: Mantenimiento de lubricación

\- Instalación: Puesta en servicio inicial

\- Retiro/Dado de baja: Retiro permanente del activo

\- Transferencia: Cambio de ubicación/dependencia

\- Auditoría: Revisión de cumplimiento normativo

\- Otro: Cualquier actividad no categorizada

2.- en editar (lapiz) cambiar la ventana emergente, reordenar. igual que en ver (ojo).
en editar(lapiz):
la caja donde se encuentra la informacion de  equipo y falla esta bien.
las listas de seleccion  NUEVO ESTADO y PRIORIDAD, lado a lado, es decir juntos y a mitad de su tamaño, son muy largos asi que ambos pueden ocupar una fila.
luego sigue TECNICO ASIGNADO y a su lado HORAS, esto por que son ambas muy largar y pueden ir en una sola fila ocupando la misma fila.
sigue en cada fila solas
ACCIONES REALIZADAS
luego
REPUESTOS UTILIZADOS

en ver (ojo)
esta ventana o modal, se muestra con barras latetales desplazables por que la ventana es pequeña y el espacio a lo vertical es bastante amplio
a libre albedrio se sugiere reacomodar esta ventana o modal.

en ESTADO en +nueva orden y en edición (lápiz), modificar "bloqueado (Esp. Repuesto)" a solo "Esp. Repuesto". desde la creación del BD.
debido a que el texto es muy largo y no permite una buena imagen en la pagina.

faltantes:

adicionar para generar luego costos: `costos\_adicionales` --> Costos adicionales incurridos durante la OT (externos, transporte, etc.).

no se hara: `firma\_digital\_tecnico` --> Espacio para firma digital del técnico al completar la OT.
no se hara firma, se determino inecesaria. a menos que exista una plantilla para generar reportes donde esta firma tenga sentido.





**MANTENIMIENTO PREVENTIVO**

faltan:

`descripcion\_detalle` --> Instrucciones detalladas o protocolo a seguir para la tarea.



como esta funcionando esto?

`condiciones\_activacion` --> Campo JSON para almacenar lógica compleja de activación (ej. "OR" entre horas y días).

`logica\_periodicidad` --> Campo JSON para almacenar patrones de periodicidad complejos (ej. 2 veces al año).

`proxima\_fecha\_vencimiento\_manual` --> Fecha objetivo manualmente reprogramada para la próxima ejecución. Tiene prioridad sobre cálculo automático.



INVENTARIO

`codigo\_equivalente` --> Código alternativo del repuesto (OEM, genérico).

`especificaciones\_tecnicas` --> Detalles técnicos específicos (voltaje, tamaño, etc.).

`imagen` --> Ruta local a la imagen del repuesto físico.

`proveedor\_ultimo` --> Nombre del último proveedor del repuesto.

`fecha\_ultima\_entrada`	--> Fecha del último registro de entrada del repuesto.

`precio\_referencia` -->	Precio de referencia para análisis de costos.



**HISTORIAL**

`tipo\_evento` --> modificar categoría del evento y evaluar su significado como ayuda

(tal vez deba ser el titulo en OT)

\- Correctivo: Reparación de falla inesperada

\- Preventivo: Mantenimiento programado por tiempo/uso

\- Predictivo: Intervención basada en condición/monitoreo

\- Calibración: Ajuste de precisión de instrumentos

\- Inspección: Revisión visual o funcional sin intervención

\- Actualización: Upgrade de firmware/software/hardware

\- Diagnóstico: Evaluación de falla sin reparación aún

\- Prueba/Validación: Verificación post-mantenimiento

\- Limpieza: Mantenimiento de limpieza general

\- Cambio de repuesto: Sustitución de componente

\- Grasa/Lubricación: Mantenimiento de lubricación

\- Instalación: Puesta en servicio inicial

\- Retiro/Dado de baja: Retiro permanente del activo

\- Transferencia: Cambio de ubicación/dependencia

\- Auditoría: Revisión de cumplimiento normativo

\- Otro: Cualquier actividad no categorizada





REPORTES
REP-05	Costos de Mantenimiento por Equipo/Periodo -->	Acumulado de costos (repuestos, horas, adicionales) por equipo o periodo. 

Tabla `Ordenes\_Trabajo` + `Ot\_Repuestos\_Utilizados`.



ESTADOS EQUIPOS

`nombre\_estado`	--> Nombre del estado del equipo (ej. "Operativo","Reparacion","Espera Repuesto","Dado de Baja",

"Fuera de Servicio","EOS","Reservado","En transito","Otro"). Debe ser único.



Estados OT

`nombre\_estado`	--> Nombre del estado de la OT (Iniciado, Pendiente, En Curso, Completada, Cancelada, Reprogramada, Otro). Debe ser único.







