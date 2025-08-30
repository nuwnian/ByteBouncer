# ByteBouncer

ByteBouncer is a disk space analyzer and file management assistant for Windows, built with Python and Streamlit. It helps you scan your drives, categorize files, and safely clean up disk space.

## Features

- Recursively scans C: and D: drives (or any available drive)
- Categorizes files as system, user, temporary/junk, large media/archive, or other
- Recommends large files that are safe to move from C: to D:
- Visualizes disk usage with charts and tables
- Allows deletion or archiving of junk/temporary files
- (Optional) Uploads selected files to Azure Blob Storage

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ByteBouncer.git
   cd ByteBouncer
   ```
2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the app locally:
   ```
   streamlit run bytebouncer/app.py
   ```
2. In your browser, select the drives you want to scan and click "Scan Selected Drives".
3. Review the results, recommendations, and take action (delete, archive, or move files).

> **Note:**  
> ByteBouncer is designed for local use. It cannot scan or clean files on remote/cloud systems when deployed to Azure or other cloud platforms.

## Optional: Azure Blob Storage Integration

- Enter your Azure connection string and container name in the sidebar to enable file uploads to Azure Blob Storage.
- This is useful for backing up files before deletion or archiving.

## Requirements

- Python 3.8+
- Windows OS (tested on Windows 10/11)
- See `requirements.txt` for Python dependencies

## Limitations

- The app cannot access or clean files on your computer if run from the cloud (e.g., Azure App Service).
- Use locally for full functionality.

## License

MIT License
