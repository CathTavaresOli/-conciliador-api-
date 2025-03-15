from fastapi import FastAPI, File, UploadFile
import pdfplumber
import pandas as pd
import re
import io

app = FastAPI(
    title="Conciliador Bancário API",
    description="API para processar e conciliar extratos bancários.",
    version="1.0",
    docs_url="/docs",  # Habilita a documentação no Swagger
    redoc_url="/redoc"  # Habilita a documentação no Redoc
)


@app.post("/processar_extrato/")
async def processar_extrato(file: UploadFile = File(...)):
    """
    API que recebe um extrato bancário em PDF, extrai os dados e retorna um Excel estruturado.
    """
    try:
        # Ler o PDF enviado pelo usuário
        pdf_bytes = await file.read()
        pdf_stream = io.BytesIO(pdf_bytes)

        movimentacoes = []
        date_pattern = re.compile(r"\d{2}/\d{2}")

        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = text.split("\n")
                    for line in lines:
                        if date_pattern.match(line[:5]):  # Verifica se a linha começa com data
                            parts = re.split(r'\s{2,}', line.strip())  # Divide pelos espaços múltiplos
                            if len(parts) >= 4:
                                movimentacoes.append(parts[:5])  # Pegamos no máximo 5 colunas

        df_movimentacoes = pd.DataFrame(movimentacoes, columns=["Data", "Descrição", "Nº Documento", "Crédito", "Débito"])

        # Criar arquivo Excel temporário
        output_stream = io.BytesIO()
        df_movimentacoes.to_excel(output_stream, index=False)
        output_stream.seek(0)

        return {
            "message": "Arquivo processado com sucesso!",
            "data": df_movimentacoes.to_dict()
        }
    
    except Exception as e:
        return {"error": str(e)}
