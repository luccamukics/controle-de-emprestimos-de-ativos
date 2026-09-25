"""
Relatorios do sistema de controle de emprestimos.

Requer:
pip install openpyxl
"""

from openpyxl import Workbook
from pathlib import Path
from modulos import servicos
from caminhos import pasta_aplicacao


PASTA_PLANILHAS = pasta_aplicacao() / "Planilha de Controle"


def caminho_planilha(nome_arquivo):
    """Mantém as exportações na pasta de planilhas do projeto."""
    return PASTA_PLANILHAS / Path(nome_arquivo).name


def relatorio_tempo_emprestado():
    """Exibe empréstimos em aberto, do mais antigo para o mais recente."""
    try:
        resultados = servicos.consultar_tempo_emprestado()
        if not resultados:
            print("\nNão há empréstimos em aberto no momento.")
        else:
            print("\nEmpréstimos em aberto (do mais antigo para o mais recente):")
            for emp_id, nome, tipo, marca, modelo, serial, saida, dias, chamado in resultados:
                print("-" * 40)
                print(f"ID empréstimo: {emp_id}\nColaborador: {nome}")
                print(f"Ativo: {tipo} {marca} {modelo}\nSerial: {serial}")
                print(f"Data saída: {saida}\nDias emprestado: {dias}")
                print(f"Chamado GLPI: {chamado}")
        return resultados
    except Exception as erro:
        print(f"Erro ao gerar relatório: {erro}")
        return []


def relatorio_por_departamento():
    """Exibe a quantidade de ativos emprestados por departamento."""
    try:
        resultados = servicos.consultar_por_departamento()
        if not resultados:
            print("\nNão há empréstimos em aberto no momento.")
        else:
            print("\nAtivos emprestados por departamento:")
            for departamento, total in resultados:
                print(f"{departamento}: {total}")
        return resultados
    except Exception as erro:
        print(f"Erro ao gerar relatório: {erro}")
        return []


# =========================================================
# EXPORTAR PARA EXCEL
# =========================================================

def exportar_para_excel(dados, cabecalho, nome_arquivo):
    """
    Recebe uma lista de tuplas e cria um arquivo Excel.
    """

    if not dados:
        print("\nNao ha dados para exportar.")
        return

    try:
        planilha = Workbook()

        aba = planilha.active

        aba.title = "Relatorio"

        # Cabecalho
        aba.append(cabecalho)

        # Dados
        for linha in dados:
            aba.append(list(linha))

        # Ajusta largura das colunas
        for coluna in aba.columns:

            maior_tamanho = 0

            letra_coluna = coluna[0].column_letter

            for celula in coluna:

                if celula.value is not None:

                    tamanho = len(str(celula.value))

                    if tamanho > maior_tamanho:
                        maior_tamanho = tamanho

            aba.column_dimensions[letra_coluna].width = (
                maior_tamanho + 2
            )

        PASTA_PLANILHAS.mkdir(parents=True, exist_ok=True)
        destino = caminho_planilha(nome_arquivo)
        planilha.save(destino)

        print(
            f"\nRelatorio exportado com sucesso:"
            f"\n{destino}"
        )
        return str(destino)

    except Exception as erro:
        print(f"\nErro ao exportar Excel: {erro}")


# =========================================================
# MENU DE RELATORIOS
# =========================================================

def menu_relatorios():

    while True:

        print("\n==============================")
        print("          RELATORIOS")
        print("==============================")
        print("1 - Emprestimos em aberto")
        print("2 - Ativos por departamento")
        print("0 - Voltar")
        print("==============================")

        opcao = input("Escolha uma opcao: ").strip()

        # -------------------------------------------------
        # RELATORIO 1
        # -------------------------------------------------

        if opcao == "1":

            dados = relatorio_tempo_emprestado()

            if dados:

                exportar = input(
                    "\nExportar para Excel? (s/n): "
                ).strip().lower()

                if exportar == "s":

                    cabecalho = [
                        "ID emprestimo",
                        "Colaborador",
                        "Tipo",
                        "Marca",
                        "Modelo",
                        "Serial",
                        "Data saida",
                        "Dias emprestado",
                        "Chamado GLPI"
                    ]

                    exportar_para_excel(
                        dados,
                        cabecalho,
                        "relatorio_emprestimos_abertos.xlsx"
                    )

        # -------------------------------------------------
        # RELATORIO 2
        # -------------------------------------------------

        elif opcao == "2":

            dados = relatorio_por_departamento()

            if dados:

                exportar = input(
                    "\nExportar para Excel? (s/n): "
                ).strip().lower()

                if exportar == "s":

                    cabecalho = [
                        "Departamento",
                        "Total emprestado"
                    ]

                    exportar_para_excel(
                        dados,
                        cabecalho,
                        "relatorio_departamentos.xlsx"
                    )

        # -------------------------------------------------
        # VOLTAR
        # -------------------------------------------------

        elif opcao == "0":
            return

        else:
            print("\nOpcao invalida.")
