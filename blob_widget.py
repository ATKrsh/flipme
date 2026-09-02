"""
blob_widget.py - 3D Realistic Alive Alien Blob Widget for FlipMe
Renders an interactive, translucent 3D raymarched alien blob using QOpenGLWidget & GLSL shaders.
Includes fluid wobble physics, mouse-tracking glowing 3D alien eyes, subsurface scattering,
instant display flipping, and smooth fade transitions on Left/Right click.
"""

import sys
import math
import time
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QSurfaceFormat, QOpenGLShader, QOpenGLShaderProgram, QCursor

VERTEX_SHADER_SRC = """
#version 330 core
layout(location = 0) in vec2 position;
out vec2 v_uv;

void main() {
    v_uv = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER_SRC = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_mouse;
uniform float u_flipX;       // Angle for vertical flip (X-axis rotation)
uniform float u_flipY;       // Angle for horizontal flip (Y-axis rotation)
uniform vec2 u_squish;       // (squishX, squishY) scale deformation
uniform float u_hover;        // Hover intensity 0..1
uniform float u_click_pulse;  // Bioluminescent flash trigger
uniform float u_fade;         // Fade transition intensity 0..1

#define MAX_STEPS 90
#define SURF_DIST 0.002
#define MAX_DIST 15.0

// Smooth minimum for organic fluid blob merging
float smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}

// 3D Rotation matrices
mat3 rotateX(float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return mat3(
        1.0, 0.0, 0.0,
        0.0, c,   -s,
        0.0, s,   c
    );
}

mat3 rotateY(float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return mat3(
        c,   0.0, s,
        0.0, 1.0, 0.0,
        -s,  0.0, c
    );
}

// Organic 3D Simplex-like noise approximation
float hash(vec3 p) {
    p = fract(p * vec3(443.897, 441.423, 437.195));
    p += dot(p, p.yzx + 19.19);
    return fract((p.x + p.y) * p.z);
}

float noise3D(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    
    return mix(
        mix(mix(hash(i + vec3(0,0,0)), hash(i + vec3(1,0,0)), f.x),
            mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
        mix(mix(hash(i + vec3(0,0,0.001)), hash(i + vec3(1,0,1)), f.x),
            mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
}

// Alien Blob Signed Distance Function (SDF)
float mapSDF(vec3 p, out int matID) {
    matID = 0; // 0 = Alien Skin, 1 = Eye Whites, 2 = Pupil/Iris
    
    // Apply squish/stretch deformation
    vec3 sp = p;
    sp.x /= u_squish.x;
    sp.y /= u_squish.y;
    
    // Apply 3D Flip rotations
    sp = rotateY(u_flipY) * rotateX(u_flipX) * sp;
    
    float t = u_time * 1.8;
    
    // Organic breathing & pulsing radius
    float pulse = sin(t * 2.0) * 0.06 + cos(t * 3.5) * 0.03;
    float baseRadius = 0.85 + pulse;
    
    // Multi-octave surface noise ripples (alive organic skin)
    float n1 = noise3D(sp * 2.2 + vec3(t * 0.5, t * 0.3, t * 0.4)) * 0.22;
    float n2 = noise3D(sp * 4.5 - vec3(t * 0.7, t * 0.9, t * 0.2)) * 0.09;
    
    // Main alien body sphere
    float dBody = length(sp) - (baseRadius + n1 + n2);
    
    // Orbiting mini-droplets (tentacles / fluid bio-blobs)
    for (int i = 0; i < 4; i++) {
        float fi = float(i);
        float angle = t * (0.8 + fi * 0.3) + fi * 1.57;
        vec3 dropPos = vec3(
            cos(angle) * (1.0 + sin(t + fi) * 0.2),
            sin(angle * 1.3) * 0.7,
            sin(angle) * (1.0 + cos(t + fi) * 0.2)
        );
        float dDrop = length(sp - dropPos) - (0.22 + sin(t * 3.0 + fi) * 0.05);
        dBody = smin(dBody, dDrop, 0.35);
    }
    
    // Alien Eyes (3D spherical eye cutouts that track mouse)
    vec3 mouseOffset = vec3((u_mouse.x - 0.5) * 0.5, (u_mouse.y - 0.5) * 0.5, 0.0);
    
    // Left Eye
    vec3 eyeL_Pos = vec3(-0.35, 0.25, 0.65) + mouseOffset * 0.3;
    float dEyeL = length(sp - eyeL_Pos) - 0.22;
    
    // Right Eye
    vec3 eyeR_Pos = vec3(0.35, 0.25, 0.65) + mouseOffset * 0.3;
    float dEyeR = length(sp - eyeR_Pos) - 0.22;
    
    // Third Center Eye (Alien feature!)
    vec3 eyeC_Pos = vec3(0.0, 0.52, 0.55) + mouseOffset * 0.4;
    float dEyeC = length(sp - eyeC_Pos) - 0.16;
    
    float dEyes = min(min(dEyeL, dEyeR), dEyeC);
    
    // Pupils
    vec3 pupilL_Pos = eyeL_Pos + vec3(mouseOffset.xy * 0.15, 0.15);
    float dPupilL = length(sp - pupilL_Pos) - 0.09;
    
    vec3 pupilR_Pos = eyeR_Pos + vec3(mouseOffset.xy * 0.15, 0.15);
    float dPupilR = length(sp - pupilR_Pos) - 0.09;
    
    vec3 pupilC_Pos = eyeC_Pos + vec3(mouseOffset.xy * 0.2, 0.12);
    float dPupilC = length(sp - pupilC_Pos) - 0.07;
    
    float dPupils = min(min(dPupilL, dPupilR), dPupilC);
    
    // Material blending
    if (dPupils < dBody && dPupils < dEyes) {
        matID = 2; // Glowing Pupil
        return dPupils;
    } else if (dEyes < dBody) {
        matID = 1; // Eye Sclera
        return dEyes;
    }
    
    matID = 0;
    return dBody;
}

// Calculate normal via gradient
vec3 calcNormal(vec3 p) {
    int dummy;
    float d = mapSDF(p, dummy);
    vec2 e = vec2(0.003, 0.0);
    vec3 n = d - vec3(
        mapSDF(p - e.xyy, dummy),
        mapSDF(p - e.yxy, dummy),
        mapSDF(p - e.yyx, dummy)
    );
    return normalize(n);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);
    
    // Ray origin and direction
    vec3 ro = vec3(0.0, 0.0, 3.2);
    vec3 rd = normalize(vec3(uv, -1.5));
    
    float dO = 0.0;
    int matID = 0;
    int hitMat = 0;
    vec3 p = ro;
    bool hit = false;
    
    for (int i = 0; i < MAX_STEPS; i++) {
        p = ro + rd * dO;
        float dS = mapSDF(p, matID);
        if (dS < SURF_DIST) {
            hit = true;
            hitMat = matID;
            break;
        }
        if (dO > MAX_DIST) break;
        dO += dS;
    }
    
    if (!hit) {
        // Transparent background
        fragColor = vec4(0.0, 0.0, 0.0, 0.0);
        return;
    }
    
    vec3 n = calcNormal(p);
    vec3 lightDir = normalize(vec3(0.8, 1.2, 1.5));
    vec3 viewDir = -rd;
    
    // Diffuse lighting
    float diff = max(dot(n, lightDir), 0.0);
    
    // Specular glossy reflection (wet liquid alien skin)
    vec3 halfDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(n, halfDir), 0.0), 32.0);
    
    // Fresnel rim light (glowing biological edge)
    float fresnel = pow(1.0 - max(dot(n, viewDir), 0.0), 3.0);
    
    // Subsurface Scattering (SSS) approximation
    float sss = pow(clamp(dot(-rd, n + lightDir * 0.5), 0.0, 1.0), 2.0) * 0.6;
    
    vec3 col = vec3(0.0);
    
    if (hitMat == 0) {
        // Alien Body Skin (Bioluminescent emerald / cyan / violet iridescent liquid)
        vec3 baseColor = mix(
            vec3(0.05, 0.85, 0.65), // Emerald Teal
            vec3(0.55, 0.15, 0.95), // Neon Purple
            sin(p.y * 2.0 + u_time) * 0.5 + 0.5
        );
        
        // Internal glowing core
        float coreGlow = sin(u_time * 4.0) * 0.15 + 0.85;
        vec3 coreColor = vec3(0.2, 0.95, 1.0) * coreGlow;
        
        col = baseColor * (diff * 0.6 + 0.3) + sss * coreColor;
        col += vec3(0.9, 1.0, 0.9) * spec * 0.85; // Wet glossy highlight
        col += vec3(0.3, 0.95, 0.8) * fresnel * (1.2 + u_hover * 0.5); // Fresnel rim
        
        // Bioluminescent click pulse flash
        col += vec3(0.8, 0.9, 1.0) * u_click_pulse * 0.6;
        
    } else if (hitMat == 1) {
        // Eye Sclera (Pearlescent alien eye white)
        col = vec3(0.85, 0.95, 0.9) * (diff * 0.7 + 0.4) + vec3(1.0) * spec;
        col += vec3(0.2, 0.8, 0.7) * fresnel * 0.5;
        
    } else if (hitMat == 2) {
        // Glowing Iris/Pupil (Bright bioluminescent cyan core)
        float pupilPulse = sin(u_time * 6.0) * 0.2 + 0.8;
        col = vec3(0.1, 1.0, 0.85) * pupilPulse * 1.6;
        col += vec3(1.0) * spec * 0.5;
    }
    
    // Fade Transition Glow Effect
    vec3 fadeGlow = vec3(0.4, 0.9, 1.0) * u_fade;
    col += fadeGlow;
    
    // Smooth alpha anti-aliasing edge & fade transition
    float alpha = clamp((1.0 - (dO / MAX_DIST)) * 1.5, 0.0, 1.0);
    alpha = mix(0.92, 1.0, fresnel);
    alpha *= (1.0 - u_fade * 0.25); // Smooth subtle fade transition

    fragColor = vec4(col, alpha);
}
"""

class AlienBlobWidget(QOpenGLWidget):
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()
    double_clicked = pyqtSignal()

    def __init__(self, display_manager=None, parent=None):
        super().__init__(parent)
        self.display_mgr = display_manager

        # Set transparent format
        fmt = QSurfaceFormat()
        fmt.setAlphaBufferSize(8)
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        self.setFormat(fmt)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.start_time = time.time()
        self.mouse_pos_normalized = (0.5, 0.5)

        # Physics & Animation states
        self.flip_angle_x = 0.0 # Vertical flip spin
        self.flip_angle_y = 0.0 # Horizontal flip spin
        self.target_flip_x = 0.0
        self.target_flip_y = 0.0

        self.squish_x = 1.0
        self.squish_y = 1.0
        self.squish_vel_x = 0.0
        self.squish_vel_y = 0.0

        self.hover_intensity = 0.0
        self.click_pulse = 0.0
        self.fade_transition = 0.0 # Fade transition parameter 0..1

        # Dragging & Click differentiation
        self.dragging = False
        self.press_pos = QPoint()
        self.drag_start_position = QPoint()
        self.last_window_pos = QPoint()
        self.pressed_button = None

        # Timer for 60 FPS rendering
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16) # ~60 FPS

        self.setMouseTracking(True)
        self.resize(320, 320)

    def initializeGL(self):
        self.shader = QOpenGLShaderProgram()
        v_ok = self.shader.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX_SHADER_SRC)
        f_ok = self.shader.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT_SHADER_SRC)
        if not (v_ok and f_ok and self.shader.link()):
            print("GLSL Shader link failed. Fallback state initialized.")

        # Quad vertex positions covering screen [-1, 1]
        self.vertices = [-1.0, -1.0,  1.0, -1.0, -1.0,  1.0,  1.0,  1.0]

    def paintGL(self):
        functions = self.context().functions()
        functions.glClearColor(0.0, 0.0, 0.0, 0.0)
        functions.glClear(0x00004000 | 0x00000100) # COLOR_BUFFER_BIT | DEPTH_BUFFER_BIT

        if not self.shader.isLinked():
            return

        self.shader.bind()
        elapsed = time.time() - self.start_time

        self.shader.setUniformValue("u_resolution", float(self.width()), float(self.height()))
        self.shader.setUniformValue("u_time", float(elapsed))
        self.shader.setUniformValue("u_mouse", self.mouse_pos_normalized[0], self.mouse_pos_normalized[1])
        self.shader.setUniformValue("u_flipX", float(self.flip_angle_x))
        self.shader.setUniformValue("u_flipY", float(self.flip_angle_y))
        self.shader.setUniformValue("u_squish", float(self.squish_x), float(self.squish_y))
        self.shader.setUniformValue("u_hover", float(self.hover_intensity))
        self.shader.setUniformValue("u_click_pulse", float(self.click_pulse))
        self.shader.setUniformValue("u_fade", float(self.fade_transition))

        self.shader.enableAttributeArray(0)
        self.shader.setAttributeArray(0, 0, self.vertices, 2)
        functions.glDrawArrays(0x0005, 0, 4) # GL_TRIANGLE_STRIP
        self.shader.disableAttributeArray(0)
        self.shader.release()

    def resizeGL(self, w, h):
        self.context().functions().glViewport(0, 0, w, h)

    def update_animation(self):
        # Smooth interpolation of 3D Flip rotations
        self.flip_angle_x += (self.target_flip_x - self.flip_angle_x) * 0.2
        self.flip_angle_y += (self.target_flip_y - self.flip_angle_y) * 0.2

        # Spring physics for squish deformation
        k = 0.28 # Spring stiffness
        d = 0.72 # Damping
        
        force_x = (1.0 - self.squish_x) * k
        self.squish_vel_x = (self.squish_vel_x + force_x) * d
        self.squish_x += self.squish_vel_x

        force_y = (1.0 - self.squish_y) * k
        self.squish_vel_y = (self.squish_vel_y + force_y) * d
        self.squish_y += self.squish_vel_y

        # Decay pulse & fade transition smoothly
        self.click_pulse *= 0.85
        self.fade_transition *= 0.82

        self.update()

    def mouseMoveEvent(self, event):
        self.mouse_pos_normalized = (event.x() / max(1, self.width()), 1.0 - (event.y() / max(1, self.height())))
        self.hover_intensity = 1.0

        if self.dragging:
            curr_pos = event.globalPos()
            delta = curr_pos - self.drag_start_position
            new_win_pos = self.pos() + delta
            self.move(new_win_pos)
            self.drag_start_position = curr_pos

            # Inertia squish based on drag velocity
            move_delta = new_win_pos - self.last_window_pos
            self.last_window_pos = new_win_pos
            self.squish_vel_x += move_delta.x() * 0.005
            self.squish_vel_y -= move_delta.y() * 0.005

    def enterEvent(self, event):
        self.hover_intensity = 1.0

    def leaveEvent(self, event):
        self.hover_intensity = 0.0
        self.mouse_pos_normalized = (0.5, 0.5)

    def trigger_fade_flash(self):
        """Triggers an instant bioluminescent flash with a smooth fade transition."""
        self.fade_transition = 1.0
        self.click_pulse = 1.0

    def contextMenuEvent(self, event):
        """Suppress default Qt context menu so right click directly triggers vertical flip!"""
        event.accept()

    def mousePressEvent(self, event):
        self.pressed_button = event.button()
        self.press_pos = event.globalPos()

        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_position = event.globalPos()
            self.last_window_pos = self.pos()
            
            # Instant press reaction
            self.squish_vel_x += 0.35
            self.squish_vel_y -= 0.25
            self.click_pulse = 0.6

        elif event.button() == Qt.RightButton:
            # Instant right press reaction
            self.squish_vel_y += 0.35
            self.squish_vel_x -= 0.25
            self.click_pulse = 0.6

    def mouseReleaseEvent(self, event):
        drag_dist = (event.globalPos() - self.press_pos).manhattanLength()

        if event.button() == Qt.LeftButton:
            self.dragging = False
            # Only trigger flip if release happened without dragging window far
            if drag_dist < 8:
                self.target_flip_y += math.pi # 180 deg spin
                self.trigger_fade_flash()
                self.left_clicked.emit()

        elif event.button() == Qt.RightButton:
            if drag_dist < 8:
                self.target_flip_x += math.pi # 180 deg spin
                self.trigger_fade_flash()
                self.right_clicked.emit()

    def mouseDoubleClickEvent(self, event):
        self.trigger_fade_flash()
        self.squish_vel_x += 0.5
        self.squish_vel_y += 0.5
        self.double_clicked.emit()
