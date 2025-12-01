# auth/deps.py
from fastapi import Cookie, HTTPException, status, Depends
from auth.auth import get_user_by_username, User

def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (cookie missing)"
        )

    user = get_user_by_username(access_token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user"
        )

    return user

def role_usuario(user: User = Depends(get_current_user)):
    if user.role != "usuario":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo usuarios pueden enviar datos."
        )
    return user

def role_autoridad(user: User = Depends(get_current_user)):
    if user.role != "autoridad":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo autoridades pueden validar."
        )
    return user
