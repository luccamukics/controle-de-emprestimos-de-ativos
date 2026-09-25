"""Menu de texto dos ativos; a interface usa as mesmas operações de serviço."""

from modulos import servicos


def cadastrar_ativo():
    print("\n===== Cadastro de ativo =====")
    print("Empresa: 1 - Arklok | 2 - Vivo")
    empresa = {"1": "Arklok", "2": "Vivo"}.get(input("Escolha a empresa: ").strip())
    serial = input("Serial number: ").strip()
    patrimonio = input("Patrimônio (opcional): ").strip() if empresa == "Arklok" else None
    tipo = input("Tipo (notebook/celular): ").strip()
    marca = input("Marca: ").strip()
    modelo = input("Modelo: ").strip()
    itens = input("Itens entregues (carregador, mouse, etc.): ").strip()
    chamado = input("ID do chamado GLPI: ").strip()
    try:
        novo_serial = servicos.cadastrar_ativo(
            serial, tipo, marca, modelo, itens, chamado, empresa, patrimonio
        )
        print(f"\nAtivo cadastrado com sucesso! Serial: {novo_serial}")
    except Exception as erro:
        print(f"Erro ao cadastrar ativo: {erro}")


def _listar(disponiveis):
    try:
        ativos = servicos.listar_ativos(disponiveis)
        if not ativos:
            print("\nNenhum ativo disponível." if disponiveis else "\nNenhum ativo cadastrado.")
            return
        print("\n===== Ativos disponíveis =====" if disponiveis else "\n===== Todos os ativos =====")
        for empresa, serial, patrimonio, tipo, marca, modelo, status, itens, chamado in ativos:
            print(f"\nEmpresa: {empresa or 'Não informada'}\nSerial: {serial}")
            if patrimonio:
                print(f"Patrimônio: {patrimonio}")
            print(f"Tipo: {tipo}\nEquipamento: {marca} {modelo}")
            if not disponiveis:
                print(f"Status: {status}")
            print(f"Itens entregues: {itens}\nChamado GLPI: {chamado}")
            print("-" * 40)
    except Exception as erro:
        print(f"Erro ao listar ativos: {erro}")


def listar_ativos_disponiveis():
    _listar(True)


def listar_todos_ativos():
    _listar(False)
