"""
Sistema de controle de emprestimos de ativos (notebooks/celulares).

Pressupoe as tabelas:
  colaboradores (login VARCHAR(10) PK, nome, CPF, departamento, cargo, campus)
  ativos        (id INT PK, tipo, marca_modelo, numero_serie, status)
  emprestimos   (id INT PK, id_colaborador VARCHAR(10) FK, id_ativo INT FK,
                 data_saida, data_devolucao_real, condicao_saida,
                 condicao_retorno, observacoes)

Ajuste os nomes de coluna aqui se a sua tabela tiver diferencas.
"""

from datetime import date
from conexao_mysql import get_connection


def cadastrar_ativo():
    tipo = input("Tipo (notebook/celular): ").strip()
    marca_modelo = input("Marca/modelo: ").strip()
    numero_serie = input("Numero de serie: ").strip()

    conexao = get_connection()
    if conexao is None:
        return

    cursor = conexao.cursor()
    cursor.execute(
        """
        INSERT INTO ativos (tipo, marca_modelo, numero_serie, status)
        VALUES (%s, %s, %s, 'disponivel')
        """,
        (tipo, marca_modelo, numero_serie),
    )
    conexao.commit()
    print(f"Ativo cadastrado com id {cursor.lastrowid}.")

    cursor.close()
    conexao.close()


def listar_ativos_disponiveis():
    conexao = get_connection()
    if conexao is None:
        return

    cursor = conexao.cursor()
    cursor.execute(
        "SELECT id, tipo, marca_modelo, numero_serie FROM ativos WHERE status = 'disponivel'"
    )
    ativos = cursor.fetchall()

    if not ativos:
        print("Nenhum ativo disponivel no momento.")
    else:
        print("\nAtivos disponiveis:")
        for ativo_id, tipo, marca_modelo, numero_serie in ativos:
            print(f"  [{ativo_id}] {tipo} - {marca_modelo} (serie {numero_serie})")

    cursor.close()
    conexao.close()


def registrar_emprestimo():
    listar_ativos_disponiveis()

    id_ativo = input("\nId do ativo a emprestar: ").strip()
    login_colaborador = input("Login do colaborador: ").strip()
    condicao_saida = input("Condicao de saida (ex: sem avarias): ").strip()
    observacoes = input("Observacoes (opcional): ").strip()

    conexao = get_connection()
    if conexao is None:
        return

    cursor = conexao.cursor()

    # confere se o ativo esta realmente disponivel antes de emprestar
    cursor.execute("SELECT status FROM ativos WHERE id = %s", (id_ativo,))
    resultado = cursor.fetchone()

    if resultado is None:
        print("Ativo nao encontrado.")
    elif resultado[0] != "disponivel":
        print("Este ativo ja esta emprestado ou em manutencao.")
    else:
        cursor.execute(
            """
            INSERT INTO emprestimos
                (id_colaborador, id_ativo, data_saida, condicao_saida, observacoes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (login_colaborador, id_ativo, date.today(), condicao_saida, observacoes),
        )
        cursor.execute(
            "UPDATE ativos SET status = 'emprestado' WHERE id = %s", (id_ativo,)
        )
        conexao.commit()
        print(f"Emprestimo registrado com id {cursor.lastrowid}.")

    cursor.close()
    conexao.close()


def registrar_devolucao():
    conexao = get_connection()
    if conexao is None:
        return

    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT e.id, e.id_ativo, a.tipo, a.marca_modelo, e.id_colaborador
        FROM emprestimos e
        JOIN ativos a ON a.id = e.id_ativo
        WHERE e.data_devolucao_real IS NULL
        """
    )
    emprestimos_abertos = cursor.fetchall()

    if not emprestimos_abertos:
        print("Nao ha emprestimos em aberto.")
        cursor.close()
        conexao.close()
        return

    print("\nEmprestimos em aberto:")
    for emp_id, id_ativo, tipo, marca_modelo, login in emprestimos_abertos:
        print(f"  [{emp_id}] {tipo} {marca_modelo} - colaborador {login}")

    id_emprestimo = input("\nId do emprestimo a devolver: ").strip()
    condicao_retorno = input("Condicao de retorno (ex: sem avarias): ").strip()

    cursor.execute(
        "SELECT id_ativo FROM emprestimos WHERE id = %s", (id_emprestimo,)
    )
    resultado = cursor.fetchone()

    if resultado is None:
        print("Emprestimo nao encontrado.")
    else:
        id_ativo = resultado[0]
        cursor.execute(
            """
            UPDATE emprestimos
            SET data_devolucao_real = %s, condicao_retorno = %s
            WHERE id = %s
            """,
            (date.today(), condicao_retorno, id_emprestimo),
        )
        cursor.execute(
            "UPDATE ativos SET status = 'disponivel' WHERE id = %s", (id_ativo,)
        )
        conexao.commit()
        print("Devolucao registrada com sucesso.")

    cursor.close()
    conexao.close()


def listar_emprestimos_ativos():
    conexao = get_connection()
    if conexao is None:
        return

    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT e.id, c.nome, a.tipo, a.marca_modelo, e.data_saida
        FROM emprestimos e
        JOIN colaboradores c ON c.login = e.id_colaborador
        JOIN ativos a ON a.id = e.id_ativo
        WHERE e.data_devolucao_real IS NULL
        """
    )
    emprestimos = cursor.fetchall()

    if not emprestimos:
        print("Nao ha emprestimos em aberto.")
    else:
        print("\nEmprestimos em aberto:")
        for emp_id, nome, tipo, marca_modelo, data_saida in emprestimos:
            print(f"  [{emp_id}] {nome} - {tipo} {marca_modelo} (desde {data_saida})")

    cursor.close()
    conexao.close()


def exibir_menu():
    print("\n===== Controle de emprestimos =====")
    print("1 - Cadastrar ativo")
    print("2 - Registrar emprestimo")
    print("3 - Registrar devolucao")
    print("4 - Listar emprestimos em aberto")
    print("0 - Sair")


def main():
    while True:
        exibir_menu()
        opcao = input("Escolha uma opcao: ").strip()

        if opcao == "1":
            cadastrar_ativo()
        elif opcao == "2":
            registrar_emprestimo()
        elif opcao == "3":
            registrar_devolucao()
        elif opcao == "4":
            listar_emprestimos_ativos()
        elif opcao == "0":
            print("Encerrando.")
            break
        else:
            print("Opcao invalida, tente novamente.")


if __name__ == "__main__":
    main()