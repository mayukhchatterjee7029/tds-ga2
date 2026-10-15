from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
from jwt.exceptions import InvalidTokenError

app = FastAPI()

class TokenRequest(BaseModel):
    token: str

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

EXPECTED_ISS = "https://idp.exam.local"
EXPECTED_AUD = "tds-wbk7ikg9.apps.exam.local"

@app.post("/verify")
def verify_token(request: TokenRequest):
    try:
        # PyJWT automatically verifies:
        # 1. Signature (against PUBLIC_KEY using RS256)
        # 2. Expiry (exp claim is in the future)
        # 3. Issuer (iss matches EXPECTED_ISS)
        # 4. Audience (aud matches EXPECTED_AUD)
        payload = jwt.decode(
            request.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            audience=EXPECTED_AUD,
            issuer=EXPECTED_ISS
        )
        
        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud")
        }
    except InvalidTokenError:
        # Catches ExpiredSignatureError, InvalidAudienceError, 
        # InvalidIssuerError, and InvalidSignatureError
        return JSONResponse(status_code=401, content={"valid": False})
    except Exception:
        # Catch-all for malformed JWTs or missing tokens
        return JSONResponse(status_code=401, content={"valid": False})