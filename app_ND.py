import streamlit as st
import sqlite3
import pandas as pd
import io

# --- INTERFEJS WSTĘPNY I SESJA LOGOWANIA ---
st.set_page_config("Zarządzanie Stanem Magazynowym", layout="wide")

placeholder = st.empty()

if "zalogowany" not in st.session_state:
    st.session_state.zalogowany = False

if not st.session_state.zalogowany:
    with placeholder.container():
        st.title("🔐 Logowanie do systemu")
        haslo = st.text_input("Wprowadź hasło:", type="password")
        if st.button("Zaloguj"):
            if haslo == "demo2025":
                st.session_state.zalogowany = True
                st.experimental_rerun()
            else:
                st.error("❌ Nieprawidłowe hasło.")
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
        lokalizacja TEXT,
        cena REAL DEFAULT 0.0
    )
""")
conn.commit()

# --- FUNKCJE ---
def dodaj_produkt(nazwa, ilosc, prog, lokalizacja, cena=0.0):
    c.execute("INSERT INTO produkty (nazwa, ilosc, prog_alertu, lokalizacja, cena) VALUES (?, ?, ?, ?, ?)",
              (nazwa, ilosc, prog, lokalizacja, cena))
    conn.commit()

def pobierz_produkty():
    return pd.read_sql("SELECT * FROM produkty", conn)

def usun_produkt(id):
    c.execute("DELETE FROM produkty WHERE id = ?", (id,))
    conn.commit()

def resetuj_baze_z_csv(sciezka):
    try:
        df = pd.read_csv(sciezka)
        c.execute("DELETE FROM produkty")
        conn.commit()
        for _, row in df.iterrows():
            cena = float(row["cena"]) if "cena" in row else 0.0
            dodaj_produkt(row["nazwa"], int(row["ilosc"]), int(row["prog_alertu"]), row["lokalizacja"], cena)
        st.success("✅ Baza została zresetowana z pliku CSV!")
    except Exception as e:
        st.error(f"❌ Błąd podczas resetowania bazy: {e}")

# --- SIDEBAR ---
with st.sidebar:
    st.title("📦 System Magazynowy")
    st.markdown("👤 Zalogowany jako: `demo2025`")

    if st.button("🔄 Resetuj bazę z demo CSV"):
        resetuj_baze_z_csv("produkty_demo.csv")
        st.experimental_rerun()

    st.markdown("---")
    menu = st.selectbox("Wybierz opcję:", ["📋 Przegląd", "➕ Dodaj Produkt", "📥 Import danych"])

# --- WIDOKI ---
if menu == "📋 Przegląd":
    df = pobierz_produkty()

    # Gwarancja kolumny 'cena'
    if "cena" not in df.columns:
        df["cena"] = 0.0

    kolumny = ["id", "nazwa", "ilosc", "prog_alertu", "lokalizacja", "cena"]
    df = df[kolumny]

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

    # --- Wylogowanie ---
    if st.button("🚪 Wyloguj"):
        st.session_state.zalogowany = False
        st.experimental_rerun()

elif menu == "➕ Dodaj Produkt":
    st.subheader("Dodaj nowy produkt")
    nazwa = st.text_input("Nazwa produktu")
    ilosc = st.number_input("Ilość", min_value=0, step=1)
    prog = st.number_input("Próg alertu", min_value=0, step=1)
    lokalizacja = st.text_input("Lokalizacja")
    cena = st.number_input("Cena (zł)", min_value=0.0, step=0.1)

    if st.button("Dodaj"):
        if nazwa:
            dodaj_produkt(nazwa, ilosc, prog, lokalizacja, cena)
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
                    cena = float(row["cena"]) if "cena" in row else 0.0
                    dodaj_produkt(row["nazwa"], int(row["ilosc"]), int(row["prog_alertu"]), row["lokalizacja"], cena)
                except Exception as e:
                    st.error(f"❌ Błąd przy wierszu: {row} | {e}")
            st.success("✅ Dane zostały zaimportowane do bazy!")
