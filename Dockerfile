# fitbot_project/Dockerfile

# Gunakan base image Python 3.9 yang ramping
FROM python:3.9-slim

# Tetapkan direktori kerja di dalam container
WORKDIR /app

# Salin file requirements terlebih dahulu untuk caching layer
COPY requirements.txt .

# Instal semua dependensi
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file proyek ke dalam direktori kerja
COPY . .

# Jalankan inisialisasi database saat build
RUN python database.py

# Ekspos port yang akan digunakan oleh Streamlit
EXPOSE 8501

# Perintah default untuk menjalankan aplikasi Streamlit saat container dimulai
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]