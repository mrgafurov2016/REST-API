from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from typing import List, Optional
from pydantic import BaseModel

# Константа для статического API ключа
API_KEY = "STATIC_API_KEY"
api_key_header = APIKeyHeader(name="X-API-Key")

# Создание базы данных SQLite
engine = create_engine("sqlite:///orgs.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Модели SQLAlchemy
class Building(Base):
    __tablename__ = "buildings"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    lat = Column(Float)
    lon = Column(Float)
    organizations = relationship("Organization", back_populates="building")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("activities.id"))
    children = relationship("Activity", backref="parent", remote_side=[id])

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phones = Column(String)  # Сохраняем номера через запятую
    building_id = Column(Integer, ForeignKey("buildings.id"))
    building = relationship("Building", back_populates="organizations")
    activities = relationship("OrganizationActivity", back_populates="organization")

class OrganizationActivity(Base):
    __tablename__ = "organization_activities"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    activity_id = Column(Integer, ForeignKey("activities.id"))
    organization = relationship("Organization", back_populates="activities")
    activity = relationship("Activity")

# Pydantic схемы
class BuildingOut(BaseModel):
    id: int
    address: str
    lat: Optional[float]
    lon: Optional[float]
    class Config: orm_mode = True

class ActivityOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    class Config: orm_mode = True

class OrganizationOut(BaseModel):
    id: int
    name: str
    phones: str
    building: BuildingOut
    activities: List[ActivityOut]
    class Config: orm_mode = True

# Инициализация FastAPI
app = FastAPI(title="Organizations Directory API")

# Зависимость для проверки API ключа
def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD эндпоинты

@app.get("/organizations/by_building/{building_id}", response_model=List[OrganizationOut], dependencies=[Depends(get_api_key)])
def orgs_by_building(building_id: int, db: Session = Depends(get_db)):
    orgs = db.query(Organization).filter(Organization.building_id == building_id).all()
    return orgs

@app.get("/organizations/by_activity/{activity_id}", response_model=List[OrganizationOut], dependencies=[Depends(get_api_key)])
def orgs_by_activity(activity_id: int, db: Session = Depends(get_db)):
    org_ids = db.query(OrganizationActivity.organization_id).filter(OrganizationActivity.activity_id == activity_id).all()
    orgs = db.query(Organization).filter(Organization.id.in_([oid[0] for oid in org_ids])).all()
    return orgs

@app.get("/organizations/by_location", response_model=List[OrganizationOut], dependencies=[Depends(get_api_key)])
def orgs_by_location(lat: float, lon: float, radius: float = Query(..., gt=0), db: Session = Depends(get_db)):
    # Простой радиусный поиск (без геоиндекса)
    buildings = db.query(Building).filter(
        ((Building.lat - lat) ** 2 + (Building.lon - lon) ** 2) ** 0.5 <= radius
    ).all()
    orgs = []
    for b in buildings:
        orgs.extend(b.organizations)
    return orgs

@app.get("/organizations/{org_id}", response_model=OrganizationOut, dependencies=[Depends(get_api_key)])
def get_organization(org_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@app.get("/activities/search", response_model=List[OrganizationOut], dependencies=[Depends(get_api_key)])
def search_by_activity_tree(activity_id: int, db: Session = Depends(get_db)):
    # Находим все дочерние виды деятельности (до 3 уровней)
    def get_descendants(act_id, depth=0):
        if depth > 2: return []
        children = db.query(Activity).filter(Activity.parent_id == act_id).all()
        ids = [act_id]
        for child in children:
            ids.extend(get_descendants(child.id, depth+1))
        return ids
    ids = get_descendants(activity_id)
    org_ids = db.query(OrganizationActivity.organization_id).filter(OrganizationActivity.activity_id.in_(ids)).all()
    orgs = db.query(Organization).filter(Organization.id.in_([oid[0] for oid in org_ids])).all()
    return orgs

@app.get("/organizations/search", response_model=List[OrganizationOut], dependencies=[Depends(get_api_key)])
def orgs_by_name(name: str, db: Session = Depends(get_db)):
    orgs = db.query(Organization).filter(Organization.name.ilike(f"%{name}%")).all()
    return orgs

# Ограничение вложенности деятельности
@app.get("/activities/tree", response_model=List[ActivityOut], dependencies=[Depends(get_api_key)])
def get_activity_tree(max_depth: int = 3, db: Session = Depends(get_db)):
    def collect_tree(parent_id=None, depth=0):
        if depth >= max_depth: return []
        acts = db.query(Activity).filter(Activity.parent_id == parent_id).all()
        result = []
        for act in acts:
            result.append(ActivityOut.from_orm(act))
            result.extend(collect_tree(act.id, depth+1))
        return result
    return collect_tree()

# Создание таблиц
Base.metadata.create_all(bind=engine)