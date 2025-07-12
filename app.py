import streamlit as st
import requests, os, tempfile, zipfile
from bs4 import BeautifulSoup
from urllib.parse import urljoin

st.set_page_config(page_title="Comic Image Downloader", page_icon="📗")

st.title("Comic Image Downloader")
start_url = st.text_input("Enter starting page URL", "")

if st.button("Start Download") and start_url:
    progress = st.empty()
    status = st.empty()
    with tempfile.TemporaryDirectory() as tmpdir:
        saved_files = []
        page_url = start_url
        count = 0
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0"}
        while page_url:
            count += 1
            progress.write(f"Processing page {count}: {page_url}")
            try:
                r = session.get(page_url, headers=headers, timeout=15)
                r.raise_for_status()
            except Exception as e:
                status.error(f"Failed to fetch {page_url}: {e}")
                break
            soup = BeautifulSoup(r.text, "html.parser")
            img_tag = soup.select_one("img#img")
            if not img_tag or not img_tag.get("src"):
                status.error("Image not found on page, stopping.")
                break
            img_src = img_tag["src"]
            try:
                img_data = session.get(img_src, headers=headers, timeout=15).content
            except Exception as e:
                status.error(f"Failed to download image: {e}")
                break
            ext = os.path.splitext(img_src.split("?")[0])[1] or ".jpg"
            img_filename = os.path.join(tmpdir, f"{count:04d}{ext}")
            with open(img_filename, "wb") as f:
                f.write(img_data)
            saved_files.append(img_filename)
            next_tag = soup.select_one("a#next")
            if next_tag and next_tag.get("href"):
                page_url = urljoin(page_url, next_tag["href"])
            else:
                page_url = None
        if saved_files:
            zip_path = os.path.join(tmpdir, "comic_images.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in saved_files:
                    zipf.write(file_path, arcname=os.path.basename(file_path))
            with open(zip_path, "rb") as f:
                st.download_button("Download ZIP", f, file_name="comic_images.zip", mime="application/zip")
            status.success(f"Finished! {len(saved_files)} images downloaded.")
        else:
            status.warning("No images downloaded.")
