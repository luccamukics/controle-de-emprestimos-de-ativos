from docxtpl import DocxTemplate
from conexao_mysql import get_connection


def gerar_termo(login, serial_number):

    conexao = get_connection()

    if conexao is None:
        print("Erro ao conectar com o banco.")
        return

    cursor = conexao.cursor()

    try:
        # Busca os dados do colaborador + ativo
        cursor.execute(
            """
            SELECT
                c.nome,
                c.CPF,
                c.login,
                c.departamento,
                c.cargo,
                c.campus,
                a.tipo,
                a.marca,
                a.modelo,
                a.serial_number,
                a.itens_entregues,
                a.id_chamado
            FROM colaboradores c
            CROSS JOIN ativos a
            WHERE c.login = %s
              AND a.serial_number = %s
            """,
            (login, serial_number)
        )

        resultado = cursor.fetchone()

        if resultado is None:
            print("Colaborador ou ativo não encontrado.")
            return

        (
            nome,
            cpf,
            login,
            departamento,
            cargo,
            campus,
            tipo,
            marca,
            modelo,
            serial,
            itens_entregues,
            id_chamado
        ) = resultado

        # Mostra o que veio do banco
        print("\n===== DADOS ENCONTRADOS =====")
        print(f"Nome: {nome}")
        print(f"CPF: {cpf}")
        print(f"Login: {login}")
        print(f"Departamento: {departamento}")
        print(f"Cargo: {cargo}")
        print(f"Campus: {campus}")
        print(f"Tipo: {tipo}")
        print(f"Marca: {marca}")
        print(f"Modelo: {modelo}")
        print(f"Serial: {serial}")
        print(f"Itens entregues: {itens_entregues}")
        print(f"Chamado GLPI: {id_chamado}")

        # Abre o modelo Word
        documento = DocxTemplate(
            "TERMO_RESPONSABILIDADE_MODELO.docx"
        )

        # Dados que substituirão {{ nome }}, {{ cpf }}, etc.
        dados = {
            "nome": nome,
            "cpf": cpf,
            "login": login,
            "departamento": departamento,
            "cargo": cargo,
            "campus": campus,
            "modelo": f"{tipo} {marca} {modelo}",
            "serial": serial,
            "itens_entregues": itens_entregues,
            "id_chamado": id_chamado
        }

        documento.render(dados)

        # Nome do novo arquivo
        nome_arquivo = f"TERMO_{login}_{serial}.docx"

        documento.save(nome_arquivo)

        print("\n================================")
        print("TERMO GERADO COM SUCESSO!")
        print("================================")
        print(f"Arquivo: {nome_arquivo}")

    except Exception as erro:
        print(f"\nErro ao gerar termo: {erro}")

    finally:
        cursor.close()
        conexao.close()


# ==================================================
# TESTE
# ==================================================

login = input("Login do colaborador: ").strip()
serial = input("Serial number do ativo: ").strip()

gerar_termo(login, serial)