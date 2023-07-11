import tempfile
import httpx
from io import BytesIO
from fastapi import BackgroundTasks, Depends, File, HTTPException, Response, UploadFile, status

from fastapi.routing import APIRouter
from app.api.dependencies.auth import get_auth_token
from app.services.pdf_utils import add_password_and_restrict_printing


router = APIRouter()
client = httpx.AsyncClient()


@router.post(
    "/pdf-encrypt",
    name="utils:pdf-encrypt",
    dependencies=[Depends(get_auth_token)],
)
async def pdf_encrypt(
    background_tasks: BackgroundTasks,
    password: str,
    file: UploadFile = File(...),
):
    if not file or file.content_type not in ["application/pdf"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="file type must be JPG or PNG type.",
        )

    input_file = BytesIO(await file.read())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        add_password_and_restrict_printing(input_file, tmp, password)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as processed_file:
        content = processed_file.read()

    print(tmp_path)
    # os.unlink(tmp_path)  # Remove o arquivo temporário após a leitura
    return Response(content=content, media_type="application/pdf")
