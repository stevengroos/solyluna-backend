from fastapi import APIRouter

router = APIRouter()

# Una lista de productos de prueba para demostrar el diseño
PRODUCTS_DATA = [
    {
        "id": 1,
        "category": "Informática",
        "title": "Notebook ASUS Vivobook 15",
        "description": "X1504UA-BQ598W 15.6\" FHD Intel Core i7 16GB 512GB SSD",
        "price": 3860000.0,
        "image_url": "https://fpjuanavqjfpcmjmapjp.supabase.co/storage/v1/object/public/productos-imagenes/test_asus.png"
    },
    {
        "id": 2,
        "category": "Informática",
        "title": "Notebook Lenovo IdeaPad Slim 5i",
        "description": "16IRH8 16\" WUXGA Intel Core i7 16GB 1TB SSD",
        "price": 6900000.0,
        "image_url": "https://fpjuanavqjfpcmjmapjp.supabase.co/storage/v1/object/public/productos-imagenes/test_lenovo.png"
    },
    {
        "id": 3,
        "category": "Informática",
        "title": "Notebook HP 15-dy2089la",
        "description": "15.6\" HD Intel Core i5 8GB 256GB SSD",
        "price": 3390000.0,
        "image_url": "https://fpjuanavqjfpcmjmapjp.supabase.co/storage/v1/object/public/productos-imagenes/test_hp.png"
    },
    {
        "id": 4,
        "category": "Electrónica",
        "title": "Smart TV Samsung 65\" 4K",
        "description": "AU7000 UHD HDR",
        "price": 4500000.0,
        "image_url": "https://fpjuanavqjfpcmjmapjp.supabase.co/storage/v1/object/public/productos-imagenes/test_tv_samsung.png"
    },
    {
        "id": 5,
        "category": "Electrónica",
        "title": "Audífonos Sony WH-1000XM4",
        "description": "Cancelación de ruido inalámbrica",
        "price": 1800000.0,
        "image_url": "https://fpjuanavqjfpcmjmapjp.supabase.co/storage/v1/object/public/productos-imagenes/test_sony.png"
    },
    {
        "id": 6,
        "category": "Muebles",
        "title": "Escritorio Gamer Pro",
        "description": "140x60cm con soporte para audífonos y vaso",
        "price": 850000.0,
        "image_url": "https://fpjuanavqjfpcmjmapjp.supabase.co/storage/v1/object/public/productos-imagenes/test_escritorio.png"
    }
]

@router.get("/api/products")
def get_products():
    return PRODUCTS_DATA

@router.get("/api/categories")
def get_categories():
    return ["Informática", "Electrónica", "Muebles"]