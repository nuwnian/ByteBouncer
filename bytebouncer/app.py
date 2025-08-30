import streamlit as st
from azure.storage.blob import BlobServiceClient
# --- Sidebar: Azure Blob Storage Config ---
st.sidebar.header("Azure Blob Storage")
azure_conn_str = st.sidebar.text_input("Azure Connection String", type="password")
azure_container = st.sidebar.text_input("Container Name")

import streamlit as st
import os
import psutil
import plotly.express as px
from pathlib import Path
from datetime import datetime

# --- Helper Functions ---
def scan_directory(root_dirs, exclude_system=True, progress_callback=None, log_callback=None):
    file_data = []
    system_folders = [r"C:\\Windows", r"C:\\Program Files", r"C:\\Program Files (x86)"]
    total_dirs = 0
    for root_dir in root_dirs:
        for _ in os.walk(root_dir):
            total_dirs += 1
    scanned_dirs = 0
    for root_dir in root_dirs:
        for dirpath, _, filenames in os.walk(root_dir):
            if exclude_system and any(dirpath.startswith(sf) for sf in system_folders):
                continue
            for fname in filenames:
                try:
                    fpath = os.path.join(dirpath, fname)
                    stat = os.stat(fpath)
                    file_info = {
                        'path': fpath,
                        'size': stat.st_size,
                        'type': Path(fpath).suffix.lower(),
                        'last_modified': datetime.fromtimestamp(stat.st_mtime)
                    }
                    file_data.append(file_info)
                    if log_callback:
                        log_callback(fpath, stat.st_size)
                except Exception:
                    continue
            scanned_dirs += 1
            if progress_callback and total_dirs > 0:
                progress_callback(scanned_dirs / total_dirs)
    if progress_callback:
        progress_callback(1.0)
    return file_data

def categorize_file(f):
    sys_paths = [r"C:\\Windows", r"C:\\Program Files", r"C:\\Program Files (x86)"]
    temp_exts = ['.tmp', '.log', '.bak']
    temp_dirs = [os.environ.get('TEMP', ''), os.environ.get('TMP', '')]
    media_exts = ['.mp4', '.mp3', '.avi', '.mov', '.mkv', '.zip', '.rar', '.7z', '.tar', '.gz']
    user_exts = ['.docx', '.psd', '.jpg', '.png', '.pdf', '.xlsx', '.pptx', '.txt']
    if any(f['path'].startswith(p) for p in sys_paths):
        return 'System-critical'
    if any(f['type'] == ext for ext in temp_exts) or any(f['path'].startswith(td) for td in temp_dirs):
        return 'Temporary/Junk'
    if f['type'] in media_exts:
        return 'Large Media/Archive'
    if f['type'] in user_exts:
        return 'User-generated'
    return 'Other'

def get_move_suggestions(files):
    suggestions = []
    for f in files:
        if f['path'].startswith('C:') and categorize_file(f) in ['User-generated', 'Large Media/Archive'] and f['size'] > 50*1024*1024:
            suggestions.append(f)
    return suggestions

def get_junk_files(files):
    # Assign severity based on file type, size, or age
    junk_list = []
    for f in files:
        if categorize_file(f) == 'Temporary/Junk':
            # Example logic: High for .tmp >50MB, Medium for .log/.bak >10MB, else Low
            ext = f['type']
            size_mb = f['size'] / (1024 * 1024)
            if ext == '.tmp' and size_mb > 50:
                severity = 'High'
            elif ext in ['.log', '.bak'] and size_mb > 10:
                severity = 'Medium'
            else:
                severity = 'Low'
            f = f.copy()
            f['severity'] = severity
            junk_list.append(f)
    return junk_list

# --- Streamlit UI ---
st.set_page_config(page_title="ByteBouncer", layout="wide")
st.title("ByteBouncer 🧹")


# --- Sidebar: Drive Selection and Exclusions ---
st.sidebar.header("Scan Settings")
drives = []
if os.path.exists(r"C:\\"):
    drives.append("C:")
if os.path.exists(r"D:\\"):
    drives.append("D:")
selected_drives = st.sidebar.multiselect("Select drive(s) to scan", drives, default=drives)
exclude_system = st.sidebar.checkbox("Exclude system folders (Windows, Program Files)", value=True)


if st.sidebar.button("Scan Selected Drives"):
    with st.spinner("Scanning drives..."):
        # Delete old scan_log.txt if it exists
        try:
            os.remove("scan_log.txt")
        except FileNotFoundError:
            pass
        scan_paths = [d + "\\" for d in selected_drives]
        progress_bar = st.progress(0)
        log_file = open("scan_log.txt", "w", encoding="utf-8")
        def progress_callback(p):
            progress_bar.progress(min(int(p * 100), 100))
        def log_callback(path, size):
            log_file.write(f"{path}\t{size}\n")
        files = scan_directory(scan_paths, exclude_system=exclude_system, progress_callback=progress_callback, log_callback=log_callback)
        log_file.close()
        for f in files:
            f['category'] = categorize_file(f)
        st.session_state['files'] = files
        st.success("Scan complete! Log saved to scan_log.txt.")

files = st.session_state.get('files', [])

if files:

    import pandas as pd
    # Add a symbol for each category and HTML tooltip
    category_symbols = {
        'System-critical': '🛑',
        'Temporary/Junk': '🗑️',
        'Large Media/Archive': '🗄️',
        'User-generated': '📄',
        'Other': '❓'
    }
    df = pd.DataFrame(files)
    def symbol_with_tooltip(row):
        sym = category_symbols.get(row['category'], '')
        cat = row['category']
        return f'<span title="{cat}">{sym}</span>'
    df['symbol'] = df.apply(symbol_with_tooltip, axis=1)

    # Pie chart: file categories
    pie = df['category'].value_counts().reset_index()
    pie.columns = ['Category', 'Count']
    fig = px.pie(pie, names='Category', values='Count', title='File Categories')
    st.plotly_chart(fig, use_container_width=True)

    # Bar chart: top space hogs
    st.subheader("Top Space Hogs")
    top_files = df.sort_values('size', ascending=False).head(10)
    bar = px.bar(top_files, x='path', y='size', color='category', title='Top 10 Largest Files')
    st.plotly_chart(bar, use_container_width=True)
    # Show table with tooltips using st.markdown and HTML
    st.markdown("**Top 10 Largest Files** (hover over symbol for category)")
    top_files_html = top_files[['symbol', 'path', 'size', 'category']].to_html(escape=False, index=False)
    st.markdown(top_files_html, unsafe_allow_html=True)

    # Safe to Move
    st.subheader('Safe to Move Recommendations')
    move_suggestions = get_move_suggestions(files)
    if move_suggestions:
        total_savings = sum(f['size'] for f in move_suggestions)
        st.write(f"{len(move_suggestions)} large user/media files on C: are safe to move to D:. Estimated space savings: {total_savings/1024/1024:.2f} MB")
        move_df = pd.DataFrame(move_suggestions)[['path', 'size', 'category']]
        st.dataframe(move_df)
        if st.button('Simulate Move (Dry Run)'):
            st.success(f"Simulated moving {len(move_suggestions)} files. No files were actually moved.")
        # Azure upload for safe-to-move files
        if azure_conn_str and azure_container:
            selected_to_upload = st.multiselect('Select files to upload to Azure Blob:', move_df['path'].tolist(), key='move_upload')
            if st.button('Upload Selected to Azure Blob'):
                try:
                    bsc = BlobServiceClient.from_connection_string(azure_conn_str)
                    container_client = bsc.get_container_client(azure_container)
                    uploaded = 0
                    for path in selected_to_upload:
                        try:
                            blob_name = os.path.basename(path)
                            with open(path, 'rb') as data:
                                container_client.upload_blob(blob_name, data, overwrite=True)
                            uploaded += 1
                        except Exception as e:
                            st.warning(f"Failed to upload {path}: {e}")
                    st.success(f"Uploaded {uploaded} files to Azure Blob container '{azure_container}'.")
                except Exception as e:
                    st.error(f"Azure upload failed: {e}")
        else:
            st.info("Enter Azure connection string and container name in the sidebar to enable upload.")
    else:
        st.write("No large user/media files found on C: that are safe to move.")

    # Cleanup Suggestions
    st.subheader('Cleanup Suggestions')
    junk_files = get_junk_files(files)
    if junk_files:
        st.write(f"{len(junk_files)} junk/temporary files detected.")
        junk_df = pd.DataFrame(junk_files)[['path', 'size', 'last_modified', 'severity']]
        # Color code severity
        def color_severity(val):
            color = {'High': '#ff4d4d', 'Medium': '#ffd11a', 'Low': '#b3ff66'}.get(val, '')
            return f'background-color: {color}' if color else ''
        st.dataframe(junk_df.style.applymap(color_severity, subset=['severity']))
        selected_junk = st.multiselect('Select junk files to delete, archive, or upload:', junk_df['path'].tolist(), key='junk_select')
        if st.button('Delete Selected Junk Files'):
            deleted = 0
            failed = []
            for path in selected_junk:
                try:
                    os.remove(path)
                    deleted += 1
                except Exception as e:
                    failed.append((path, str(e)))
            st.success(f"Deleted {deleted} files.")
            if failed:
                st.warning(f"Failed to delete {len(failed)} files:")
                for fpath, err in failed:
                    st.text(f"{fpath}: {err}")
        if st.button('Archive Selected Junk Files (move to D:\\JunkArchive)'):
            archive_dir = r"D:\\JunkArchive"
            os.makedirs(archive_dir, exist_ok=True)
            archived = 0
            for path in selected_junk:
                try:
                    fname = os.path.basename(path)
                    dest = os.path.join(archive_dir, fname)
                    os.rename(path, dest)
                    archived += 1
                except Exception:
                    continue
            st.success(f"Archived {archived} files to {archive_dir}.")
        # Azure upload for junk files
        if azure_conn_str and azure_container:
            if st.button('Upload Selected Junk Files to Azure Blob'):
                try:
                    bsc = BlobServiceClient.from_connection_string(azure_conn_str)
                    container_client = bsc.get_container_client(azure_container)
                    uploaded = 0
                    for path in selected_junk:
                        try:
                            blob_name = os.path.basename(path)
                            with open(path, 'rb') as data:
                                container_client.upload_blob(blob_name, data, overwrite=True)
                            uploaded += 1
                        except Exception as e:
                            st.warning(f"Failed to upload {path}: {e}")
                    st.success(f"Uploaded {uploaded} junk files to Azure Blob container '{azure_container}'.")
                except Exception as e:
                    st.error(f"Azure upload failed: {e}")
        else:
            st.info("Enter Azure connection string and container name in the sidebar to enable upload.")
    else:
        st.write("No junk/temporary files found.")
else:
    st.info("Select drives and click 'Scan Selected Drives' to begin.")

st.sidebar.markdown("---")
tone = st.sidebar.radio("Tone", ["Technical", "Playful"])
if tone == "Playful":
    st.sidebar.success("Let's bounce some bytes! 🕺💾")
else:
    st.sidebar.info("Ready for disk analysis.")
