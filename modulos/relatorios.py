"""
Relatorios do sistema de controle de emprestimos.

Requer:
pip install openpyxl
"""

from openpyxl import Workbook
from conexao_mysql import get_connection


# =========================================================
# RELATORIO - TEMPO EM ABERTO
# =========================================================

def relatorio_tempo_em_aberto():
    """
    Lista todos os emprestimos em aberto,
    do mais antigo para o mais recente.
    """

    conexao = get_connection()

    if conexao is None:
        return []

    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            SELECT
                e.id,
                c.nome,
                a.tipo,
                a.marca,
                a.modelo,
                a.serial_number,
                e.data_saida,
                DATEDIFF(CURDATE(), e.data_saida) AS dias_em_aberto,
                a.id_chamado
            FROM emprestimos e
            JOIN colaboradores c
                ON c.login = e.id_colaborador
            JOIN ativos a
                ON a.serial_number = e.id_ativo
            WHERE e.data_devolucao IS NULL
            ORDER BY dias_em_aberto DESC
            """
        )

        resultados = cursor.fetchall()

        if not resultados:
            print("\nNao ha emprestimos em aberto no momento.")

        else:
            print(
                "\nEmprestimos em aberto "
                "(do mais antigo para o mais recente):"
            )

            for (
                emp_id,
                nome,
                tipo,
                marca,
                modelo,
                serial,
                data_saida,
                dias,
                id_chamado
            ) in resultados:

                print("----------------------------------------")
                print(f"ID emprestimo: {emp_id}")
                print(f"Colaborador:   {nome}")
                print(f"Ativo:         {tipo} {marca} {modelo}")
                print(f"Serial:        {serial}")
                print(f"Data saida:    {data_saida}")
                print(f"Dias aberto:   {dias}")
                print(f"Chamado GLPI:  {id_chamado}")

        return resultados

    except Exception as erro:
        print(f"\nErro ao gerar relatorio: {erro}")
        return []

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# RELATORIO - POR DEPARTAMENTO
# =========================================================

def relatorio_por_departamento():
    """
    Conta quantos ativos estao atualmente emprestados,
    agrupados por departamento.
    """

    conexao = get_connection()

    if conexao is None:
        return []

    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            SELECT
                c.departamento,
                COUNT(*) AS total_emprestados

            FROM emprestimos e

            JOIN colaboradores c
                ON c.login = e.id_colaborador

            WHERE e.data_devolucao IS NULL

            GROUP BY c.departamento

            ORDER BY total_emprestados DESC
            """
        )

        resultados = cursor.fetchall()

        if not resultados:
            print("\nNao ha emprestimos em aberto no momento.")

        else:
            print("\nAtivos emprestados por departamento:")

            for departamento, total in resultados:
                print(f"{departamento}: {total}")

        return resultados

    except Exception as erro:
        print(f"\nErro ao gerar relatorio: {erro}")
        return []

    finally:
        cursor.close()
        conexao.close()


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

        planilha.save(nome_arquivo)

        print(
            f"\nRelatorio exportado com sucesso:"
            f"\n{nome_arquivo}"
        )

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

            dados = relatorio_tempo_em_aberto()

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
                        "Dias em aberto",
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