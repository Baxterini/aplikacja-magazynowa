# 📦 Aplikacja Streamlit – Zarządzanie Stanami Magazynowymi

To intuicyjna aplikacja webowa do zarządzania stanami magazynowymi z poziomu przeglądarki – bez potrzeby instalacji dodatkowego oprogramowania.

## 🔑 Funkcje

- 🔐 Logowanie z hasłem (domyślnie: `demo2025`)
- ➕ Dodawanie i edycja produktów
- 📊 Alerty niskiego stanu magazynowego
- ✏️ Edytowalna tabela z bezpośrednim zapisem do bazy
- 📥 Import danych z pliku CSV / Excel
- 📤 Eksport danych do CSV / Excel
- 🔄 Reset bazy z pliku
- 🚪 Wylogowanie

## 💾 Technologie

- Python + Streamlit
- SQLite (lokalna baza danych)
- Pandas
- XlsxWriter

## 🚀 Uruchomienie lokalne

```bash
# 1. Zainstaluj wymagane biblioteki
pip install -r requirements.txt

# 2. Uruchom aplikację
streamlit run app.py
