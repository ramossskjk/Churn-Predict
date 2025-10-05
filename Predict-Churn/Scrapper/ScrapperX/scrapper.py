import requests
import sqlite3
import os
from datetime import datetime
from config import X_BEARER_TOKEN

if not X_BEARER_TOKEN:
    raise ValueError("❌ Token da API do X não encontrado! Verifique o arquivo config.py")

BEARER_TOKEN = X_BEARER_TOKEN

NEGATIVE_WORDS = [
    "péssimo", "ruim", "choro", "chateado", "furioso", "raiva", "odio", "não aguento",
    "demorou", "lento", "erro", "bug", "não funciona", "cancelar", "quero sair",
    "falso", "enganou", "tarifa abusiva", "cobrança errada", "atendimento horrível",
    "nunca mais", "pior", "incompetente", "desapontado", "fraude", "trapaceiro",
    "não recomendo", "mal atendido", "não resolveu", "perdi dinheiro", "prejuizo" 
]

POSITIVE_WORDS = [
    "ótimo", "bom", "excelente", "perfeito", "recomendo", "amei", "gostei",
    "rápido", "eficiente", "atendimento bom", "suporte excelente", "melhor",
    "valeu", "satisfatório", "confiável", "sem problemas", "nota 10", "top",
    "agradeço", "parabéns", "profissional", "resolveram rápido", "bom serviço",
    "atendeu bem", "foi ótimo", "me ajudou", "superou expectativas"
]

def classify_sentiment(text):
    text_lower = text.lower()
    neg_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    pos_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    if neg_count > pos_count and neg_count >= 1:
        return "Insatisfeito"
    elif pos_count > neg_count and pos_count >= 1:
        return "Satisfeito"
    else:
        return "Neutro"

BASE_PATH = r"C:\Users\pires\OneDrive\Documentos\Faculdade\P.D.Extensão\Predict-Churn"
DATA_DIR = os.path.join(BASE_PATH, "Data")
DB_PATH = os.path.join(DATA_DIR, "database.db")
os.makedirs(DATA_DIR, exist_ok=True)

def insert_mencao_x(plataforma, autor, texto, data_postagem, url, contexto, sentimento):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO mencoes 
            (plataforma, autor, texto, data_postagem, url, contexto, sentimento_inicial)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (plataforma, autor, texto, data_postagem, url, contexto, sentimento))
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        return 0
    finally:
        conn.close()

print("\n" + "="*60)
print("🔍 SCRAPER DE COMENTÁRIOS DO X PARA PREDIÇÃO DE CHURN")
print("="*60)
SEARCH_SERVICE = input("\nDigite o serviço que deseja buscar (ex: Correios): ").strip()

if not SEARCH_SERVICE:
    print("❌ Nenhum serviço digitado. Encerrando.")
    exit()

print(f"\n🔎 Buscando tweets sobre: '{SEARCH_SERVICE}'...")

MAX_RESULTS = 10
TWEET_FIELDS = "created_at,author_id,text,public_metrics,id"
USER_FIELDS = "name,username"
EXPANSIONS = "author_id"

URL = "https://api.x.com/2/tweets/search/recent"
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

PARAMS = {
    "query": f'"{SEARCH_SERVICE}" -is:retweet lang:pt',
    "max_results": MAX_RESULTS,
    "tweet.fields": TWEET_FIELDS,
    "user.fields": USER_FIELDS,
    "expansions": EXPANSIONS
}

try:
    print("⏳ Enviando requisição à API do X... (aguarde)")
    response = requests.get(URL, headers=HEADERS, params=PARAMS)
    if response.status_code == 429:
        print("🔴 MUITAS REQUISIÇÕES! A API limitou seu acesso.")
        print("   ⏳ Espere 15 minutos antes de tentar novamente.")
        exit()
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na requisição à API: {e}")
    exit()

data = response.json()
inseridos = 0

if 'data' not in data or len(data['data']) == 0:
    print("⚠️ Nenhum tweet encontrado com esse termo nos últimos 7 dias.")
else:
    users = {}
    if 'includes' in data and 'users' in data['includes']:
        for user in data['includes']['users']:
            users[user['id']] = {
                'name': user.get('name', 'Desconhecido'),
                'username': user.get('username', 'desconhecido')
            }

    for tweet in data['data']:
        author_id = tweet['author_id']
        user_info = users.get(author_id, {'name': 'Desconhecido', 'username': 'desconhecido'})
        created_at = datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        data_formatada = created_at.strftime('%Y-%m-%d %H:%M:%S')
        tweet_url = f"https://twitter.com/{user_info['username']}/status/{tweet['id']}"
        sentiment = classify_sentiment(tweet['text'])
        texto_limpo = tweet['text'].replace('\n', ' ').strip()[:1000]
        inseridos += insert_mencao_x(
            plataforma='x',
            autor=f"@{user_info['username']}",
            texto=texto_limpo,
            data_postagem=data_formatada,
            url=tweet_url,
            contexto=SEARCH_SERVICE,
            sentimento=sentiment
        )

print(f"\n✅ Coleta concluída! {inseridos} tweets salvos no banco de dados.")
