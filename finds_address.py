"""
Finds the complete address of a given Brazilian zip code.
"""

import requests

while True:
    cep = str(input(f"\nCEP: "))

    try:
        r = requests.get(f"http://viacep.com.br/ws/{cep}/json")
        endereco_completo = r.json()
        print(f"Endereço: {endereco_completo['logradouro'].upper()}, "
              f"{endereco_completo['bairro'].upper()}, "
              f"{endereco_completo['localidade'].upper()}/{endereco_completo['uf'].upper()}.")

    except:
        print("CEP inválido")