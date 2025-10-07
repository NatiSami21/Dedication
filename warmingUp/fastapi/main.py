from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from model import Product
from database import SessionLocal, engine
import database_models
from sqlalchemy.orm import Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
)

database_models.Base.metadata.create_all(bind=engine)

@app.get("/")
  
def greet():
    return "Hello, FastAPI!"

products = [
    Product(id=1, name="Laptop", description="A high-performance laptop", price=999.99, quantity=10),
    Product(id=2, name="Smartphone", description="A latest model smartphone", price=699.99, quantity=25),
    Product(id=3, name="Headphones", description="Noise-cancelling headphones", price=199.99, quantity=50),
    Product(id=4, name="Monitor", description="4K UHD Monitor", price=299.99, quantity=15),
    Product(id=5, name="Keyboard", description="Mechanical keyboard", price=89.99, quantity=30),
]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    db = SessionLocal()

    exist_count = db.query(database_models.Product).count()

    if exist_count == 0:
        for product in products:
            db.add(database_models.Product(**product.model_dump()))
        db.commit()
    db.close()

init_db()

@app.get("/products")
def get_all_products (db: Session = Depends(get_db)): #depedecy injection
    fetch_products = db.query(database_models.Product).all()
    return fetch_products

@app.get("/product/{id}")
def get_product(id: int, db: Session = Depends(get_db)): #depedecy injection
    single_product =  db.query(database_models.Product).filter(database_models.Product.id==id).first()
    if  single_product :
        return single_product
    return "Product Not found"

@app.post("/product")
def add_product(product:Product,  db: Session = Depends(get_db)) :
    db.add(database_models.Product(**product.model_dump()))
    db.commit()
    return product

@app.put("/product/{id}")
def update_product(id: int, product:Product, db: Session = Depends(get_db)):
    old_product =  db.query(database_models.Product).filter(database_models.Product.id==id).first()
    if old_product:
        old_product.name = product.name
        old_product.description = product.description
        old_product.price = product.price
        old_product.quantity = product.quantity
        db.commit()
        return "Successfully updated"
    else:
        return "Product Not found"


@app.delete("/product/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    product =  db.query(database_models.Product).filter(database_models.Product.id==id).first()
    if product:
        db.delete(product)
        db.commit()
    else:
        return "Product Not found"