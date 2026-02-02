# ispeak/context_detector.py

import os
import sys

class ContextDetector:
    def __init__(self):
        self.platform = sys.platform

        if self.platform == "darwin":  # macOS
            try:
                from AppKit import NSWorkspace
                self.workspace = NSWorkspace.sharedWorkspace()
                self.has_appkit = True
            except ImportError:
                print("Warning: AppKit not available. Install: pip install pyobjc-framework-Cocoa")
                self.has_appkit = False
        else:
            self.has_appkit = False

    def get_current_context(self) -> dict:
        """
        Get context about current environment
        Returns dict with: app_name, bundle_id, file_type
        """
        if not self.has_appkit:
            return {
                'app_name': 'Unknown',
                'bundle_id': '',
                'file_type': '',
            }

        try:
            active_app = self.workspace.frontmostApplication()

            context = {
                'app_name': active_app.localizedName(),
                'bundle_id': active_app.bundleIdentifier(),
                'file_type': self._guess_file_type(active_app),
            }

            return context

        except Exception as e:
            print(f"Error getting context: {e}")
            return {
                'app_name': 'Unknown',
                'bundle_id': '',
                'file_type': '',
            }

    def _guess_file_type(self, app) -> str:
        """
        Try to determine what file user is editing
        This is a basic heuristic - could be improved with accessibility API
        Note: Returns empty string for generic code editors to avoid wrong assumptions
        """
        app_name = app.localizedName()

        # Map specialized IDEs to their primary file types
        # Generic editors (VS Code, Sublime) return empty since they're multi-language
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

        # Generic multi-language editors - return empty to avoid wrong assumptions
        # Code formatting will still apply based on app detection in is_code_editor()
        return ''

    def is_code_editor(self, app_name: str) -> bool:
        """Check if given app is a code editor"""
        code_editors = [
            'Code', 'VS Code', 'Visual Studio Code',
            'PyCharm', 'IntelliJ', 'WebStorm', 'GoLand',
            'Xcode', 'Sublime Text', 'Atom', 'Cursor',
            'TextMate', 'BBEdit', 'Nova'
        ]

        return any(editor.lower() in app_name.lower() for editor in code_editors)
