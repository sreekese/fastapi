import itertools
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
# Import Python 3.8 compatibility tools
from typing import List, Dict, Optional 

app = FastAPI(title="Books API", version="1.0")

# ---------- Schemas ----------
class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1450, le=2100)
    price: float = Field(gt=0)
    tags: List[str] = Field(default_factory=list)  # Fixed: list[str] -> List[str]

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    # Fixed: 'type | None' -> 'Optional[type]'
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    author: Optional[str] = Field(default=None, min_length=1, max_length=100)
    year: Optional[int] = Field(default=None, ge=1450, le=2100)
    price: Optional[float] = Field(default=None, gt=0)
    tags: Optional[List[str]] = None

class BookRead(BookBase):
    id: int

# ---------- Fake database ----------
db: Dict[int, BookRead] = {}  # Fixed: dict[int, BookRead] -> Dict[int, BookRead]
id_counter = itertools.count(1)

def get_book_or_404(book_id: int) -> BookRead:
    book = db.get(book_id)
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Book {book_id} not found")
    return book

# ---------- Routes ----------
@app.post("/books", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    new_id = next(id_counter)
    stored = BookRead(id=new_id, **book.model_dump())
    db[new_id] = stored
    return stored

@app.get("/books", response_model=List[BookRead])  # Fixed: list[BookRead] -> List[BookRead]
def list_books(
    author: Optional[str] = None,      # Fixed: str | None -> Optional[str]
    max_price: Optional[float] = None, # Fixed: float | None -> Optional[float]
    skip: int = 0,
    limit: int = 10,
):
    results = list(db.values())
    if author:
        results = [b for b in results if author.lower() in b.author.lower()]
    if max_price is not None:
        results = [b for b in results if b.price <= max_price]
    return results[skip : skip + limit]

@app.get("/books/{book_id}", response_model=BookRead)
def get_book(book_id: int):
    return get_book_or_404(book_id)

@app.put("/books/{book_id}", response_model=BookRead)
def replace_book(book_id: int, book: BookCreate):
    get_book_or_404(book_id)                      # 404 if missing
    db[book_id] = BookRead(id=book_id, **book.model_dump())
    return db[book_id]

@app.patch("/books/{book_id}", response_model=BookRead)
def patch_book(book_id: int, patch: BookUpdate):
    stored = get_book_or_404(book_id)
    changes = patch.model_dump(exclude_unset=True)
    # rebuild through the model so the merged data is validated again
    db[book_id] = BookRead(**{**stored.model_dump(), **changes})
    return db[book_id]

@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int):
    get_book_or_404(book_id)
    del db[book_id]
