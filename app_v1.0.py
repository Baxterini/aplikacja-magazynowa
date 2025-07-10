import streamlit as st
import sqlite3
import pandas as pd
import io

# --- ZABEZPIECZENIE HASŁEM ---
haslo = st.text_input("🔒 Podaj hasło, aby uzyskać dostęp:", type="password")
if haslo != "demo2025":
    st.warning("Nieprawidłowe hasło. Dostęp zablokowany.")
    st.stop()

# --- BAZA DANYCH ---
conn = sqlite3.connect("produkty.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS produkty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nazwa TEXT NOT NULL,
        ilosc INTEGER NOT NULL,
        prog_alertu INTEGER,
        lokalizacja TEXT
    )
""")
conn.commit()

# --- FUNKCJE ---
def dodaj_produkt(nazwa, ilosc, prog, lokalizacja):
    c.execute("INSERT INTO produkty (nazwa, ilosc, prog_alertu, lokalizacja) VALUES (?, ?, ?, ?)",
              (nazwa, ilosc, prog, lokalizacja))
    conn.commit()

def pobierz_produkty():
    return pd.read_sql("SELECT * FROM produkty", conn)

def usun_produkt(id):
    c.execute("DELETE FROM produkty WHERE id = ?", (id,))
    conn.commit()

# --- INTERFEJS ---
st.set_page_config("Zarządzanie Stanem Magazynowym", layout="wide")
st.title("📦 System Zarządzania Magazynem")

menu = st.sidebar.selectbox("Wybierz opcję:", ["📋 Przegląd", "➕ Dodaj Produkt", "📥 Import danych"])

if menu == "📋 Przegląd":
    df = pobierz_produkty()
    st.subheader("📦 Lista Produktów")

    def koloruj_wiersz(val):
        if val["ilosc"] <= val["prog_alertu"]:
            return ["background-color: #ffcccc"] * len(val)
        else:
            return [""] * len(val)

    st.dataframe(df.style.apply(koloruj_wiersz, axis=1))

    # --- Eksport danych ---
    with st.expander("📤 Eksport danych"):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Pobierz jako CSV",
            data=csv,
            file_name="produkty_backup.csv",
            mime="text/csv"
        )

    if st.checkbox("🗑️ Usuń produkt"):
        id_do_usuniecia = st.number_input("Podaj ID produktu do usunięcia:", min_value=1, step=1)
        if st.button("Usuń"):
            usun_produkt(id_do_usuniecia)
            st.success(f"Usunięto produkt o ID {id_do_usuniecia}.")

elif menu == "➕ Dodaj Produkt":
    st.subheader("Dodaj nowy produkt")
    nazwa = st.text_input("Nazwa produktu")
    ilosc = st.number_input("Ilość", min_value=0, step=1)
    prog = st.number_input("Próg alertu", min_value=0, step=1)
    lokalizacja = st.text_input("Lokalizacja")

    if st.button("Dodaj"):
        if nazwa:
            dodaj_produkt(nazwa, ilosc, prog, lokalizacja)
            st.success("✅ Produkt dodany!")
        else:
            st.warning("⚠️ Podaj nazwę produktu!")

elif menu == "📥 Import danych":
    st.subheader("Importuj dane z pliku")
    uploaded_file = st.file_uploader("📄 Wczytaj plik CSV lub Excel", type=["csv", "xlsx"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df_import = pd.read_csv(uploaded_file)
        else:
            df_import = pd.read_excel(uploaded_file)

        st.write("Podgląd danych z pliku:")
        st.dataframe(df_import)

        if st.button("📤 Załaduj dane do bazy"):
            for _, row in df_import.iterrows():
                try:
                    dodaj_produkt(row["nazwa"], int(row["ilosc"]), int(row["prog_alertu"]), row["lokalizacja"])
                except Exception as e:
                    st.error(f"❌ Błąd przy wierszu: {row} | {e}")
            st.success("✅ Dane zostały zaimportowane do bazy!")
