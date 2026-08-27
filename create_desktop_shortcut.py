r"""
Windows Desktop Shortcut Creator for Yakob Assistant.
Creates 1-click desktop shortcuts on your Windows Desktop (C:\Users\HP\Desktop)
that launch Yakob and Yakob Floating Widget silently without showing any black console window.
"""
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def create_shortcuts():
    desktop_dir = str(Path(os.path.expanduser("~")) / "Desktop").replace("\\", "/")
    project_dir = str(Path(__file__).resolve().parent).replace("\\", "/")
    
    python_dir = Path(sys.executable).parent
    pythonw_exe = str(python_dir / "pythonw.exe" if (python_dir / "pythonw.exe").exists() else Path(sys.executable)).replace("\\", "/")
    main_py = f"{project_dir}/main.py"

    vbs_script = f'''
Set WshShell = CreateObject("WScript.Shell")

' 1. Create Main App Shortcut
Set oLink = WshShell.CreateShortcut("{desktop_dir}/Yakob Assistant.lnk")
oLink.TargetPath = "{pythonw_exe}"
oLink.Arguments = """{main_py}"""
oLink.WorkingDirectory = "{project_dir}"
oLink.Description = "Yakob (ያዕቆብ) - Multilingual Voice Assistant"
oLink.Save

' 2. Create Floating Widget Shortcut
Set oWidgetLink = WshShell.CreateShortcut("{desktop_dir}/Yakob Widget.lnk")
oWidgetLink.TargetPath = "{pythonw_exe}"
oWidgetLink.Arguments = """{main_py}""" & " --widget"
oWidgetLink.WorkingDirectory = "{project_dir}"
oWidgetLink.Description = "Yakob Floating Desktop Widget"
oWidgetLink.Save
'''
    vbs_path = Path(__file__).resolve().parent / "make_shortcuts.vbs"
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_script)

    os.system(f'cscript //nologo "{vbs_path}"')
    if vbs_path.exists():
        vbs_path.unlink()

    print(f"✅ Desktop shortcuts created successfully at: {desktop_dir}")
    print(f"   1. 'Yakob Assistant.lnk' (Full App)")
    print(f"   2. 'Yakob Widget.lnk' (Floating Desktop Widget)")


if __name__ == "__main__":
    create_shortcuts()
