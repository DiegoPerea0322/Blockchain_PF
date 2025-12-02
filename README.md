# Blockchain_PF
Proyecto Final de Blockchain

Este proyecto implementa una cadena de bloques sencilla para registrar etapas dentro de una cadena de suministro, con validación multi-autoridad y firma distribuida entre validadores.

1. Activación del entorno virtual

Desde el directorio raíz del proyecto (Blockchain/), activa el entorno virtual:

Windows (PowerShell/CMD):
.\Scripts\activate

Si la activación fue exitosa deberías ver algo así al inicio de tu línea:

(venv) usuario@pc:~/Blockchain$

2. Instalación de dependencias con requirements.txt

Una vez activado el entorno virtual, instala todas las dependencias necesarias ejecutando:

pip install -r requirements.txt

Esto garantiza que tu entorno tendrá exactamente las mismas librerías requeridas para ejecutar el proyecto.

3. Activación del servidor FastAPI

Para iniciar el backend de FastAPI ejecuta:

uvicorn main:app --reload

El servidor se iniciará en:

http://127.0.0.1:8000

4. Las credenciales para probar funcionalidad son:
   "alice": User(username="alice", password="alicepw", role="usuario"),
    "maria": User(username="maria", password="mariapw", role="usuario"),
    "validator_1": User(username="validator_1", password="valpw", role="autoridad"),
    "validator_2": User(username="validator_2", password="valpw", role="autoridad"),
    "validator_3": User(username="validator_3", password="valpw", role="autoridad"),
    "validator_4": User(username="validator_4", password="valpw", role="autoridad"),
    "validator_5": User(username="validator_5", password="valpw", role="autoridad")

5. Para probar se debe: iniciar sesion con alice o maria, llenar el formulario, el cual envia solicitud de verificacion.
6. Iniciar sesión con cualquier validador y ver que el bloque aparece, para firmar se da click en el boton validar.
7. Una vez firmen 4 autoridades o validadores, el bloque se añade a la blockchain y puede ser visto por la autoridad en el boton de Ver Blockchain
