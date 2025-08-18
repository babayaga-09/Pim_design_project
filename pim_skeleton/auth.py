
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()



VALID_USER = "admin"
VALID_PASS = "password"

#basic "session" using a global variable
_logged_in_user: str | None = None

def login(username: str, password: str) -> bool:
    """
    Authenticates the user and sets a simple session.
    """
    global _logged_in_user
    if username == VALID_USER and password == VALID_PASS:
        _logged_in_user = username
        return True
    return False

def logout() -> None:
    """
    Logs the user out by clearing the session.
    """
    global _logged_in_user
    _logged_in_user = None

def require_user() -> str:
    """
    Checks if a user is logged in. Raises an exception if not.
    """
    if _logged_in_user is not None:
        return _logged_in_user
    raise Exception("User not logged in")

def is_user_logged_in() -> bool:
    """
    Returns True if a user is currently logged in.
    """
    return _logged_in_user is not None


#####
#logged in if they present Basic auth with correct credentials on every request.
#def require_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
 #   if credentials.username == VALID_USER and credentials.password == VALID_PASS:
  #      return credentials.username
   # raise HTTPException(status_code=401, detail="Invalid credentials")

