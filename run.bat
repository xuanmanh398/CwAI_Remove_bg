@echo off
title AI Video Background Remover
echo ========================================================
echo   DANG KHOI DONG PHAN MEM XOA NEN VIDEO AI (WEB GUI)
echo ========================================================
python -m streamlit run app.py --server.port 8501 --server.headless false
pause
