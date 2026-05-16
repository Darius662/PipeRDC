#!/usr/bin/env python3
"""
PipeRDC - A modern RDP Connection Manager for Linux
"""

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from src.main import main

if __name__ == "__main__":
    sys.exit(main())