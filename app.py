import streamlit as st
import sqlite3
import pandas as pd
import io
from io import BytesIO

# --- INTERFEJS WSTĘPNY I SESJA LOGOWANIA ---
st.set_page_config("Zarządzanie Stanem Magazynowym", layout="wide")

if "zalogowany" not in st.session_state:
    st.session_state.zalogowany = False

if not st.session_state.zalogowany:
    st.title("🔐 Logowanie do systemu")
    haslo = st.text_input("Wprowadź hasło:", type="password")
    if st.button("Zaloguj") and haslo == "demo2025":
        st.session_state.zalogowany = True
        st.rerun()
    elif haslo and haslo != "demo2025":
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

def aktualizuj_produkt(id, nazwa, ilosc, prog_alertu, lokalizacja, cena):
    c.execute("""
        UPDATE produkty SET 
        nazwa = ?, 
        ilosc = ?, 
        prog_alertu = ?, 
        lokalizacja = ?, 
        cena = ? 
        WHERE id = ?
    """, (nazwa, ilosc, prog_alertu, lokalizacja, cena, id))
    conn.commit()

# --- SIDEBAR ---
with st.sidebar:
    st.title("📦 System Magazynowy")
    st.markdown("👤 Zalogowany jako: `demo2025`")

    uploaded = st.file_uploader("🔄 Załaduj plik CSV lub Excel, aby zresetować bazę", type=["csv", "xlsx"])

    if uploaded:
        if st.button("✅ Resetuj bazę z pliku"):
            try:
                if uploaded.name.endswith(".csv"):
                    df_reset = pd.read_csv(uploaded)
                else:
                    df_reset = pd.read_excel(uploaded)

                c.execute("DELETE FROM produkty")
                conn.commit()

                for _, row in df_reset.iterrows():
                    cena = float(row["cena"]) if "cena" in row else 0.0
                    dodaj_produkt(row["nazwa"], int(row["ilosc"]), int(row["prog_alertu"]), row["lokalizacja"], cena)

                st.success("✅ Baza została zresetowana z przesłanego pliku!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Błąd przy przetwarzaniu pliku: {e}")

    st.markdown("---")
    menu = st.selectbox("Wybierz opcję:", ["📋 Przegląd", "➕ Dodaj Produkt", "📥 Import danych"])

# --- WIDOKI ---
if menu == "📋 Przegląd":
    df = pobierz_produkty()

    if "cena" not in df.columns:
        df["cena"] = 0.0

    kolumny = ["id", "nazwa", "ilosc", "prog_alertu", "lokalizacja", "cena"]
    df = df[kolumny]
    df["cena"] = df["cena"].map(lambda x: round(x, 2))

    # Dodajemy kolumnę z alertem
    df["🔴 ALERT"] = df.apply(lambda row: "❗" if row["ilosc"] <= row["prog_alertu"] else "", axis=1)

    st.subheader("📦 Lista Produktów (edytowalna)")

    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    if st.button("💾 Zapisz zmiany"):
        for index, row in edited_df.iterrows():
            try:
                aktualizuj_produkt(
                    int(row["id"]),
                    row["nazwa"],
                    int(row["ilosc"]),
                    int(row["prog_alertu"]),
                    row["lokalizacja"],
                    float(row["cena"])
                )
            except Exception as e:
                st.error(f"❌ Błąd przy zapisie rekordu ID {row['id']}: {e}")
        st.success("✅ Zmiany zostały zapisane do bazy!")

    with st.expander("📤 Eksport danych"):
        export_df = pobierz_produkty()
        export_df["cena"] = export_df["cena"].map(lambda x: f"{x:.2f} zł")

        # Eksport CSV
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Pobierz jako CSV", data=csv, file_name="produkty_backup.csv", mime="text/csv")

        # Eksport Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, index=False, sheet_name="Produkty")
        st.download_button(
            label="⬇️ Pobierz jako Excel",
            data=buffer.getvalue(),
            file_name="produkty_backup.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if st.button("🚪 Wyloguj"):
        st.session_state.zalogowany = False
        st.rerun()

elif menu == "➕ Dodaj Produkt":
    st.subheader("Dodaj nowy produkt")
    nazwa = st.text_input("Nazwa produktu")
    ilosc = st.number_input("Ilość", min_value=0, step=1)
    prog = st.number_input("Próg alertu", min_value=0, step=1)
    lokalizacja = st.text_input("Lokalizacja")
    cena = st.number_input("Cena (zł)", min_value=0.0, step=0.1, format="%.2f")

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
        st.dataframe(df_import.reset_index(drop=True))

        if st.button("📤 Załaduj dane do bazy"):
            for _, row in df_import.iterrows():
                try:
                    cena = float(row["cena"]) if "cena" in row else 0.0
                    dodaj_produkt(row["nazwa"], int(row["ilosc"]), int(row["prog_alertu"]), row["lokalizacja"], cena)
                except Exception as e:
                    st.error(f"❌ Błąd przy wierszu: {row} | {e}")
            st.success("✅ Dane zostały zaimportowane do bazy!")
