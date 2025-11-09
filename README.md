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

> 💡 El proxy mantiene `/api/*` apuntando al ESP32. Si cambias el puerto con `--port` o `SERVIDOR_PUERTO`, actualiza también cualquier variable de entorno que use la interfaz (por ejemplo `VITE_PROXY_TARGET`).

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
4. Desde la página puedes iniciar/detener el ciclo del semáforo y ver el estado actual. La tarjeta **Configurar API** del panel
   permite indicar otra URL base si sirves la interfaz desde un origen diferente al proxy.

Si recibes un error 502, revisa la conexión del ESP32 y que el puerto 80 esté accesible desde tu PC.

---

## 6. Desarrollo local opcional
Para realizar cambios rápidos en el front-end puedes usar el servidor de desarrollo de Vite:
```powershell
cd PaginaSemaforos/PaginaSemaforos
npm run dev
```
El servidor de desarrollo ahora escucha en `http://localhost:5173` y reenvía automáticamente las rutas `/api/*` hacia `http://127.0.0.1:8080` (el proxy Python). Mantén `servidor_final.py` en ejecución o ajusta el destino con:

```powershell
$env:VITE_PROXY_TARGET = "http://192.168.1.120:80"
npm run dev
```

Si despliegas la web sin el proxy, define `VITE_API_BASE_URL` para apuntar directamente al ESP32:

```powershell
$env:VITE_API_BASE_URL = "http://192.168.1.120/api"
npm run build
```

---

## 7. Solución de problemas
- **`python3` no es reconocido**: En Windows usa `python` o `py`.
- **Timeout al abrir la página**: verifica el firewall de Windows o utiliza `--bind 0.0.0.0` para escuchar en todas las interfaces.
- **`npm` no está instalado**: instala Node.js (versión 18 o superior recomendada).
- **Errores 502 en la web**: revisa que `servidor_final.py` esté apuntando a la IP correcta del ESP32 y que `VITE_PROXY_TARGET`/`VITE_API_BASE_URL` usen ese mismo destino cuando trabajes en desarrollo o despliegues personalizados.

Con estos pasos deberías poder levantar toda la solución y controlar el semáforo físico desde la web.
