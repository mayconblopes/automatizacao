import flet
from flet import Page, UserControl, TextField, Column, AppBar, Text, colors, IconButton, icons, Row, View, TextButton, WindowDragArea, Container
import requests

class FindsAddressByCEP(UserControl):

    def build(self):
        self.cep = TextField(label='CEP')
        self.results = TextField(label='Resultado', disabled=False, multiline=True, expand=True, text_size=12) 

        # app's root
        root = Column(
            controls=[
                        
                        Row(controls=[
                            self.cep,
                            IconButton(icon=icons.SEARCH, icon_color=colors.BLUE, on_click=self.find_by_cep),
                            ]),
                        Row([self.results]),
            ],
        )

        return root

    def find_by_cep(self, e):
        try:
            request = requests.get(f'http://viacep.com.br/ws/{self.cep.value}/json')
            address = request.json()

            self.results.value = f"Endereço: {address['logradouro'].upper()}, {address['bairro'].upper()}, {address['localidade'].upper()}/{address['uf'].upper()}."

        except:
            self.results.value = 'CEP inválido' 

        self.update()

class FindsCEPByAddress(UserControl):

    def build(self):
        self.uf = TextField(label='UF')
        self.city = TextField(label='Cidade')
        self.street = TextField(label='Rua')
        self.results = TextField(label='Resultado', disabled=False, multiline=True, expand=True, text_size=12)

        # app's root
        root = Column(
            controls=[
                    Column(
                        controls=[
                            self.uf,
                            self.city,
                            Row(controls=[
                                self.street,
                                IconButton(icon=icons.SEARCH, icon_color=colors.BLUE, on_click=self.find_cep_by_address)
                                ]),
                        ],
                    ),
                    Row([self.results]),
            ],
        )

        return root

    def find_cep_by_address(self, e):
        try:
            request = requests.get(f"http://viacep.com.br/ws/{self.uf.value}/{self.city.value}/{self.street.value}/json")
            addresses = request.json()
            
            # algumas vezes a busca retorna uma lista vazia, entao é melhor checar isso:
            if addresses != []:
                results = ''
                for item in addresses:
                    index = addresses.index(item)+1
                    results += f"Endereço {index}: {item['logradouro'].upper()}, {item['complemento'].upper()} {item['bairro'].upper()}, {item['localidade'].upper()}/{item['uf'].upper()}, CEP {item['cep'].upper()} \n"
                self.results.value = results[:-1] # slice para retirar a última quebra de linha
            else:
                self.results.value = 'Endereço não encontrado'
        except:
            self.results.value = 'Erro interno'

        self.uf.value = ''
        self.city.value = ''
        self.street.value = ''
        self.update()

def main(page: Page):
    page.title = 'Finds Address'
    page.window_frameless = True
    page.theme_mode = 'dark'
    page.window_height = 600
    page.window_width = 379
    page.window_maximized = False
    page.scroll = 'auto'
    page.auto_scroll = True
    finds_address_by_cep = FindsAddressByCEP()
    finds_cep_by_address = FindsCEPByAddress()

    def route_change(route):
        page.views.clear()

        appbar = AppBar(
                        automatically_imply_leading=False,
                        title=WindowDragArea(Container(Text('Finds Address'+' '*1000, size=16))),
                        bgcolor=colors.SURFACE_VARIANT,
                        actions=[
                            TextButton(text='Buca avançada',  scale=.8, on_click=lambda _: page.go('/busca-cep-pelo-endereco')),
                            IconButton(icons.CLOSE, on_click=lambda _: page.window_close())
                            ]
                        )
        
        page.views.append(
            View(
                route='/',
                controls=[appbar, finds_address_by_cep],
            ),
        )
        if page.route == '/busca-cep-pelo-endereco':
            appbar.actions = actions=[
                                    TextButton(text='Bucar simples', scale=.8, on_click=lambda _: page.go('/')),
                                    IconButton(icons.CLOSE, on_click=lambda _: page.window_close())
                                ]
            page.views.append(
                View(
                    route='/busca-cep-pelo-endereco',
                    controls=[appbar, finds_cep_by_address],
                ),
                
            )
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


flet.app(target=main, port=8000, route_url_strategy='path')
