from fastapi import APIRouter, UploadFile, File, HTTPException
from vercel_blob import put
import uuid
from ..config import settings
import os

router = APIRouter(
    prefix="/upload",
    tags=["Uploads"]
)

@router.post("/profile-picture")
async def upload_profile_picture(file: UploadFile = File(...)):
    # Valida o tipo de ficheiro
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Tipo de arquivo inválido. Apenas PNG ou JPEG são permitidos.")

    # Gera um nome de ficheiro único para evitar conflitos
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"profiles/{uuid.uuid4()}.{file_extension}"

    try:
        blob = put(
            pathname=unique_filename,
            body=file.file,
            options={'access': 'public'}
        )

        # A variável 'blob' contém um dicionário com o URL, pathname, etc.
        public_url = blob['url']

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload do ficheiro: {str(e)}")
    finally:
        file.file.close()

    # Retorna a URL pública completa do ficheiro
    return {"file_url": public_url}