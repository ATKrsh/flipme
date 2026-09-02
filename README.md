# 👽 FlipMe - 3D Realistic Alive Alien Blob & Display Flipper

**FlipMe** is a sleek, semi-transparent floating desktop app featuring a hardware-accelerated **3D Realistic Alive Alien Blob**. Clicking on the alien blob instantly flips your Windows screen display orientation with a smooth bioluminescent fade transition.

---

## ✨ Features

- **3D Realistic Alive Alien Blob**:
  - Hardware-accelerated GLSL Raymarching shader running at 60 FPS.
  - Subsurface scattering, wet specular highlights, and Fresnel rim lighting.
  - Organic breathing, fluid pulsating tendrils, and dynamic jelly wobbling physics.
  - Glowing 3D alien eyes that track mouse cursor movement across the desktop.
- **Display Flipping Mechanics**:
  - **Left Click**: 3D Horizontal Flip Spin animation + Instant Horizontal Display Flip.
  - **Right Click**: 3D Vertical Flip Spin animation + Instant Vertical Display Flip.
  - **Fade Transition**: Instant flip action with a soft glowing fade transition flash.
- **Safety & Fail-safes**:
  - **Double-Click / Middle-Click**: Instantly resets screen to normal orientation (`0°`).
  - **Global Hotkey**: Press `Ctrl + Shift + R` anytime to restore default screen orientation.
  - **Auto-Revert Timer**: Optional 10-second safety auto-revert mode in system tray.
  - **System Tray Control**: Full context menu control for resetting, toggling "Always on Top", or exiting.

---

## 🚀 Quick Start

### Running from Python
```bash
python flipme.py
```

### Executable Build
The standalone executable `FlipMe_v1.exe` is located in the `dist/` directory.

---

## 🛠 Tech Stack

- **Python 3.12**
- **PyQt5** (`QOpenGLWidget`, `QSystemTrayIcon`)
- **GLSL Shaders** (Raymarching Signed Distance Functions)
- **Win32 API** (`ChangeDisplaySettingsExW`, `EnumDisplaySettingsW`)
- **PyInstaller** (Standalone executable build)
