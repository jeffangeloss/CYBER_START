# CYBER_START – Guía rápida

Este repositorio contiene tres piezas principales:

1. **Firmware ESP32** (`ESP32_CONTROL/ESP32_CONTROL.ino`) – se compila y sube con el IDE de Arduino o PlatformIO.
2. **Interfaz web** (`PaginaSemaforos/PaginaSemaforos`) – aplicación React/Vite que controla el semáforo.
3. **Proxy Python** (`servidor_final.py`) – sirve la carpeta `dist` y reenvía las peticiones `/api/*` hacia el ESP32.

Sigue los pasos siguientes para ejecutarlo en tu equipo.

---

## 1. Clonar y preparar el proyecto
```powershell
cd $HOME\Downloads
# Reemplaza la URL con la de tu fork si aplica
git clone https://github.com/jeffangeloss/CYBER_START.git CYBER_START
cd CYBER_START
```

> ℹ️ En PowerShell **no copies los comentarios** que aparecen tras un `#`.

---

## 2. Construir la interfaz web
```powershell
cd PaginaSemaforos/PaginaSemaforos
npm install
npm run build
cd ../..   # vuelve a la raíz del repositorio
```
El comando `npm run build` genera la carpeta `dist` que el proxy servirá más adelante.

---

## 3. Configurar y arrancar el proxy HTTP
Edita `servidor_final.py` o usa argumentos/variables para apuntar al ESP32:

```powershell
# Ejemplos de ejecución
python servidor_final.py --esp32 192.168.1.120
python servidor_final.py --esp32 192.168.1.120 --port 8081 --bind 0.0.0.0
```

Variables de entorno alternativas:
```powershell
$env:ESP32_HOST = "192.168.1.120"
$env:SERVIDOR_PUERTO = "8080"
python servidor_final.py
```

El banner inicial mostrará todas las URL disponibles (localhost y las IP de la red). Si necesitas indicar manualmente dónde está la carpeta `dist`, añade `--web-dir "Ruta\al\dist"`.

---

## 4. Cargar el firmware en el ESP32
1. Abre `ESP32_CONTROL/ESP32_CONTROL.ino`.
2. Configura `WIFI_SSID` y `WIFI_PASS`.
3. Compila y sube el sketch.
4. Toma nota de la IP que imprime el ESP32 en el monitor serie (será la que uses en `--esp32`).

---

## 5. Probar todo junto
1. Asegúrate de que el ESP32 y tu PC estén en la misma red.
2. Arranca `servidor_final.py` con la IP real del ESP32.
3. Abre `http://localhost:8080` (o la IP que muestre el banner) en el navegador.
4. Desde la página puedes iniciar/detener el ciclo del semáforo y ver el estado actual.

Si recibes un error 502, revisa la conexión del ESP32 y que el puerto 80 esté accesible desde tu PC.

---

## 6. Desarrollo local opcional
Para realizar cambios rápidos en el front-end puedes usar el servidor de desarrollo de Vite:
```powershell
cd PaginaSemaforos/PaginaSemaforos
npm run dev
```
Ten en cuenta que el proxy Python también usa el puerto 8080 por defecto; detén el servidor de Vite antes de iniciar el proxy o utiliza `--port` para cambiar el puerto público del proxy.

---

## 7. Solución de problemas
- **`python3` no es reconocido**: En Windows usa `python` o `py`.
- **Timeout al abrir la página**: verifica el firewall de Windows o utiliza `--bind 0.0.0.0` para escuchar en todas las interfaces.
- **`npm` no está instalado**: instala Node.js (versión 18 o superior recomendada).

Con estos pasos deberías poder levantar toda la solución y controlar el semáforo físico desde la web.
