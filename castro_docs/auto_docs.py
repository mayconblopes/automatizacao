from fileinput import filename
from genericpath import isfile
from typing import Dict
import flet
from flet import Page, ElevatedButton, TextField, Column, Row, UserControl, AppBar, Text, View, colors, Dropdown, dropdown, Checkbox, Card, Container, margin, IconButton, icons, AlertDialog, TextButton, FilePicker, FilePickerResultEvent, WindowDragArea
from docxtpl import DocxTemplate
import webbrowser
import orm_sqlite, sqlite3
from validate_docbr import CPF
import datetime
import requests
from time import sleep
from decouple import config
import pyrebase
import tempfile
import os


class ClienteModel (orm_sqlite.Model):
    cpf = orm_sqlite.IntegerField(primary_key=True)
    nome_cliente = orm_sqlite.StringField()
    nacionalidade = orm_sqlite.StringField()
    estado_civil = orm_sqlite.StringField()
    profissao = orm_sqlite.StringField()
    data_nascimento = orm_sqlite.StringField()
    rg = orm_sqlite.StringField()
    logradouro = orm_sqlite.StringField()
    numero = orm_sqlite.StringField()
    bairro = orm_sqlite.StringField()
    cidade = orm_sqlite.StringField()
    uf = orm_sqlite.StringField()
    cep = orm_sqlite.StringField()
    email = orm_sqlite.StringField()
                                    

class DocForm(UserControl):

    def __init__(self, page: Page, database: orm_sqlite.Database):
        super().__init__()
        self.page = page
        self.database = database
        self.firebase_config = {
                    "apiKey": config('apiKey'),
                    "authDomain": config('authDomain'),
                    "projectId": config('projectId'),
                    "storageBucket": config('storageBucket'),
                    "messagingSenderId": config('messagingSenderId'),
                    "appId": config('appId'),
                    'databaseURL': '',
                    }

        self.firebase = pyrebase.initialize_app(self.firebase_config)
        self.auth = self.firebase.auth()
        self.storage = self.firebase.storage()

        try:
            user = self.auth.sign_in_with_email_and_password(config('email'), config('pwd'))
            print('Templates carregados com sucesso.')
            # self.show_alert(Text('Templates carregados com sucesso.'))
        except:
            print('Não foi possível carregar os templates. Verifique sua conexão com a internet.')
            # self.show_alert(Text('Não foi possível carregar os templates. Verifique sua conexão com a internet.'))

    def build(self):

        # START - constantes
        self.TEMPLATE_PROCURACAO = 'templates/procuracao.docx'
        self.TEMPLATE_DECLARACAO_HIPOSSUFICIENCIA = 'templates/declaracao_hipossuficiencia.docx'
        self.TEMPLATE_CONTRATO_HONORARIOS = 'templates/contrato_honorarios.docx'
        self.OPCOES_HONORARIOS = {
            '30% ao final': '30% do aproveitamento econômico somente ao final do processo',
            '25% ao final': '25% do aproveitamento econômico somente ao final do processo',
            '20% ao final': '20% do aproveitamento econômico somente ao final do processo',
            '15% ao final': '15% do aproveitamento econômico somente ao final do processo',
            '10% ao final': '10% do aproveitamento econômico somente ao final do processo',
            'Outro': None,
        }
        self.DEFAULT_HONORARIOS = list(self.OPCOES_HONORARIOS.keys())[0]

        OPCOES_ESTADO_CIVIL = ['solteiro(a)', 'casado(a)', 'separado(a)', 'divorciado(a)', 'viúvo(a)']

        # END - constantes


        # START -- campos comuns à Procuracao, Declaracao de Hip. e Contrato de Honorários --
        self.cpf: TextField = TextField(label='CPF', width=150, on_blur=self.cpf_check, autofocus=True, helper_text='Informe o CPF')
        self.nome_cliente: TextField = TextField(label='NOME DO CLIENTE', on_blur=self.hot_save, width=300)
        self.nacionalidade: TextField = TextField(label='NACIONALIDADE', on_blur=self.hot_save, width=160)
        self.estado_civil: Dropdown = Dropdown(label='ESTADO CIVIL', on_change=self.hot_save, width=150)
        for estado_civil in OPCOES_ESTADO_CIVIL:
            self.estado_civil.options.append(dropdown.Option(estado_civil))
        self.profissao: TextField = TextField(label='PROFISSÃO', on_blur=self.hot_save, width=150)
        self.data_nascimento: TextField = TextField(label='NASCIMENTO', on_blur=self.data_nascimento_check, width=150, hint_text='dd/mm/aaaa')
        self.rg: TextField = TextField(label='RG', on_blur=self.hot_save, width=150)
        self.logradouro: TextField = TextField(label='LOGRADOURO', on_blur=self.hot_save, width=310)
        self.numero: TextField = TextField(label='Nº', on_blur=self.hot_save, width=100)
        self.bairro: TextField = TextField(label='BAIRRO', on_blur=self.hot_save, width=200)
        self.cidade: TextField = TextField(label='CIDADE', on_blur=self.hot_save, width=220)
        self.uf: TextField = TextField(label='UF', on_blur=self.uf_check, width=80)
        self.cep: TextField = TextField(label='CEP', on_blur=self.cep_check, width=120)
        self.email: TextField = TextField(label='E-MAIL', on_blur=self.hot_save, width=180, text_size=12)
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

        # campos específicos à qualifificacao do cliente
        self.qualificacao = [
                        Row([
                            self.cpf, self.nome_cliente, self.nacionalidade, 
                        ], wrap=True),

                        Row([
                            self.estado_civil, self.profissao, self.data_nascimento, self.rg,
                        ], wrap=True),

                        Row([
                            self.email, self.cep, self.cidade, self.uf,
                        ], wrap=True),

                        Row([
                            self.bairro, self.logradouro, self.numero,
                        ], wrap=True),
        ]

        # campos que são específicos para os documentos a serem gerados
        self.formulario_docs = [
                        
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
                            Column(self.qualificacao + self.formulario_docs),
                            
                            Column([
                                Card(
                                    content=Container(
                                        Column(self.botoes, horizontal_alignment='center', spacing=48),
                                        padding=30,
                                        bgcolor=colors.BLUE_GREY_900,
                                        border_radius=10,
                                    ),
                                    margin = margin.only(left=25, top=10),
                                ),
                                self.folder_path,
                            ], horizontal_alignment='center'),
                        ])
        

        # change text size of all TextFields to 11
        # for control in self.qualificacao + self.formulario_docs:
        #     try:
        #         for field in control.controls:
        #             field.text_size = 11
        #     except AttributeError:
        #         pass

        
        return self.root

    # def desabilita_campos_exceto(self, e, exceto):
    #     """Desabilita todos os campos menos exceto"""
    #     for control in self.qualificacao:
    #         for field in control.controls:
    #             field.disabled = True
    #     exceto.disabled = False

    def hot_save(self, e):
        self.cpf_check(e, limpa_qualificacao=False)

    def data_nascimento_check(self, e):
        data_nascimento = self.data_nascimento.value
        try:
            datetime.datetime.strptime(data_nascimento, '%d/%m/%Y')
            self.data_nascimento.error_text = None
            self.update()
            self.hot_save(e)
        except ValueError:
            self.data_nascimento.value = None
            self.data_nascimento.error_text = 'DD/MM/AAAA'
            self.data_nascimento.focus()
            self.update()
    
    def uf_check(self, e):

        uf_list = ['RO', 'AC', 'AM', 'RR', 'PA', 'AP', 'TO', 'MA', 'PI', 'CE', 'RN', 'PB', 'PE', 
                   'AL', 'SE', 'BA', 'MG', 'ES', 'RJ', 'SP', 'PR', 'SC', 'RS', 'MS', 'MT', 'GO', 'DF'] 
        
        self.uf.value = str(self.uf.value).upper()
        if self.uf.value not in uf_list:
            self.uf.error_text = 'Inválido'
            self.uf.value = ''
            self.uf.focus()
            self.update()
        else:
            self.uf.error_text = None
            self.hot_save(e)
            self.update()
    
    def cep_check(self, e):
        try:
            request = requests.get(f'http://viacep.com.br/ws/{self.cep.value}/json')
            address = request.json()
            self.logradouro.value = address['logradouro'].title()
            self.bairro.value = address['bairro'].title()
            self.cidade.value = address['localidade'].title()
            self.uf.value = address['uf'].upper()
            self.cep.error_text = None
            self.hot_save(e)
            self.update()

        except:
            # self.cep.value = ''
            self.cep.error_text = 'Não encontrado'
            self.hot_save(e)
            self.update()

        self.update()

    def cpf_check(self, e, limpa_qualificacao=True):
        """
            Valida o CPF e salva no banco, mas apenas se todos os campos de qualificação do cliente estiverem preenchidos.
            limpa_qualificacao = True significa que self.limpar_campos vai apagar todos os campos, incluindo os de qualificação.
        """
        cpf = CPF()

        # se o CPF não for válido, apresenta mensagem de erro
        if not cpf.validate(self.cpf.value):
            cpf = self.cpf.value
            self.limpar_campos(e, limpa_qualificao=limpa_qualificacao)
            self.cpf.value = cpf
            self.cpf.error_text = 'CPF inválido' if self.cpf.value else 'Digite um CPF válido'
            self.cpf.focus()

            self.update()
        
        # se o CPF for válido...
        else:
            self.cpf.error_text = None
            cliente = self.recuperar_do_banco_pelo_cpf(e, self.cpf.value)
            
            # ... se o cliente não existe no banco, limpa todos os campos (exceto o CPF digitado), 
            # apresenta mensagem indicando ser um novo cliente e aguarda todos os campos serem preenchidos para salvar no banco
            if not cliente:
                cpf = self.cpf.value
                self.limpar_campos(e, limpa_qualificao=limpa_qualificacao)
                self.cpf.value = cpf
                self.cpf.helper_text = 'Novo cliente'
                self.update()

                # START -- validando campos vazios antes de salvar novo cliente no banco--
                salvar = False
                while not salvar:
                    print('Aguardando todos os campos serem preenchidos para salvar no BD...')
                    for control in self.qualificacao:
                        for field in control.controls:

                            # se o campo não estiver visível ou o campo estiver desabilitado...
                            if field.visible == False or field.disabled == True:
                                # ... ignora o campo que não está visível ou que está desabilitado
                                continue

                            # se algum campo possui valor vazio, salvar = False e interrompe o loop
                            if field.value == '':
                                salvar = False
                                sleep(1)
                                break

                            # se nenhum campo está vazio, salvar = True
                            else:
                                salvar = True

                # o código abaixo somente será executado se salvar = True, o que significa que todos os campos foram preenchidos
                self.salvar_no_banco(e)
            
            # ... se o cliente já existe no banco de dados, limpa todos os campos (exceto CPF) e recupera suas informações do banco
            else: 
                cpf = self.cpf.value
                self.limpar_campos(e, limpa_qualificao=limpa_qualificacao)
                self.cpf.value = cpf

                # recupera do BD se o campo for vazio, se não significa que o campo foi alterado pelo usuário, então mantém o campo como está
                self.cpf.value = cliente['cpf'] if not self.cpf.value else self.cpf.value
                self.nome_cliente.value = cliente['nome_cliente'] if not self.nome_cliente.value else self.nome_cliente.value
                self.nacionalidade.value = cliente['nacionalidade'] if not self.nacionalidade.value else self.nacionalidade.value
                self.estado_civil.value = cliente['estado_civil'] if not self.estado_civil.value else self.estado_civil.value
                self.profissao.value = cliente['profissao'] if not self.profissao.value else self.profissao.value
                self.data_nascimento.value = cliente['data_nascimento'] if not self.data_nascimento.value else self.data_nascimento.value
                self.rg.value = cliente['rg'] if not self.rg.value else self.rg.value
                self.logradouro.value = cliente['logradouro'] if not self.logradouro.value else self.logradouro.value
                self.numero.value = cliente['numero'] if not self.numero.value else self.numero.value
                self.bairro.value = cliente['bairro'] if not self.bairro.value else self.bairro.value
                self.cidade.value = cliente['cidade'] if not self.cidade.value else self.cidade.value
                self.uf.value = cliente['uf'] if not self.uf.value else self.uf.value
                self.cep.value = cliente['cep'] if not self.cep.value else self.cep.value
                self.email.value = cliente['email'] if not self.email.value else self.email.value
                self.salvar_no_banco(e)
                self.update()

    def salvar_no_banco(self, e):
        ClienteModel.objects.backend = self.database
        self.CLIENTE_DB = ClienteModel({'cpf': self.cpf.value, 
                                        'nome_cliente': self.nome_cliente.value,
                                        'nacionalidade': self.nacionalidade.value,
                                        'estado_civil': self.estado_civil.value,
                                        'profissao': self.profissao.value,
                                        'data_nascimento': self.data_nascimento.value,
                                        'rg': self.rg.value,
                                        'logradouro': self.logradouro.value,
                                        'numero': self.numero.value,
                                        'bairro': self.bairro.value,
                                        'cidade': self.cidade.value,
                                        'uf': self.uf.value,
                                        'cep': self.cep.value,
                                        'email': self.email.value,
                                        })

        self.CLIENTE_DB.save()
        self.CLIENTE_DB.update()
        print('BD atualizado')
    
    def recuperar_do_banco_pelo_cpf(self, e, cpf):
        try:
            ClienteModel.objects.backend = self.database
            cliente = ClienteModel.objects.get(pk=cpf)
        except sqlite3.OperationalError as err:
            if 'no such table' in str(err):
                print('Banco de dados ainda não foi criado... preencher todos os campos para que o banco seja criado pela primeira vez')
                cliente = None
            else:
                print(err)

        return cliente
     
    
    def limpar_campos(self, e, limpa_qualificao=True):
        # self.nome_cliente.value = ''
        # self.nacionalidade.value = ''
        # (...)
        # empty all fields with FOR
        for control in self.root.controls[0].controls:
            # se limpa_qualificacao=False, entao ignora os campos de qualificacao
            if not limpa_qualificao and control in self.qualificacao:
                continue
            else:
                for field in control.controls:
                    try:
                        # o if é para ignorar os checkboxes
                        field.value = '' if isinstance(field, TextField) else None
                        field.error_text = None
                        field.helper_text = None
                    except AttributeError:
                        # como ElevatedButton não possui o campo value, ocorre erro ao tentar atribuir = '', o que basta ser ignorado neste caso
                        pass
        self.honorarios.value = self.DEFAULT_HONORARIOS
        self.honorarios_iniciais.disabled = True
        self.custom_honorarios.visible = False
        self.update()

    def gerar_doc(self, tipo, template):

        # START -- validando campos vazios --
        gerar = True
        for control in self.formulario_docs:
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
    
    def gerar_doc_pelo_template(self, template):
        """template é um parametro para implementar um strategy"""

        tmp_dir = tempfile.gettempdir()
        print(tmp_dir)
        tmp_proc_path = f'{tmp_dir}/proc.tmp'
        tmp_dec_path = f'{tmp_dir}/dec.tmp'
        tmp_contr_path = f'{tmp_dir}/contr.tmp'
        
       	user = self.auth.sign_in_with_email_and_password(config('email'), config('pwd'))

        if template == 'templates/procuracao.docx':
            storage = self.storage.child(self.TEMPLATE_PROCURACAO)
            if os.path.isfile(tmp_proc_path):
                self.gerar_doc(tipo='Procuracao', template=tmp_proc_path)
            else:
                storage.download(path=f'', filename=tmp_proc_path)
                self.gerar_doc(tipo='Procuracao', template=tmp_proc_path)

        
        elif template == 'templates/declaracao_hipossuficiencia.docx':
            storage = self.storage.child(self.TEMPLATE_DECLARACAO_HIPOSSUFICIENCIA)
            if os.path.isfile(tmp_dec_path):
                self.gerar_doc(tipo='Declaracao de Hipossuficiencia', template=tmp_dec_path)
            else:
                storage.download(path='', filename=tmp_dec_path)
                self.gerar_doc(tipo='Declaracao de Hipossuficiencia', template=tmp_dec_path)
        
        elif template == 'templates/contrato_honorarios.docx':
            storage = self.storage.child(self.TEMPLATE_CONTRATO_HONORARIOS)
            if os.path.isfile(tmp_contr_path):
                self.gerar_doc(tipo='Contrato de Honorarios', template=tmp_contr_path)
            else:    
                storage.download(path='', filename=tmp_contr_path)
                self.gerar_doc(tipo='Contrato de Honorarios', template=tmp_contr_path)
        else:
            raise AttributeError("Template não é válido")


    def gerar_procuracao(self, e):
        self.gerar_doc_pelo_template(self.TEMPLATE_PROCURACAO)

    def gerar_declaracao_hipossuficiencia(self, e):
        self.gerar_doc_pelo_template(self.TEMPLATE_DECLARACAO_HIPOSSUFICIENCIA)

    def gerar_contrato_honorarios(self, e):
        self.gerar_doc_pelo_template(self.TEMPLATE_CONTRATO_HONORARIOS)

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
    class Database(orm_sqlite.Database):
        """
        Custom Database, based on orm_sqlite.Database, that is used to override connect method so it's possible to set check_same_thread=False
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        
        def connect(self):
           """
           Overrides connect method to set check_same_thread=False
           """
           super().connect() 
           self._connection = sqlite3.connect(*self.args, **self.kwargs, check_same_thread=False)
           self._connection.row_factory = sqlite3.Row
           self._cursor = self._connection.cursor()
           self._connected = True

    # database = orm_sqlite.Database('data/sqlite.db')
    database = Database('data/sqlite.db') # use my custom Database instead of orm_sqlite.Database
    page.window_maximized = False
    page.theme_mode = 'dark'
    page.title = 'AutoDocs'
    page.window_width = 900
    page.window_height = 750
    page.window_frameless = True

    def route_change(route):
        page.views.clear()
        page.views.append(
            
            View('/', [
                AppBar(
                    title=WindowDragArea(
                        Text('AutoDocs'+' '*1000)
                    ), 
                    bgcolor=colors.BLUE_GREY_900,
                    actions=[
                        IconButton(icons.CLOSE, on_click=lambda _: page.window_close())
                    ]
                ),
                DocForm(page=page, database=database),
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

    def clean_tmp(e):
        tmp_dir = tempfile.gettempdir()
        
        try:
            os.remove(f'{tmp_dir}/proc.tmp')
            print('Template da Procuração encontrado e removido da pasta de temporários')    
        except FileNotFoundError:
            print('Template da Procuração não encontrado na pasta de temporários')    

        try:
            os.remove(f'{tmp_dir}/dec.tmp')
            print('Template da Declaração de Hipossuficiência encontrado e removido da pasta de temporários')    
        except FileNotFoundError:
            print('Template da Declaração de Hipossuficiência não encontrado na pasta de temporários')    
        
        try:    
            os.remove(f'{tmp_dir}/contr.tmp')
            print('Template do Contrato de Honorários encontrado e removido da pasta de temporários')    
        except FileNotFoundError:
            print('Template do Contrato de Honorários não encontrado na pasta de temporários')    
        



    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.on_disconnect = clean_tmp
    
    page.go(page.route)
    
    

flet.app(target=main, port=8000, route_url_strategy='path')
