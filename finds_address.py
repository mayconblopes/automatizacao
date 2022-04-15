"""
Finds the complete address of a given Brazilian zip code.
"""

import requests

cep = str(input(f"CEP: "))

try:
    r = requests.get(f"http://viacep.com.br/ws/{cep}/json")
    endereco_completo = r.json()

    for item in endereco_completo:
        print(
            f"{item}: {endereco_completo[item]}") if item == "localidade" or item == "logradouro" or item == "bairro" else None
except:
    print("CEP inválido")
