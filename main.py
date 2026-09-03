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
    data_devolucao DATE
    condicao_saida VARCHAR(100)
    condicao_retorno VARCHAR(100)
    observacoes VARCHAR(255)

Sistema criado por Lucca da Silva Mukics
"""

from modulos.relatorios import menu_relatorios
from modulos.termos import gerar_termo_existente
from modulos.ativos import (
    cadastrar_ativo,
    listar_ativos_disponiveis,
    listar_todos_ativos
)
from modulos.emprestimos import (
    registrar_emprestimo,
    registrar_devolucao,
    listar_emprestimos_ativos
)

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
    print("7 - Gerar/Reimprimir termo de responsabilidade")
    print("8 - Relatórios")
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

        elif opcao == "7":
            gerar_termo_existente()

        elif opcao == "8":
            menu_relatorios()

        elif opcao == "0":
            print("\nEncerrando sistema.")
            break

        else:
            print("\nOpção inválida. Tente novamente.")


if __name__ == "__main__":
    main()