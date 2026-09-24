from docxtpl import DocxTemplate
import os
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent.parent

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
        documento = DocxTemplate(str(PASTA_PROJETO / "TERMO_RESPONSABILIDADE_MODELO.docx"))

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

        pasta = str(PASTA_PROJETO / "termos_empréstimos")

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
        documento = DocxTemplate(str(PASTA_PROJETO / "TERMO_DEVOLUCAO_MODELO.docx"))

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

        pasta = str(PASTA_PROJETO / "termos_devolucao")

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
    """Reimprime um termo pelo ID no menu de texto."""
    from modulos import servicos

    try:
        emprestimos = servicos.listar_emprestimos(False)
        if not emprestimos:
            print("\nNenhum empréstimo cadastrado.")
            return
        print("\n===== EMPRÉSTIMOS CADASTRADOS =====")
        for emp_id, login, nome, serial, tipo, marca, modelo, saida, _, _ in emprestimos:
            print(f"{emp_id}: {nome} ({login}), {tipo} {marca} {modelo}, "
                  f"serial {serial}, saída {saida}")
        emp_id = input("\nID do empréstimo para gerar o termo: ").strip()
        caminho = servicos.reimprimir_termo(emp_id)
        print(f"Termo gerado: {caminho}")
    except Exception as erro:
        print(f"Erro ao gerar termo: {erro}")
