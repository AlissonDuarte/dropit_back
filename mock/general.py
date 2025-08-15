import random
from utils import security
from database import SYNC_DATABASE_URL
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker
from models import Base, User, UserSubscription, Post, PostReaction, PostReactionCount, PostBookmark, Tag

# Configuração do SQLite
DATABASE_URL = SYNC_DATABASE_URL  # Altere para o caminho do seu banco de dados
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Inicializa o Faker
fake = Faker('pt_BR')

# Dados iniciais para tags (como você forneceu)
TAGS_DATA =  [
  { "name": "Desabafo", "group": "Emoções", "color": "#f43f5e" },
  { "name": "Ansiedade", "group": "Emoções", "color": "#fb7185" },
  { "name": "Tristeza", "group": "Emoções", "color": "#60a5fa" },
  { "name": "Raiva", "group": "Emoções", "color": "#f97316" },
  { "name": "Esperança", "group": "Emoções", "color": "#34d399" },
  { "name": "Solidão", "group": "Emoções", "color": "#6366f1" },
  { "name": "Superação", "group": "Emoções", "color": "#10b981" },
  { "name": "Confusão", "group": "Emoções", "color": "#facc15" },

  { "name": "Amor", "group": "Relações", "color": "#f472b6" },
  { "name": "Amizade", "group": "Relações", "color": "#3b82f6" },
  { "name": "Família", "group": "Relações", "color": "#9333ea" },
  { "name": "Relacionamento", "group": "Relações", "color": "#e879f9" },
  { "name": "Término", "group": "Relações", "color": "#ef4444" },
  { "name": "Rejeição", "group": "Relações", "color": "#f87171" },
  { "name": "Carência", "group": "Relações", "color": "#a78bfa" },
  { "name": "Perda", "group": "Relações", "color": "#6b7280" },

  { "name": "Sonho", "group": "Crescimento Pessoal", "color": "#0ea5e9" },
  { "name": "Mudança", "group": "Crescimento Pessoal", "color": "#3b82f6" },
  { "name": "Liberdade", "group": "Crescimento Pessoal", "color": "#22c55e" },
  { "name": "Propósito", "group": "Crescimento Pessoal", "color": "#8b5cf6" },
  { "name": "Autoconhecimento", "group": "Crescimento Pessoal", "color": "#10b981" },
  { "name": "Coragem", "group": "Crescimento Pessoal", "color": "#f59e0b" },
  { "name": "Perdão", "group": "Crescimento Pessoal", "color": "#a3e635" },
  { "name": "Conquista", "group": "Crescimento Pessoal", "color": "#38bdf8" },
  { "name": "Reflexão", "group": "Crescimento Pessoal", "color": "#c084fc" },

  { "name": "Trauma", "group": "Temas Sensíveis", "color": "#b91c1c" },
  { "name": "Abuso", "group": "Temas Sensíveis", "color": "#dc2626" },
  { "name": "Luto", "group": "Temas Sensíveis", "color": "#1f2937" },
  { "name": "Saúde Mental", "group": "Temas Sensíveis", "color": "#4b5563" },
  { "name": "Dependência", "group": "Temas Sensíveis", "color": "#78350f" },
  { "name": "Bullying", "group": "Temas Sensíveis", "color": "#f43f5e" },
  { "name": "Autoestima", "group": "Temas Sensíveis", "color": "#facc15" },
  { "name": "Identidade", "group": "Temas Sensíveis", "color": "#7c3aed" },
  { "name": "Suicídio", "group": "Temas Sensíveis", "color": "#7f1d1d" },

  { "name": "Segredo", "group": "Outros", "color": "#6b21a8" },
  { "name": "Infância", "group": "Outros", "color": "#fde68a" },
  { "name": "Cotidiano", "group": "Outros", "color": "#64748b" },
  { "name": "Sexualidade", "group": "Outros", "color": "#ec4899" },
  { "name": "Trabalho", "group": "Outros", "color": "#22d3ee" },
  { "name": "Estudos", "group": "Outros", "color": "#60a5fa" },
  { "name": "Espiritualidade", "group": "Outros", "color": "#7dd3fc" },
  { "name": "Frustração", "group": "Outros", "color": "#fbbf24" },
  { "name": "Vício", "group": "Outros", "color": "#f87171" },
  { "name": "Inspiração", "group": "Outros", "color": "#a3e635" }
]


# Criação de dados fictícios
def create_fake_users(count=100):
    users = []
    for _ in range(count):
        profile = fake.profile()
        user = User(
            uuid=uuid.uuid4(),
            username=profile['username'],
            email=fake.email(),
            bio=fake.sentence(nb_words=10),
            photo_url="",
            password=security.hash_password("Password@123"),
            created_at=fake.date_time_this_year()
        )
        users.append(user)

        user = User(
            uuid=uuid.uuid4(),
            username="akaza",
            email="alisson@gmail.com",
            bio="Fukuna",
            password=security.hash_password("Grindphanter2@"),
            created_at=fake.date_time_this_year()
        )
        users.append(user)
    return users

def create_fake_tags():
    tags = []
    for tag_data in TAGS_DATA:
        tag = Tag(
            uuid=uuid.uuid4(),
            name=tag_data['name'],
            group=tag_data['group'],
            color=tag_data['color'],
            created_at=fake.date_time_this_year()
        )
        tags.append(tag)
    return tags

def create_fake_posts(users, tags, count=400):
    posts = []
    for _ in range(count):
        user = random.choice(users)
        post = Post(
            uuid=uuid.uuid4(),
            title=fake.sentence(nb_words=6),
            content=fake.text(max_nb_chars=1500),
            user_id=user.uuid,
            created_at=fake.date_time_this_year()
        )
        
        # Adiciona 1-3 tags aleatórias ao post
        post_tags_to_add = random.sample(tags, k=random.randint(1, 3))
        post.tags.extend(post_tags_to_add)
        
        posts.append(post)
    return posts

def create_fake_reactions(users, posts):
    reactions = []
    reaction_types = ['LIKE', 'LOVE', 'SUPPORT', 'SAD']
    
    for post in posts:
        # Cria contagem de reações para cada post
        reaction_count = PostReactionCount(
            post_id=post.uuid,
            love=random.randint(0, 10),
            like=random.randint(0, 15),
            support=random.randint(0, 5),
            sad=random.randint(0, 3)
        )
        reactions.append(reaction_count)
        
        # Cria reações individuais de usuários
        reactors = random.sample(users, k=random.randint(0, len(users)))
        for user in reactors:
            reaction = PostReaction(
                user_id=user.uuid,
                post_id=post.uuid,
                reaction_type=random.choice(reaction_types),
                created_at=fake.date_time_this_year()
            )
            reactions.append(reaction)
    
    return reactions

def create_fake_bookmarks(users, posts):
    bookmarks = []
    for user in users:
        # Cada usuário marca 1-5 posts como favorito
        posts_to_bookmark = random.sample(posts, k=random.randint(1, 5))
        for post in posts_to_bookmark:
            bookmark = PostBookmark(
                uuid=uuid.uuid4(),
                post_id=post.uuid,
                user_id=user.uuid,
                created_at=fake.date_time_this_year()
            )
            bookmarks.append(bookmark)
    return bookmarks

def main():
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Criando dados fictícios...")
        
        # Cria usuários
        # users = create_fake_users()
        # db.add_all(users)
        # db.commit()
        
        # Cria tags
        tags = create_fake_tags()
        db.add_all(tags)
        db.commit()
        
        # Cria posts
        # posts = create_fake_posts(users, tags)
        # db.add_all(posts)
        # db.commit()
        
        # # Cria reações
        # reactions = create_fake_reactions(users, posts)
        # db.add_all(reactions)
        # db.commit()
        
        # # # Cria bookmarks
        # bookmarks = create_fake_bookmarks(users, posts)
        # db.add_all(bookmarks)
        # db.commit()
        
        print("Seed concluído com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"Erro durante o seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()