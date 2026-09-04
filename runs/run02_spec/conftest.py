"""把被测项目加入 sys.path"""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
TARGET = ROOT / "targets" / "pypinyin"
if str(TARGET) not in sys.path:
    sys.path.insert(0, str(TARGET))
