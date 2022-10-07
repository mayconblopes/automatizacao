from ast import Str
from typing import Dict
import flet
from flet import Page, ElevatedButton, TextField, Column, Row, UserControl, AppBar, Text, View, colors
from docxtpl import DocxTemplate


class ClienteForm(UserControl):
    def build(self):
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
        self.context: Dict 
        self.template_procuracao: Str = 'templates/procuracao.docx'
        self.template_declaracao_hipossuficiencia: Str = 'templates/declaracao_hipossuficiencia.docx'
        self.template_contrato_honorarios: Str ='templates/contrato_honorarios.docx'

        root =  Column([

                    Row([
                        self.nome_cliente, self.nacionalidade, self.estado_civil, 
                    ], wrap=True),

                    Row([
                        self.profissao, self.data_nascimento, self.rg, self.cpf,
                    ], wrap=True),

                    Row([
                        self.logradouro, self.numero, self.bairro
                    ], wrap=True),

                    Row([
                        self.cidade, self.uf, self.cep, self.email
                    ], wrap=True),

                    Row([self.finalidade], wrap=True),

                    Row([
                        ElevatedButton('Limpar campos', on_click=self.limpar_campos, bgcolor=colors.RED_ACCENT_100, color='black'),
                        ElevatedButton('Nova Procuração', on_click=self.gerar_procuracao),
                        ElevatedButton('Nova Declaração de Hip.', on_click=self.gerar_declaracao_hipossuficiencia),
                    ])
                ])
        
        return root
    
    def limpar_campos(self, e):
            self.nome_cliente.value = ''
            self.nacionalidade.value = ''
            self.estado_civil.value = ''
            self.profissao.value = ''
            self.data_nascimento.value = ''
            self.rg.value = ''
            self.cpf.value = ''
            self.logradouro.value = ''
            self.numero.value = ''
            self.bairro.value = ''
            self.cidade.value = ''
            self.uf.value = ''
            self.cep.value = ''
            self.email.value = ''
            self.finalidade.value = ''
            self.update()

    def gerar_doc(self, tipo, template):
      # doc = DocxTemplate('templates/procuracao.docx')
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
        }    

        doc.render(self.context)
        primeiro_nome = self.nome_cliente.value.split(' ')[0]
        doc.save(f'{tipo}_{primeiro_nome}.docx')
    
    def gerar_procuracao(self, e):
        self.gerar_doc(tipo='Procuracao', template='templates/procuracao.docx')
    
    def gerar_declaracao_hipossuficiencia(self, e):
        self.gerar_doc(tipo='Declaracao_Hipossuficiencia', template='templates/declaracao _hipossuficiencia.docx')




    

def main(page: Page):
    

    def route_change(route):
        page.views.clear()
        page.theme_mode = 'dark'
        page.window_width = 700
        page.window_height = 550
        page.window_maximized = False
        page.views.append(
            
            View('/', [
                AppBar(title=Text('Sistema gerador de documentos'), bgcolor=colors.BLUE_GREY_900),
                ClienteForm()
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

