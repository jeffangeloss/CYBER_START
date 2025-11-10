const Defacement = () => {
  const timestamp = new Date().toISOString();

  return (
    <div className="min-h-screen bg-black text-red-500 flex flex-col items-center justify-center p-6 overflow-hidden relative">
      {/* Animated background effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-red-900/30 via-black to-green-900/30 animate-pulse"></div>

      {/* Glitch effect overlay */}
      <div className="absolute inset-0 opacity-10 bg-[repeating-linear-gradient(0deg,transparent,transparent_2px,#ff0000_2px,#ff0000_4px)]"></div>

      <div className="relative z-10 text-center space-y-8 max-w-5xl">
        <div className="text-8xl animate-bounce mb-8">⚠️</div>

        <h1 className="text-5xl md:text-7xl font-black uppercase tracking-[0.4em] animate-pulse drop-shadow-[0_0_25px_rgba(255,0,0,0.8)]">
          SISTEMA INTERVENIDO
        </h1>

        <div className="border-t-4 border-b-4 border-red-500 py-6 my-8 uppercase font-mono text-lg md:text-2xl">
          Operación "Gab0tados" completada — Raspberry Pi #12 comprometida
        </div>

        <div className="bg-red-950/60 border-2 border-red-500 p-6 rounded-lg backdrop-blur-sm text-left font-mono text-sm md:text-base space-y-3">
          <p className="text-white font-semibold text-center">
            ⚠️ Evidencia del ataque coordinado desde Kali Linux hacia el laboratorio IoT ⚠️
          </p>
          <p className="text-gray-300">
            1. Se verificó conectividad física realizando <code>ping</code> entre la Kali virtual y la Raspberry Pi rotulada con el número <strong>12</strong>.
          </p>
          <p className="text-gray-300">
            2. Reconocimiento activo: <code>fping -g 192.168.51.1 192.168.51.254</code> para detectar hosts vivos en la subred universitaria.
          </p>
          <p className="text-gray-300">
            3. Escaneo dirigido según hallazgos OSINT del "Archivo 1": <code>nmap 192.168.51.220-254</code> — identificada la Raspberry por su MAC "Raspberry Pi Trading".
          </p>
          <p className="text-gray-300">
            4. Servicios expuestos: <strong>SSH</strong> y <strong>blackice-icecap</strong>. Vulnerabilidad crítica: credenciales por defecto (<code>pi</code>/<code>raspberry</code>).
          </p>
          <p className="text-gray-300">
            5. Acceso obtenido vía SSH. Sitio IoT encontrado en <code>http://192.168.51.232:8081</code> controlando el semáforo ESP32.
          </p>
          <p className="text-red-400 text-center font-semibold">
            Dumpster diving + contraseñas por defecto = toma total del ecosistema semafórico.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-4 mt-8 text-left font-mono text-xs md:text-sm">
          <div className="bg-black/80 border border-red-500/60 p-4 rounded">
            <p className="text-green-400 mb-2">{'>'} LOG DE RECONOCIMIENTO</p>
            <p className="text-gray-300">[+] fping reveló 192.168.51.232 vivo</p>
            <p className="text-gray-300">[+] nmap detectó SSH abierto (22/tcp)</p>
            <p className="text-gray-300">[+] Servicio web escondido en 8081/tcp</p>
            <p className="text-gray-300">[!] MAC: Raspberry Pi Trading Ltd.</p>
          </div>

          <div className="bg-black/80 border border-red-500/60 p-4 rounded">
            <p className="text-green-400 mb-2">{'>'} LECCIONES PARA LA DEFENSA</p>
            <p className="text-gray-300">- Cambia credenciales predeterminadas</p>
            <p className="text-gray-300">- Protege documentación sensible</p>
            <p className="text-gray-300">- Segmenta los IoT críticos</p>
            <p className="text-gray-300">- Monitorea escaneos de red</p>
          </div>
        </div>

        <div className="bg-black border-2 border-green-500 p-4 rounded-lg text-left font-mono text-xs md:text-sm overflow-hidden">
          <p className="text-green-400">root@kali:~# nmap -sV 192.168.51.220-254</p>
          <p className="text-gray-400">Starting Nmap 7.94 ( https://nmap.org ) at 2025-11-09 10:30 UTC</p>
          <p className="text-green-400">PORT     STATE SERVICE     VERSION</p>
          <p className="text-gray-300">22/tcp   open  ssh         OpenSSH 8.4p1 Debian 5 (protocol 2.0)</p>
          <p className="text-gray-300">8081/tcp open  blackice-icecap</p>
          <p className="text-red-400 animate-pulse">⚠️ SSH vulnerable a credenciales por defecto ⚠️</p>
        </div>

        <div className="text-yellow-400 text-lg font-semibold mt-8 animate-pulse">
          🔒 Semáforo IoT intervenido — acceso restablecido sólo mediante respuesta forense 🔒
        </div>

        <div className="text-gray-500 text-xs mt-8 font-mono">
          TIMESTAMP: {timestamp} | HOST KALI: 192.168.51.10 | OBJETIVO: 192.168.51.232
        </div>
      </div>

      {/* Matrix-like falling effect */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute top-0 left-0 text-green-500 font-mono text-xs animate-pulse">
          {Array.from({ length: 50 }, (_, i) => (
            <div
              key={i}
              style={{
                position: "absolute",
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 5}s`,
                animation: "fall 5s linear infinite",
              }}
            >
              {Math.random() > 0.5 ? "1" : "0"}
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes fall {
          0% { top: -20px; }
          100% { top: 100vh; }
        }
      `}</style>
    </div>
  );
};

export default Defacement;
