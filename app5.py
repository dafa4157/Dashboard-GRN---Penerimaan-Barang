import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Konstanta ---
DATA_FILE = "data.csv"

# --- Fungsi ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            expected_cols = ["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN", "File_PO_Path", "File_GRN_Path"]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception as e:
            st.error(f"Gagal memuat data: {e}")
            return pd.DataFrame(columns=expected_cols)
    else:
        df = pd.DataFrame(columns=["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN", "File_PO_Path", "File_GRN_Path"])
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    try:
        df.to_csv(DATA_FILE, index=False)
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")

def make_download_link(file_path):
    if pd.isna(file_path) or file_path == "" or not os.path.exists(file_path):
        return None
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        return st.download_button(label=f"Download {filename}", data=f, file_name=filename)

def colored_status(status):
    if status == "Sudah Dibuat":
        return "✅ Sudah Dibuat"
    elif status == "Belum Dibuat":
        return "❌ Belum Dibuat"
    else:
        return status

# --- Setup session state ---
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False
if "selected_po_index" not in st.session_state:
    st.session_state["selected_po_index"] = None

# --- Load data ---
df = load_data()

# --- Judul utama ---
st.title("Dashboard GRN - Penerimaan Barang")

# --- Admin Section ---
if st.session_state["admin_logged_in"]:
    st.sidebar.success("Anda login sebagai admin.")
    if st.sidebar.button("Logout"):
        st.session_state["admin_logged_in"] = False
        st.experimental_rerun()

    st.subheader("Rekap Data User & Status GRN")
    if df.empty:
        st.info("Belum ada data.")
    else:
        df_display = df.copy()
        df_display["Status"] = df_display["Status_GRN"].apply(colored_status)
        st.dataframe(df_display[["Tanggal", "Nomor_PO", "Nama_Vendor", "Status"]])

    st.subheader("Cari File PO User & Upload GRN")
    search_po = st.text_input("Cari Nomor PO").strip()
    search_vendor = st.text_input("Cari Nama Vendor").strip()

    filtered_df = df.copy()
    filtered_df["Nomor_PO"] = filtered_df["Nomor_PO"].astype(str)
    filtered_df["Nama_Vendor"] = filtered_df["Nama_Vendor"].astype(str)

    if search_po:
        filtered_df = filtered_df[filtered_df["Nomor_PO"].str.contains(search_po, case=False, na=False)]
    if search_vendor:
        filtered_df = filtered_df[filtered_df["Nama_Vendor"].str.contains(search_vendor, case=False, na=False)]

    if not filtered_df.empty:
        options = filtered_df.apply(lambda r: f"Nomor PO: {r['Nomor_PO']} - Vendor: {r['Nama_Vendor']}", axis=1).tolist()
        selected_option = st.selectbox("Pilih data:", options)
        selected_index = options.index(selected_option)
        selected_data = filtered_df.iloc[selected_index]
        st.session_state["selected_po_index"] = selected_data.name

        download_button = make_download_link(selected_data["File_PO_Path"])
        if download_button is None:
            st.info("File PO belum tersedia atau tidak ditemukan.")

        file_grn = st.file_uploader("Upload File GRN (PDF/JPG/PNG)", type=["pdf", "jpg", "png"])
        if st.button("Upload File GRN dan Update Status"):
            if not file_grn:
                st.warning("Silakan upload file GRN terlebih dahulu.")
            else:
                idx = st.session_state["selected_po_index"]
                selected_data = df.loc[idx]

                grn_dir = "uploaded_grn"
                os.makedirs(grn_dir, exist_ok=True)
                safe_name = f"{selected_data['Nomor_PO']}_{file_grn.name}"
                grn_path = os.path.join(grn_dir, safe_name).replace("\\", "/")
                with open(grn_path, "wb") as f:
                    f.write(file_grn.getbuffer())

                df.loc[idx, "Status_GRN"] = "Sudah Dibuat"
                df.loc[idx, "File_GRN_Path"] = grn_path
                save_data(df)
                st.success("File GRN berhasil diupload dan status diperbarui.")
                st.experimental_rerun()
    else:
        st.warning("Tidak ada hasil pencarian.")

    st.subheader("Hapus Duplikat Nomor PO")
    if st.button("Hapus Duplikat"):
        before = len(df)
        df = df.drop_duplicates(subset="Nomor_PO", keep="first")
        save_data(df)
        after = len(df)
        st.success(f"Duplikat dihapus. Sebelum: {before}, Sesudah: {after}")
        st.experimental_rerun()

# --- User Section ---
else:
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
                st.error(f"Nomor PO {nomor_po} sudah ada.")
            else:
                po_path = ""
                if file_po:
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

    st.subheader("Daftar Barang & Status GRN")
    if df.empty:
        st.info("Belum ada data.")
    else:
        st.write(df[["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN"]])

        filtered_df = df[(df["File_PO_Path"] != "") & df["File_PO_Path"].notna()]
        if not filtered_df.empty:
            idx = st.selectbox("Pilih Nomor PO (User Upload):", options=filtered_df.index,
                               format_func=lambda i: f"{filtered_df.loc[i, 'Nomor_PO']} - {filtered_df.loc[i, 'Nama_Vendor']}")
            download_button = make_download_link(filtered_df.loc[idx, "File_PO_Path"])
            if download_button is None:
                st.info("File PO belum tersedia atau tidak ditemukan.")

        filtered_grn = df[(df["File_GRN_Path"] != "") & df["File_GRN_Path"].notna()]
        if not filtered_grn.empty:
            idx2 = st.selectbox("Pilih Nomor PO (Admin GRN):", options=filtered_grn.index,
                                format_func=lambda i: f"{filtered_grn.loc[i, 'Nomor_PO']} - {filtered_grn.loc[i, 'Nama_Vendor']}")
            download_button2 = make_download_link(filtered_grn.loc[idx2, "File_GRN_Path"])
            if download_button2 is None:
                st.info("File GRN belum tersedia atau tidak ditemukan.")

# --- Admin Login ---
st.sidebar.title("Admin Login")
if not st.session_state["admin_logged_in"]:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state["admin_logged_in"] = True
            st.experimental_rerun()
        else:
            st.sidebar.error("Username atau password salah.")





