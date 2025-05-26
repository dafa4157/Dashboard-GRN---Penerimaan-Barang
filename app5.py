import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "data.csv"

# Fungsi load data dari CSV
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

# Fungsi simpan data ke CSV
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Fungsi buat tombol download file
def make_download_link(file_path):
    if pd.isna(file_path) or file_path == "" or not os.path.exists(file_path):
        return None
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        return st.download_button(label=f"Download {filename}", data=f, file_name=filename)

# Inisialisasi session_state login admin
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

# Load data awal
df = load_data()

st.title("📦 Dashboard GRN - Penerimaan Barang")

# Sidebar untuk login admin
st.sidebar.title("Admin Login")
if not st.session_state["admin_logged_in"]:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state["admin_logged_in"] = True
            st.experimental_rerun()  # <- fix
        else:
            st.sidebar.error("Username atau password salah.")
else:
    st.sidebar.success("Anda login sebagai admin.")
    if st.sidebar.button("Logout"):
        st.session_state["admin_logged_in"] = False
        st.experimental_rerun()  # <- fix

# Konten utama berdasarkan role
if st.session_state["admin_logged_in"]:
    # Panel admin
    st.subheader("📊 Rekap Data User & Status GRN")
    if df.empty:
        st.info("Belum ada data.")
    else:
        def status_badge(status):
            return f"✅ {status}" if status == "Sudah Dibuat" else f"❌ {status}"

        display_df = df.copy()
        display_df["Status_GRN"] = display_df["Status_GRN"].apply(status_badge)
        st.table(display_df[["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN"]])

    st.subheader("📥 Cari File PO User & Upload GRN")

    search_po = st.text_input("Cari Nomor PO")
    search_vendor = st.text_input("Cari Nama Vendor")
    filtered_admin_df = df.copy()

    if search_po:
        filtered_admin_df = filtered_admin_df[filtered_admin_df["Nomor_PO"].astype(str).str.contains(search_po, case=False)]
    if search_vendor:
        filtered_admin_df = filtered_admin_df[filtered_admin_df["Nama_Vendor"].str.contains(search_vendor, case=False)]

    if filtered_admin_df.empty:
        st.warning("Tidak ada hasil pencarian.")
    else:
        opsi = filtered_admin_df.apply(lambda r: f"Nomor PO: {r['Nomor_PO']} - Vendor: {r['Nama_Vendor']}", axis=1).tolist()
        selected_row = st.selectbox("Pilih data:", opsi)
        idx = opsi.index(selected_row)
        selected_data = filtered_admin_df.iloc[idx]

        po_download = make_download_link(selected_data["File_PO_Path"])
        if po_download is None:
            st.info("File PO belum diupload user.")

        file_grn = st.file_uploader("Upload File GRN (PDF/JPG/PNG)", type=["pdf", "jpg", "png"])
        if st.button("Upload File GRN dan Update Status"):
            if file_grn is not None:
                grn_dir = "uploaded_grn"
                os.makedirs(grn_dir, exist_ok=True)
                safe_name = f"{selected_data['Nomor_PO']}_{file_grn.name}"
                grn_path = os.path.join(grn_dir, safe_name).replace("\\", "/")
                with open(grn_path, "wb") as f:
                    f.write(file_grn.getbuffer())

                df.loc[df["Nomor_PO"] == selected_data["Nomor_PO"], "Status_GRN"] = "Sudah Dibuat"
                df.loc[df["Nomor_PO"] == selected_data["Nomor_PO"], "File_GRN_Path"] = grn_path
                save_data(df)
                st.success("File GRN berhasil diupload dan status diperbarui.")
                st.experimental_rerun()  # <- fix
            else:
                st.warning("Silakan pilih file GRN terlebih dahulu.")

    st.subheader("🧹 Hapus Duplikat Nomor PO")
    if st.button("Hapus Duplikat"):
        before = len(df)
        df = df.drop_duplicates(subset="Nomor_PO", keep="first")
        save_data(df)
        after = len(df)
        st.success(f"Duplikat dihapus. Sebelum: {before}, Sesudah: {after}")
        st.experimental_rerun()  # <- fix

else:
    # Panel user input
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
                st.experimental_rerun()  # <- fix

    st.subheader("📋 Daftar Barang & Status GRN")
    if df.empty:
        st.info("Belum ada data.")
    else:
        st.write(df[["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN"]])

        filtered_df = df[(df["File_PO_Path"] != "") & df["File_PO_Path"].notna()]
        if not filtered_df.empty:
            idx = st.selectbox("Pilih Nomor PO (User Upload):", options=filtered_df.index,
                               format_func=lambda i: f"{filtered_df.loc[i, 'Nomor_PO']} - {filtered_df.loc[i, 'Nama_Vendor']}")
            make_download_link(filtered_df.loc[idx, "File_PO_Path"])

        filtered_grn = df[(df["File_GRN_Path"] != "") & df["File_GRN_Path"].notna()]
        if not filtered_grn.empty:
            idx2 = st.selectbox("Pilih Nomor PO (Admin GRN):", options=filtered_grn.index,
                                format_func=lambda i: f"{filtered_grn.loc[i, 'Nomor_PO']} - {filtered_grn.loc[i, 'Nama_Vendor']}")
            make_download_link(filtered_grn.loc[idx2, "File_GRN_Path"])







