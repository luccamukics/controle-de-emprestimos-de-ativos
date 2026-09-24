"""Operações do sistema usadas pela interface e pelo menu de texto."""

from datetime import date

from conexao_mysql import get_connection
from modulos.termos import gerar_termo, gerar_termo_devolucao


class ErroOperacao(Exception):
    """Erro de validação ou de regra de negócio exibível ao usuário."""


def _texto(valor, nome, limite, obrigatorio=True):
    texto = str(valor or "").strip()
    if obrigatorio and not texto:
        raise ErroOperacao(f"Informe {nome}.")
    if len(texto) > limite:
        raise ErroOperacao(f"{nome} deve ter no máximo {limite} caracteres.")
    return texto


def _numero_positivo(valor, nome):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ErroOperacao(f"{nome} deve ser um número inteiro.") from None
    if numero <= 0:
        raise ErroOperacao(f"{nome} deve ser maior que zero.")
    return numero


def _conexao():
    conexao = get_connection()
    if conexao is None:
        raise ErroOperacao("Não foi possível conectar ao MySQL. Confira o arquivo .env.")
    return conexao


def _consultar(sql, parametros=()):
    conexao = _conexao()
    try:
        cursor = conexao.cursor()
        try:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        conexao.close()


def listar_ativos(disponiveis=False):
    filtro = "WHERE at_status = 'disponivel'" if disponiveis else ""
    return _consultar(
        f"""SELECT empresa, serial_number, patrimonio, tipo, marca, modelo,
                   at_status, itens_entregues, id_chamado
            FROM ativos {filtro} ORDER BY tipo, marca, modelo"""
    )


def _empresa_patrimonio(empresa, patrimonio):
    if empresa not in ("Arklok", "Vivo"):
        raise ErroOperacao("Selecione Arklok ou Vivo no campo Empresa.")
    patrimonio = _texto(patrimonio, "o patrimônio", 20, False) or None
    if empresa == "Vivo" and patrimonio:
        raise ErroOperacao("Patrimônio só pode ser preenchido para ativos da Arklok.")
    return patrimonio


def buscar_colaborador(login):
    login = _texto(login, "o login", 10)
    linhas = _consultar(
        "SELECT login, nome, CPF, departamento, cargo, campus "
        "FROM colaboradores WHERE login = %s", (login,)
    )
    return dict(zip(("login", "nome", "cpf", "departamento", "cargo", "campus"),
                    linhas[0])) if linhas else None


def listar_emprestimos(em_aberto=True):
    filtro = "WHERE e.data_devolucao IS NULL" if em_aberto else ""
    return _consultar(
        f"""SELECT e.id, c.login, c.nome, a.serial_number, a.tipo, a.marca,
                   a.modelo, e.data_saida, e.data_devolucao, e.condicao_saida
            FROM emprestimos e
            JOIN colaboradores c ON c.login = e.id_colaborador
            JOIN ativos a ON a.serial_number = e.id_ativo
            {filtro} ORDER BY e.id DESC"""
    )


def consultar_tempo_emprestado():
    return _consultar(
        """SELECT e.id, c.nome, a.tipo, a.marca, a.modelo,
                  a.serial_number, e.data_saida,
                  DATEDIFF(CURDATE(), e.data_saida) AS dias_emprestado,
                  a.id_chamado
           FROM emprestimos e
           JOIN colaboradores c ON c.login = e.id_colaborador
           JOIN ativos a ON a.serial_number = e.id_ativo
           WHERE e.data_devolucao IS NULL
           ORDER BY dias_emprestado DESC"""
    )


def consultar_por_departamento():
    return _consultar(
        """SELECT c.departamento, COUNT(*) AS total_emprestados
           FROM emprestimos e
           JOIN colaboradores c ON c.login = e.id_colaborador
           WHERE e.data_devolucao IS NULL
           GROUP BY c.departamento
           ORDER BY total_emprestados DESC"""
    )


def cadastrar_ativo(serial, tipo, marca, modelo, itens_entregues, id_chamado,
                   empresa, patrimonio=None):
    patrimonio = _empresa_patrimonio(empresa, patrimonio)
    serial = _texto(serial, "o serial", 15)
    tipo = _texto(tipo, "o tipo", 20)
    marca = _texto(marca, "a marca", 30)
    modelo = _texto(modelo, "o modelo", 30)
    itens_entregues = _texto(itens_entregues, "os itens entregues", 30, False)
    id_chamado = _numero_positivo(id_chamado, "O chamado GLPI")
    conexao = _conexao()
    try:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT serial_number FROM ativos WHERE serial_number = %s", (serial,))
            if cursor.fetchone():
                raise ErroOperacao("Já existe um ativo com esse serial.")
            cursor.execute(
                """INSERT INTO ativos (empresa, serial_number, patrimonio, tipo,
                       modelo, marca, at_status, itens_entregues, id_chamado)
                   VALUES (%s, %s, %s, %s, %s, %s, 'disponivel', %s, %s)""",
                (empresa, serial, patrimonio, tipo, modelo, marca,
                 itens_entregues, id_chamado),
            )
            conexao.commit()
            return serial
        except Exception:
            conexao.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conexao.close()


def editar_ativo(serial_original, empresa, serial, patrimonio, tipo, marca,
                modelo, status, itens_entregues, id_chamado):
    serial_original = _texto(serial_original, "o serial original", 15)
    patrimonio = _empresa_patrimonio(empresa, patrimonio)
    serial = _texto(serial, "o serial", 15)
    tipo = _texto(tipo, "o tipo", 20)
    marca = _texto(marca, "a marca", 30)
    modelo = _texto(modelo, "o modelo", 30)
    itens_entregues = _texto(itens_entregues, "os itens entregues", 30, False)
    id_chamado = _numero_positivo(id_chamado, "O chamado GLPI")
    if status not in ("disponivel", "emprestado"):
        raise ErroOperacao("Status inválido.")

    conexao = _conexao()
    try:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "SELECT serial_number, patrimonio FROM ativos "
                "WHERE serial_number = %s FOR UPDATE",
                (serial_original,),
            )
            anterior = cursor.fetchone()
            if anterior is None:
                raise ErroOperacao("Ativo não encontrado. Atualize a lista.")
            cursor.execute(
                "SELECT COUNT(*) FROM emprestimos "
                "WHERE id_ativo = %s AND data_devolucao IS NULL", (serial_original,)
            )
            aberto = cursor.fetchone()[0] > 0
            if status != ("emprestado" if aberto else "disponivel"):
                raise ErroOperacao("O status deve acompanhar os empréstimos em aberto do ativo.")
            if patrimonio:
                cursor.execute(
                    "SELECT serial_number FROM ativos "
                    "WHERE patrimonio = %s AND serial_number <> %s",
                    (patrimonio, serial_original),
                )
                if cursor.fetchone():
                    raise ErroOperacao("Já existe um ativo com esse patrimônio.")
            dados = (empresa, patrimonio, tipo, marca, modelo, status,
                     itens_entregues, id_chamado)
            if serial == serial_original:
                cursor.execute(
                    """UPDATE ativos SET empresa = %s, patrimonio = %s, tipo = %s,
                              marca = %s, modelo = %s, at_status = %s,
                              itens_entregues = %s, id_chamado = %s
                       WHERE serial_number = %s""", (*dados, serial_original),
                )
            else:
                cursor.execute("SELECT serial_number FROM ativos WHERE serial_number = %s",
                               (serial,))
                if cursor.fetchone():
                    raise ErroOperacao("Já existe um ativo com o novo serial.")
                # Cria a nova chave, transfere o histórico e só então remove a antiga.
                # Isso funciona mesmo quando a FK de empréstimos não tem ON UPDATE CASCADE.
                if patrimonio and patrimonio == anterior[1]:
                    cursor.execute(
                        "UPDATE ativos SET patrimonio = NULL WHERE serial_number = %s",
                        (serial_original,),
                    )
                cursor.execute(
                    """INSERT INTO ativos (serial_number, empresa, patrimonio,
                              tipo, marca, modelo, at_status, itens_entregues, id_chamado)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (serial, *dados),
                )
                cursor.execute("UPDATE emprestimos SET id_ativo = %s WHERE id_ativo = %s",
                               (serial, serial_original))
                cursor.execute("DELETE FROM ativos WHERE serial_number = %s",
                               (serial_original,))
            conexao.commit()
            return serial
        except Exception:
            conexao.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conexao.close()


def contar_emprestimos_ativo(serial):
    """Retorna (total, em_aberto) para orientar a exclusão."""
    serial = _texto(serial, "o serial", 15)
    linhas = _consultar(
        """SELECT COUNT(*), COALESCE(SUM(data_devolucao IS NULL), 0)
           FROM emprestimos WHERE id_ativo = %s""", (serial,)
    )
    return linhas[0]


def excluir_ativo(serial, emprestimos_confirmados=0):
    """Remove o ativo e, se confirmados, seus empréstimos já encerrados."""
    serial = _texto(serial, "o serial", 15)
    if not isinstance(emprestimos_confirmados, int) or emprestimos_confirmados < 0:
        raise ErroOperacao("Quantidade de empréstimos inválida.")
    conexao = _conexao()
    try:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "SELECT serial_number FROM ativos WHERE serial_number = %s FOR UPDATE",
                (serial,),
            )
            if cursor.fetchone() is None:
                raise ErroOperacao("Ativo não encontrado. Atualize a lista.")
            cursor.execute(
                """SELECT COUNT(*), COALESCE(SUM(data_devolucao IS NULL), 0)
                   FROM emprestimos WHERE id_ativo = %s""", (serial,)
            )
            total, abertos = cursor.fetchone()
            if abertos:
                raise ErroOperacao(
                    "Este ativo possui empréstimo em aberto. Registre a devolução antes de excluí-lo."
                )
            if total != emprestimos_confirmados:
                raise ErroOperacao(
                    "O histórico de empréstimos mudou. Atualize a lista e confirme novamente."
                )
            if total:
                cursor.execute("DELETE FROM emprestimos WHERE id_ativo = %s", (serial,))
                if cursor.rowcount != total:
                    raise ErroOperacao("Não foi possível apagar todo o histórico. Nada foi excluído.")
            cursor.execute("DELETE FROM ativos WHERE serial_number = %s", (serial,))
            if cursor.rowcount != 1:
                raise ErroOperacao("O ativo não foi excluído. Atualize a lista.")
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conexao.close()


def registrar_emprestimo(login, serial, condicao_saida, observacoes="", colaborador=None):
    login = _texto(login, "o login", 10)
    serial = _texto(serial, "o serial", 15)
    condicao_saida = _texto(condicao_saida, "a condição de saída", 100)
    observacoes = _texto(observacoes, "as observações", 255, False)
    conexao = _conexao()
    try:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "SELECT nome, CPF, departamento, cargo, campus FROM colaboradores "
                "WHERE login = %s FOR UPDATE", (login,)
            )
            pessoa = cursor.fetchone()
            if pessoa is None:
                if colaborador is None:
                    raise ErroOperacao("Colaborador não cadastrado. Preencha os dados dele.")
                pessoa = (
                    _texto(colaborador.get("nome"), "o nome", 40),
                    _texto(colaborador.get("cpf"), "o CPF", 15),
                    _texto(colaborador.get("departamento"), "o departamento", 30),
                    _texto(colaborador.get("cargo"), "o cargo", 30),
                    _texto(colaborador.get("campus"), "o campus", 30),
                )
                cursor.execute(
                    """INSERT INTO colaboradores
                       (login, nome, CPF, departamento, cargo, campus)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (login, *pessoa),
                )
            nome, cpf, departamento, cargo, campus = pessoa
            cursor.execute(
                """SELECT tipo, marca, modelo, at_status, itens_entregues, id_chamado
                   FROM ativos WHERE serial_number = %s FOR UPDATE""", (serial,)
            )
            ativo = cursor.fetchone()
            if ativo is None:
                raise ErroOperacao("Ativo não encontrado.")
            tipo, marca, modelo, status, itens, chamado = ativo
            if status != "disponivel":
                raise ErroOperacao("Este ativo não está disponível.")
            cursor.execute(
                "SELECT id FROM emprestimos WHERE id_ativo = %s "
                "AND data_devolucao IS NULL LIMIT 1", (serial,)
            )
            if cursor.fetchone():
                raise ErroOperacao("Este ativo já possui um empréstimo em aberto.")
            cursor.execute(
                """INSERT INTO emprestimos
                   (id_colaborador, id_ativo, data_saida, condicao_saida, observacoes)
                   VALUES (%s, %s, %s, %s, %s)""",
                (login, serial, date.today(), condicao_saida, observacoes),
            )
            id_emprestimo = cursor.lastrowid
            cursor.execute(
                "UPDATE ativos SET at_status = 'emprestado' "
                "WHERE serial_number = %s AND at_status = 'disponivel'", (serial,)
            )
            if cursor.rowcount != 1:
                raise ErroOperacao("O ativo deixou de estar disponível. Atualize a lista.")
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conexao.close()
    # A geração do documento ocorre após a confirmação no banco, como no menu antigo.
    caminho = gerar_termo(login, nome, cpf, departamento, cargo, campus,
                          serial, tipo, marca, modelo, itens, chamado)
    return {"id": id_emprestimo, "termo": caminho}


def registrar_devolucao(id_emprestimo, condicao_retorno, chamado_devolucao):
    id_emprestimo = _numero_positivo(id_emprestimo, "O ID do empréstimo")
    condicao_retorno = _texto(condicao_retorno, "a condição de retorno", 100)
    chamado_devolucao = _numero_positivo(chamado_devolucao, "O chamado GLPI")
    conexao = _conexao()
    try:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """SELECT e.id_ativo, c.login, c.nome, c.CPF,
                          a.tipo, a.marca, a.modelo
                   FROM emprestimos e
                   JOIN colaboradores c ON c.login = e.id_colaborador
                   JOIN ativos a ON a.serial_number = e.id_ativo
                   WHERE e.id = %s AND e.data_devolucao IS NULL FOR UPDATE""",
                (id_emprestimo,),
            )
            dados = cursor.fetchone()
            if dados is None:
                raise ErroOperacao("Empréstimo não encontrado ou já devolvido.")
            serial, login, nome, cpf, tipo, marca, modelo = dados
            hoje = date.today()
            cursor.execute(
                """UPDATE emprestimos SET data_devolucao = %s,
                          condicao_retorno = %s, chamado_devolucao = %s
                   WHERE id = %s AND data_devolucao IS NULL""",
                (hoje, condicao_retorno, chamado_devolucao, id_emprestimo),
            )
            if cursor.rowcount != 1:
                raise ErroOperacao("Empréstimo já devolvido. Atualize a lista.")
            cursor.execute(
                "UPDATE ativos SET at_status = 'disponivel' WHERE serial_number = %s",
                (serial,),
            )
            if cursor.rowcount != 1:
                raise ErroOperacao("Ativo não encontrado; a devolução foi cancelada.")
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conexao.close()
    caminho = gerar_termo_devolucao(login, nome, cpf, serial, tipo, marca, modelo,
                                    hoje, condicao_retorno, chamado_devolucao)
    return {"id": id_emprestimo, "termo": caminho}


def reimprimir_termo(id_emprestimo):
    id_emprestimo = _numero_positivo(id_emprestimo, "O ID do empréstimo")
    linhas = _consultar(
        """SELECT c.login, c.nome, c.CPF, c.departamento, c.cargo, c.campus,
                  a.serial_number, a.tipo, a.marca, a.modelo,
                  a.itens_entregues, a.id_chamado
           FROM emprestimos e
           JOIN colaboradores c ON c.login = e.id_colaborador
           JOIN ativos a ON a.serial_number = e.id_ativo
           WHERE e.id = %s""", (id_emprestimo,),
    )
    if not linhas:
        raise ErroOperacao("Empréstimo não encontrado.")
    caminho = gerar_termo(*linhas[0])
    if caminho is None:
        raise ErroOperacao("Não foi possível gerar o termo. Verifique o modelo DOCX.")
    return caminho
