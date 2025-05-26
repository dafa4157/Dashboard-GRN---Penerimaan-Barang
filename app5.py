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
    if pd.isna(file_path) or file_path == "":
        return None
    if not os.path.exists(file_path):
        return None
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        data = f.read()
    return st.download_button(label=f"Download {filename}", data=data, file_name=filename)

# --- Session & Load ---
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False
if "data_updated" in st.session_state and st.session_state["data_updated"]:
    st.session_state["data_updated"] = False

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
                st.error("Nomor PO hanya boleh berisi angka (tanpa huruf atau simbol).")
            elif nomor_po in df["Nomor_PO"].astype(str).values:
                st.error(f"Nomor PO {nomor_po} sudah pernah diinput. Gunakan nomor yang berbeda.")
            else:
                po_path = ""
                if file_po is not None:
                    po_dir = "uploaded_po_user"  # folder khusus untuk file PO user
                    os.makedirs(po_dir, exist_ok=True)
                    safe_name = f"{nomor_po}_{file_po.name}"
                    po_path = os.path.join(po_dir, safe_name)
                    with open(po_path, "wb") as f:
                        f.write(file_po.getbuffer())
                    po_path = po_path.replace("\\", "/")

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
                st.session_state["data_updated"] = True
                st.experimental_rerun()

    st.subheader("📋 Daftar Barang & Status GRN")

    if df.empty:
        st.info("Belum ada data barang yang masuk.")
    else:
        display_df = df.copy()
        filtered_df = display_df[
            (display_df["Nomor_PO"].notna()) & (display_df["Nama_Vendor"].notna()) &
            (display_df["Nomor_PO"].astype(str).str.strip() != "") &
            (display_df["Nama_Vendor"].str.strip() != "")
        ].reset_index(drop=True)

        st.write(filtered_df[["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN"]])

        selected_index = st.selectbox("Pilih Nomor PO untuk download File PO (User Upload):",
                                      options=filtered_df.index,
                                      format_func=lambda x: f"{filtered_df.loc[x, 'Nomor_PO']} - {filtered_df.loc[x, 'Nama_Vendor']}")

        file_po_path = filtered_df.loc[selected_index, "File_PO_Path"]
        download_button = make_download_link(file_po_path)
        if download_button is None:
            st.write("File PO tidak tersedia atau tidak ditemukan.")

        st.markdown("---")
        st.markdown("**File GRN (Admin Upload):**")
        filtered_grn = filtered_df[filtered_df["File_GRN_Path"].notna() & (filtered_df["File_GRN_Path"] != "")]
        if filtered_grn.empty:
            st.write("Belum ada file GRN yang diupload admin.")
        else:
            selected_grn_index = st.selectbox("Pilih Nomor PO untuk download File GRN (Admin Upload):",
                                             options=filtered_grn.index,
                                             format_func=lambda x: f"{filtered_grn.loc[x, 'Nomor_PO']} - {filtered_grn.loc[x, 'Nama_Vendor']}")

            file_grn_path = filtered_grn.loc[selected_grn_index, "File_GRN_Path"]
            download_button_grn = make_download_link(file_grn_path)
            if download_button_grn is None:
                st.write("File GRN tidak tersedia atau tidak ditemukan.")

# --- ADMIN SECTION ---
st.sidebar.title("Admin Login")

if not st.session_state["admin_logged_in"]:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login = st.sidebar.button("Login sebagai Admin")

    if login:
        if username == "admin" and password == "admin123":
            st.session_state["admin_logged_in"] = True
            st.sidebar.success("Login berhasil!")
            st.experimental_rerun()
        else:
            st.sidebar.error("Username atau password salah.")
else:
    st.sidebar.success("Anda login sebagai admin.")
    if st.sidebar.button("Logout"):
        st.session_state["admin_logged_in"] = False
        st.experimental_rerun()

    st.subheader("🔍 Cari Data User (Admin Only)")
    search_po = st.text_input("Cari Nomor PO")
    search_vendor = st.text_input("Cari Nama Vendor")

    filtered_df_admin = df.copy()

    if search_po.strip() != "":
        filtered_df_admin = filtered_df_admin[filtered_df_admin["Nomor_PO"].astype(str).str.contains(search_po.strip(), case=False, na=False)]
    if search_vendor.strip() != "":
        filtered_df_admin = filtered_df_admin[filtered_df_admin["Nama_Vendor"].str.contains(search_vendor.strip(), case=False, na=False)]

    if filtered_df_admin.empty:
        st.warning("Data tidak ditemukan.")
    else:
        st.write(filtered_df_admin[["Tanggal", "Nomor_PO", "Nama_Vendor", "Status_GRN"]])

        st.markdown("**File PO User Upload:**")
        selected_po_user = st.selectbox(
            "Pilih Nomor PO untuk download File PO User",
            options=filtered_df_admin["Nomor_PO"].unique()
        )
        po_path_user = filtered_df_admin.loc[filtered_df_admin["Nomor_PO"] == selected_po_user, "File_PO_Path"].values
        if len(po_path_user) > 0 and po_path_user[0] != "" and os.path.exists(po_path_user[0]):
            with open(po_path_user[0], "rb") as f:
                st.download_button(
                    label=f"Download File PO User: {os.path.basename(po_path_user[0])}",
                    data=f,
                    file_name=os.path.basename(po_path_user[0]),
                )
        else:
            st.write("File PO User tidak tersedia atau tidak ditemukan.")

        st.markdown("---")
        st.markdown("**Update Status GRN dan Upload File GRN (Admin Only)**")

        selected_po = st.selectbox("Pilih Nomor PO untuk update", filtered_df_admin["Nomor_PO"].unique())
        file_grn = st.file_uploader("Upload File GRN (PDF/JPG/PNG)", type=["pdf", "jpg", "png"])

        if st.button("Tandai GRN Sudah Dibuat dan Simpan File GRN") and selected_po:
            grn_path = ""
            if file_grn is not None:
                grn_dir = "uploaded_grn"
                os.makedirs(grn_dir, exist_ok=True)
                safe_name = f"{selected_po}_{file_grn.name}"
                grn_path = os.path.join(grn_dir, safe_name)
                with open(grn_path, "wb") as f:
                    f.write(file_grn.getbuffer())
                grn_path = grn_path.replace("\\", "/")

            idx = df.index[df["Nomor_PO"] == selected_po


