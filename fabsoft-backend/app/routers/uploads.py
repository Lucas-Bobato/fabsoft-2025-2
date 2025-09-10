from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import uuid
from pathlib import Path

router = APIRouter(
    prefix="/upload",
    tags=["Uploads"]
)

# Define o caminho para salvar as imagens
UPLOAD_DIR = Path("static/images/profiles")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True) # Garante que o diretório exista

@router.post("/profile-picture")
async def upload_profile_picture(file: UploadFile = File(...)):
    # Valida o tipo de arquivo
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Tipo de arquivo inválido. Apenas PNG ou JPEG são permitidos.")

    # Gera um nome de arquivo único para evitar conflitos
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Salva o arquivo no disco
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
        
    # Retorna a URL pública do arquivo
    # O caminho começa com /static/ pois é como vamos configurar o FastAPI para servir os arquivos
    public_url = f"/static/images/profiles/{unique_filename}"
    return {"file_url": public_url}