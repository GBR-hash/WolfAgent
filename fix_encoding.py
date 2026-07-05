"""
WolfAgent ????????
??: python fix_encoding.py [????]
??????? app/ ??? .py ??
"""
import sys, os, glob

def detect_and_fix(filepath):
    """??????????? UTF-8?????????"""
    # ????????
    encodings = ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]
    best_text = None
    best_enc = None
    
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc) as f:
                text = f.read()
            best_text = text
            best_enc = enc
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if best_text is None:
        print(f"  SKIP {filepath}: cannot decode")
        return False
    
    # ????????: \ufffd? ? ??????
    fixes = [
        ("\ufffd\ufffd", "?"),   # ???? ? ?
        ("\ufffd?", "?"),         # ???+?? ? ?
        ("\ufffd", "?"),          # ???? ? ?
    ]
    
    changed = False
    for old, new in fixes:
        if old in best_text:
            best_text = best_text.replace(old, new)
            changed = True
    
    # ????? \n
    if "\r\n" in best_text:
        best_text = best_text.replace("\r\n", "\n")
        changed = True
    if "\r" in best_text:
        best_text = best_text.replace("\r", "\n")
        changed = True
    
    if changed or best_enc != "utf-8":
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(best_text)
        print(f"  FIXED {filepath} ({best_enc} ? utf-8)")
        return True
    
    print(f"  OK   {filepath} (utf-8)")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        targets = sys.argv[1:]
    else:
        targets = glob.glob("app/**/*.py", recursive=True) + ["main.py"]
    
    fixed = 0
    for t in targets:
        if os.path.isfile(t):
            if detect_and_fix(t):
                fixed += 1
    print(f"\nDone. Fixed {fixed} files.")
