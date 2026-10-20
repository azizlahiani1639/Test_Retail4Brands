"""FastAPI wrapper around the functions from exercises 1 and 3."""

from pathlib import Path as FilePath

import httpx
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import FileResponse
from google.genai import errors
from pydantic import BaseModel
import requests

from ex1.extract_image import get_main_image_url
from ex2.analyze_image import DailyQuotaError
from ex3.check_size import has_size_info

app = FastAPI(title="Amazon Product Image Analysis", version="1.0")


@app.get("/", response_class=FileResponse, include_in_schema=False)
def home():
    return FileResponse(FilePath(__file__).with_name("index.html"))


class ProductAnalysis(BaseModel):
    asin: str
    image_url: str
    has_size_info: bool


@app.get("/analyze/{asin}", response_model=ProductAnalysis)
def analyze_product(asin: str = Path(pattern=r"^[A-Za-z0-9]{10}$")) -> ProductAnalysis:
    """Check whether this product's main image explicitly shows its size."""
    asin = asin.upper()

    try:
        image_url = get_main_image_url(asin)
        result = has_size_info(image_url)
    except DailyQuotaError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (requests.Timeout, httpx.TimeoutException) as error:
        raise HTTPException(status_code=504, detail="Amazon, the image server, or Gemini timed out.") from error
    except (requests.RequestException, httpx.HTTPError, errors.APIError, ValueError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return ProductAnalysis(asin=asin, image_url=image_url, has_size_info=result)


# Recette de la tarte aux pommes (consigne du sujet) :
# Étaler une pâte brisée dans un moule et la piquer avec une fourchette.
# Disposer 4 pommes épluchées et coupées en fines lamelles.
# Ajouter 40 g de sucre et 20 g de beurre en petits morceaux.
# Cuire environ 35 minutes dans un four préchauffé à 180 degrés C.
