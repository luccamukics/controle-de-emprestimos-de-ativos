"""Operações do sistema usadas pela interface e pelo menu de texto."""

from datetime import date
from uuid import uuid4

from conexao_mysql import get_connection
from modulos.formatacao import iniciais_maiusculas, iniciais_maiusculas_funcao, maiusculas
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


def listar_ativos_com_colaborador(disponiveis=False):
    """Inclui nome e setor do empréstimo aberto mais recente de cada ativo."""
    filtro = "WHERE a.at_status = 'disponivel'" if disponiveis else ""
    return _consultar(
        f"""SELECT a.empresa, a.serial_number, a.patrimonio, a.tipo, a.marca,
                   a.modelo, a.at_status, c.nome, c.departamento,
                   a.itens_entregues, a.id_chamado
            FROM ativos a
            LEFT JOIN emprestimos e ON e.id = (
                SELECT e2.id FROM emprestimos e2
                WHERE e2.id_ativo = a.serial_number
                  AND e2.data_devolucao IS NULL
                ORDER BY e2.id DESC LIMIT 1
            )
            LEFT JOIN colaboradores c ON c.login = e.id_colaborador
            {filtro} ORDER BY a.tipo, a.marca, a.modelo"""
    )


def buscar_dados_celular(serial):
    """Busca detalhes do celular sem alterar a lista e a planilha de ativos."""
    linhas = _consultar(
        "SELECT imei_1, imei_2, numero_celular FROM ativos WHERE serial_number = %s",
        (serial,),
    )
    if not linhas:
        raise ErroOperacao("Ativo não encontrado. Atualize a lista.")
    return tuple(valor or "" for valor in linhas[0])


def _dados_celular(tipo, imei_1, imei_2, numero_celular):
    if tipo != "CELULAR":
        return None, None, None
    dados = []
    for nome, valor in (("IMEI 1", imei_1), ("IMEI 2", imei_2)):
        valor = _texto(valor, nome, 15, False)
        if valor and (len(valor) != 15 or not valor.isascii() or not valor.isdecimal()):
            raise ErroOperacao(f"{nome} deve ter exatamente 15 dígitos.")
        dados.append(valor or None)
    numero = _texto(numero_celular, "o número de celular", 20, False)
    if numero and (not 8 <= sum(c.isdigit() for c in numero) <= 15 or
                   any(c not in "+ ()-0123456789" for c in numero)):
        raise ErroOperacao("Número de celular inválido. Use de 8 a 15 dígitos.")
    return *dados, numero or None


def _empresa_patrimonio(empresa, patrimonio):
    if empresa not in ("Arklok", "Vivo"):
        raise ErroOperacao("Selecione Arklok ou Vivo no campo Empresa.")
    patrimonio = _texto(maiusculas(patrimonio), "o patrimônio", 20, False) or None
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
                   empresa, patrimonio=None, imei_1=None, imei_2=None,
                   numero_celular=None):
    patrimonio = _empresa_patrimonio(empresa, patrimonio)
    serial = _texto(maiusculas(serial), "o serial", 15)
    tipo = _texto(maiusculas(tipo), "o tipo", 20)
    imei_1, imei_2, numero_celular = _dados_celular(
        tipo, imei_1, imei_2, numero_celular
    )
    marca = _texto(maiusculas(marca), "a marca", 30)
    modelo = _texto(maiusculas(modelo), "o modelo", 30)
    itens_entregues = _texto(maiusculas(itens_entregues), "os itens entregues", 30, False)
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
                       modelo, marca, at_status, itens_entregues, id_chamado,
                       imei_1, imei_2, numero_celular)
                   VALUES (%s, %s, %s, %s, %s, %s, 'disponivel', %s, %s,
                           %s, %s, %s)""",
                (empresa, serial, patrimonio, tipo, modelo, marca,
                 itens_entregues, id_chamado, imei_1, imei_2, numero_celular),
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
                modelo, status, itens_entregues, id_chamado, imei_1=None,
                imei_2=None, numero_celular=None):
    serial_original = _texto(serial_original, "o serial original", 15)
    patrimonio = _empresa_patrimonio(empresa, patrimonio)
    serial = _texto(maiusculas(serial), "o serial", 15)
    tipo = _texto(maiusculas(tipo), "o tipo", 20)
    imei_1, imei_2, numero_celular = _dados_celular(
        tipo, imei_1, imei_2, numero_celular
    )
    marca = _texto(maiusculas(marca), "a marca", 30)
    modelo = _texto(maiusculas(modelo), "o modelo", 30)
    itens_entregues = _texto(maiusculas(itens_entregues), "os itens entregues", 30, False)
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
                     itens_entregues, id_chamado, imei_1, imei_2, numero_celular)
            if serial == serial_original:
                cursor.execute(
                    """UPDATE ativos SET empresa = %s, patrimonio = %s, tipo = %s,
                              marca = %s, modelo = %s, at_status = %s,
                              itens_entregues = %s, id_chamado = %s,
                              imei_1 = %s, imei_2 = %s, numero_celular = %s
                       WHERE serial_number = %s""", (*dados, serial_original),
                )
            else:
                cursor.execute("SELECT serial_number FROM ativos WHERE serial_number = %s",
                               (serial,))
                existente = cursor.fetchone()
                if existente and existente[0] != serial_original:
                    raise ErroOperacao("Já existe um ativo com o novo serial.")
                # Cria a nova chave, transfere o histórico e só então remove a antiga.
                # Isso funciona mesmo quando a FK de empréstimos não tem ON UPDATE CASCADE.
                # Sob collation sem distinção de caixa, o novo serial pode ser
                # considerado igual ao antigo; nesse caso, usa uma chave temporária.
                troca_so_de_caixa = serial.casefold() == serial_original.casefold()
                serial_intermediario = serial
                if troca_so_de_caixa:
                    for _ in range(5):
                        candidato = "TMP" + uuid4().hex[:12].upper()
                        cursor.execute(
                            "SELECT serial_number FROM ativos WHERE serial_number = %s",
                            (candidato,),
                        )
                        if cursor.fetchone() is None:
                            serial_intermediario = candidato
                            break
                    else:
                        raise ErroOperacao("Não foi possível reservar um serial temporário.")
                if patrimonio and anterior[1] and patrimonio.casefold() == anterior[1].casefold():
                    cursor.execute(
                        "UPDATE ativos SET patrimonio = NULL WHERE serial_number = %s",
                        (serial_original,),
                    )
                cursor.execute(
                    """INSERT INTO ativos (serial_number, empresa, patrimonio,
                              tipo, marca, modelo, at_status, itens_entregues, id_chamado,
                              imei_1, imei_2, numero_celular)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (serial_intermediario, *dados),
                )
                cursor.execute("UPDATE emprestimos SET id_ativo = %s WHERE id_ativo = %s",
                               (serial_intermediario, serial_original))
                cursor.execute("DELETE FROM ativos WHERE serial_number = %s",
                               (serial_original,))
                if troca_so_de_caixa:
                    if patrimonio:
                        cursor.execute(
                            "UPDATE ativos SET patrimonio = NULL WHERE serial_number = %s",
                            (serial_intermediario,),
                        )
                    cursor.execute(
                        """INSERT INTO ativos (serial_number, empresa, patrimonio,
                                  tipo, marca, modelo, at_status, itens_entregues, id_chamado,
                                  imei_1, imei_2, numero_celular)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (serial, *dados),
                    )
                    cursor.execute(
                        "UPDATE emprestimos SET id_ativo = %s WHERE id_ativo = %s",
                        (serial, serial_intermediario),
                    )
                    cursor.execute(
                        "DELETE FROM ativos WHERE serial_number = %s",
                        (serial_intermediario,),
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
                    _texto(iniciais_maiusculas(colaborador.get("nome")), "o nome", 40),
                    _texto(colaborador.get("cpf"), "o CPF", 15),
                    _texto(iniciais_maiusculas_funcao(colaborador.get("departamento")),
                           "o departamento", 30),
                    _texto(iniciais_maiusculas_funcao(colaborador.get("cargo")),
                           "o cargo", 30),
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
