from typing import Dict
import flet
from flet import Page, ElevatedButton, TextField, Column, Row, UserControl, AppBar, Text, View, colors, Dropdown, dropdown
from docxtpl import DocxTemplate


class DocForm(UserControl):
    def build(self):

        # START - constantes
        self.TEMPLATE_PROCURACAO: str = 'templates/procuracao.docx'
        self.TEMPLATE_DECLARACAO_HIPOSSUFICIENCIA: str = 'templates/declaracao_hipossuficiencia.docx'
        self.TEMPLATE_CONTRATO_HONORARIOS: str ='templates/contrato_honorarios.docx'
        self.OPCOES_HONORARIOS = {
            '30% ao final': '30% do aproveitamento econômico somente ao final do processo',
            '25% ao final': '25% do aproveitamento econômico somente ao final do processo',
            '20% ao final': '20% do aproveitamento econômico somente ao final do processo',
            '15% ao final': '15% do aproveitamento econômico somente ao final do processo',
            '10% ao final': '10% do aproveitamento econômico somente ao final do processo',
            'Outro': None,
        }
        # END - constantes


        # START -- campos comuns à Procuracao, Declaracao de Hip. e Contrato de Honorários --
        self.nome_cliente: TextField = TextField(label='NOME DO CLIENTE', width=300, autofocus=True)
        self.nacionalidade: TextField = TextField(label='NACIONALIDADE', width=160)
        self.estado_civil: TextField = TextField(label='ESTADO CIVIL', width=150)
        self.profissao: TextField = TextField(label='PROFISSÃO', width=150)
        self.data_nascimento: TextField = TextField(label='NASCIMENTO', width=150)
        self.rg: TextField = TextField(label='RG', width=150)
        self.cpf: TextField = TextField(label='CPF', width=150)
        self.logradouro: TextField = TextField(label='LOGRADOURO', width=310)
        self.numero: TextField = TextField(label='Nº', width=100)
        self.bairro: TextField = TextField(label='BAIRRO', width=200)
        self.cidade: TextField = TextField(label='CIDADE', width=250)
        self.uf: TextField = TextField(label='UF', width=100)
        self.cep: TextField = TextField(label='CEP', width=100)
        self.email: TextField = TextField(label='E-MAIL', width=150)
        self.finalidade: TextField = TextField(label='FINALIDADE', width=630, multiline=True)
        # END -- campos comuns à Procuracao, Declaracao de Hip. e Contrato de Honorários --

        # START -- campos específicos para o Contrato de honorários --
        self.administrador_contrato: TextField = TextField(label='ADMINISTRADOR', hint_text='Nome do advogado administrador do contrato de honorários', width=300)
        self.honorarios: Dropdown = Dropdown(label='HONORÁRIOS', width=200, on_change=self.custom_hono)
        self.custom_honorarios: TextField = TextField(label='Descrição dos honorários', visible=False, width=630, multiline=True)
        for opcao in self.OPCOES_HONORARIOS.keys():
            self.honorarios.options.append(dropdown.Option(opcao))
        # END -- campos específicos para o Contrato de honorários --
        
        self.context: Dict 
        self.root =  Column([

                    Row([
                        self.nome_cliente, self.nacionalidade, self.estado_civil, 
                    ], wrap=True),

                    Row([
                        self.profissao, self.data_nascimento, self.rg, self.cpf,
                    ], wrap=True),

                    Row([
                        self.logradouro, self.numero, self.bairro,
                    ], wrap=True),

                    Row([
                        self.cidade, self.uf, self.cep, self.email,
                    ], wrap=True),

                    Row([self.finalidade], wrap=True),
                    
                    Row([
                        self.administrador_contrato, self.honorarios, self.custom_honorarios,
                    ], wrap=True),

                    Row([
                        ElevatedButton('Limpar campos', on_click=self.limpar_campos, bgcolor=colors.RED_ACCENT_100, color='black'),
                        ElevatedButton('Nova Procuração', on_click=self.gerar_procuracao),
                        ElevatedButton('Nova Declaração de Hip.', on_click=self.gerar_declaracao_hipossuficiencia),
                        ElevatedButton('Novo Contrato de Honorários.', on_click=self.gerar_contrato_honorarios),
                    ]),
                    
                ])
        
        return self.root
    
    def limpar_campos(self, e):
        # self.nome_cliente.value = ''
        # self.nacionalidade.value = ''
        # (...)
        # empty all fields with FOR
        for control in self.root.controls:
            for field in control.controls:
                field.value = ''
        
        self.update()

    def gerar_doc(self, tipo, template):
        # template is a string like 'templates/procuracao.docx'
        doc = DocxTemplate(template)

        self.context = { 
            
            'nome_cliente': self.nome_cliente.value,
            'nacionalidade': self.nacionalidade.value,
            'estado_civil': self.estado_civil.value, 
            'profissao': self.profissao.value, 
            'data_nascimento': self.data_nascimento.value,
            'rg': self.rg.value,
            'cpf': self.cpf.value,
            'logradouro': self.logradouro.value,
            'numero': self.numero.value,
            'bairro': self.bairro.value,
            'cidade': self.cidade.value,
            'uf': self.uf.value,
            'cep': self.cep.value,
            'email': self.email.value,
            'finalidade': self.finalidade.value,
            'administrador_contrato': self.administrador_contrato.value,
            'honorarios': self.custom_honorarios.value or self.OPCOES_HONORARIOS[self.honorarios.value]
        }    

        doc.render(self.context)
        primeiro_nome = self.nome_cliente.value.split(' ')[0]
        doc.save(f'{tipo}_{primeiro_nome}.docx')
    
    def gerar_procuracao(self, e):
        self.gerar_doc(tipo='Procuracao', template=self.TEMPLATE_PROCURACAO)
    
    def gerar_declaracao_hipossuficiencia(self, e):
        self.gerar_doc(tipo='Declaracao_Hipossuficiencia', template=self.TEMPLATE_DECLARACAO_HIPOSSUFICIENCIA)

    def gerar_contrato_honorarios(self, e):
        self.gerar_doc(tipo='Contrato_Honorarios', template=self.TEMPLATE_CONTRATO_HONORARIOS)

    def custom_hono(self, e):
        if self.honorarios.value == 'Outro':
            self.custom_honorarios.visible = True
        else:
            self.custom_honorarios.visible = False
            self.custom_honorarios.value = None
        self.update()


def main(page: Page):
    

    def route_change(route):
        page.views.clear()
        page.theme_mode = 'dark'
        page.window_width = 800
        page.window_height = 650
        page.window_maximized = False
        page.views.append(
            
            View('/', [
                AppBar(title=Text('AutoDocs'), bgcolor=colors.BLUE_GREY_900),
                DocForm()
            ]),
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

