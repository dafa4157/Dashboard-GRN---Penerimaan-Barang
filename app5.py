# ... tetap bagian atas sama (import, load_data, dsb)

# --- Load Data ---
df = load_data()

# --- Session State Setup ---
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False
if "selected_po_index" not in st.session_state:
    st.session_state["selected_po_index"] = None

# --- Admin Section ---
if st.session_state["admin_logged_in"]:
    st.sidebar.success("Anda login sebagai admin.")
    if st.sidebar.button("Logout"):
        st.session_state["admin_logged_in"] = False
        st.experimental_rerun()

    st.subheader("Cari File PO User & Upload GRN")

    search_po = st.text_input("Cari Nomor PO").strip()
    search_vendor = st.text_input("Cari Nama Vendor").strip()

    filtered_admin_df = df.copy()
    filtered_admin_df["Nomor_PO"] = filtered_admin_df["Nomor_PO"].astype(str).fillna("")
    filtered_admin_df["Nama_Vendor"] = filtered_admin_df["Nama_Vendor"].astype(str).fillna("")

    if search_po:
        filtered_admin_df = filtered_admin_df[filtered_admin_df["Nomor_PO"].str.contains(search_po, case=False, na=False)]
    if search_vendor:
        filtered_admin_df = filtered_admin_df[filtered_admin_df["Nama_Vendor"].str.contains(search_vendor, case=False, na=False)]

    if filtered_admin_df.empty:
        st.warning("Tidak ada hasil pencarian.")
    else:
        opsi = filtered_admin_df.apply(lambda r: f"Nomor PO: {r['Nomor_PO']} - Vendor: {r['Nama_Vendor']}", axis=1).tolist()
        selected_option = st.selectbox("Pilih data:", opsi)

        selected_index = opsi.index(selected_option)
        selected_data = filtered_admin_df.iloc[selected_index]
        st.session_state["selected_po_index"] = selected_data.name  # Simpan ke session

        # Tampilkan tombol download PO
        download_button = make_download_link(selected_data["File_PO_Path"])
        if download_button is None:
            st.info("File PO belum tersedia atau tidak ditemukan.")

        file_grn = st.file_uploader("Upload File GRN (PDF/JPG/PNG)", type=["pdf", "jpg", "png"])

        if st.button("Upload File GRN dan Update Status"):
            if not file_grn:
                st.warning("Silakan upload file GRN terlebih dahulu.")
            else:
                idx = st.session_state["selected_po_index"]
                selected_data = df.loc[idx]  # Ambil ulang dari dataframe utama

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





