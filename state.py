# state.py
from typing import List, Dict, Any
from blockchain import setup_network, SimpleBlockchain, threshold_q
import time

# Pending proposals shared across the whole app
pending_blocks: List[Dict[str, Any]] = []

# Initialize validator nodes
validators, others = setup_network(k_validators=5, extra_nodes=3)

# Threshold q = floor(2k/3) + 1
q = threshold_q(len(validators))

# Blockchain singleton
chain = SimpleBlockchain(validators, q)
chain.genesis()

# Global counter for pending block IDs
pending_id_counter = 1
