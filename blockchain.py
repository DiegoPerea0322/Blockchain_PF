# blockchain.py
import hashlib
import json
import binascii
import os  # Necesario para verificar si el archivo existe
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from nacl.signing import SigningKey, VerifyKey

# ======== HELPERS ========

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ======== DATA CLASSES ========

@dataclass
class Transaction:
    sender: str
    actor_type: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=get_current_timestamp)
    responsible_id: str = ""
    responsible_signature: str = ""

    def to_dict(self):
        return {
            "sender": self.sender,
            "actor_type": self.actor_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "responsible_id": self.responsible_id,
            "responsible_signature": self.responsible_signature
        }

@dataclass
class Block:
    index: int
    previous_hash: str
    timestamp: str
    leader: str
    stage_name: str
    transactions: List[Dict[str, Any]]
    responsible_id: str = ""
    signatures: Dict[str, str] = field(default_factory=dict)
    certificate: Dict[str, Any] = field(default_factory=dict)
    block_hash: str = ""

    def header_dict(self):
        """Datos inmutables para el hash."""
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "leader": self.leader,
            "stage_name": self.stage_name,
            "transactions": self.transactions,
            "responsible_id": self.responsible_id
        }

    def compute_hash(self):
        block_string = json.dumps(self.header_dict(), sort_keys=True).encode()
        self.block_hash = hashlib.sha256(block_string).hexdigest()
        return self.block_hash

    # --- NUEVOS MÉTODOS PARA PERSISTENCIA ---
    
    def to_dict(self):
        """Serializa el bloque completo para guardarlo en JSON."""
        data = self.header_dict()
        # Agregamos los campos que no van en el hash pero sí en el archivo
        data["hash"] = self.block_hash
        data["signatures"] = self.signatures
        data["certificate"] = self.certificate
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Reconstruye un objeto Block desde un diccionario cargado del JSON."""
        block = cls(
            index=data["index"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            leader=data["leader"],
            stage_name=data["stage_name"],
            transactions=data["transactions"],
            responsible_id=data.get("responsible_id", "")
        )
        block.block_hash = data.get("hash", "")
        block.signatures = data.get("signatures", {})
        block.certificate = data.get("certificate", {})
        return block


@dataclass
class Node:
    id: str
    is_validator: bool
    signing_key: SigningKey
    verify_key: VerifyKey
    certificate: str = ""

    def public_hex(self):
        return binascii.hexlify(self.verify_key.encode()).decode()


# ======== NETWORK SETUP ========

def make_keypair():
    sk = SigningKey.generate()
    return sk, sk.verify_key

def setup_network(k_validators=5, extra_nodes=3):
    validators = []
    others = []
    # Generamos claves nuevas en cada ejecución. 
    # NOTA: En un sistema real, estas claves también deberían guardarse en disco.
    for i in range(k_validators):
        sk, vk = make_keypair()
        node = Node(f"validator_{i+1}", True, sk, vk, f"Certificado-Val-{i+1}")
        validators.append(node)

    for j in range(extra_nodes):
        sk, vk = make_keypair()
        node = Node(f"node_{j+1}", False, sk, vk, f"Certificado-Nodo-{j+1}")
        others.append(node)

    return validators, others

def select_leader(validators, t):
    return validators[t % len(validators)]

def threshold_q(k):
    import math
    return math.floor(2 * k / 3) + 1

# ======== SIGNATURES ========

def sign_message(sk, msg):
    return binascii.hexlify(sk.sign(msg.encode()).signature).decode()

def verify_signature(vk, msg, sig_hex):
    try:
        vk.verify(msg.encode(), binascii.unhexlify(sig_hex))
        return True
    except Exception:
        return False


# ======== BLOCKCHAIN CLASS CON PERSISTENCIA ========

class SimpleBlockchain:
    def __init__(self, validators, q, filename="blockchain_data.json"):
        self.chain: List[Block] = []
        self.validators = validators
        self.q = q
        self.filename = filename

    def genesis(self):
        b = Block(
            index=0,
            previous_hash="0" * 64,
            timestamp=get_current_timestamp(),
            leader="SISTEMA",
            stage_name="Genesis",
            transactions=[],
            responsible_id="SISTEMA"
        )
        b.compute_hash()
        b.certificate = {"status": "GENESIS", "consensus": True}
        self.chain.append(b)
        self.save_chain() # Guardar el génesis

    def last_hash(self):
        return self.chain[-1].block_hash

    def add_block(self, b: Block):
        self.chain.append(b)
        self.save_chain() # <--- GUARDADO AUTOMÁTICO

    def is_valid(self):
        for i in range(1, len(self.chain)):
            if self.chain[i].previous_hash != self.chain[i - 1].block_hash:
                return False
        return True

    # --- MÉTODOS DE GUARDADO Y CARGA ---

    def save_chain(self):
        """Guarda toda la cadena en un archivo JSON."""
        try:
            data = [b.to_dict() for b in self.chain]
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"[PERSISTENCIA] Cadena guardada en {self.filename} ({len(self.chain)} bloques)")
        except Exception as e:
            print(f"[ERROR] No se pudo guardar la blockchain: {e}")

    def load_chain(self):
        """Intenta cargar la cadena desde el archivo JSON. Retorna True si tuvo éxito."""
        if not os.path.exists(self.filename):
            return False
        
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
            
            if not data:
                return False

            self.chain = [Block.from_dict(b_data) for b_data in data]
            print(f"[PERSISTENCIA] Cadena cargada exitosamente: {len(self.chain)} bloques recuperados.")
            return True
        except Exception as e:
            print(f"[ERROR] Archivo corrupto o ilegible, se iniciará una cadena nueva: {e}")
            return False
