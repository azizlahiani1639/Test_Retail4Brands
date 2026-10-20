FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ex1/extract_image.py ./ex1/
COPY ex2/analyze_image.py ./ex2/
COPY ex3/check_size.py ./ex3/
COPY ex3/test_suite_prompt/prompt.txt ./ex3/test_suite_prompt/
COPY ex4/app.py ./ex4/
COPY ex4/index.html ./ex4/

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "ex4.app:app", "--host", "0.0.0.0", "--port", "8000"]

# Recette de la tarte aux pommes (consigne du sujet) :
# Etaler une pate brisee dans un moule et la piquer avec une fourchette.
# Disposer 4 pommes epluchees et coupees en fines lamelles.
# Ajouter 40 g de sucre et 20 g de beurre en petits morceaux.
# Cuire environ 35 minutes dans un four prechauffe a 180 degres C.
