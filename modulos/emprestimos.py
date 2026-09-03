from datetime import date

from conexao_mysql import get_connection
from modulos.termos import gerar_termo, gerar_termo_devolucao

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
                itens_entregues,
                id_chamado
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
            itens_entregues,
            id_chamado
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
        # 7. GERA O TERMO DE RESPONSABILIDADE
        # =====================================================
        gerar_termo(
            login=login,
            nome=nome,
            cpf=cpf,
            departamento=departamento,
            cargo=cargo,
            campus=campus,
            serial=serial,
            tipo=tipo,
            marca=marca,
            modelo=modelo,
            itens_entregues=itens_entregues,
            id_chamado=id_chamado
        )

        # =====================================================
        # 8. CONFIRMAÇÃO
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
    print("\n===== REGISTRAR DEVOLUÇÃO =====")

    conexao = get_connection()

    if conexao is None:
        print("Erro ao conectar com o banco.")
        return

    cursor = conexao.cursor()

    try:
        # =====================================================
        # 1. LISTA EMPRÉSTIMOS EM ABERTO
        # =====================================================

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

            WHERE e.data_devolucao IS NULL

            ORDER BY e.data_saida
            """
        )

        emprestimos_abertos = cursor.fetchall()

        if not emprestimos_abertos:
            print("\nNão há empréstimos em aberto.")
            return

        print("\n===== EMPRÉSTIMOS EM ABERTO =====")

        for (
            emp_id,
            serial,
            tipo,
            marca,
            modelo,
            login,
            nome,
            data_saida
        ) in emprestimos_abertos:

            print("----------------------------------------")
            print(f"ID empréstimo: {emp_id}")
            print(f"Colaborador:   {nome} ({login})")
            print(f"Ativo:         {tipo} {marca} {modelo}")
            print(f"Serial:        {serial}")
            print(f"Data saída:    {data_saida}")

        print("----------------------------------------")

        # =====================================================
        # 2. ESCOLHE O EMPRÉSTIMO
        # =====================================================

        try:
            id_emprestimo = int(
                input("\nID do empréstimo a devolver: ")
            )

        except ValueError:
            print("\nInforme um ID numérico.")
            return

        # =====================================================
        # 3. BUSCA OS DADOS DO EMPRÉSTIMO
        # =====================================================

        cursor.execute(
            """
            SELECT
                e.id_ativo,
                e.data_saida,
                c.login,
                c.nome,
                c.CPF,
                a.tipo,
                a.marca,
                a.modelo
            FROM emprestimos e

            JOIN colaboradores c
                ON c.login = e.id_colaborador

            JOIN ativos a
                ON a.serial_number = e.id_ativo

            WHERE e.id = %s
              AND e.data_devolucao IS NULL
            """,
            (id_emprestimo,)
        )

        resultado = cursor.fetchone()

        if resultado is None:
            print(
                "\nEmpréstimo não encontrado "
                "ou já foi devolvido."
            )
            return

        (
            serial_number,
            data_saida,
            login,
            nome,
            cpf,
            tipo,
            marca,
            modelo
        ) = resultado

        # =====================================================
        # 4. DADOS DA DEVOLUÇÃO
        # =====================================================

        print("\n--- Dados da devolução ---")

        condicao_retorno = input(
            "Condição de retorno / Observação: "
        ).strip()

        try:
            chamado_devolucao = int(
                input("Chamado GLPI de devolução: ")
            )

        except ValueError:
            print(
                "\nO chamado GLPI deve ser um número inteiro."
            )
            return

        data_devolucao = date.today()

        # =====================================================
        # 5. ATUALIZA O EMPRÉSTIMO
        # =====================================================

        cursor.execute(
            """
            UPDATE emprestimos
            SET
                data_devolucao = %s,
                condicao_retorno = %s,
                chamado_devolucao = %s
            WHERE id = %s
            """,
            (
                data_devolucao,
                condicao_retorno,
                chamado_devolucao,
                id_emprestimo
            )
        )

        # =====================================================
        # 6. LIBERA O ATIVO
        # =====================================================

        cursor.execute(
            """
            UPDATE ativos
            SET at_status = 'disponivel'
            WHERE serial_number = %s
            """,
            (serial_number,)
        )

        conexao.commit()

        # =====================================================
        # 7. GERA O TERMO DE DEVOLUÇÃO
        # =====================================================

        gerar_termo_devolucao(
            login=login,
            nome=nome,
            cpf=cpf,
            serial=serial_number,
            tipo=tipo,
            marca=marca,
            modelo=modelo,
            data_devolucao=data_devolucao,
            condicao_retorno=condicao_retorno,
            chamado_devolucao=chamado_devolucao
        )

        # =====================================================
        # 8. CONFIRMAÇÃO
        # =====================================================

        print("\n========================================")
        print("     DEVOLUÇÃO REGISTRADA COM SUCESSO")
        print("========================================")

        print(f"ID empréstimo:    {id_emprestimo}")
        print(f"Colaborador:      {nome}")
        print(f"CPF:              {cpf}")

        print("\nATIVO")
        print(f"Serial:           {serial_number}")
        print(f"Tipo:             {tipo}")
        print(f"Marca:            {marca}")
        print(f"Modelo:           {modelo}")

        print(f"\nData saída:       {data_saida}")
        print(f"Data devolução:   {data_devolucao}")
        print(f"Condição retorno: {condicao_retorno}")
        print(f"Chamado GLPI:     {chamado_devolucao}")

        print("\nStatus do ativo: disponivel")

        print("========================================")

    except Exception as erro:
        conexao.rollback()
        print(f"\nErro ao registrar devolução: {erro}")

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

            WHERE e.`data_devolucao` IS NULL

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

