# block_ops.py
from fastapi import HTTPException
from blockchain import Transaction, Block, sign_message, verify_signature, select_leader, get_current_timestamp
from state import (
    chain,
    validators,
    pending_blocks,
    pending_id_counter,
    q
)

def propose_block_from_tx(tx: Transaction):
    """Crea una propuesta de bloque a partir de una transacción."""
    global pending_id_counter

    index = len(chain.chain)
    prev_hash = chain.last_hash()
    leader_node = select_leader(validators, index)

    # Creamos el bloque con Timestamp legible
    block = Block(
        index=index,
        previous_hash=prev_hash,
        timestamp=get_current_timestamp(),
        leader=leader_node.id,
        stage_name=tx.payload.get("stage", "Etapa General"),
        transactions=[tx.to_dict()],
        # Si la tx ya trae un responsable firmado, lo subimos al nivel de bloque
        responsible_id=tx.responsible_id 
    )
    
    # Calculamos el hash (esto llama al header_dict corregido)
    block.compute_hash()

    # Preparamos el objeto para la lista de pendientes
    pb = {
        "id": pending_id_counter,
        "block": block,
        "approvals": {}  # validator_id -> firma hex
    }
    
    # El líder (si es honesto) firma su propia propuesta automáticamente
    # Nota: En una red real esto es distinto, pero para simulación ayuda.
    leader_sig = sign_message(leader_node.signing_key, block.block_hash)
    pb["approvals"][leader_node.id] = leader_sig
    
    pending_id_counter += 1
    pending_blocks.append(pb)

    print(f"[BLOCKCHAIN] Propuesta #{pending_id_counter-1} creada por {leader_node.id}. Hash: {block.block_hash[:10]}...")
    return pb

def mark_pending_block_failed(pending_id: int):
    """
    Marca un bloque pendiente como REJECTED.
    CAMBIO IMPORTANTE: Ahora SÍ lo agrega a la cadena para que quede constancia.
    """
    pb = next((p for p in pending_blocks if p["id"] == pending_id), None)
    if pb is None:
        raise HTTPException(status_code=404, detail="Bloque no encontrado")

    block = pb["block"]

    # Recalcular firmas válidas que tenía hasta el momento
    valid_signatures = {}
    for vid, s in pb["approvals"].items():
        vk = next((v.verify_key for v in validators if v.id == vid), None)
        if vk and verify_signature(vk, block.block_hash, s):
            valid_signatures[vid] = s

    collected = len(valid_signatures)
    
    # Actualizamos el bloque
    block.signatures = valid_signatures
    block.certificate = {
        "status": "REJECTED",
        "q_required": q,
        "q_collected": collected,
        "reason": "Rechazado manualmente (Demo Fallo Consenso)"
    }

    # 1. IMPORTANTE: Agregamos el bloque "fallido" a la cadena principal
    # para que aparezca en el historial /chain
    chain.add_block(block)

    # 2. Lo sacamos de la lista de pendientes
    pending_blocks.remove(pb)

    return {
        "status": "rejected",
        "message": f"Bloque #{block.index} marcado como REJECTED ({collected}/{q} firmas) y archivado."
    }


def list_pending_blocks():
    """Retorna lista limpia para el HTML."""
    result = []
    for pb in pending_blocks:
        block = pb["block"]
        result.append({
            "id": pb["id"],
            "index": block.index,
            "stage_name": block.stage_name,
            "timestamp": block.timestamp,  # Ahora se verá bonito en la web
            "proposed_by": block.leader,
            "responsible": block.responsible_id,
            "approvals": list(pb["approvals"].keys()),
            "approvals_count": len(pb["approvals"]),
            "quorum_needed": q
        })
    return result


def sign_pending_block(pending_id: int, validator_id: str):
    """Un validador firma un bloque pendiente."""

    # 1. Buscar el bloque pendiente
    pb = next((p for p in pending_blocks if p["id"] == pending_id), None)
    if pb is None:
        raise HTTPException(status_code=404, detail="Bloque no encontrado")

    block = pb["block"]

    # 2. Buscar al nodo validador
    v_node = next((v for v in validators if v.id == validator_id), None)
    if v_node is None:
        raise HTTPException(status_code=400, detail="Validador no encontrado en la red")

    # 3. Evitar doble firma
    if validator_id in pb["approvals"]:
        raise HTTPException(status_code=400, detail="Ya has firmado este bloque")

    # 4. Firmar el hash del bloque
    sig = sign_message(v_node.signing_key, block.block_hash)
    pb["approvals"][validator_id] = sig

    # 5. Verificar firmas acumuladas (por seguridad)
    valid_signatures = {}
    for vid, s in pb["approvals"].items():
        vk = next((v.verify_key for v in validators if v.id == vid), None)
        if vk and verify_signature(vk, block.block_hash, s):
            valid_signatures[vid] = s

    # 6. Chequear Quórum
    collected = len(valid_signatures)
    
    # Actualizamos el estado interno del bloque con las firmas actuales
    block.signatures = valid_signatures
    block.certificate = {
        "status": "PENDING",
        "q_required": q,
        "q_collected": collected
    }

    if collected >= q:
        # ¡CONSENSO ALCANZADO!
        print(f"✔ QUÓRUM ALCANZADO ({collected}/{q}). Sellando bloque #{block.index}.")
        
        block.certificate["status"] = "ACCEPTED"
        block.certificate["consensus_timestamp"] = get_current_timestamp()
        
        chain.add_block(block)
        pending_blocks.remove(pb)
        
        return {
            "status": "accepted",
            "message": f"Bloque #{block.index} agregado a la cadena.",
            "final_hash": block.block_hash
        }

    return {
        "status": "waiting",
        "message": f"Firma registrada. Faltan {q - collected} firmas.",
        "progress": f"{collected}/{q}"
    }

def chain_as_dict():
    """Serializa toda la cadena para verla en /chain"""
    # Usamos header_dict + los campos extra que no están en el header
    out = []
    for b in chain.chain:
        data = b.header_dict()
        # Agregamos manualmente lo que header_dict excluye por seguridad
        data["hash"] = b.block_hash
        data["signatures"] = b.signatures
        data["certificate"] = b.certificate
        out.append(data)
    return out
    
# block_ops.py

# ... (imports y otras funciones siguen igual) ...

def mark_pending_block_failed(pending_id: int):
    """
    Marca un bloque pendiente como REJECTED si no alcanzó el quórum q.
    """
    pb = next((p for p in pending_blocks if p["id"] == pending_id), None)
    if pb is None:
        raise HTTPException(status_code=404, detail="Bloque no encontrado")

    block = pb["block"]

    # Recalcular firmas válidas
    valid_signatures = {}
    for vid, s in pb["approvals"].items():
        vk = next((v.verify_key for v in validators if v.id == vid), None)
        if vk and verify_signature(vk, block.block_hash, s):
            valid_signatures[vid] = s

    collected = len(valid_signatures)
    block.signatures = valid_signatures
    block.certificate = {
        "status": "REJECTED",
        "q_required": q,
        "q_collected": collected,
        "reason": "Rechazo forzado (Demo)"
    }

    # --- AQUÍ ESTABA EL ERROR ---
    # Faltaba esta línea para guardar el bloque rechazado en el historial:
    chain.add_block(block) 
    # ----------------------------

    # Lo sacamos de la lista de pendientes
    pending_blocks.remove(pb)

    return {
        "status": "rejected",
        "message": f"Bloque #{block.index} marcado como REJECTED ({collected}/{q} firmas)."
    }
