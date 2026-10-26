"""Tái tạo dữ liệu và thực nghiệm: python -m src.run_all."""
import subprocess
import sys
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    steps=[['-m','src.kt1'],['-m','src.experiments'],['-m','src.plots'],
           ['docs/build_notebook.py'],['docs/build_model_notebooks.py'],
           ['docs/build_latex.py'],['docs/build_full_report.py'],['docs/build_readme.py'],
           ['-m','unittest','discover','-s','tests','-v']]
    for step in steps:
        print('RUN',*step,flush=True)
        env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
        subprocess.run([sys.executable,*step],cwd=ROOT,check=True,env=env)
if __name__=='__main__':main()
