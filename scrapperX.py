import requests
import csv
import time
from datetime import datetime

from config import X_BEARER_TOKEN

if not X_BEARER_TOKEN:
    raise ValueError("❌ Token da API do X não encontrado! Verifique o arquivo config.py")

BEARER_TOKEN = X_BEARER_TOKEN
print("✅ Token carregado com sucesso.")


NEGATIVE_WORDS = [
    "péssimo", "ruim", "choro", "chateado", "furioso", "raiva", "odio", "não aguento",
    "demorou", "lento", "erro", "bug", "não funciona", "cancelar", "quero sair",
    "falso", "enganou", "tarifa abusiva", "cobrança errada", "atendimento horrível",
    "nunca mais", "pior", "incompetente", "desapontado", "fraude", "trapaceiro",
    "não recomendo", "mal atendido", "não resolveu", "perdi dinheiro", "engana"
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

print("\n" + "="*60)
print("🔍 SCRAPER DE COMENTÁRIOS PARA PREDIÇÃO DE CHURN")
print("="*60)
SEARCH_SERVICE = input("\nDigite o serviço que deseja buscar (ex: 'serviço de limpeza'): ").strip()

if not SEARCH_SERVICE:
    print("❌ Nenhum serviço digitado. Encerrando.")
    exit()

print(f"\n🔎 Buscando tweets sobre: '{SEARCH_SERVICE}'...")


MAX_RESULTS = 10
TWEET_FIELDS = "created_at,author_id,text,public_metrics"
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

results = []

try:
    print("⏳ Enviando requisição à API do X... (aguarde)")
    response = requests.get(URL, headers=HEADERS, params=PARAMS)
    
    if response.status_code == 429:
        print("🔴 MUITAS REQUISIÇÕES! A API limitou seu acesso.")
        print("   ⏳ Espere 15 minutos antes de tentar novamente.")
        print("   💡 Dica: Execute o script menos vezes e espere entre execuções.")
        exit()
    
    response.raise_for_status()

except requests.exceptions.RequestException as e:
    print(f"❌ Erro na requisição à API: {e}")
    exit()

#
time.sleep(1)

data = response.json()

if 'data' not in data or len(data['data']) == 0:
    print("⚠️ Nenhum tweet encontrado com esse termo nos últimos 7 dias.")
    print("   💡 Dica: Tente termos mais genéricos como 'atendimento detran' ou 'multa detran'.")
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
        
        sentiment = classify_sentiment(tweet['text'])

        results.append({
            'servico': SEARCH_SERVICE,
            'texto': tweet['text'].replace('\n', ' ').strip()[:500],
            'autor': user_info['name'],
            'usuario': f"@{user_info['username']}",
            'data': tweet['created_at'],
            'curtidas': tweet['public_metrics']['like_count'],
            'retweets': tweet['public_metrics']['retweet_count'],
            'respostas': tweet['public_metrics']['reply_count'],
            'sentimento': sentiment
        })

safe_filename = SEARCH_SERVICE.replace(' ', '_').replace('/', '_').replace('\\', '_')[:50]
output_file = f"resultados_{safe_filename}.csv"

with open(output_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'servico', 'texto', 'autor', 'usuario', 'data', 'curtidas', 'retweets', 'respostas', 'sentimento'
    ])
    writer.writeheader()
    writer.writerows(results)


print(f"\n✅ Sucesso! Foram encontrados {len(results)} tweets sobre '{SEARCH_SERVICE}'.")
print(f"💾 Resultados salvos em: {output_file}")


sat = sum(1 for r in results if r['sentimento'] == "Satisfeito")
insat = sum(1 for r in results if r['sentimento'] == "Insatisfeito")
neutro = len(results) - sat - insat

print(f"\n📊 RESUMO DE SENTIMENTOS:")
print(f"   😊 Satisfeitos: {sat}")
print(f"   😡 Insatisfeitos: {insat}")
print(f"   😐 Neutros: {neutro}")
print(f"   ⚠️ Taxa de insatisfação: {insat / len(results) * 100:.1f}%" if len(results) > 0 else "   ⚠️ Taxa de insatisfação: 0%")

if insat > 0:
    print("\n=== PRIMEIROS COMENTÁRIOS INSATISFEITOS (mais curtidos) ===")
    worst = sorted([r for r in results if r['sentimento'] == "Insatisfeito"], key=lambda x: x['curtidas'], reverse=True)[:3]
    for i, tweet in enumerate(worst, 1):
        print(f"\n{i}. @{tweet['usuario']} ({tweet['autor']})")
        print(f"   \"{tweet['texto']}\"")
        print(f"   👍 {tweet['curtidas']} curtidas | 📅 {tweet['data']}")
