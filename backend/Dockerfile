# Usa Node como base
FROM node:18

# Instala Python e ferramentas necessárias
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# Cria diretório de trabalho
WORKDIR /app

# Cria ambiente virtual Python
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copia arquivos do projeto
COPY . .

# Instala dependências Node
RUN npm install

# Instala bibliotecas Python dentro da venv
RUN pip install pandas openpyxl reportlab

# Comando para iniciar o backend
CMD ["npm", "start"]
