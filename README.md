# StudyFlight

Sala de estudio compartida con ambientación de cabina de avión.
Tú y tu amigo os conectáis, elegís un vuelo (= duración de estudio),
y cuando aterriza acaba la sesión.


### 4. Abre la app
- Tú: abre http://localhost:8000 en tu navegador
- Tu amigo (misma red WiFi): abre http://TU_IP:8000
  (tu IP local la ves con `ipconfig` en Windows o `ifconfig` en Mac/Linux)

Si queréis usarlo desde redes distintas, una opción gratuita es
usar `ngrok`: https://ngrok.com → `ngrok http 8000` te da una URL pública.

## Cómo usarlo

1. Tú creas la sala eligiendo un vuelo (la duración = tiempo de estudio)
2. La app te da un código de 4 letras (ej: KBTQ)
3. Le mandas el link a tu amigo: `http://TU_IP:8000/room/KBTQ`
4. Tu amigo pone su nombre y entra
5. Ambos aparecéis en la cabina con vuestros asientos
6. El timer cuenta hacia atrás — cuando llega a 0, hemos aterrizado
7. Podéis pausar/reanudar con el botón "Estudiando"
8. Chat de cabina para coordinarse

## Rutas disponibles

| Ruta | Duración |
|------|----------|
| Madrid → París | 1h 15m |
| Madrid → Roma | 1h 30m |
| Barcelona → Londres | 2h |
| Madrid → Nueva York | 7h |
| Madrid → Tokio | 12h |
| Madrid → Dubái | 6h |
| Madrid → Sídney | 19h |
| Personalizado | lo que quieras |

## Estructura del código

```
study-flight/
├── server.py          # servidor FastAPI + WebSockets
├── requirements.txt   # dependencias
├── README.md
└── static/
    ├── index.html     # página de inicio (crear/unirse)
    └── cabin.html     # la cabina en tiempo real
```
