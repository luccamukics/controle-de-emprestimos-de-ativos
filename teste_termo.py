from docxtpl import DocxTemplate


# Abre o nosso documento modelo
documento = DocxTemplate("TERMO_RESPONSABILIDADE_MODELO.docx")


# Dados de teste
dados = {
    "nome": "João da Silva",
    "cpf": "123.456.789-00",
    "login": "jsilva",
    "departamento": "Tecnologia da Informação",
    "cargo": "Analista de Sistemas",
    "campus": "Campus Interlagos",
    "modelo": "Notebook Dell Latitude 5420",
    "serial": "ABC123456",
    "itens_entregues": "Notebook + Fonte de Energia",
    "id_chamado": "123456"
}


# Substitui os {{ campos }} do Word
documento.render(dados)


# Salva um novo documento
documento.save("TERMO_TESTE.docx")


print("Termo gerado com sucesso!")