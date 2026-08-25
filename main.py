"""
Sistema de controle de empréstimos de ativos.

Tabelas utilizadas:

colaboradores
    login VARCHAR(10) PRIMARY KEY
    nome VARCHAR(40)
    CPF VARCHAR(15)
    departamento VARCHAR(30)
    cargo VARCHAR(30)
    campus VARCHAR(30)

ativos
    serial_number VARCHAR(15) PRIMARY KEY
    tipo VARCHAR(20)
    modelo VARCHAR(30)
    marca VARCHAR(30)
    at_status VARCHAR(20)
    itens_entregues VARCHAR(30)
    id_chamado INT

emprestimos
    id INT PRIMARY KEY AUTO_INCREMENT
    id_colaborador VARCHAR(10) FOREIGN KEY
    id_ativo VARCHAR(15) FOREIGN KEY
    data_saida DATE
    data_devolução DATE
    condicao_saida VARCHAR(100)
    condicao_retorno VARCHAR(100)
    observacoes VARCHAR(255)
"""

from datetime import date
from conexao_mysql import get_connection


# =========================================================
# CADASTRO DE ATIVO
# =========================================================

def cadastrar_ativo():
    print("\n===== Cadastro de ativo =====")

    serial_number = input("Serial number: ").strip()
    tipo = input("Tipo (notebook/celular): ").strip()
    marca = input("Marca: ").strip()
    modelo = input("Modelo: ").strip()
    itens_entregues = input(
        "Itens entregues (carregador, mouse, etc.): "
    ).strip()

    try:
        id_chamado = int(input("ID do chamado GLPI: "))
    except ValueError:
        print("ID do chamado deve ser um número inteiro.")
        return

    conexao = get_connection()

    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
        # Verifica se já existe ativo com esse serial
        cursor.execute(
            """
            SELECT serial_number
            FROM ativos
            WHERE serial_number = %s
            """,
            (serial_number,),
        )

        if cursor.fetchone():
            print("Já existe um ativo com esse serial number.")
            return

        cursor.execute(
            """
            INSERT INTO ativos
            (
                serial_number,
                tipo,
                modelo,
                marca,
                at_status,
                itens_entregues,
                id_chamado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                serial_number,
                tipo,
                modelo,
                marca,
                "disponivel",
                itens_entregues,
                id_chamado,
            ),
        )

        conexao.commit()

        print("\nAtivo cadastrado com sucesso!")
        print(f"Serial: {serial_number}")

    except Exception as erro:
        conexao.rollback()
        print(f"Erro ao cadastrar ativo: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# LISTAR ATIVOS DISPONÍVEIS
# =========================================================

def listar_ativos_disponiveis():
    conexao = get_connection()

    if conexao is None:
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            SELECT
                serial_number,
                tipo,
                marca,
                modelo,
                itens_entregues,
                id_chamado
            FROM ativos
            WHERE at_status = 'disponivel'
            ORDER BY tipo, marca, modelo
            """
        )

        ativos = cursor.fetchall()

        if not ativos:
            print("\nNenhum ativo disponível no momento.")
            return

        print("\n===== Ativos disponíveis =====")

        for (
            serial,
            tipo,
            marca,
            modelo,
            itens,
            chamado,
        ) in ativos:

            print(
                f"\nSerial: {serial}"
                f"\nTipo: {tipo}"
                f"\nEquipamento: {marca} {modelo}"
                f"\nItens: {itens}"
                f"\nChamado GLPI: {chamado}"
            )

            print("-" * 40)

    except Exception as erro:
        print(f"Erro ao listar ativos: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# REGISTRAR EMPRÉSTIMO
# =========================================================

def registrar_emprestimo():
    print("\n===== REGISTRAR EMPRÉSTIMO =====")

    conexao = get_connection()

    if conexao is None:
        print("Erro ao conectar com o banco.")
        return

    cursor = conexao.cursor()

    try:
        # =====================================================
        # 1. DADOS DO COLABORADOR
        # =====================================================

        print("\n--- Dados do colaborador ---")

        login = input("Login: ").strip()

        # Verifica se o colaborador já está cadastrado
        cursor.execute(
            """
            SELECT nome, CPF, departamento, cargo, campus
            FROM colaboradores
            WHERE login = %s
            """,
            (login,)
        )

        colaborador = cursor.fetchone()

        if colaborador:
            nome, cpf, departamento, cargo, campus = colaborador

            print("\nColaborador encontrado!")
            print(f"Nome:         {nome}")
            print(f"CPF:          {cpf}")
            print(f"Departamento: {departamento}")
            print(f"Cargo:        {cargo}")
            print(f"Campus:       {campus}")

        else:
            print("\nColaborador não cadastrado.")
            print("Preencha os dados abaixo:")

            nome = input("Nome: ").strip()
            cpf = input("CPF: ").strip()
            departamento = input("Departamento: ").strip()
            cargo = input("Cargo: ").strip()
            campus = input("Campus: ").strip()

            # Cadastra o colaborador
            cursor.execute(
                """
                INSERT INTO colaboradores (
                    login,
                    nome,
                    CPF,
                    departamento,
                    cargo,
                    campus
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    login,
                    nome,
                    cpf,
                    departamento,
                    cargo,
                    campus
                )
            )

            print("\nColaborador cadastrado.")

        # =====================================================
        # 2. MOSTRA ATIVOS DISPONÍVEIS
        # =====================================================

        cursor.execute(
            """
            SELECT
                serial_number,
                tipo,
                marca,
                modelo,
                itens_entregues
            FROM ativos
            WHERE at_status = 'disponivel'
            ORDER BY tipo, marca, modelo
            """
        )

        ativos = cursor.fetchall()

        if not ativos:
            print("\nNenhum ativo disponível para empréstimo.")

            # Desfaz também o cadastro do colaborador,
            # caso ele tenha acabado de ser inserido.
            conexao.rollback()
            return

        print("\n===== ATIVOS DISPONÍVEIS =====")

        for serial, tipo, marca, modelo, itens in ativos:
            print("----------------------------------------")
            print(f"Serial: {serial}")
            print(f"Tipo:   {tipo}")
            print(f"Marca:  {marca}")
            print(f"Modelo: {modelo}")
            print(f"Itens:  {itens}")

        print("----------------------------------------")

        # =====================================================
        # 3. ESCOLHA DO ATIVO
        # =====================================================

        serial_number = input(
            "\nSerial number do ativo: "
        ).strip()

        cursor.execute(
            """
            SELECT
                serial_number,
                tipo,
                marca,
                modelo,
                at_status,
                itens_entregues
            FROM ativos
            WHERE serial_number = %s
            """,
            (serial_number,)
        )

        ativo = cursor.fetchone()

        if ativo is None:
            print("\nAtivo não encontrado.")
            conexao.rollback()
            return

        (
            serial,
            tipo,
            marca,
            modelo,
            status,
            itens_entregues
        ) = ativo

        if status != "disponivel":
            print("\nEste ativo não está disponível.")
            print(f"Status atual: {status}")
            conexao.rollback()
            return

        # =====================================================
        # 4. DADOS DO EMPRÉSTIMO
        # =====================================================

        print("\n--- Dados do empréstimo ---")

        condicao_saida = input(
            "Condição de saída: "
        ).strip()

        observacoes = input(
            "Observações (opcional): "
        ).strip()

        # =====================================================
        # 5. CADASTRA O EMPRÉSTIMO
        # =====================================================

        cursor.execute(
            """
            INSERT INTO emprestimos (
                id_colaborador,
                id_ativo,
                data_saida,
                condicao_saida,
                observacoes
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                login,
                serial_number,
                date.today(),
                condicao_saida,
                observacoes
            )
        )

        id_emprestimo = cursor.lastrowid

        # =====================================================
        # 6. ALTERA STATUS DO ATIVO
        # =====================================================

        cursor.execute(
            """
            UPDATE ativos
            SET at_status = 'emprestado'
            WHERE serial_number = %s
            """,
            (serial_number,)
        )

        conexao.commit()

        # =====================================================
        # 7. CONFIRMAÇÃO
        # =====================================================

        print("\n========================================")
        print("   EMPRÉSTIMO REGISTRADO COM SUCESSO")
        print("========================================")

        print(f"ID empréstimo: {id_emprestimo}")

        print("\nCOLABORADOR")
        print(f"Login:        {login}")
        print(f"Nome:         {nome}")
        print(f"CPF:          {cpf}")
        print(f"Departamento: {departamento}")
        print(f"Cargo:        {cargo}")
        print(f"Campus:       {campus}")

        print("\nATIVO")
        print(f"Serial:       {serial}")
        print(f"Tipo:         {tipo}")
        print(f"Marca:        {marca}")
        print(f"Modelo:       {modelo}")
        print(f"Itens:        {itens_entregues}")

        print(f"\nData saída:   {date.today()}")
        print(f"Condição:     {condicao_saida}")

        print("========================================")

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao registrar empréstimo: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# REGISTRAR DEVOLUÇÃO
# =========================================================

def registrar_devolucao():
    conexao = get_connection()

    if conexao is None:
        return

    cursor = conexao.cursor()

    try:

        # -------------------------------------------------
        # Lista empréstimos ainda não devolvidos
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                e.id,
                e.id_ativo,
                a.tipo,
                a.marca,
                a.modelo,
                e.id_colaborador,
                c.nome,
                e.data_saida
            FROM emprestimos e

            JOIN ativos a
                ON a.serial_number = e.id_ativo

            JOIN colaboradores c
                ON c.login = e.id_colaborador

            WHERE e.`data_devolução` IS NULL

            ORDER BY e.data_saida
            """
        )

        emprestimos_abertos = cursor.fetchall()

        if not emprestimos_abertos:
            print("\nNão há empréstimos em aberto.")
            return

        print("\n===== Empréstimos em aberto =====")

        for (
            emp_id,
            serial,
            tipo,
            marca,
            modelo,
            login,
            nome,
            data_saida,
        ) in emprestimos_abertos:

            print(
                f"\nID empréstimo: {emp_id}"
                f"\nAtivo: {tipo} - {marca} {modelo}"
                f"\nSerial: {serial}"
                f"\nColaborador: {nome} ({login})"
                f"\nData saída: {data_saida}"
            )

            print("-" * 40)

        # -------------------------------------------------
        # Escolha do empréstimo
        # -------------------------------------------------

        try:
            id_emprestimo = int(
                input("\nID do empréstimo a devolver: ")
            )
        except ValueError:
            print("Informe um ID numérico.")
            return

        condicao_retorno = input(
            "Condição de retorno: "
        ).strip()

        # -------------------------------------------------
        # Busca empréstimo
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT id_ativo
            FROM emprestimos
            WHERE id = %s
              AND `data_devolução` IS NULL
            """,
            (id_emprestimo,),
        )

        resultado = cursor.fetchone()

        if resultado is None:
            print(
                "Empréstimo não encontrado "
                "ou já foi devolvido."
            )
            return

        serial_number = resultado[0]

        # -------------------------------------------------
        # Registra devolução
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE emprestimos
            SET
                `data_devolução` = %s,
                condicao_retorno = %s
            WHERE id = %s
            """,
            (
                date.today(),
                condicao_retorno,
                id_emprestimo,
            ),
        )

        # -------------------------------------------------
        # Libera ativo novamente
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE ativos
            SET at_status = 'disponivel'
            WHERE serial_number = %s
            """,
            (serial_number,),
        )

        conexao.commit()

        print("\nDevolução registrada com sucesso!")
        print(f"Ativo {serial_number} está disponível novamente.")

    except Exception as erro:
        conexao.rollback()
        print(f"Erro ao registrar devolução: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# LISTAR EMPRÉSTIMOS EM ABERTO
# =========================================================

def listar_emprestimos_ativos():
    conexao = get_connection()

    if conexao is None:
        return

    cursor = conexao.cursor()

    try:

        cursor.execute(
            """
            SELECT
                e.id,
                c.nome,
                c.login,
                a.tipo,
                a.marca,
                a.modelo,
                a.serial_number,
                e.data_saida,
                e.condicao_saida
            FROM emprestimos e

            JOIN colaboradores c
                ON c.login = e.id_colaborador

            JOIN ativos a
                ON a.serial_number = e.id_ativo

            WHERE e.`data_devolução` IS NULL

            ORDER BY e.data_saida
            """
        )

        emprestimos = cursor.fetchall()

        if not emprestimos:
            print("\nNão há empréstimos em aberto.")
            return

        print("\n===== Empréstimos em aberto =====")

        for (
            emp_id,
            nome,
            login,
            tipo,
            marca,
            modelo,
            serial,
            data_saida,
            condicao_saida,
        ) in emprestimos:

            print(
                f"\nID: {emp_id}"
                f"\nColaborador: {nome} ({login})"
                f"\nAtivo: {tipo} - {marca} {modelo}"
                f"\nSerial: {serial}"
                f"\nData saída: {data_saida}"
                f"\nCondição saída: {condicao_saida}"
            )

            print("-" * 40)

    except Exception as erro:
        print(f"Erro ao listar empréstimos: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# LISTAR TODOS OS ATIVOS
# =========================================================

def listar_todos_ativos():
    conexao = get_connection()

    if conexao is None:
        return

    cursor = conexao.cursor()

    try:

        cursor.execute(
            """
            SELECT
                serial_number,
                tipo,
                marca,
                modelo,
                at_status,
                itens_entregues,
                id_chamado
            FROM ativos
            ORDER BY tipo, marca, modelo
            """
        )

        ativos = cursor.fetchall()

        if not ativos:
            print("\nNenhum ativo cadastrado.")
            return

        print("\n===== Todos os ativos =====")

        for (
            serial,
            tipo,
            marca,
            modelo,
            status,
            itens,
            chamado,
        ) in ativos:

            print(
                f"\nSerial: {serial}"
                f"\nTipo: {tipo}"
                f"\nEquipamento: {marca} {modelo}"
                f"\nStatus: {status}"
                f"\nItens entregues: {itens}"
                f"\nChamado GLPI: {chamado}"
            )

            print("-" * 40)

    except Exception as erro:
        print(f"Erro ao listar ativos: {erro}")

    finally:
        cursor.close()
        conexao.close()


# =========================================================
# MENU
# =========================================================

def exibir_menu():
    print("\n===================================")
    print("     CONTROLE DE EMPRÉSTIMOS")
    print("===================================")
    print("1 - Cadastrar ativo")
    print("2 - Registrar empréstimo")
    print("3 - Registrar devolução")
    print("4 - Listar empréstimos em aberto")
    print("5 - Listar ativos disponíveis")
    print("6 - Listar todos os ativos")
    print("0 - Sair")
    print("===================================")


# =========================================================
# MAIN
# =========================================================

def main():

    while True:

        exibir_menu()

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_ativo()

        elif opcao == "2":
            registrar_emprestimo()

        elif opcao == "3":
            registrar_devolucao()

        elif opcao == "4":
            listar_emprestimos_ativos()

        elif opcao == "5":
            listar_ativos_disponiveis()

        elif opcao == "6":
            listar_todos_ativos()

        elif opcao == "0":
            print("\nEncerrando sistema.")
            break

        else:
            print("\nOpção inválida. Tente novamente.")


if __name__ == "__main__":
    main()