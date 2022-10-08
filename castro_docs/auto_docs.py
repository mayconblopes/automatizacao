from pickle import FALSE
from typing import Dict
import flet
from flet import Page, ElevatedButton, TextField, Column, Row, UserControl, AppBar, Text, View, colors, Dropdown, dropdown, Checkbox, Card, Container, margin, IconButton, icons, AlertDialog, TextButton, FilePicker, FilePickerResultEvent
from docxtpl import DocxTemplate
import webbrowser


class DocForm(UserControl):

    def __init__(self, page):
        super().__init__()
        self.page = page

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
        self.DEFAULT_HONORARIOS = list(self.OPCOES_HONORARIOS.keys())[0]
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
        self.administrador_contrato: TextField = TextField(label='ADMINISTRADOR', hint_text='Administrador do contrato', width=300)
        self.checkbox_honorarios_iniciais: Checkbox = Checkbox(value=False, on_change=self.toggle_honorarios_iniciais)
        self.honorarios_iniciais: TextField = TextField(label='Honorários iniciais', disabled=True, width=580, 
                                                        hint_text="Exemplo: R$ XXXX,XX na data da assinatura deste contrato")
        self.honorarios: Dropdown = Dropdown(
                                                label='HONORÁRIOS',
                                                width=200,
                                                on_change=self.custom_hono,
                                                value=self.DEFAULT_HONORARIOS,
                                            )
        self.custom_honorarios: TextField = TextField(label='Descrição dos honorários', visible=False, width=630, multiline=True)
        for opcao in self.OPCOES_HONORARIOS.keys():
            self.honorarios.options.append(dropdown.Option(opcao))
        # END -- campos específicos para o Contrato de honorários --

        self.file_picker = FilePicker(on_result=self.configurar_diretorio)
        self.folder_path = Text('', visible=False, size=10)
        self.context: Dict = {}

        self.page.dialog = AlertDialog()
        self.page.overlay.append(self.file_picker)

        self.formulario = [
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

                        Row([self.checkbox_honorarios_iniciais, self.honorarios_iniciais]),
                        
                        Row([
                            self.administrador_contrato, self.honorarios, 
                        ], wrap=True),

                        Row([
                            self.custom_honorarios,
                        ], wrap=True),
                    ]

        self.botoes = [
                    ElevatedButton('Configurar diretório...', on_click=lambda _: self.file_picker.get_directory_path()),
                    ElevatedButton('Nova Procuração', on_click=self.gerar_procuracao, disabled=True),
                    ElevatedButton('Nova Dec Hipossuficiência', on_click=self.gerar_declaracao_hipossuficiencia, disabled=True),
                    ElevatedButton('Novo Contrato de Honorários', on_click=self.gerar_contrato_honorarios, disabled=True),
                    ElevatedButton('Limpar campos', on_click=self.limpar_campos,
                                                    bgcolor=colors.RED_ACCENT_100, color='black'),
                ]

        self.root = Row(
                        vertical_alignment='start', 
                        controls=[
                            Column(self.formulario),
                            
                            Column([
                                Card(
                                    content=Container(
                                        Column(self.botoes, horizontal_alignment='center', spacing=30),
                                        padding=30,
                                        bgcolor=colors.BLUE_GREY_900,
                                        border_radius=10,
                                    ),
                                    margin = margin.only(left=50),
                                ),
                                self.folder_path,
                            ], horizontal_alignment='center'),
                        ])
        

        # change text size of all TextFields to 11
        for control in self.formulario:
            try:
                for field in control.controls:
                    field.text_size = 11
            except AttributeError:
                pass

        
        return self.root
    
    def limpar_campos(self, e):
        # self.nome_cliente.value = ''
        # self.nacionalidade.value = ''
        # (...)
        # empty all fields with FOR
        for control in self.root.controls[0].controls:
            for field in control.controls:
                try:
                    # o if é para ignorar os checkboxes
                    field.value = '' if isinstance(field, TextField) else None
                except AttributeError:
                    # como ElevatedButton não possui o campo value, ocorre erro ao tentar atribuir = '', o que basta ser ignorado neste caso
                    pass
        self.honorarios.value = self.DEFAULT_HONORARIOS
        self.update()

    def gerar_doc(self, tipo, template):

        # START -- validando campos vazios --
        gerar = True
        for control in self.formulario:
            for field in control.controls:
                if field.visible == False or field.disabled == True:
                    continue
                if field.value == '':
                    gerar = False
                    break

        if not gerar:
            self.show_alert(Text('Preencha todos os campos antes', color=colors.AMBER_400))

        # se não tem campo vazio no formulário, então continua com o algoritmo para gerar o arquivo
        else:
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
                'checkbox_honorarios_iniciais': self.checkbox_honorarios_iniciais.value,
                'honorarios_iniciais': self.honorarios_iniciais.value,
                'honorarios': self.custom_honorarios.value or self.OPCOES_HONORARIOS[self.honorarios.value]
            }    

            doc.render(self.context)
            primeiro_nome = self.nome_cliente.value.split(' ')[0]
            save_folder = self.folder_path.value.split('\n')[1]
            doc.save(f'{save_folder}/{tipo}_{primeiro_nome}.docx')
            self.show_alert(Text(f'Documento {tipo} gerado com sucesso!'))
    
    def show_alert(self, message):
        self.page.dialog.title = message
        self.page.dialog.open = True
        self.page.dialog.bgcolor = 'pink'
        self.page.update()
    
    def gerar_procuracao(self, e):
        self.gerar_doc(tipo='Procuracao', template=self.TEMPLATE_PROCURACAO)

    def gerar_declaracao_hipossuficiencia(self, e):
        self.gerar_doc(tipo='Declaracao de Hipossuficiencia', template=self.TEMPLATE_DECLARACAO_HIPOSSUFICIENCIA)

    def gerar_contrato_honorarios(self, e):
        self.gerar_doc(tipo='Contrato de Honorarios', template=self.TEMPLATE_CONTRATO_HONORARIOS)

    def custom_hono(self, e):
        if self.honorarios.value == 'Outro':
            self.custom_honorarios.visible = True
        else:
            self.custom_honorarios.visible = False
            self.custom_honorarios.value = None
        self.update()

    def toggle_honorarios_iniciais(self, e):
        self.honorarios_iniciais.disabled = not self.checkbox_honorarios_iniciais.value
        self.context['honorarios_iniciais'] = self.checkbox_honorarios_iniciais.value
        self.update()
    
    def configurar_diretorio(self, e: FilePickerResultEvent):
        try:
            self.folder_path.value = 'Salvando arquivos em \n' + e.path
            self.folder_path.visible = True
            for botao in self.botoes:
                botao.disabled = False

        except TypeError:
            if not self.folder_path.value:
                self.show_alert(Text('Operação cancelada. Por favor, escolha um diretório válido.'))
            else:
                pass
        self.update()
        
        


def main(page: Page):
    page.window_maximized = False
    page.window_resizable = True
    page.theme_mode = 'dark'
    page.title = 'AutoDocs'
    page.window_width = 1000
    page.window_height = 650

    def route_change(route):
        page.views.clear()
        page.views.append(
            
            View('/', [
                AppBar(title=Text('AutoDocs'), bgcolor=colors.BLUE_GREY_900),
                DocForm(page),
                Row([TextButton(text='Dev by mayconblopes', on_click=mayconblopes)])
            ], bgcolor='0xFF424242'),
        )

        page.update()
    
    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    def mayconblopes(e):
        webbrowser.open('https://github.com/mayconblopes')

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    
    page.go(page.route)
    
    

flet.app(target=main, port=8000, route_url_strategy='path')
