"""
Finds the complete address of a given Brazilian zip code.
"""

import requests
import os


# def cls():
#     os.system('cls' if os.name == 'nt' else 'clear')

while True:
    print("Digite ENTER para entrar ou reiniciar o sistema de busca CEP")
    input()
    os.system('cls')
    print("Desenvolvido por Maycon Lopes (https://github.com/mayconblopes)")
    print("\n1 - Pesquisa por CEP")
    print("2 - Pesquisa por ENDEREÇO \n")
    pesquisa = str(input('Tipo de busca (1 ou 2): '))
    if pesquisa != '1' and pesquisa != '2':
        print('\033[31m' + "\n Opção inválida \n" + '\033[0;0m')
        continue
    elif pesquisa == '1':
        cep = str(input(f"\nCEP: "))

        try:
            r = requests.get(f"http://viacep.com.br/ws/{cep}/json")
            endereco_completo = r.json()
            print(f"Endereço: {endereco_completo['logradouro'].upper()}, "
                  f"{endereco_completo['bairro'].upper()}, "
                  f"{endereco_completo['localidade'].upper()}/{endereco_completo['uf'].upper()}. \n")

        except:
            print('\033[31m' + "\n CEP inválido \n" + '\033[0;0m')
    else:
        uf = str(input('Digite o nome da UF: ')).upper()[:2]
        cidade = str(input('Digite o nome da cidade: ')).title()
        rua = str(input('Digite o nome da rua: ')).upper().title()
        try:
            r = requests.get(f"http://viacep.com.br/ws/{uf}/{cidade}/{rua}/json")
            enderecos = r.json()
            print('\n')
            # algumas vezes a busca retorna uma lista vazia, entao é melhor checar isso:
            if enderecos != []:
                for item in enderecos:
                    print(f"Endereço: {item['logradouro'].upper()}, "
                          f"{item['complemento'].upper()} "
                          f"{item['bairro'].upper()}, "
                          f"{item['localidade'].upper()}/{item['uf'].upper()}, "
                          f"CEP {item['cep'].upper()} \n")
            else:
                print('\033[31m' + "\n Endereço não encontrado \n" + '\033[0;0m')
        except:
            print('\033[31m' + "\n Endereço não encontrado \n" + '\033[0;0m')
