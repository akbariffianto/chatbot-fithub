# fitbot_project/agent_logic.py

import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.prebuilt import create_react_agent

from database import DB_NAME, log_workout as log_workout_to_db

# --- 1. Definisikan Tools untuk Agen ---

@tool
def generate_workout_plan(goal: str, fitness_level: str, equipment: str) -> str:
    """
    Membuat rencana latihan yang dipersonalisasi berdasarkan input pengguna.
    Gunakan tool ini ketika pengguna secara eksplisit meminta rencana latihan baru.
    
    Args:
        goal (str): Tujuan utama pengguna (e.g., 'lose weight', 'build muscle').
        fitness_level (str): Tingkat kebugaran pengguna (e.g., 'beginner', 'intermediate').
        equipment (str): Peralatan yang tersedia (e.g., 'bodyweight only', 'dumbbells', 'full gym').
    """
    # Untuk versi ini, kita akan menggunakan LLM untuk membuat rencana secara dinamis
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    prompt = ChatPromptTemplate.from_template(
        """
        Buatkan rencana latihan yang detail dan terstruktur untuk seseorang dengan tujuan: {goal}, 
        tingkat kebugaran: {fitness_level}, dan peralatan yang tersedia: {equipment}.

        Rencana harus mencakup:
        1. Nama latihan (4-5 latihan).
        2. Jumlah set dan repetisi yang disarankan.
        3. Sedikit pemanasan dan pendinginan.

        Berikan jawaban dalam format markdown yang rapi.
        """
    )
    
    chain = prompt | llm
    response = chain.invoke({
        "goal": goal, 
        "fitness_level": fitness_level, 
        "equipment": equipment
    })
    return response.content

@tool
def log_workout(exercise_name: str, sets: int, reps: int, weight_kg: float = 0) -> str:
    """
    Mencatat sesi latihan yang telah diselesaikan oleh pengguna ke dalam database.
    Gunakan tool ini ketika pengguna menyatakan bahwa mereka telah menyelesaikan latihan.
    
    Args:
        exercise_name (str): Nama latihan yang diselesaikan.
        sets (int): Jumlah set yang diselesaikan.
        reps (int): Jumlah repetisi yang diselesaikan.
        weight_kg (float): Berat beban yang digunakan, default 0 jika bodyweight.
    """
    # Kita akan menggunakan user_id default untuk kesederhanaan
    return log_workout_to_db('default_user', exercise_name, sets, reps, weight_kg)


# --- 2. Setup SQL Assistant Tool ---

# Inisialisasi koneksi database untuk LangChain
db = SQLDatabase.from_uri(f"sqlite:///{DB_NAME}")
llm_sql = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# SQLDatabaseToolkit menyediakan serangkaian tools untuk berinteraksi dengan DB
# seperti "query_sql_db", "info_sql_db", dll.
sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm_sql)
sql_tools = sql_toolkit.get_tools()


# --- 3. Buat Agen Menggunakan LangGraph ---

def create_fitbot_agent():
    """
    Membangun dan mengembalikan agen ReAct yang stateful menggunakan LangGraph.
    Agen ini akan memiliki akses ke semua tools yang telah kita definisikan.
    """
    # Gabungkan semua tools
    all_tools = [generate_workout_plan, log_workout] + sql_tools
    
    # Inisialisasi LLM utama untuk agen
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )
    
    # System prompt untuk mengarahkan perilaku agen
    system_prompt = """
    Anda adalah FitBot, seorang asisten kebugaran AI yang ramah dan membantu.
    Tugas Anda adalah membantu pengguna mencapai tujuan kebugaran mereka.
    
    Anda memiliki akses ke beberapa alat (tools):
    1. `generate_workout_plan`: Untuk membuat rencana latihan baru.
    2. `log_workout`: Untuk mencatat latihan yang sudah selesai ke database.
    3. Tools SQL (`sql_db_query`, `sql_db_schema`, dll.): Untuk menjawab pertanyaan tentang riwayat latihan pengguna dari database.
    
    Alur Kerja:
    - Jika pengguna meminta rencana latihan, gunakan `generate_workout_plan`.
    - Jika pengguna mengatakan mereka telah selesai berlatih, ekstrak detailnya dan gunakan `log_workout`.
    - Jika pengguna bertanya tentang riwayat latihan mereka (misalnya, "kapan terakhir kali aku latihan?"), gunakan tools SQL untuk menemukan jawabannya.
    - Untuk pertanyaan umum tentang kebugaran, jawablah menggunakan pengetahuan Anda.
    
    Selalu berkomunikasi dengan cara yang jelas dan memotivasi.
    """
    
    # Create the prompt template that includes the system prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{messages}"),
        ("assistant", "Remaining steps: {remaining_steps}")
    ])
    
    # Create the agent with the prompt template
    agent_executor = create_react_agent(
        model=llm,
        tools=all_tools,
        prompt=prompt
    )
    
    return agent_executor