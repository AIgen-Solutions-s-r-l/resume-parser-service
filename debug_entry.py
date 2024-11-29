import nest_asyncio
import uvicorn
from app.main import app  # Adjust the import path as necessary

# Apply the nest_asyncio patch
nest_asyncio.apply()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)