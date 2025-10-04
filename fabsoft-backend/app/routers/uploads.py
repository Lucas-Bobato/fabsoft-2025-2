from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
from vercel_blob import put
from ..config import settings

router = APIRouter(
    prefix="/upload",
    tags=["Uploads"]
)

@router.post("/profile-picture")
async def upload_profile_picture(file: UploadFile = File(...)):
    """
    Upload de foto de perfil para o Vercel Blob Storage.
    
    Args:
        file: Arquivo de imagem (JPEG ou PNG)
    
    Returns:
        dict: URL pública da imagem no Vercel Blob
    """
    # Valida o tipo de arquivo
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail="Tipo de arquivo inválido. Apenas PNG ou JPEG são permitidos."
        )
    
    # Valida tamanho do arquivo (máximo 5MB)
    file.file.seek(0, 2)  # Move para o final do arquivo
    file_size = file.file.tell()  # Pega o tamanho
    file.file.seek(0)  # Volta para o início
    
    max_size = 5 * 1024 * 1024  # 5MB
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Tamanho máximo: 5MB. Tamanho enviado: {file_size / (1024 * 1024):.2f}MB"
        )
    
    try:
        # Gera um nome de arquivo único
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"profiles/{uuid.uuid4()}.{file_extension}"
        
        # Lê o conteúdo do arquivo
        file_content = await file.read()
        
                # Faz upload para o Vercel Blob
        blob_response = put(
            path=unique_filename,
            data=file_content,
            options={
                'access': 'public',
                'token': settings.BLOB_READ_WRITE_TOKEN,
                'addRandomSuffix': False
            }
        )
        
        # Retorna a URL pública
        return {
            "file_url": blob_response['url'],
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