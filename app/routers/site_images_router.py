import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_admin
from app.models.models import SiteImage
from app.schemas.palace_schemas import SiteImageResponse, SiteImageUpdate

router = APIRouter(prefix="/site-images", tags=["Site Images"])

CLOUDINARY_UPLOAD_URL = "https://api.cloudinary.com/v1_1/dkcq4gtxp/image/upload"
CLOUDINARY_UPLOAD_PRESET = "palace_lounge"


def upsert_site_image(db: Session, key: str, image_url: str) -> SiteImage:
    item = db.query(SiteImage).filter(SiteImage.key == key).first()
    if item:
        item.image_url = image_url
    else:
        item = SiteImage(key=key, image_url=image_url)
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[SiteImageResponse])
@router.get("/", response_model=list[SiteImageResponse])
def list_site_images(db: Session = Depends(get_db)):
    return db.query(SiteImage).all()


@router.put("/{key}", response_model=SiteImageResponse)
def set_site_image(
    key: str,
    payload: SiteImageUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    return upsert_site_image(db, key, payload.image_url)


@router.post("/{key}/upload", response_model=SiteImageResponse)
async def upload_site_image(
    key: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin=Depends(get_admin),
):
    contents = await file.read()

    async with httpx.AsyncClient() as client:
        cloud_response = await client.post(
            CLOUDINARY_UPLOAD_URL,
            data={"upload_preset": CLOUDINARY_UPLOAD_PRESET},
            files={"file": (file.filename, contents, file.content_type)},
        )

    if cloud_response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Erro ao enviar imagem para o Cloudinary")

    image_url = cloud_response.json()["secure_url"]
    return upsert_site_image(db, key, image_url)


@router.delete("/{key}")
def reset_site_image(key: str, db: Session = Depends(get_db), _admin=Depends(get_admin)):
    item = db.query(SiteImage).filter(SiteImage.key == key).first()
    if item:
        db.delete(item)
        db.commit()
    return {"message": "Imagem reposta para o padrao"}