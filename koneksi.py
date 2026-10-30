import streamlit as st
from supabase import create_client

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

kolom_x = ["harga_beras", "harga_minyak_goreng", "harga_gula_pasir",
           "harga_daging_sapi", "harga_telur_ayam"]
kolom_y = "harga_ayam"
semua_kolom = ["tanggal"] + kolom_x + [kolom_y]
