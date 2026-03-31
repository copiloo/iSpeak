# ispeak/context_detector.py

import os
import sys

class ContextDetector:
    def __init__(self):
        self.platform = sys.platform

        if self.platform == "darwin":
            try:
                from AppKit import NSWorkspace
                self.workspace = NSWorkspace.sharedWorkspace()
                self.has_appkit = True
            except ImportError:
                print("Warning: AppKit not available. Install: pip install pyobjc-framework-Cocoa")
                self.has_appkit = False
        elif self.platform == "win32":
            try:
                import win32gui
                import win32process
                import psutil
                self._win32gui = win32gui
                self._win32process = win32process
                self._psutil = psutil
                self.has_win32 = True
            except ImportError:
                print("Warning: pywin32/psutil not available. Install: pip install pywin32 psutil")
                self.has_win32 = False
        else:
            self.has_appkit = False

    def get_current_context(self) -> dict:
        """
        Get context about current environment.
        Returns dict with: app_name, bundle_id, file_type
        """
        if self.platform == "darwin":
            return self._get_context_macos()
        elif self.platform == "win32":
            return self._get_context_windows()
        return self._unknown_context()

    def _get_context_macos(self) -> dict:
        if not self.has_appkit:
            return self._unknown_context()
        try:
            active_app = self.workspace.frontmostApplication()
            return {
                'app_name': active_app.localizedName(),
                'bundle_id': active_app.bundleIdentifier(),
                'file_type': self._guess_file_type_macos(active_app),
            }
        except Exception as e:
            print(f"Error getting macOS context: {e}")
            return self._unknown_context()

    def _get_context_windows(self) -> dict:
        if not self.has_win32:
            return self._unknown_context()
        try:
            hwnd = self._win32gui.GetForegroundWindow()
            _, pid = self._win32process.GetWindowThreadProcessId(hwnd)
            proc = self._psutil.Process(pid)
            exe_name = proc.name()  # e.g. "Code.exe"
            app_name = os.path.splitext(exe_name)[0]  # e.g. "Code"

            return {
                'app_name': app_name,
                'bundle_id': '',
                'file_type': self._guess_file_type_windows(app_name),
            }
        except Exception as e:
            print(f"Error getting Windows context: {e}")
            return self._unknown_context()

    def _guess_file_type_macos(self, app) -> str:
        app_name = app.localizedName()
        app_file_map = {
            'PyCharm': '.py',
            'IntelliJ IDEA': '.java',
            'WebStorm': '.js',
            'GoLand': '.go',
            'RubyMine': '.rb',
            'Xcode': '.swift',
            'Android Studio': '.kt',
            'TextEdit': '.txt',
        }
        for key, file_type in app_file_map.items():
            if key in app_name:
                return file_type
        return ''

    def _guess_file_type_windows(self, app_name: str) -> str:
        # Map exe names (without extension) to primary file types
        app_file_map = {
            'pycharm64': '.py',
            'pycharm': '.py',
            'idea64': '.java',
            'idea': '.java',
            'webstorm64': '.js',
            'webstorm': '.js',
            'goland64': '.go',
            'goland': '.go',
            'rubymine64': '.rb',
            'rubymine': '.rb',
            'studio64': '.kt',      # Android Studio
            'notepad': '.txt',
        }
        lower = app_name.lower()
        return app_file_map.get(lower, '')

    def _unknown_context(self) -> dict:
        return {'app_name': 'Unknown', 'bundle_id': '', 'file_type': ''}

    def is_code_editor(self, app_name: str) -> bool:
        """Check if given app is a code editor"""
        code_editors = [
            'Code', 'VS Code', 'Visual Studio Code', 'Cursor',
            'PyCharm', 'pycharm', 'IntelliJ', 'idea',
            'WebStorm', 'webstorm', 'GoLand', 'goland',
            'Xcode', 'Sublime Text', 'sublime_text', 'Atom',
            'TextMate', 'BBEdit', 'Nova', 'Fleet',
            'notepad++', 'Notepad++',
        ]
        return any(editor.lower() in app_name.lower() for editor in code_editors)
