"""Gera CSV inteiramente SINTÉTICO para testar o servidor; NÃO são dados reais."""
from pathlib import Path
import csv

p = Path(__file__).with_name("sinan_tube_SINTETICO.csv")
with p.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE", "NM_PACIENT"])
    w.writeheader()
    for i in range(60):
        w.writerow({"ID_MN_RESI": "221100", "CS_SEXO": "F" if i % 2 else "M",
                    "CS_RACA": "4", "SITUA_ENCE": "2" if i < 24 else "1",
                    "NM_PACIENT": f"PERSONAGEM_FICTICIO_{i}"})
print(f"Gerado exemplo SINTÉTICO em {p}")
