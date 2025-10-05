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
    "porra", "caralho", "merda", "filho da puta", "fdp", "puta que pariu", "vai se foder", "se foder", "cacete", "bosta", "bostaa", "merdaaa",
    "que porra é essa", "que merda é essa", "tá de sacanagem", "tô farto", "já chega", "chega né", "não aguento mais",
    "me fodeu", "me lascou", "me roubaram", "me enganaram", "fui lesado", "fui fudido", "fuderam comigo",

                                  
    
    "scam", "bullshit", "worst", "terrible", "awful", "horrible", "fuck", "fucking", "shit", "garbage", "trash", "ripoff", "fraud",
    "worst service ever", "never again", "dont recommend", "waste of money", "broken", "useless", "overpriced", "disappointed", "angry", "furious",
    "this sucks", "total scam", "fake", "liar", "cheated", "stolen", "not working", "slow as hell", "customer service sucks"

]

POSITIVE_WORDS = [
    
    "ótimo", "bom", "excelente", "perfeito", "maravilhoso", "sensacional", "incrível", "fantástico", "amei", "gostei", "apaixonei", "recomendo", "super recomendo", "indico", "top", "show", "nota 10", "10/10", "5 estrelas",
    "rápido", "ágil", "eficiente", "prático", "fácil", "sem burocracia", "resolveram rápido", "solução imediata",
    "atendimento excelente", "suporte ótimo", "atendeu bem", "educado", "prestativo", "atencioso", "profissional", "gentil",
    "resolveu", "funcionou", "deu certo", "me ajudou", "salvou meu dia", "superou expectativas", "melhor que eu esperava",
    "confiável", "seguro", "transparente", "honesto", "sério", "responsável", "qualidade", "bom serviço", "sem problemas",
    "valeu", "obrigado", "agradeço", "muito obrigado", "parabéns", "vocês arrasaram", "equipe nota 10",
    
                                        
    
    "awesome", "amazing", "perfect", "best", "love it", "great", "excellent", "fantastic", "brilliant", "outstanding",
    "highly recommend", "works perfectly", "fast support", "saved me", "thank you", "you guys rock", "5 stars", "top notch",
    "reliable", "trustworthy", "smooth", "no issues", "easy to use", "well done", "impressed", "exceeded expectations",
    "awesome", "amazing", "fantastic", "excellent", "outstanding", "brilliant", "incredible", "superb", "phenomenal", "stellar",
    "perfect", "flawless", "impeccable", "top-notch", "first-class", "world-class", "exceptional", "remarkable", "fabulous", "splendid",
    "love it", "loved it", "i love", "i loved", "highly recommend", "strongly recommend", "10/10", "five stars", "5 stars",
    "best ever", "best in class", "best service", "best product", "best support", "best experience",
    "works perfectly", "works like a charm", "smooth", "seamless", "hassle-free", "easy to use", "user-friendly", "intuitive",
    "fast", "quick", "lightning fast", "responsive", "reliable", "stable", "consistent",
    "great support", "awesome support", "helpful team", "responsive team", "saved me", "they saved me", "went above and beyond",
    "customer service is amazing", "support team rocks", "thank you team", "you guys are awesome", "you guys rock",
    "thank you", "thanks a lot", "big thanks", "huge thanks", "much appreciated", "well done", "kudos", "props to you",
    "you nailed it", "you crushed it", "impressed", "blown away", "exceeded my expectations", "wow",
    "trustworthy", "reliable", "dependable", "honest", "transparent", "professional", "quality", "premium", "worth every penny",
    "great value", "fair price", "no regrets", "glad i chose", "happy customer", "satisfied customer"
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


