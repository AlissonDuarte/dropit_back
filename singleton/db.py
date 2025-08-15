from database import SessionLocal, AsyncSessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close

async def get_async_db():
    async with AsyncSessionLocal() as db:
        yield db