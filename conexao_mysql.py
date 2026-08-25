"""
Modulo de conexao com o banco de dados MySQL.

Antes de rodar:
1) pip install mysql-connector-python python-dotenv
2) Crie um arquivo ".env" na mesma pasta com o seguinte conteudo
   (ajuste os valores para o seu ambiente):

   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=sua_senha
   DB_NAME=controle_emprestimos

Nunca coloque usuario/senha direto no codigo -- use o .env,
e adicione o .env no seu .gitignore se for versionar o projeto.
"""

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()  # le as variaveis do arquivo .env


def get_connection():
    """
    Abre e retorna uma conexao com o banco de dados MySQL.
    Retorna None se a conexao falhar (e imprime o motivo do erro).
    """
    try:
        conexao = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 3306),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "controle_emprestimos"),
        )
        if conexao.is_connected():
            return conexao
    except Error as erro:
        print(f"Erro ao conectar no MySQL: {erro}")
        return None


def testar_conexao():
    """Testa a conexao e mostra informacoes basicas do banco."""
    conexao = get_connection()
    if conexao is None:
        print("Nao foi possivel conectar ao banco.")
        return

    cursor = conexao.cursor()
    cursor.execute("SELECT DATABASE(), VERSION();")
    banco, versao = cursor.fetchone()
    print(f"Conectado com sucesso!")
    print(f"Banco atual: {banco}")
    print(f"Versao do MySQL: {versao}")

    cursor.close()
    conexao.close()


if __name__ == "__main__":
    testar_conexao()
