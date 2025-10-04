import praw
import sqlite3
import os
import re
from datetime import datetime
from config_reddit import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

BASE_PATH = r"C:\Users\pires\OneDrive\Documentos\Faculdade\P.D.Extensão\Predict-Churn"
DATA_DIR = os.path.join(BASE_PATH, "Data")
DB_PATH = os.path.join(DATA_DIR, "database.db")
os.makedirs(DATA_DIR, exist_ok=True)

NEGATIVE_WORDS = [
    "péssimo", "ruim", "horrível", "terrível", "detestei", "odiado", "odiei", "chateado", "frustrado", "decepcionado", "desapontado", "irritado", "furioso", "raiva", "ódio", "não aguento", "cansado", "farto", "enjoado",
    "demorou", "lento", "bug", "erro", "falha", "não funciona", "travou", "quebrou", "parou", "congelou", "instável",
    "atendimento horrível", "mal atendido", "ignorado", "não resolveram", "empurra-empurra", "burocracia", "sem solução",
    "cancelar", "quero sair", "vou cancelar", "nunca mais", "não volto", "não recomendo", "evitem", "me arrependi",
    "falso", "enganou", "fraude", "golpe", "trapaceiro", "mentira", "prometeram e não cumpriram",
    "tarifa abusiva", "cobrança errada", "valor absurdo", "caro demais", "perdi dinheiro", "prejuízo", "dinheiro jogado fora",
    "incompetente", "amador", "desorganizado", "pior", "não presta", "lixo", "vergonha", "falta de respeito",

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
    text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
    neg_count = sum(1 for word in NEGATIVE_WORDS if word in text_clean)
    pos_count = sum(1 for word in POSITIVE_WORDS if word in text_clean)
    if neg_count > pos_count and neg_count >= 1:
        return "Insatisfeito"
    elif pos_count > neg_count and pos_count >= 1:
        return "Satisfeito"
    else:
        return "Neutro"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mencoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plataforma TEXT NOT NULL,
            autor TEXT NOT NULL,
            texto TEXT,
            data_postagem TEXT,
            url TEXT UNIQUE,
            contexto TEXT,
            data_coleta TEXT DEFAULT (datetime('now')),
            sentimento_inicial TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_mencao(plataforma, autor, texto, data_postagem, url, contexto, sentimento):
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
        print(f"⚠️ Erro ao inserir {url}: {e}")
        return 0
    finally:
        conn.close()

print("\n" + "="*60)
print("🔍 SCRAPER DO REDDIT PARA PREDIÇÃO DE CHURN")
print("="*60)

DEFAULT_SUB = "Brasil"
subreddit_input = input(f"\nDigite o subreddit (ex: Brasil, consumidor) [padrão: {DEFAULT_SUB}]: ").strip()
subreddit_name = subreddit_input if subreddit_input else DEFAULT_SUB

SEARCH_SERVICE = input("\nDigite o serviço que deseja buscar (ex: Correios, Detran): ").strip()
if not SEARCH_SERVICE:
    print("❌ Nenhum serviço digitado. Encerrando.")
    exit()

init_db()

try:
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    test_sub = reddit.subreddit(subreddit_name)
    test_sub.id
    print(f"✅ Subreddit r/{subreddit_name} encontrado.")
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
    exit()

print(f"\n🔎 Buscando posts e comentários em r/{subreddit_name} sobre: '{SEARCH_SERVICE}'...")

inseridos = 0
MAX_POSTS = 15
MAX_COMMENTS_PER_POST = 5

try:
    subreddit = reddit.subreddit(subreddit_name)
    query = f'"{SEARCH_SERVICE}"'
    print("⏳ Coletando e salvando no banco...")

    for post in subreddit.search(query, sort='new', limit=MAX_POSTS):
        full_text = f"{post.title} {post.selftext}".strip()
        if full_text and len(full_text) > 10 and full_text not in ["[removed]", "[deleted]"]:
            url_post = f"https://reddit.com{post.permalink}"
            sentimento = classify_sentiment(full_text)
            autor = str(post.author) if post.author else "Desconhecido"
            data_post = datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S')
            inseridos += insert_mencao(
                plataforma='reddit',
                autor=f"u/{autor}",
                texto=full_text.replace('\n', ' ')[:1000],
                data_postagem=data_post,
                url=url_post,
                contexto=subreddit_name,
                sentimento=sentimento
            )

        post.comments.replace_more(limit=0)
        for comment in post.comments.list()[:MAX_COMMENTS_PER_POST]:
            if comment.body and len(comment.body) > 10 and comment.body not in ["[deleted]", "[removed]"]:
                url_comment = f"https://reddit.com{comment.permalink}"
                sentimento = classify_sentiment(comment.body)
                autor = str(comment.author) if comment.author else "Desconhecido"
                data_comment = datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')
                inseridos += insert_mencao(
                    plataforma='reddit',
                    autor=f"u/{autor}",
                    texto=comment.body.replace('\n', ' ')[:1000],
                    data_postagem=data_comment,
                    url=url_comment,
                    contexto=subreddit_name,
                    sentimento=sentimento
                )

except Exception as e:
    print(f"⚠️ Erro durante a coleta: {e}")

print(f"\n✅ Coleta concluída! {inseridos} novas menções salvas em '{DB_PATH}'.")