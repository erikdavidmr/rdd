# Changelog — POS Verifone Terminal Integration

## [18.0.1.3.0] — 2025-05-11

### Added
- Soporte para flujo asincrónico de pagos Verifone vía canal `VERIFONE_LATEST_RESPONSE`.
- Manejo de respuesta diferida mediante método `handleVerifoneStatusResponse`.
- Notificaciones visuales (`this.env.services.notification.add`) para pagos aprobados.
- Registro estructurado del payload de Verifone en consola con `console.debug`.

### Improved
- Validación más robusta para localizar la línea de pago activa (`waitingCard`) en `verifone_pos_patch.js`.
- Mensajes de error más claros en casos de rechazo o errores de conexión.
- Compatibilidad con múltiples líneas de pago o flujos simultáneos.

### Technical
- Nuevo archivo `verifone_pos_patch.js` incluido como asset de POS.
- Actualización del `__manifest__.py` a versión `18.0.1.3.0` y organización de assets.
- Código preparado para futura integración con webhook o middleware externo.

---

## [18.0.1.2.0]
- Versión base con integración inicial con middleware Verifone local (LAN).
- Envío síncrono del pago desde POS a `/pay` en middleware simulado.
- Configuración de IP y puerto desde `pos.payment.method`.