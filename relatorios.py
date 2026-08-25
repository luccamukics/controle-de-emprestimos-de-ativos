"""
Relatorios do sistema de controle de emprestimos.

Requer: pip install openpyxl
"""

from openpyxl import Workbook
from conexao_mysql import get_connection


def relatorio_tempo_em_aberto():
    """
    Lista todos os emprestimos em aberto, ordenados do mais antigo para o mais
    recente. Como nao ha prazo fixo de devolucao (so devolve quando o
    colaborador solicita ou e desligado), isso serve para dar visibilidade,
    nao para marcar "atraso".
    """
    conexao = get_connection()
    if conexao is None:
        return []

    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT e.id, c.nome, a.tipo, a.marca_modelo, e.data_saida,
               DATEDIFF(CURDATE(), e.data_saida) AS dias_em_aberto
        FROM emprestimos e
        JOIN colaboradores c ON c.login = e.id_colaborador
        JOIN ativos a ON a.id = e.id_ativo
        WHERE e.data_devolucao_real IS NULL
        ORDER BY dias_em_aberto DESC
        """
    )
    resultados = cursor.fetchall()

    cursor.close()
    conexao.close()

    if not resultados:
        print("Nao ha emprestimos em aberto no momento.")
    else:
        print("\nEmprestimos em aberto (do mais antigo para o mais recente):")
        for emp_id, nome, tipo, marca_modelo, data_saida, dias in resultados:
            print(f"  [{emp_id}] {nome} - {tipo} {marca_modelo} - {dias} dias (desde {data_saida})")

    return resultados


def relatorio_por_departamento():
    """Conta quantos ativos estao emprestados agora, agrupado por departamento."""
    conexao = get_connection()
    if conexao is None:
        return []

    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT c.departamento, COUNT(*) AS total_emprestados
        FROM emprestimos e
        JOIN colaboradores c ON c.login = e.id_colaborador
        WHERE e.data_devolucao_real IS NULL
        GROUP BY c.departamento
        ORDER BY total_emprestados DESC
        """
    )
    resultados = cursor.fetchall()

    cursor.close()
    conexao.close()

    if not resultados:
        print("Nao ha emprestimos em aberto no momento.")
    else:
        print("\nAtivos emprestados por departamento:")
        for departamento, total in resultados:
            print(f"  {departamento}: {total}")

    return resultados


def exportar_para_excel(dados, cabecalho, nome_arquivo):
    """
    Recebe uma lista de tuplas (dados) e uma lista de nomes de coluna (cabecalho),
    e gera um arquivo .xlsx com esses dados.
    """
    if not dados:
        print("Nao ha dados para exportar.")
        return

    planilha = Workbook()
    aba = planilha.active
    aba.append(cabecalho)

    for linha in dados:
        aba.append(list(linha))

    planilha.save(nome_arquivo)
    print(f"Relatorio exportado para {nome_arquivo}")


def menu_relatorios():
    print("\n----- Relatorios -----")
    print("1 - Emprestimos em aberto (tempo decorrido)")
    print("2 - Ativos emprestados por departamento")
    print("0 - Voltar")

    opcao = input("Escolha uma opcao: ").strip()

    if opcao == "1":
        dados = relatorio_tempo_em_aberto()
        if dados and input("Exportar para Excel? (s/n): ").strip().lower() == "s":
            cabecalho = ["Id emprestimo", "Colaborador", "Tipo", "Marca/Modelo", "Data saida", "Dias em aberto"]
            exportar_para_excel(dados, cabecalho, "relatorio_emprestimos_abertos.xlsx")

    elif opcao == "2":
        dados = relatorio_por_departamento()
        if dados and input("Exportar para Excel? (s/n): ").strip().lower() == "s":
            cabecalho = ["Departamento", "Total emprestado"]
            exportar_para_excel(dados, cabecalho, "relatorio_departamentos.xlsx")

    elif opcao == "0":
        return
    else:
        print("Opcao invalida.")