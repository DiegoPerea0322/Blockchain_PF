# block_ops.py
from fastapi import HTTPException
from blockchain import Transaction, Block, sign_message, verify_signature, select_leader
from state import (
    chain,
    validators,
    pending_blocks,
    pending_id_counter,
    q
)

import time


def propose_block_from_tx(tx: Transaction):
    """Create a block proposal from a submitted transaction."""
    global pending_id_counter

    index = len(chain.chain)
    prev_hash = chain.last_hash()
    leader = select_leader(validators, index)

    block = Block(
        index=index,
        previous_hash=prev_hash,
        timestamp=time.time(),
        leader=leader.id,
        stage_name=tx.payload.get("stage", "Stage"),
        transactions=[tx.to_dict()]
    )
    block.compute_hash()

    pb = {
        "id": pending_id_counter,
        "block": block,
        "approvals": {}  # validator_id -> signature hex
    }
    pending_id_counter += 1

    pending_blocks.append(pb)

    print(f"[DEBUG] Nuevo pendiente agregado. pending_blocks id={id(pending_blocks)} len={len(pending_blocks)}")

    return pb


def list_pending_blocks():
    """Return a clean list of pending blocks for UI."""
    result = []
    for pb in pending_blocks:
        block = pb["block"]
        result.append({
            "id": pb["id"],
            "index": block.index,
            "stage_name": block.stage_name,
            "proposed_by": block.leader,
            "approvals": list(pb["approvals"].keys()),
            "approvals_count": len(pb["approvals"])
        })
    return result


def sign_pending_block(pending_id: int, validator_id: str):
    """Sign a pending block and check quorum."""

    # 1. Buscar el pending block
    pb = next((p for p in pending_blocks if p["id"] == pending_id), None)
    if pb is None:
        raise HTTPException(status_code=404, detail="Pending block not found")

    block = pb["block"]

    # ⚠️ VERY IMPORTANT:
    # Si por alguna razón el block aún no tiene hash, lo calculamos.
    if not block.block_hash:
        block.compute_hash()

    # 2. Verificar que el validador exista
    v_node = next((v for v in validators if v.id == validator_id), None)
    if v_node is None:
        raise HTTPException(status_code=400, detail="Validator not found")

    # 3. Evitar doble firma
    if validator_id in pb["approvals"]:
        raise HTTPException(status_code=400, detail="Validator already signed")

    # 4. Firmar correctamente
    sig = sign_message(v_node.signing_key, block.block_hash)
    pb["approvals"][validator_id] = sig

    # 5. Verificar todas las firmas acumuladas
    valid = {}
    for vid, s in pb["approvals"].items():
        vk = next((v.verify_key for v in validators if v.id == vid), None)
        if vk and verify_signature(vk, block.block_hash, s):
            valid[vid] = s

    # Guardar estado real del bloque
    block.signatures = valid
    block.certificate = {
        "q_required": q,
        "q_collected": len(valid),
        "validators": len(validators)
    }

    # 6. Verificar quorum
    accepted = len(valid) >= q

    if accepted:
        print(f"✔ QUORUM alcanzado: {len(valid)}/{q}")
        chain.add_block(block)
        pending_blocks.remove(pb)
        return {
            "status": "accepted",
            "message": "Block added to chain",
            "index": block.index
        }

    return {
        "status": "waiting",
        "message": f"Signed ({len(valid)}/{q}), waiting for more signatures",
        "index": block.index
    }



def chain_as_dict():
    """Return the whole chain serialized."""
    out = []
    for b in chain.chain:
        out.append({
            "index": b.index,
            "previous_hash": b.previous_hash,
            "timestamp": b.timestamp,
            "leader": b.leader,
            "stage_name": b.stage_name,
            "transactions": b.transactions,
            "nonce": b.nonce,
            "signatures": b.signatures,
            "block_hash": b.block_hash,
            "certificate": b.certificate
        })
    return out
