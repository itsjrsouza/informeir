# Imagem base com Node
FROM node:18

# Instala Python e dependências
RUN apt-get update && apt-get install -y python3 python3-pip

# Define diretório de trabalho
WORKDIR /app

# Copia arquivos do projeto
COPY . .

# Instala dependências Node
RUN npm install

# Comando para iniciar o backend
CMD ["npm", "start"]

RUN pip3 install pandas openpyxl reportlab
