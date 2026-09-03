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