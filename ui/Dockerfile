FROM node:20

WORKDIR /app

COPY ui/package.json ./package.json
RUN npm install

# ソースはボリュームでマウント（開発用）

ENV VITE_API_BASE=${VITE_API_BASE}

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

