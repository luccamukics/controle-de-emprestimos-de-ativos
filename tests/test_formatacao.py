"""Confere os valores enviados ao banco e a edição de seriais antigos."""

import sqlite3
import sys
import types
import unittest
from datetime import date
from unittest.mock import patch

# Os testes de formatação não dependem de um servidor MySQL nem de Word.
sys.modules.setdefault(
    "conexao_mysql", types.SimpleNamespace(get_connection=lambda: None)
)
sys.modules.setdefault(
    "modulos.termos",
    types.SimpleNamespace(gerar_termo=lambda *args: None,
                          gerar_termo_devolucao=lambda *args: None),
)

from modulos import servicos
from modulos.formatacao import iniciais_maiusculas, iniciais_maiusculas_funcao, maiusculas


class Cursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, sql, parametros=()):
        parametros = tuple(valor.isoformat() if isinstance(valor, date) else valor
                           for valor in parametros)
        self.cursor.execute(sql.replace("%s", "?").replace(" FOR UPDATE", ""),
                            parametros)

    def __getattr__(self, nome):
        return getattr(self.cursor, nome)


class Conexao:
    def __init__(self, uri):
        self.conexao = sqlite3.connect(uri, uri=True)
        self.conexao.execute("PRAGMA foreign_keys=ON")

    def cursor(self):
        return Cursor(self.conexao.cursor())

    def __getattr__(self, nome):
        return getattr(self.conexao, nome)


class TestFormatacao(unittest.TestCase):
    def setUp(self):
        self.uri = f"file:teste_{id(self)}?mode=memory&cache=shared"
        self.banco = sqlite3.connect(self.uri, uri=True)
        self.banco.execute("PRAGMA foreign_keys=ON")
        self.banco.executescript("""
            CREATE TABLE ativos (
                serial_number TEXT PRIMARY KEY COLLATE NOCASE,
                empresa TEXT, patrimonio TEXT UNIQUE COLLATE NOCASE,
                tipo TEXT, marca TEXT, modelo TEXT, at_status TEXT,
                itens_entregues TEXT, id_chamado INTEGER,
                imei_1 TEXT, imei_2 TEXT, numero_celular TEXT
            );
            CREATE TABLE colaboradores (
                login TEXT PRIMARY KEY, nome TEXT, CPF TEXT,
                departamento TEXT, cargo TEXT, campus TEXT
            );
            CREATE TABLE emprestimos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_colaborador TEXT REFERENCES colaboradores(login),
                id_ativo TEXT REFERENCES ativos(serial_number),
                data_saida TEXT, data_devolucao TEXT,
                condicao_saida TEXT, observacoes TEXT
            );
        """)
        self.conexao = patch.object(servicos, "_conexao",
                                   lambda: Conexao(self.uri))
        self.conexao.start()

    def tearDown(self):
        self.conexao.stop()
        self.banco.close()

    def test_formatadores(self):
        self.assertEqual(maiusculas("dell óptiplex 7020"), "DELL ÓPTIPLEX 7020")
        self.assertEqual(iniciais_maiusculas("lUCCA dA silVA"), "Lucca Da Silva")
        self.assertEqual(iniciais_maiusculas("tÉcnico DE informÁtica"),
                         "Técnico De Informática")
        self.assertEqual(iniciais_maiusculas_funcao("tÉcnico DE informÁtica"),
                         "Técnico de Informática")
        self.assertEqual(iniciais_maiusculas_funcao("suporte de ti"),
                         "Suporte de TI")

    def test_cadastro_e_colaborador_aplicam_formato_antes_de_salvar(self):
        serial = servicos.cadastrar_ativo(
            "ab-01", "notebook", "dell", "latitude 5420",
            "carregador e fonte", 1234, "Arklok", "pat-01"
        )
        self.assertEqual(serial, "AB-01")
        self.assertEqual(
            self.banco.execute(
                "SELECT serial_number, patrimonio, tipo, marca, modelo, "
                "itens_entregues FROM ativos"
            ).fetchone(),
            ("AB-01", "PAT-01", "NOTEBOOK", "DELL", "LATITUDE 5420",
             "CARREGADOR E FONTE"),
        )
        with patch.object(servicos, "gerar_termo", return_value="termo.docx"):
            servicos.registrar_emprestimo(
                "lucca", serial, "bom", colaborador={
                    "nome": "lUCCA dA silVA", "cpf": "123",
                    "departamento": "sUPORTE tÉCNICO",
                    "cargo": "aNALISTA de sUPORTE", "campus": "CMI",
                }
            )
        self.assertEqual(
            self.banco.execute(
                "SELECT nome, departamento, cargo FROM colaboradores"
            ).fetchone(),
            ("Lucca Da Silva", "Suporte Técnico", "Analista de Suporte"),
        )

    def test_edita_serial_antigo_preservando_historico(self):
        self.banco.execute(
            """INSERT INTO ativos (serial_number, empresa, patrimonio, tipo,
                 marca, modelo, at_status, itens_entregues, id_chamado) VALUES
               ('abc001', 'Arklok', 'pat1', 'notebook', 'dell',
                'latitude', 'emprestado', 'fonte', 10)"""
        )
        self.banco.execute(
            """INSERT INTO colaboradores VALUES
               ('lucca', 'Lucca', '123', 'Suporte', 'Analista', 'CMI')"""
        )
        self.banco.execute(
            """INSERT INTO emprestimos
               (id_colaborador, id_ativo, data_saida, condicao_saida)
               VALUES ('lucca', 'abc001', '2026-09-20', 'bom')"""
        )
        self.banco.commit()
        serial = servicos.editar_ativo(
            "abc001", "Arklok", "abc001", "pat1", "notebook",
            "dell", "latitude", "emprestado", "fonte", 10
        )
        self.assertEqual(serial, "ABC001")
        self.assertEqual(
            self.banco.execute(
                "SELECT serial_number, patrimonio, tipo, marca FROM ativos"
            ).fetchall(),
            [("ABC001", "PAT1", "NOTEBOOK", "DELL")],
        )
        self.assertEqual(
            self.banco.execute("SELECT id_ativo FROM emprestimos").fetchone(),
            ("ABC001",),
        )

    def test_celular_salva_edita_e_limpa_dados_ao_mudar_tipo(self):
        serial = servicos.cadastrar_ativo(
            "cel-01", "celular", "samsung", "a55", "carregador", 123,
            "Vivo", None, "123456789012345", "987654321098765", "(11) 99999-1234"
        )
        self.assertEqual(
            servicos.buscar_dados_celular(serial),
            ("123456789012345", "987654321098765", "(11) 99999-1234"),
        )
        servicos.editar_ativo(
            serial, "Vivo", "cel-02", None, "celular", "samsung", "a55",
            "disponivel", "carregador", 123, "123456789012345", "", "11999991234"
        )
        self.assertEqual(servicos.buscar_dados_celular("CEL-02"),
                         ("123456789012345", "", "11999991234"))
        servicos.editar_ativo(
            "CEL-02", "Vivo", "CEL-02", None, "notebook", "dell", "latitude",
            "disponivel", "fonte", 123, "123456789012345", "", "11999991234"
        )
        self.assertEqual(servicos.buscar_dados_celular("CEL-02"), ("", "", ""))

    def test_imei_invalido_nao_cadastra(self):
        with self.assertRaisesRegex(servicos.ErroOperacao, "15 dígitos"):
            servicos.cadastrar_ativo("CEL-01", "CELULAR", "SAMSUNG", "A55",
                                    "FONTE", 123, "Vivo", None, "123", "", "")
        self.assertEqual(self.banco.execute("SELECT COUNT(*) FROM ativos").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
