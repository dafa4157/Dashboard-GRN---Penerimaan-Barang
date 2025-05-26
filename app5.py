import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "data.csv"

# --- Load Data ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        expected_cols = ["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN", "File_PO_Path", "File_GRN_Path"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        df = pd.DataFrame(columns=["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN", "File_PO_Path", "File_GRN_Path"])
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def make_download_link(file_path):
    if pd.isna(file_path) or file_path == "" or not os.path.exists(file_path):
        return None
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        data = f.read()
    return st.download_button(label=f"Download {filename}", data=data, file_name=filename)

# --- Session & Load ---
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

df = load_data()

# --- Judul Utama ---
st.title("📦 Dashboard GRN - Penerimaan Barang")

# --- USER SECTION ---
if not st.session_state["admin_logged_in"]:
    st.subheader("Input Barang Diterima (User)")

    with st.form("form_input"):
        tanggal = st.date_input("Tanggal Diterima", value=datetime.today())
        nomor_po = st.text_input("Nomor PO")
        vendor = st.text_input("Nama Vendor")
        file_po = st.file_uploader("Upload File PO (PDF/JPG/PNG)", type=["pdf", "jpg", "png"])
        submitted = st.form_submit_button("Simpan Data")

        if submitted:
            nomor_po = nomor_po.strip()
            vendor = vendor.strip()

            if nomor_po == "" or vendor == "":
                st.warning("Nomor PO dan Nama Vendor harus diisi.")
            elif not nomor_po.isdigit():
                st.error("Nomor PO hanya boleh berisi angka.")
            elif nomor_po in df["Nomor_PO"].astype(str).values:
                st.error(f"Nomor PO {nomor_po} sudah pernah diinput.")
            else:
                po_path = ""
                if file_po is not None:
                    po_dir = "uploaded_po"
                    os.makedirs(po_dir, exist_ok=True)
                    safe_name = f"{nomor_po}_{file_po.name}"
                    po_path = os.path.join(po_dir, safe_name).replace("\\", "/")
                    with open(po_path, "wb") as f:
                        f.write(file_po.getbuffer())

                new_row = {
                    "Tanggal": tanggal.strftime("%Y-%m-%d"),
                    "Nomor_PO": nomor_po,
                    "Nama_Vendor": vendor,
                    "Status_GRN": "Belum Dibuat",
                    "File_PO_Path": po_path,
                    "File_GRN_Path": ""
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("Data berhasil disimpan.")
                st.experimental_rerun()

    st.subheader("📋 Daftar Barang & Status GRN")

    if df.empty:
        st.info("Belum ada data.")
    else:
        st.write(df[["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN"]])

        filtered = df[df["File_PO_Path"] != ""]
        if not filtered.empty:
            idx = st.selectbox("Pilih File PO untuk Download:", filtered.index,
                               format_func=lambda x: f"{filtered.loc[x, 'Nomor_PO']} - {filtered.loc[x, 'Nama_Vendor']}")
            po_path = filtered.loc[idx, "File_PO_Path"]
            if make_download_link(po_path) is None:
                st.warning("File tidak ditemukan.")

        filtered_grn = df[df["File_GRN_Path"] != ""]
        if not filtered_grn.empty:
            idx = st.selectbox("Pilih File GRN:", filtered_grn.index,
                               format_func=lambda x: f"{filtered_grn.loc[x, 'Nomor_PO']} - {filtered_grn.loc[x, 'Nama_Vendor']}")
            grn_path = filtered_grn.loc[idx, "File_GRN_Path"]
            if make_download_link(grn_path) is None:
                st.warning("File tidak ditemukan.")

# --- ADMIN SECTION ---
st.sidebar.title("Admin Login")
if not st.session_state["admin_logged_in"]:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state["admin_logged_in"] = True
            st.experimental_rerun()
        else:
            st.sidebar.error("Login gagal.")
else:
    st.sidebar.success("Login sebagai admin")
    if st.sidebar.button("Logout"):
        st.session_state["admin_logged_in"] = False
        st.experimental_rerun()

    st.subheader("🔧 Panel Admin")
    st.write("Data Saat Ini:")
    st.dataframe(df[["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN"]])

    st.subheader("🔍 Cari File PO User")
    search_po = st.text_input("Cari Nomor PO")
    search_vendor = st.text_input("Cari Nama Vendor")

    filtered_admin = df.copy()
    if search_po:
        filtered_admin = filtered_admin[filtered_admin["Nomor_PO"].astype(str).str.contains(search_po, case=False)]
    if search_vendor:
        filtered_admin = filtered_admin[filtered_admin["Nama_Vendor"].str.contains(search_vendor, case=False)]

    if not filtered_admin.empty:
        pilihan = filtered_admin.apply(lambda row: f"Nomor PO: {row['Nomor_PO']} - Vendor: {row['Nama_Vendor']}", axis=1)
        selected = st.selectbox("Pilih File PO User", pilihan)
        idx = pilihan[pilihan == selected].index[0]
        path = filtered_admin.iloc[idx]["File_PO_Path"]
        if make_download_link(path) is None:
            st.warning("File tidak ditemukan.")
    else:
        st.info("Data tidak ditemukan.")

    st.subheader("📤 Upload File GRN")
    pilih_po = st.selectbox("Pilih PO untuk Upload GRN", df["Nomor_PO"].unique())
    file_grn = st.file_uploader("Upload File GRN", type=["pdf", "jpg", "png"])

    if st.button("Simpan GRN"):
        if file_grn is not None:
            grn_dir = "uploaded_grn"
            os.makedirs(grn_dir, exist_ok=True)
            safe_name = f"{pilih_po}_{file_grn.name}"
            grn_path = os.path.join(grn_dir, safe_name).replace("\\", "/")
            with open(grn_path, "wb") as f:
                f.write(file_grn.getbuffer())
            df.loc[df["Nomor_PO"] == pilih_po, "File_GRN_Path"] = grn_path
            df.loc[df["Nomor_PO"] == pilih_po, "Status_GRN"] = "Sudah Dibuat"
            save_data(df)
            st.success("File GRN berhasil diupload.")
            st.experimental_rerun()

    st.subheader("🧹 Hapus Duplikat Nomor PO")
    if st.button("Hapus Duplikat"):
        before = len(df)
        df = df.drop_duplicates(subset=["Nomor_PO"], keep="first")
        save_data(df)
        st.success(f"Duplikat dihapus. Total: {before} → {len(df)}")




