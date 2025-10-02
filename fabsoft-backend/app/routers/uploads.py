from fastapi import APIRouter, UploadFile, File, HTTPException
import boto3
from botocore.exceptions import NoCredentialsError
import uuid
from ..config import settings

router = APIRouter(
    prefix="/upload",
    tags=["Uploads"]
)

# Configurar o cliente S3 para o Cloudflare R2
s3_client = boto3.client(
    's3',
    endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    region_name='auto'
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
        # Faz o upload do ficheiro para o bucket do R2
        s3_client.upload_fileobj(
            file.file,
            settings.R2_BUCKET_NAME,
            unique_filename,
            ExtraArgs={
                'ContentType': file.content_type
            }
        )
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Credenciais do serviço de armazenamento não encontradas.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload do ficheiro: {str(e)}")
    finally:
        file.file.close()

    # Retorna a URL pública completa do ficheiro
    public_url = f"{settings.R2_PUBLIC_URL}/{unique_filename}"
    
    return {"file_url": public_url}