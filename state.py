# state.py
from typing import List, Dict, Any
from blockchain import setup_network, SimpleBlockchain, threshold_q
import time

# Pending proposals shared across the whole app
pending_blocks: List[Dict[str, Any]] = []

# Initialize validator nodes
# NOTA: En un sistema real de persistencia, las claves de los validadores 
# también deberían cargarse de disco para que sean los "mismos" validadores siempre.
# Por ahora, regeneramos la red, pero mantenemos la historia de la blockchain.
validators, others = setup_network(k_validators=5, extra_nodes=3)

# Threshold q = floor(2k/3) + 1
q = threshold_q(len(validators))

# Blockchain singleton
chain = SimpleBlockchain(validators, q, filename="blockchain_data.json")

# --- LÓGICA DE INICIO ---
# Intentamos cargar la historia previa. Si no existe, creamos el Génesis.
if not chain.load_chain():
    print("[INIT] No se encontró historial. Creando Bloque Génesis.")
    chain.genesis()
else:
    print("[INIT] Historial recuperado correctamente.")

# Global counter for pending block IDs
pending_id_counter = 1
