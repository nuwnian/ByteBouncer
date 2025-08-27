#!/bin/bash
pip install -r requirements.txt
streamlit run bytebouncer/app.py --server.port=8000 --server.address=0.0.0.0 > streamlit.log 2>&1