"""把被测项目加入 sys.path，避免依赖 editable install（其 finder 依赖 cwd，不可靠）"""
import sys, pathlib
ROOT = pathlib.Path(__file__).parent.resolve()
TARGET = ROOT / "targets" / "pypinyin"
if str(TARGET) not in sys.path:
    sys.path.insert(0, str(TARGET))
