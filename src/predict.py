"""Demo dự đoán USD: python -m src.predict --example hoặc --input houses.csv."""
from pathlib import Path
import argparse
import json
import sys
import joblib
import pandas as pd
from .preprocessing import load_raw
from .modeling import predict_nonnegative

ROOT=Path(__file__).resolve().parents[1]

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description='Dự đoán giá nhà Ames bằng mô hình đã huấn luyện')
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--example',action='store_true'); group.add_argument('--input',type=Path)
    p.add_argument('--output',type=Path); args=p.parse_args()
    model_path=ROOT/'models/final_model.joblib'
    if not model_path.exists(): p.error('Chưa có model. Chạy python -m src.experiments trước.')
    model=joblib.load(model_path)
    if args.example:
        raw=load_raw(ROOT/'data/raw/AmesHousing.tsv')
        x=raw[raw['Yr Sold']==2010].head(5).drop(columns='SalePrice').copy()
    elif args.input.suffix.lower()=='.json':
        payload=json.loads(args.input.read_text(encoding='utf-8'))
        x=pd.DataFrame(payload if isinstance(payload,list) else [payload])
    else:
        x=pd.read_csv(args.input,keep_default_na=False,dtype={'PID':str,'MS SubClass':str})
    required=set(load_raw(ROOT/'data/raw/AmesHousing.tsv').columns)-{'Order','PID','SalePrice','Sale Type','Sale Condition'}
    missing=required-set(x.columns)
    if missing:p.error('Thiếu cột đầu vào: '+', '.join(sorted(missing)))
    result=pd.DataFrame({'prediction_usd':predict_nonnegative(model,x)})
    if 'PID' in x:result.insert(0,'PID',x.PID.to_numpy())
    print(result.to_string(index=False))
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); result.to_csv(args.output,index=False)

if __name__=='__main__':main()
