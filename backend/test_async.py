import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    db_url = "postgresql+asyncpg://postgres:Sathwik7619@localhost:5432/HvaApp"
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            print("Successfully connected via asyncpg!")
    except Exception as e:
        print("Failed to connect:", e)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test())
