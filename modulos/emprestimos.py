"""Menu de texto de empréstimos; compartilha as regras com a interface."""

from modulos import servicos


def registrar_emprestimo():
    print("\n===== REGISTRAR EMPRÉSTIMO =====")
    try:
        login = input("Login: ").strip()
        colaborador = servicos.buscar_colaborador(login)
        if colaborador:
            print(f"Colaborador encontrado: {colaborador['nome']}")
        else:
            print("Colaborador não cadastrado. Preencha os dados:")
            colaborador = {
                "nome": input("Nome: ").strip(),
                "cpf": input("CPF: ").strip(),
                "departamento": input("Departamento: ").strip(),
                "cargo": input("Cargo: ").strip(),
                "campus": input("Campus: ").strip(),
            }
        ativos = servicos.listar_ativos(True)
        if not ativos:
            print("Nenhum ativo disponível para empréstimo.")
            return
        print("\n===== ATIVOS DISPONÍVEIS =====")
        for empresa, serial, patrimonio, tipo, marca, modelo, _, itens, _ in ativos:
            print(f"{serial}: {empresa or 'Sem empresa'}, {tipo} {marca} {modelo}"
                  f" — Patrimônio: {patrimonio or '-'} — Itens: {itens}")
        serial = input("Serial number do ativo: ").strip()
        condicao = input("Condição de saída: ").strip()
        observacoes = input("Observações (opcional): ").strip()
        resultado = servicos.registrar_emprestimo(
            login, serial, condicao, observacoes, colaborador
        )
        print(f"\nEmpréstimo registrado com sucesso! ID: {resultado['id']}")
        if resultado["termo"]:
            print(f"Termo: {resultado['termo']}")
        else:
            print("Atenção: empréstimo gravado, mas o termo não foi gerado. Reimprima-o.")
    except Exception as erro:
        print(f"Erro ao registrar empréstimo: {erro}")


def registrar_devolucao():
    print("\n===== REGISTRAR DEVOLUÇÃO =====")
    try:
        emprestimos = servicos.listar_emprestimos(True)
        if not emprestimos:
            print("Não há empréstimos em aberto.")
            return
        for emp_id, login, nome, serial, tipo, marca, modelo, saida, _, _ in emprestimos:
            print(f"{emp_id}: {nome} ({login}), {tipo} {marca} {modelo}, "
                  f"serial {serial}, saída {saida}")
        emp_id = input("ID do empréstimo a devolver: ").strip()
        condicao = input("Condição de retorno / Observação: ").strip()
        chamado = input("Chamado GLPI de devolução: ").strip()
        resultado = servicos.registrar_devolucao(emp_id, condicao, chamado)
        print(f"\nDevolução registrada com sucesso! ID: {resultado['id']}")
        if resultado["termo"]:
            print(f"Termo: {resultado['termo']}")
        else:
            print("Atenção: devolução gravada, mas o termo não foi gerado.")
    except Exception as erro:
        print(f"Erro ao registrar devolução: {erro}")


def listar_emprestimos_ativos():
    try:
        emprestimos = servicos.listar_emprestimos(True)
        if not emprestimos:
            print("\nNão há empréstimos em aberto.")
            return
        print("\n===== EMPRÉSTIMOS EM ABERTO =====")
        for emp_id, login, nome, serial, tipo, marca, modelo, saida, _, condicao in emprestimos:
            print(f"\nID: {emp_id}\nColaborador: {nome} ({login})"
                  f"\nAtivo: {tipo} {marca} {modelo} ({serial})"
                  f"\nData saída: {saida}\nCondição saída: {condicao}")
            print("-" * 40)
    except Exception as erro:
        print(f"Erro ao listar empréstimos: {erro}")
