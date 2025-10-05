# fitbot_project/database.py

import sqlite3
from datetime import datetime

DB_NAME = "fitbot.db"

def init_db():
    """
    Menginisialisasi database dan membuat tabel workouts jika belum ada.
    Skema ini akan menyimpan riwayat latihan setiap pengguna.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Membuat tabel untuk mencatat sesi latihan
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        session_date TEXT NOT NULL,
        exercise_name TEXT NOT NULL,
        sets INTEGER NOT NULL,
        reps INTEGER NOT NULL,
        weight_kg REAL
    )
    """)
    
    conn.commit()
    conn.close()
    print("Database berhasil diinisialisasi.")

def log_workout(user_id: str, exercise_name: str, sets: int, reps: int, weight_kg: float = 0):
    """
    Mencatat satu sesi latihan ke dalam database.
    
    Args:
        user_id (str): ID unik untuk pengguna (dalam aplikasi ini kita gunakan 'default_user').
        exercise_name (str): Nama latihan yang dilakukan.
        sets (int): Jumlah set.
        reps (int): Jumlah repetisi per set.
        weight_kg (float): Berat beban yang digunakan (opsional).
        
    Returns:
        str: Pesan konfirmasi bahwa latihan berhasil dicatat.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    session_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute("""
        INSERT INTO workouts (user_id, session_date, exercise_name, sets, reps, weight_kg)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, session_date, exercise_name, sets, reps, weight_kg))
        
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        return f"Gagal mencatat latihan: {e}"
    
    conn.close()
    return f"Berhasil mencatat latihan: {exercise_name} ({sets} set x {reps} reps)."

# Jalankan file ini secara langsung untuk membuat database saat pertama kali
if __name__ == "__main__":
    init_db()