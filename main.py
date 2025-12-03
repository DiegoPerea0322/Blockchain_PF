# main.py
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
import json  # <--- NUEVO
from fastapi import Response  # <--- CAMBIO: Usaremos Response en vez de JSONResponse
from block_ops import chain_as_dict

from auth.auth import authenticate
from auth.deps import role_usuario, role_autoridad
from blockchain import Transaction
from block_ops import (
    propose_block_from_tx,
    list_pending_blocks,
    sign_pending_block,
    chain_as_dict
)
from state import pending_blocks, chain
from fastapi.encoders import jsonable_encoder

app = FastAPI()
templates = Jinja2Templates(directory="./templates")


@app.get("/")
async def root():
    return RedirectResponse(url="/login")


# ---------- LOGIN ----------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_action(username: str = Form(...), password: str = Form(...)):
    user = authenticate(username, password)

    if not user:
        return RedirectResponse("/login", status_code=303)

    # Redirección según el rol
    if user.role == "usuario":
        redirect_url = "/form"
    elif user.role == "autoridad":
        redirect_url = "/pendientes"
    else:
        redirect_url = "/login"

    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(key="access_token", value=user.username)
    return response


# ---------- SOLO USUARIOS ----------
@app.get("/form", response_class=HTMLResponse)
async def form_page(request: Request, user=Depends(role_usuario)):
    return templates.TemplateResponse("form.html", {"request": request, "user": user})


@app.post("/form")
async def submit_form(
    batch: str = Form(...),
    descripcion: str = Form(...),
    responsable: str = Form(...),
    stage_name: str = Form(...),
    user=Depends(role_usuario)
):
    tx = Transaction(
        sender=user.username,
        actor_type="usuario",
        payload={
            "batch": batch,
            "descripcion": descripcion,
            "stage": stage_name,
            "responsable": responsable,  # 👈 AGREGAR ESTO
        },
        # si tienes más campos, déjalos igual
    )

    pending = propose_block_from_tx(tx)
    print(">> Nuevo bloque propuesto:", pending)

    return RedirectResponse("/form?msg=success", status_code=303)



# ---------- AUTORIDADES: VALIDACIÓN ----------
from block_ops import (
    propose_block_from_tx,
    list_pending_blocks,
    sign_pending_block,
    chain_as_dict
)
# ...

@app.get("/pendientes", response_class=HTMLResponse)
async def revisar_pendientes(request: Request, user=Depends(role_autoridad)):
    pendientes_limpios = list_pending_blocks()
    return templates.TemplateResponse(
        "pendientes.html",
        {
            "request": request,
            "user": user,
            "pendientes": pendientes_limpios
        }
    )



@app.post("/firmar")
async def firmar_bloque(
    
    pending_id: int = Form(...),
    user=Depends(role_autoridad)
):
    """
    Endpoint llamado por el botón 'Firmar' del template pendientes.html.
    user.username debe coincidir con el id del validador (validator_1 ... validator_5).
    """
    validator_id = user.username  # mapeo simple: username == validator_id
    try:
        result = sign_pending_block(pending_id, validator_id)
    except HTTPException as e:
        # si block_ops lanza HTTPException, lo mostramos (puedes mejorar la UI luego)
        print("Error al firmar:", e.detail)
        return RedirectResponse("/pendientes?msg=error", status_code=303)
    except Exception as e:
        print("Error inesperado al firmar:", e)
        return RedirectResponse("/pendientes?msg=error", status_code=303)

    # result es dict con "status" ("accepted" o "waiting") y "message"
    print("Resultado firma:", result)
    return RedirectResponse("/pendientes", status_code=303)


#-------- Mostrar Blockchain ----------#

# ...

from block_ops import (
    propose_block_from_tx,
    list_pending_blocks,
    sign_pending_block,
    chain_as_dict,
)
# ...

@app.get("/chain", response_class=HTMLResponse)
def view_chain(request: Request):
    chain_json = chain_as_dict()  # incluye hash, certificate, etc.
    return templates.TemplateResponse(
        "chain.html",
        {
            "request": request,
            "chain": chain_json,
        }
    )


from block_ops import mark_pending_block_failed
# ...

@app.post("/rechazar")
async def rechazar_bloque(
    pending_id: int = Form(...),
    user=Depends(role_autoridad)
):
    try:
        result = mark_pending_block_failed(pending_id)
        print("Resultado rechazo:", result)
    except HTTPException as e:
        print("Error al rechazar:", e.detail)
        return RedirectResponse("/pendientes?msg=error", status_code=303)
    except Exception as e:
        print("Error inesperado al rechazar:", e)
        return RedirectResponse("/pendientes?msg=error", status_code=303)

    return RedirectResponse("/pendientes", status_code=303)



@app.get("/download_chain")
def download_chain_file():
    """Genera un archivo JSON descargable y BONITO (pretty-printed)"""
    data = chain_as_dict()
    
    # Aquí está el truco: indent=4 hace que se vea estructurado
    pretty_json_str = json.dumps(data, indent=4, default=str)
    
    return Response(
        content=pretty_json_str,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=blockchain_data.json"}
    )
