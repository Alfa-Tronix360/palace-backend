from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from app.models.models import Company

DOMAIN_MAP = {
    "palace-frontend.vercel.app": "palace",
    "noa-frontend-xamv.vercel.app": "noa",
    "localhost:5173": "palace",
    "127.0.0.1:5173": "palace",
}

def get_company_from_request(request: Request, db: Session) -> Company:
    origin = request.headers.get("origin", "") or request.headers.get("referer", "")
    
    slug = "palace"  # default
    for domain, company_slug in DOMAIN_MAP.items():
        if domain in origin:
            slug = company_slug
            break
    
    company = db.query(Company).filter(Company.slug == slug).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Empresa '{slug}' nao encontrada")
    
    return company


def get_company_id(request: Request, db: Session) -> int:
    company = get_company_from_request(request, db)
    return company.id