# Khush Salecha — Interactive Game Boy Color Portfolio

An authentic, ultra-polished 3D Game Boy Color interactive developer portfolio crafted in the exact style and engineering architecture of [sadok.mx](https://sadok.mx/).

---

## 🎮 Key Features

- **3D Interactive Game Boy Color Console**:
  - Full 3D model with orbital tilt, drag inspection, and click-responsive hardware controls (D-Pad, A/B buttons, Start/Select buttons, Power switch).
  - True-to-era Game Boy boot sequence and chime, authentic Pokémon-style chiptune sound effects, and volume toggle.
- **Title Screen & Interactive Menus**:
  - **Projects Showcase Carousel**: Cycle through featured engineering projects with pixel-dithered retro LCD video loops and live captions.
  - **About & Trainer Card Encounter**: Classic Pokémon battle transition triggering a 16-bit Trainer Card with pixel art avatar, gym badges, academic stats, technical stack, coursework, and story.
  - **Blog & Technical Notes**: Interactive typewriter-themed article archive covering IoT, local-first architecture, operating system scheduling, and AI integrations.
- **Docked Case Study Drawer**:
  - Pressing **A** (Enter / P) on any project smoothly slides up a full-width case study overlay with high-resolution hero videos, domain metadata, impact briefs, system architectures, and Pokémon-style Continue menus.
  - Pressing **B** (Backspace / L) or **Escape** slides back seamlessly to the 3D Game Boy.
- **Python Backend & SQLite Database (`contacts.db`)**:
  - Live Contact Me form on the About page and `/contact/` saving `name`, `number` (phone), `email`, and `message` directly into an SQLite database (`contacts.db`).
  - Interactive **SQLite Database Inspector** (`/database/`) to view all submissions in real-time with export-to-CSV functionality.
  - Native Python server (`server.py`) with zero external dependencies and HTTP Range video streaming.
- **100% Offline-Capable & Self-Contained**:
  - All 3D models (`gameboy.glb`), audio clips (`intro.mp3`, `violet.mp3`, `trainer-battle.mp3`, `ui.json`), pixel font atlases, webp posters, and hero videos are stored locally.
- **Accessible & SEO-Friendly**:
  - Full semantic HTML fallback list for search engines, screen readers, and environments without WebGL.
  - Real-time incrementing retro visitor counter.

---

## 🕹️ Controls

| Action | Keyboard | Game Boy Hardware |
| :--- | :--- | :--- |
| **Navigate Menu / Projects** | `↑ ↓ ← →` or `W A S D` | Click D-Pad buttons |
| **Confirm / Open Case Study (A)** | `Enter` or `P` | Click **A** button |
| **Back / Close Case Study (B)** | `Backspace` or `L` / `Esc` | Click **B** button |
| **Start / Pause** | `Space` | Click **Start** |
| **Select** | `Shift` | Click **Select** |
| **Mute / Unmute** | Sound toggle top-right | Click Speaker Icon |

---

## 🚀 How to Run Locally

### Using Python (Includes Full SQLite Backend API):
```bash
py server.py
# Server runs on http://localhost:8080
```

### Using Node.js:
```bash
npm start
# or: node server.js
```
Then open [http://localhost:8080](http://localhost:8080) in your web browser.

---

## 🌐 Deploying Online

Because this is a static site with client-side WebGL and clean routing, it can be deployed instantly to:
- **Vercel**: Run `vercel` or connect your GitHub repository.
- **Netlify**: Drag and drop the folder or connect your Git repo.
- **GitHub Pages**: Push this directory to your GitHub repository and enable GitHub Pages under repository settings.

---

## 📂 Project Directory Structure

```text
Khush/
├── index.html                   # Main landing page with 3D Game Boy canvas
├── ring-data.json               # Master configuration for models, loops, and projects
├── server.js                    # Local static server with byte-range video streaming
├── package.json                 # Node package configuration
├── models/                      # 3D GLTF/GLB models
│   └── gameboy.glb              # High-fidelity Game Boy Color 3D model
├── audio/                       # Audio sound effects and background music
│   ├── intro.mp3                # Game Boy boot sound
│   ├── violet.mp3               # Pokémon Violet showcase music loop
│   ├── trainer-battle.mp3       # Pokémon trainer encounter battle theme
│   ├── blog-intro.mp3           # Blog transition chime
│   └── ui.json                  # Button click and UI blip sprite data
├── atlas/                       # Pixel font atlases (JSON & PNG)
├── fonts/                       # Emerald-Bold WOFF2 font
├── media/hero/                  # 41 MP4 video loops & WebP hero posters
├── _astro/                      # Bundled Three.js engine, styles, and scripts
├── about/                       # Trainer Card & deep-dive profile
├── projects/                    # Plain accessible project list & case studies
│   ├── agriculture-platform/    # Smart Agriculture Platform case study
│   ├── smart-farming-iot/       # IoT & ESP32 Hardware Integration case study
│   ├── farmers-offline-software/# Farmers Offline Management case study
│   ├── festos-architecture/     # FestOS College Fest Architecture case study
│   ├── data-processing-engine/  # Python Systems Engine case study
│   └── apex-treasury-study/     # ApexTreasury Fintech Study case study
└── blog/                        # Technical writings and articles
    ├── iot-gateways-esp32/      # Low-cost IoT gateways with ESP32
    ├── local-first-agriculture/ # Local-first software for rural farming
    ├── process-scheduling-internals/ # CPU scheduling deep dive
    └── gemini-api-agriculture/  # Integrating Gemini API in web apps
```

---

Designed and engineered for **Khush Salecha** (AIML, Jain University).

