from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
import os
from pathlib import Path

router = APIRouter(
    prefix="/upload",
    tags=["Uploads"]
)

# Diretório para armazenar os uploads
UPLOAD_DIR = Path("uploads/profiles")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/profile-picture")
async def upload_profile_picture(file: UploadFile = File(...)):
    """
    Upload de foto de perfil para armazenamento local.
    
    Args:
        file: Arquivo de imagem (JPEG ou PNG)
    
    Returns:
        dict: URL pública da imagem
    """
    # Valida o tipo de arquivo
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail="Tipo de arquivo inválido. Apenas PNG ou JPEG são permitidos."
        )
    
    # Valida tamanho do arquivo (máximo 10MB)
    file.file.seek(0, 2)  # Move para o final do arquivo
    file_size = file.file.tell()  # Pega o tamanho
    file.file.seek(0)  # Volta para o início
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Tamanho máximo: 10MB. Tamanho enviado: {file_size / (1024 * 1024):.2f}MB"
        )
    
    try:
        # Gera um nome de arquivo único
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Salva o arquivo localmente
        file_content = await file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Retorna a URL relativa para acessar o arquivo
        file_url = f"/uploads/profiles/{unique_filename}"
        
        return {
            "file_url": file_url,
            "filename": unique_filename,
            "size": file_size
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fazer upload da imagem: {str(e)}"
        )
    finally:
        await file.close()