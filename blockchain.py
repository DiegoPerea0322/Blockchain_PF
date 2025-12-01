# blockchain.py
import hashlib
import json
import time
import binascii
from dataclasses import dataclass, field
from typing import List, Dict, Any
from nacl.signing import SigningKey, VerifyKey
import pprint

pp = pprint.PrettyPrinter(indent=2).pprint


# ======== DATA CLASSES ========

@dataclass
class Transaction:
    sender: str
    actor_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "sender": self.sender,
            "actor_type": self.actor_type,
            "payload": self.payload,
            "timestamp": self.timestamp
        }


@dataclass
class Block:
    index: int
    previous_hash: str
    timestamp: float
    leader: str
    stage_name: str
    transactions: List[Dict[str, Any]]
    nonce: int = 0
    signatures: Dict[str, str] = field(default_factory=dict)
    block_hash: str = ""
    certificate: Dict[str, Any] = field(default_factory=dict)

    def header_dict(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "leader": self.leader,
            "stage_name": self.stage_name,
            "transactions": self.transactions,
            "hash": self.block_hash,
            "nonce": self.nonce

        }

    def compute_hash(self):
        h = hashlib.sha256(json.dumps(self.header_dict(), sort_keys=True).encode()).hexdigest()
        self.block_hash = h
        return h


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

    for i in range(k_validators):
        sk, vk = make_keypair()
        node = Node(f"validator_{i+1}", True, sk, vk, f"cert-validator-{i+1}")
        validators.append(node)

    for j in range(extra_nodes):
        sk, vk = make_keypair()
        node = Node(f"node_{j+1}", False, sk, vk, f"cert-node-{j+1}")
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


# ======== BLOCKCHAIN CLASS ========

class SimpleBlockchain:
    def __init__(self, validators, q):
        self.chain: List[Block] = []
        self.validators = validators
        self.q = q

    def genesis(self):
        b = Block(
            index=0,
            previous_hash="0" * 64,
            timestamp=time.time(),
            leader="genesis",
            stage_name="Genesis",
            transactions=[]
        )
        b.compute_hash()
        self.chain.append(b)

    def last_hash(self):
        return self.chain[-1].block_hash

    def add_block(self, b: Block):
        self.chain.append(b)

    def is_valid(self):
        for i in range(1, len(self.chain)):
            if self.chain[i].previous_hash != self.chain[i - 1].block_hash:
                return False
        return True
