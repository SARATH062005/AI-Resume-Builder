#!/bin/bash

# A simple, robust installer script for the AI Resume Builder

# --- Configuration ---
APP_NAME="AI-Resume-Builder"
INSTALL_DIR="/opt/$APP_NAME"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"

# --- NEW: Automatically find the script's own directory ---
# This makes the script runnable from anywhere.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# --- Script Start ---
echo "Starting installation of AI Resume Builder..."

# Check for root privileges
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root. Please use sudo." >&2
  exit 1
fi

# 1. Copy Application Files
echo "--> Creating installation directory at $INSTALL_DIR..."
rm -rf "$INSTALL_DIR" # Remove old installation if it exists
mkdir -p "$INSTALL_DIR"
# MODIFIED: Use the SCRIPT_DIR variable to find the source files
cp -r "$SCRIPT_DIR/dist/$APP_NAME/"* "$INSTALL_DIR/"
chmod -R 755 "$INSTALL_DIR"

# 2. Create a symbolic link to the executable
echo "--> Creating executable link in $BIN_DIR..."
ln -sf "$INSTALL_DIR/$APP_NAME" "$BIN_DIR/ai-resume-builder"

# 3. Install the Desktop Entry (for the application menu)
echo "--> Creating menu entry..."
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/ai-resume-builder.desktop" <<EOL
[Desktop Entry]
Version=1.0
Name=AI Resume Builder
Comment=Create professional resumes with AI assistance
Exec=ai-resume-builder
Icon=$ICON_DIR/ai-resume-builder.png
Terminal=false
Type=Application
Categories=Office;
EOL

# 4. Install the Icon
echo "--> Installing application icon..."
mkdir -p "$ICON_DIR"
# MODIFIED: Use the SCRIPT_DIR variable to find the icon
cp "$SCRIPT_DIR/logo.png" "$ICON_DIR/ai-resume-builder.png"

# --- Finalization ---
echo ""
echo "Installation complete!"
echo "You can now run 'AI Resume Builder' from your application menu."
echo "To run from the terminal, just type: ai-resume-builder"
