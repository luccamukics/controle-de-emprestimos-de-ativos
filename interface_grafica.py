"""Interface desktop do controle de empréstimos de ativos.

Executar na pasta do projeto: python main.py
"""

import tkinter as tk
from tkinter import messagebox, ttk

from modulos import servicos
from modulos.formatacao import iniciais_maiusculas, iniciais_maiusculas_funcao, maiusculas
from modulos.relatorios import caminho_planilha, exportar_para_excel


COLUNAS_ATIVOS = (
    ("empresa", "Empresa", 95), ("serial", "Serial", 135),
    ("patrimonio", "Patrimônio", 115), ("tipo", "Tipo", 105),
    ("marca", "Marca", 105), ("modelo", "Modelo", 150),
    ("status", "Status", 100), ("colaborador", "Colaborador", 190),
    ("setor", "Setor", 165),
    ("itens", "Itens entregues", 195),
    ("chamado", "Chamado", 95),
)


def tabela(parent, colunas, altura=15):
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True, pady=(10, 0))
    nomes = [coluna[0] for coluna in colunas]
    arvore = ttk.Treeview(frame, columns=nomes, show="headings", height=altura,
                          selectmode="browse")
    for nome, titulo, largura in colunas:
        arvore.heading(nome, text=titulo)
        arvore.column(nome, width=largura, minwidth=75, stretch=True)
    vertical = ttk.Scrollbar(frame, orient="vertical", command=arvore.yview)
    horizontal = ttk.Scrollbar(frame, orient="horizontal", command=arvore.xview)
    arvore.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    arvore.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return arvore


def preencher(arvore, linhas):
    filhos = arvore.get_children()
    if filhos:
        arvore.delete(*filhos)
    for linha in linhas:
        arvore.insert("", "end", values=["" if v is None else v for v in linha])


class Formulario(tk.Toplevel):
    def __init__(self, app, titulo, largura=570):
        super().__init__(app)
        self.app = app
        self.title(titulo)
        self.geometry(f"{largura}x560")
        self.resizable(True, True)
        self.transient(app)
        self.grab_set()
        self.corpo = ttk.Frame(self, padding=22)
        self.corpo.pack(fill="both", expand=True)
        self.corpo.columnconfigure(1, weight=1)
        self.campos = {}
        ttk.Label(self.corpo, text=titulo, style="Titulo.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 18)
        )
        self.linha = 1

    def campo(self, rotulo, valor="", combo=None, formatar=None):
        ttk.Label(self.corpo, text=rotulo).grid(
            row=self.linha, column=0, sticky="w", padx=(0, 10), pady=6
        )
        inicial = "" if valor is None else str(valor)
        variavel = tk.StringVar(value=formatar(inicial) if formatar else inicial)
        widget = (ttk.Combobox(self.corpo, textvariable=variavel,
                               values=combo, state="readonly") if combo is not None
                  else ttk.Entry(self.corpo, textvariable=variavel))
        widget.grid(row=self.linha, column=1, columnspan=2, sticky="ew", pady=6)
        if formatar and combo is None:
            def atualizar(*_args):
                texto = variavel.get()
                formatado = formatar(texto)
                if texto != formatado:
                    posicao = widget.index(tk.INSERT)
                    variavel.set(formatado)
                    widget.icursor(min(posicao, len(formatado)))
            variavel.trace_add("write", atualizar)
        self.campos[rotulo] = widget
        self.linha += 1
        return variavel

    def botoes(self, acao, rotulo="Salvar"):
        barra = ttk.Frame(self.corpo)
        barra.grid(row=self.linha, column=0, columnspan=3,
                   sticky="e", pady=(22, 0))
        ttk.Button(barra, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(barra, text=rotulo, command=acao).pack(side="right", padx=(0, 10))


class Aplicacao(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Empréstimos de Ativos")
        self.geometry("1160x690")
        self.minsize(820, 550)
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 17, "bold"))
        estilo.configure("Cabecalho.TLabel", font=("Segoe UI", 10))
        self.status = tk.StringVar(value="Conectando ao banco de dados...")
        topo = ttk.Frame(self, padding=(20, 18, 20, 10))
        topo.pack(fill="x")
        ttk.Label(topo, text="Controle de empréstimos de ativos",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(topo, text="Cadastro, empréstimos, devoluções e relatórios",
                  style="Cabecalho.TLabel").pack(anchor="w")
        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.aba_ativos = ttk.Frame(self.abas, padding=14)
        self.aba_emprestimos = ttk.Frame(self.abas, padding=14)
        self.aba_relatorios = ttk.Frame(self.abas, padding=14)
        self.abas.add(self.aba_ativos, text="Ativos")
        self.abas.add(self.aba_emprestimos, text="Empréstimos")
        self.abas.add(self.aba_relatorios, text="Relatórios")
        self.criar_ativos()
        self.criar_emprestimos()
        self.criar_relatorios()
        ttk.Label(self, textvariable=self.status, anchor="w",
                  padding=(20, 8)).pack(fill="x")
        self.after(100, self.atualizar_tudo)

    def executar(self, funcao):
        try:
            return funcao()
        except Exception as erro:
            self.status.set("Não foi possível concluir a operação.")
            messagebox.showerror("Erro", str(erro), parent=self)
            return None

    def criar_ativos(self):
        barra = ttk.Frame(self.aba_ativos)
        barra.pack(fill="x")
        ttk.Button(barra, text="Cadastrar ativo", command=self.novo_ativo).pack(side="left")
        ttk.Button(barra, text="Editar ativo", command=self.editar_ativo).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(barra, text="Excluir ativo", command=self.excluir_ativo).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(barra, text="Atualizar", command=self.atualizar_ativos).pack(
            side="left", padx=8
        )
        ttk.Button(barra, text="Exportar Excel", command=self.exportar_ativos).pack(
            side="left"
        )
        self.somente_disponiveis = tk.BooleanVar(value=False)
        ttk.Checkbutton(barra, text="Somente disponíveis",
                        variable=self.somente_disponiveis,
                        command=self.atualizar_ativos).pack(side="right")
        self.arvore_ativos = tabela(self.aba_ativos, COLUNAS_ATIVOS)
        self.dados_ativos = []

    def atualizar_ativos(self):
        def buscar():
            linhas = servicos.listar_ativos_com_colaborador(
                self.somente_disponiveis.get()
            )
            preencher(self.arvore_ativos, linhas)
            self.dados_ativos = linhas
            self.status.set(f"{len(linhas)} ativo(s) exibido(s).")
        self.executar(buscar)

    def exportar_ativos(self):
        if not self.dados_ativos:
            messagebox.showinfo("Sem ativos", "Não há ativos na tabela para exportar.",
                                parent=self)
            return
        nome = "relatorio_ativos.xlsx"
        destino = caminho_planilha(nome)
        if destino.exists() and not messagebox.askyesno(
            "Substituir planilha", f"O arquivo {destino.name} já existe. Substituir?",
            parent=self,
        ):
            return

        def salvar():
            resultado = exportar_para_excel(
                self.dados_ativos, [titulo for _, titulo, _ in COLUNAS_ATIVOS], nome
            )
            if resultado is None:
                raise servicos.ErroOperacao("Não foi possível salvar a planilha.")
            self.status.set(f"Planilha salva: {resultado}")
            messagebox.showinfo("Exportação concluída", resultado, parent=self)
        self.executar(salvar)

    def novo_ativo(self):
        janela = Formulario(self, "Cadastrar ativo")
        empresa = janela.campo("Empresa *", combo=("Arklok", "Vivo"))
        serial = janela.campo("Serial number *", formatar=maiusculas)
        patrimonio = janela.campo("Patrimônio", formatar=maiusculas)
        self.condicionar_patrimonio(janela, empresa, patrimonio)
        tipo = janela.campo("Tipo *", combo=("NOTEBOOK", "CELULAR"))
        marca = janela.campo("Marca *", formatar=maiusculas)
        modelo = janela.campo("Modelo *", formatar=maiusculas)
        itens = janela.campo("Itens entregues", formatar=maiusculas)
        chamado = janela.campo("Chamado GLPI *")

        def salvar():
            def acao():
                novo_serial = servicos.cadastrar_ativo(
                    serial.get(), tipo.get(), marca.get(), modelo.get(),
                    itens.get(), chamado.get(), empresa.get(), patrimonio.get()
                )
                janela.destroy()
                self.atualizar_ativos()
                self.status.set(f"Ativo {novo_serial} cadastrado com sucesso.")
            self.executar(acao)
        janela.botoes(salvar, "Cadastrar")

    @staticmethod
    def condicionar_patrimonio(janela, empresa, patrimonio):
        def atualizar(*_args):
            if empresa.get() == "Arklok":
                janela.campos["Patrimônio"].configure(state="normal")
            else:
                patrimonio.set("")
                janela.campos["Patrimônio"].configure(state="disabled")
        empresa.trace_add("write", atualizar)
        atualizar()

    def ativo_selecionado(self):
        selecao = self.arvore_ativos.selection()
        if not selecao:
            messagebox.showinfo("Selecione um ativo", "Selecione um ativo na tabela.",
                                parent=self)
            return None
        return self.arvore_ativos.item(selecao[0], "values")

    def editar_ativo(self):
        registro = self.ativo_selecionado()
        if registro is None:
            return
        (empresa_atual, serial_atual, patrimonio_atual, tipo_atual, marca_atual,
         modelo_atual, status_atual, _colaborador_atual, _setor_atual, itens_atuais,
         chamado_atual) = registro
        janela = Formulario(self, "Editar ativo")
        empresa = janela.campo("Empresa *", empresa_atual, combo=("Arklok", "Vivo"))
        serial = janela.campo("Serial number *", serial_atual, formatar=maiusculas)
        patrimonio = janela.campo("Patrimônio", patrimonio_atual, formatar=maiusculas)
        self.condicionar_patrimonio(janela, empresa, patrimonio)
        tipo = janela.campo("Tipo *", tipo_atual,
                            combo=("NOTEBOOK", "CELULAR"), formatar=maiusculas)
        marca = janela.campo("Marca *", marca_atual, formatar=maiusculas)
        modelo = janela.campo("Modelo *", modelo_atual, formatar=maiusculas)
        status = janela.campo("Status *", status_atual,
                              combo=("disponivel", "emprestado"))
        itens = janela.campo("Itens entregues", itens_atuais, formatar=maiusculas)
        chamado = janela.campo("Chamado GLPI *", chamado_atual)

        def salvar():
            def acao():
                novo_serial = servicos.editar_ativo(
                    serial_atual, empresa.get(), serial.get(), patrimonio.get(),
                    tipo.get(), marca.get(), modelo.get(), status.get(),
                    itens.get(), chamado.get()
                )
                janela.destroy()
                self.atualizar_tudo()
                self.status.set(f"Ativo {novo_serial} atualizado com sucesso.")
                messagebox.showinfo("Ativo atualizado",
                                    f"Dados do ativo {novo_serial} salvos.", parent=self)
            self.executar(acao)
        janela.botoes(salvar, "Salvar alterações")

    def excluir_ativo(self):
        registro = self.ativo_selecionado()
        if registro is None:
            return
        empresa, serial = registro[:2]
        contagem = self.executar(lambda: servicos.contar_emprestimos_ativo(serial))
        if contagem is None:
            return
        total, abertos = contagem
        if abertos:
            messagebox.showinfo(
                "Empréstimo em aberto",
                "Registre a devolução do ativo antes de excluí-lo.", parent=self,
            )
            return
        detalhe = (
            f"\n\nTambém serão apagados {total} empréstimo(s) já devolvido(s) "
            "vinculado(s) a ele. Essa ação não pode ser desfeita."
            if total else "\n\nEssa ação não pode ser desfeita."
        )
        if not messagebox.askyesno(
            "Excluir ativo", f"Excluir definitivamente o ativo {serial} "
            f"({empresa or 'empresa não informada'}) do banco de dados?{detalhe}",
            parent=self,
        ):
            return

        def acao():
            servicos.excluir_ativo(serial, emprestimos_confirmados=total)
            self.atualizar_ativos()
            self.atualizar_emprestimos()
            self.status.set(f"Ativo {serial} excluído.")
            messagebox.showinfo("Ativo excluído",
                                f"O ativo {serial} foi removido do banco.", parent=self)
        self.executar(acao)

    def criar_emprestimos(self):
        barra = ttk.Frame(self.aba_emprestimos)
        barra.pack(fill="x")
        ttk.Button(barra, text="Novo empréstimo",
                   command=self.novo_emprestimo).pack(side="left")
        ttk.Button(barra, text="Registrar devolução",
                   command=self.nova_devolucao).pack(side="left", padx=8)
        ttk.Button(barra, text="Gerar/Reimprimir termo",
                   command=self.reimprimir).pack(side="left")
        ttk.Button(barra, text="Atualizar",
                   command=self.atualizar_emprestimos).pack(side="left", padx=8)
        self.mostrar_historico = tk.BooleanVar(value=False)
        ttk.Checkbutton(barra, text="Incluir devolvidos",
                        variable=self.mostrar_historico,
                        command=self.atualizar_emprestimos).pack(side="right")
        self.arvore_emprestimos = tabela(self.aba_emprestimos, (
            ("id", "ID", 65), ("login", "Login", 100), ("nome", "Colaborador", 190),
            ("serial", "Serial", 135), ("tipo", "Tipo", 90),
            ("marca", "Marca", 110), ("modelo", "Modelo", 140),
            ("saida", "Data saída", 110), ("devolucao", "Devolução", 110),
            ("condicao", "Condição de saída", 210),
        ))
        self.arvore_emprestimos.bind("<Double-1>", lambda _event: self.nova_devolucao())

    def atualizar_emprestimos(self):
        def buscar():
            linhas = servicos.listar_emprestimos(not self.mostrar_historico.get())
            preencher(self.arvore_emprestimos, linhas)
            self.status.set(f"{len(linhas)} empréstimo(s) exibido(s).")
        self.executar(buscar)

    def atualizar_tudo(self):
        self.atualizar_ativos()
        self.atualizar_emprestimos()

    def selecionado(self):
        selecao = self.arvore_emprestimos.selection()
        if not selecao:
            messagebox.showinfo("Selecione um empréstimo",
                                "Selecione um empréstimo na tabela.", parent=self)
            return None
        return self.arvore_emprestimos.item(selecao[0], "values")

    def novo_emprestimo(self):
        def abrir():
            ativos = servicos.listar_ativos(True)
            if not ativos:
                messagebox.showinfo("Sem ativos", "Não há ativos disponíveis.", parent=self)
                return
            janela = Formulario(self, "Registrar empréstimo", 650)
            janela.geometry("650x690")
            login = janela.campo("Login *")
            nome = janela.campo("Nome (novo colaborador)",
                                formatar=iniciais_maiusculas)
            cpf = janela.campo("CPF")
            departamento = janela.campo("Departamento",
                                        formatar=iniciais_maiusculas_funcao)
            cargo = janela.campo("Cargo", formatar=iniciais_maiusculas_funcao)
            campus = janela.campo("Campus")
            opcoes = [f"{a[1]} — {a[0] or 'Sem empresa'} — {a[3]} {a[4]} {a[5]}"
                      for a in ativos]
            serial_por_opcao = dict(zip(opcoes, (a[1] for a in ativos)))
            ativo = janela.campo("Ativo disponível *", combo=opcoes)
            condicao = janela.campo("Condição de saída *")
            observacoes = janela.campo("Observações")
            aviso = tk.StringVar(value="Preencha o login e consulte o colaborador.")
            ttk.Label(janela.corpo, textvariable=aviso, wraplength=570).grid(
                row=janela.linha, column=0, columnspan=3, sticky="w", pady=(5, 0)
            )
            janela.linha += 1

            def consultar():
                def acao():
                    pessoa = servicos.buscar_colaborador(login.get())
                    if pessoa:
                        for variavel, campo in ((nome, "nome"), (cpf, "cpf"),
                                                (departamento, "departamento"),
                                                (cargo, "cargo"), (campus, "campus")):
                            variavel.set(pessoa[campo])
                        aviso.set("Colaborador encontrado. Os dados cadastrados serão usados.")
                    else:
                        for variavel in (nome, cpf, departamento, cargo, campus):
                            variavel.set("")
                        aviso.set("Novo colaborador: preencha nome, CPF, departamento, cargo e campus.")
                self.executar(acao)

            ttk.Button(janela.corpo, text="Buscar login", command=consultar).grid(
                row=1, column=3, padx=(8, 0)
            )

            def salvar():
                def acao():
                    if not ativo.get():
                        raise servicos.ErroOperacao("Selecione um ativo disponível.")
                    dados_pessoa = {
                        "nome": nome.get(), "cpf": cpf.get(),
                        "departamento": departamento.get(), "cargo": cargo.get(),
                        "campus": campus.get(),
                    }
                    serial = serial_por_opcao[ativo.get()]
                    resultado = servicos.registrar_emprestimo(
                        login.get(), serial, condicao.get(), observacoes.get(), dados_pessoa
                    )
                    janela.destroy()
                    self.atualizar_tudo()
                    self.mostrar_resultado("Empréstimo", resultado)
                self.executar(acao)
            janela.botoes(salvar, "Registrar")
        self.executar(abrir)

    def nova_devolucao(self):
        registro = self.selecionado()
        if registro is None:
            return
        if registro[8]:
            messagebox.showinfo("Empréstimo devolvido",
                                "Esse empréstimo já foi devolvido.", parent=self)
            return
        emp_id, login, nome, serial = registro[:4]
        janela = Formulario(self, "Registrar devolução")
        ttk.Label(janela.corpo, text=f"Empréstimo {emp_id} • {nome} ({login})\nAtivo: {serial}",
                  wraplength=490).grid(row=janela.linha, column=0, columnspan=3,
                                       sticky="w", pady=(0, 12))
        janela.linha += 1
        condicao = janela.campo("Condição de retorno *")
        chamado = janela.campo("Chamado GLPI de devolução *")

        def salvar():
            def acao():
                resultado = servicos.registrar_devolucao(emp_id, condicao.get(), chamado.get())
                janela.destroy()
                self.atualizar_tudo()
                self.mostrar_resultado("Devolução", resultado)
            self.executar(acao)
        janela.botoes(salvar, "Confirmar devolução")

    def reimprimir(self):
        registro = self.selecionado()
        if registro is None:
            return
        if not messagebox.askyesno("Gerar termo",
                                   f"Gerar novamente o termo do empréstimo {registro[0]}?\n"
                                   "O arquivo existente desse ativo poderá ser substituído.",
                                   parent=self):
            return
        def acao():
            caminho = servicos.reimprimir_termo(registro[0])
            self.status.set(f"Termo gerado: {caminho}")
            messagebox.showinfo("Termo gerado", caminho, parent=self)
        self.executar(acao)

    def mostrar_resultado(self, operacao, resultado):
        if resultado["termo"]:
            mensagem = f"{operacao} {resultado['id']} registrado(a).\nTermo: {resultado['termo']}"
            self.status.set(f"{operacao} {resultado['id']} registrado(a).")
            messagebox.showinfo("Operação concluída", mensagem, parent=self)
        else:
            mensagem = (f"{operacao} {resultado['id']} registrado(a) no banco, "
                        "mas o termo não foi gerado. Confira o modelo DOCX.")
            self.status.set(mensagem)
            messagebox.showwarning("Documento pendente", mensagem, parent=self)

    def criar_relatorios(self):
        barra = ttk.Frame(self.aba_relatorios)
        barra.pack(fill="x")
        ttk.Label(barra, text="Relatório:").pack(side="left")
        self.tipo_relatorio = tk.StringVar(value="Empréstimos em aberto")
        ttk.Combobox(barra, textvariable=self.tipo_relatorio, state="readonly",
                     values=("Empréstimos em aberto", "Ativos por departamento"),
                     width=29).pack(side="left", padx=8)
        ttk.Button(barra, text="Consultar", command=self.consultar_relatorio).pack(side="left")
        ttk.Button(barra, text="Exportar Excel", command=self.exportar).pack(side="left", padx=8)
        self.area_relatorio = ttk.Frame(self.aba_relatorios)
        self.area_relatorio.pack(fill="both", expand=True)
        self.relatorio_dados = []
        self.relatorio_colunas = []
        self.relatorio_nome = ""
        self.tipo_consultado = None
        self.arvore_relatorio = None

    def consultar_relatorio(self):
        def acao():
            if self.tipo_relatorio.get() == "Empréstimos em aberto":
                dados = servicos.consultar_tempo_emprestado()
                colunas = (
                    ("id", "ID", 65), ("nome", "Colaborador", 185),
                    ("tipo", "Tipo", 100), ("marca", "Marca", 105),
                    ("modelo", "Modelo", 145), ("serial", "Serial", 135),
                    ("saida", "Data saída", 100), ("dias", "Dias emprestado", 125),
                    ("chamado", "Chamado GLPI", 110),
                )
                nome = "relatorio_emprestimos_abertos.xlsx"
            else:
                dados = servicos.consultar_por_departamento()
                colunas = (("departamento", "Departamento", 240),
                           ("total", "Total emprestado", 180))
                nome = "relatorio_departamentos.xlsx"
            for filho in self.area_relatorio.winfo_children():
                filho.destroy()
            self.arvore_relatorio = tabela(self.area_relatorio, colunas)
            preencher(self.arvore_relatorio, dados)
            self.relatorio_dados = dados
            self.relatorio_colunas = [col[1] for col in colunas]
            self.relatorio_nome = nome
            self.tipo_consultado = self.tipo_relatorio.get()
            self.status.set(f"Relatório carregado: {len(dados)} registro(s).")
        self.executar(acao)

    def exportar(self):
        if self.tipo_consultado != self.tipo_relatorio.get():
            messagebox.showinfo("Atualize o relatório",
                                "Clique em Consultar antes de exportar esse relatório.",
                                parent=self)
            return
        if not self.relatorio_dados:
            messagebox.showinfo("Sem dados", "Consulte um relatório com registros primeiro.",
                                parent=self)
            return
        destino = caminho_planilha(self.relatorio_nome)
        if destino.exists() and not messagebox.askyesno(
            "Substituir planilha", f"O arquivo {destino.name} já existe. Substituir?",
            parent=self,
        ):
            return

        def salvar():
            resultado = exportar_para_excel(
                self.relatorio_dados, self.relatorio_colunas, self.relatorio_nome
            )
            if resultado is None:
                raise servicos.ErroOperacao("Não foi possível salvar a planilha.")
            self.status.set(f"Planilha salva: {resultado}")
            messagebox.showinfo("Exportação concluída", resultado, parent=self)
        self.executar(salvar)


def main():
    Aplicacao().mainloop()


if __name__ == "__main__":
    main()
