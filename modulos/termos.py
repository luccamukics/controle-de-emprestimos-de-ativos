from docxtpl import DocxTemplate
import os
from conexao_mysql import get_connection

def gerar_termo(

    login,
    nome,
    cpf,
    departamento,
    cargo,
    campus,
    serial,
    tipo,
    marca,
    modelo,
    itens_entregues,
    id_chamado
):

    try:
        documento = DocxTemplate(
            "TERMO_RESPONSABILIDADE_MODELO.docx"
        )

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

        pasta = "termos"

        if not os.path.exists(pasta):
            os.makedirs(pasta)

        nome_arquivo = f"TERMO_{login}_{serial}.docx"

        caminho = os.path.join(
            pasta,
            nome_arquivo
        )

        documento.save(caminho)

        print("\nTermo de responsabilidade gerado com sucesso!")
        print(f"Arquivo: {caminho}")

        return caminho

    # EVITAR QUE UM PROBLEMA NO WORD ENCERRE O PROGRAMA INTEIRO

    except Exception as erro:
        print(f"\nErro ao gerar termo: {erro}")
        return None

# =========================================================
# DATA POR EXTENSO
# =========================================================

def data_por_extenso(data):
    meses = [
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro"
    ]

    return (
        f"{data.day} de "
        f"{meses[data.month - 1]} de "
        f"{data.year}"
    )


# =========================================================
# GERAR TERMO DE DEVOLUÇÃO
# =========================================================

def gerar_termo_devolucao(
    login,
    nome,
    cpf,
    serial,
    tipo,
    marca,
    modelo,
    data_devolucao,
    condicao_retorno,
    chamado_devolucao
):
    try:
        documento = DocxTemplate(
            "TERMO_DEVOLUCAO_MODELO.docx"
        )

        dados = {
            "nome": nome,
            "cpf": cpf,
            "login": login,
            "tipo": tipo,
            "marca": marca,
            "modelo": modelo,
            "serial": serial,

            "data_extenso": data_por_extenso(
                data_devolucao
            ),

            "data_devolucao": (
                data_devolucao.strftime("%d/%m/%Y")
            ),

            "observacoes": condicao_retorno,
            "chamado_devolucao": chamado_devolucao
        }

        documento.render(dados)

        pasta = "termos_devolucao"

        if not os.path.exists(pasta):
            os.makedirs(pasta)

        nome_arquivo = (
            f"TERMO_DEVOLUCAO_{login}_{serial}.docx"
        )

        caminho = os.path.join(
            pasta,
            nome_arquivo
        )

        documento.save(caminho)

        print("\nTermo de devolução gerado com sucesso!")
        print(f"Arquivo: {caminho}")

        return caminho

    except Exception as erro:
        print(f"\nErro ao gerar termo de devolução: {erro}")
        return None


def gerar_termo_existente():
    print("\n===== GERAR TERMO DE RESPONSABILIDADE =====")

    conexao = get_connection()

    if conexao is None:
        print("Erro ao conectar com o banco.")
        return

    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            SELECT
                e.id,
                c.login,
                c.nome,
                a.serial_number,
                a.tipo,
                a.marca,
                a.modelo,
                e.data_saida
            FROM emprestimos e

            JOIN colaboradores c
                ON c.login = e.id_colaborador

            JOIN ativos a
                ON a.serial_number = e.id_ativo

            ORDER BY e.id DESC
            """
        )

        emprestimos = cursor.fetchall()

        if not emprestimos:
            print("\nNenhum empréstimo cadastrado.")
            return

        print("\n===== EMPRÉSTIMOS CADASTRADOS =====")

        for (
            emp_id,
            login,
            nome,
            serial,
            tipo,
            marca,
            modelo,
            data_saida
        ) in emprestimos:

            print("----------------------------------------")
            print(f"ID empréstimo: {emp_id}")
            print(f"Colaborador:   {nome} ({login})")
            print(f"Ativo:         {tipo} {marca} {modelo}")
            print(f"Serial:        {serial}")
            print(f"Data saída:    {data_saida}")

        print("----------------------------------------")

        try:
            id_emprestimo = int(
                input("\nID do empréstimo para gerar o termo: ")
            )
        except ValueError:
            print("Informe um ID numérico.")
            return

        cursor.execute(
            """
            SELECT
                c.login,
                c.nome,
                c.CPF,
                c.departamento,
                c.cargo,
                c.campus,
                a.serial_number,
                a.tipo,
                a.marca,
                a.modelo,
                a.itens_entregues,
                a.id_chamado
            FROM emprestimos e

            JOIN colaboradores c
                ON c.login = e.id_colaborador

            JOIN ativos a
                ON a.serial_number = e.id_ativo

            WHERE e.id = %s
            """,
            (id_emprestimo,)
        )

        resultado = cursor.fetchone()

        if resultado is None:
            print("\nEmpréstimo não encontrado.")
            return

        (
            login,
            nome,
            cpf,
            departamento,
            cargo,
            campus,
            serial,
            tipo,
            marca,
            modelo,
            itens_entregues,
            id_chamado
        ) = resultado

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

    except Exception as erro:
        print(f"\nErro ao gerar termo: {erro}")

    finally:
        cursor.close()
        conexao.close()