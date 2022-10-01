
import flet
from flet import Page, UserControl, TextField, Column, AppBar, Text, colors, IconButton, icons, Row, View, ProgressBar, TextButton, ListView
import requests

class FindsAddressAppByCEP(UserControl):

    def build(self):
        self.cep = TextField(label='CEP')
        self.results = Column()

        # app's root
        root = Column(
            controls=[
                        
                        Row(controls=[
                            self.cep,
                            IconButton(icon=icons.SEARCH, icon_color=colors.BLUE, on_click=self.find_by_cep),
                            ]),
                        self.results,
            ],
        )

        return root

    def find_by_cep(self, e):
        try:
            request = requests.get(f'http://viacep.com.br/ws/{self.cep.value}/json')
            address = request.json()
            self.results.controls.append(Text(
                f"Endereço: {address['logradouro'].upper()}, {address['bairro'].upper()}, {address['localidade'].upper()}/{address['uf'].upper()}.")
            )
        except:
            self.results.controls.append(Text('CEP inválido'))

        self.cep.value = ''
        self.update()

class FindsCEPByAddress(UserControl):

    def build(self):
        self.uf = TextField(label='UF')
        self.city = TextField(label='Cidade')
        self.street = TextField(label='Rua')
        self.results = ListView(expand=True, auto_scroll=True)

        # app's root
        root = Column(
            controls=[
                    Column(
                        controls=[
                            self.uf,
                            self.city,
                            Row(controls=[
                                self.street,
                                IconButton(icon=icons.SEARCH, icon_color=colors.BLUE, on_click=self.find_by_address)
                                ]),
                        ],
                    ),
                    self.results,
            ],
        )

        return root

    def find_by_address(self, e):
        try:
            request = requests.get(f"http://viacep.com.br/ws/{self.uf.value}/{self.city.value}/{self.street.value}/json")
            addresses = request.json()
            
            # algumas vezes a busca retorna uma lista vazia, entao é melhor checar isso:
            if addresses != []:
                for item in addresses:
                    self.results.controls.append(Text(
                        f"Endereço: {item['logradouro'].upper()}, "
                        f"{item['complemento'].upper()} "
                            f"{item['bairro'].upper()}, "
                            f"{item['localidade'].upper()}/{item['uf'].upper()}, "
                            f"CEP {item['cep'].upper()} \n")
                    )
                else:
                    self.results.controls.append(Text('Endereço não encontrado'))
        except:
            self.results.controls.append(Text('Endereço não encontrado'))

        self.uf.value = ''
        self.city.value = ''
        self.street.value = ''
        self.update()

def main(page: Page):
    page.title = 'Finds Address'
    page.window_height = 500
    page.window_width = 379
    page.window_maximized = False

    def route_change(route):
        page.views.clear()
        page.views.append(
            View(
                route='/',
                controls=[
                    AppBar(title=Text('Busca ENDEREÇO pelo CEP', size=12), bgcolor=colors.SURFACE_VARIANT, actions=[
                        TextButton(text='Bucar CEP pelo ENDEREÇO',  scale=.8, on_click=lambda _: page.go('/busca-cep-pelo-endereco'))
                    ]),
                    FindsAddressAppByCEP(),

                ],
            ),
        )
        if page.route == '/busca-cep-pelo-endereco':
            page.views.append(
                View(
                    route='/busca-cep-pelo-endereco',
                    controls=[
                        AppBar(title=Text('Busca CEP pelo ENDEREÇO', size=12), bgcolor=colors.SURFACE_VARIANT, actions=[
                            TextButton(text='Bucar ENDEREÇO pelo CEP', scale=.8, on_click=lambda _: page.go('/'))
                            ]),
                        FindsCEPByAddress(),
                    ],
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
    # app = FindsAddressApp()
    # page.add(navbar, app)


flet.app(target=main, port=8000, route_url_strategy='path')
