# Curriculum Curator

A desktop-first, privacy-focused tool for generating weekly educational content using AI. Built with Tauri for native performance and user experience.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Tauri](https://img.shields.io/badge/Tauri-2.5-blue.svg)
![React](https://img.shields.io/badge/React-19.1-blue.svg)
![Rust](https://img.shields.io/badge/Rust-1.70+-orange.svg)

## Overview

Curriculum Curator is a powerful desktop application that helps educators create comprehensive curriculum content using AI. It supports multiple LLM providers and generates various educational materials including slides, instructor notes, worksheets, quizzes, and activity guides.

### Key Features

- **🤖 Multiple AI Providers**: Supports OpenAI, Claude, Gemini, and Ollama (for offline use)
- **📝 Comprehensive Content Generation**: Create slides, instructor notes, worksheets, quizzes, and activity guides
- **🎨 Dual Interface Modes**: Wizard mode for guided creation and Expert mode for advanced users
- **💾 Session Management**: Save, load, and organize your curriculum sessions
- **📤 Multiple Export Formats**: Export to PDF, Word, HTML, and Quarto
- **🔒 Privacy-First**: All data stored locally with secure API key management
- **🔄 Version Control**: Built-in Git integration for tracking changes
- **💼 Backup & Recovery**: Automatic and manual backup options
- **🌐 Offline Capable**: Works with local LLMs via Ollama

## Installation

### Prerequisites

- Node.js 18+ and npm
- Rust 1.70+ (for building from source)
- Git (optional, for version control features)

### Download Pre-built Binaries

Visit the [Releases](https://github.com/michael-borck/curriculum-curator/releases) page to download the latest version for your platform:

- **Windows**: `Curriculum-Curator_x.x.x_x64.msi`
- **macOS**: `Curriculum-Curator_x.x.x_x64.dmg`
- **Linux**: `curriculum-curator_x.x.x_amd64.deb` or `.AppImage`

### Build from Source

```bash
# Clone the repository
git clone https://github.com/michael-borck/curriculum-curator.git
cd curriculum-curator

# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for production
npm run build
```

## Quick Start

1. **Launch the Application**: Open Curriculum Curator from your applications menu

2. **Configure LLM Provider**: 
   - Click "Setup LLM" in the header
   - Choose your provider (OpenAI, Claude, Gemini, or Ollama)
   - Enter your API key (stored securely)

3. **Create Content**:
   - **Wizard Mode** (Default): Follow the step-by-step guide
   - **Expert Mode**: Access all features from a single interface

4. **Generate Materials**: 
   - Define your topic and audience
   - Set learning objectives
   - Select content types
   - Configure AI enhancements
   - Click "Generate Content"

5. **Export Results**: Save your generated content in your preferred format

## Features in Detail

### Content Types

- **📊 Slides**: Presentation slides with key points and visuals
- **📝 Instructor Notes**: Detailed teaching notes and guidance
- **📄 Worksheets**: Student practice exercises and activities
- **❓ Quizzes**: Various assessment types (multiple choice, short answer, etc.)
- **👥 Activity Guides**: Interactive learning activities
- **🎨 Custom Types**: Create your own specialized content types

### AI Enhancement Options

- Adaptive difficulty levels
- Real-world examples integration
- Visual learning suggestions
- Interactive elements
- Accessibility features
- Multi-language support

### Session Management

- Save and load curriculum sessions
- Browse session history
- Duplicate and modify existing sessions
- Track costs and statistics
- Batch content generation

### Export Options

- **PDF**: Professional formatted documents
- **Word**: Editable .docx files
- **HTML**: Web-ready content
- **Quarto**: For academic publishing
- **Batch Export**: Export multiple sessions at once

## Configuration

### Settings Panel

Access the settings panel (⚙️) to configure:

- **User Profile**: Name, subject, institution
- **Content Defaults**: Preferred content types, duration, complexity
- **UI Preferences**: Theme, layout, preview options
- **Advanced Options**: Custom templates, AI parameters

### LLM Provider Setup

1. **OpenAI**: Requires API key from [platform.openai.com](https://platform.openai.com)
2. **Claude**: Requires API key from [console.anthropic.com](https://console.anthropic.com)
3. **Gemini**: Requires API key from [makersuite.google.com](https://makersuite.google.com)
4. **Ollama**: Install locally from [ollama.ai](https://ollama.ai)

## Development

### Project Structure

```
curriculum-curator/
├── src/                    # React frontend
│   ├── components/        # UI components
│   ├── hooks/            # Custom React hooks
│   ├── contexts/         # React contexts
│   └── utils/           # Utility functions
├── src-tauri/           # Rust backend
│   ├── src/
│   │   ├── content/     # Content generation
│   │   ├── llm/        # LLM providers
│   │   ├── export/     # Export functionality
│   │   ├── session/    # Session management
│   │   └── database/   # SQLite integration
│   └── Cargo.toml
├── package.json
└── tauri.conf.json
```

### Available Scripts

```bash
# Development
npm run dev              # Run in development mode
npm run dev:check       # Run type checking and linting
npm run dev:format      # Format code

# Building
npm run build           # Build for production
npm run tauri:build    # Build Tauri app

# Testing
npm run rust:test      # Run Rust tests
npm run lint          # Run ESLint
npm run type-check    # TypeScript checking
```

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

**LLM Provider not working**
- Verify API key is correct
- Check internet connection
- Ensure provider service is available

**Export failing**
- Check file permissions
- Ensure sufficient disk space
- Verify export path exists

**Ollama not detected**
- Install Ollama from [ollama.ai](https://ollama.ai)
- Ensure Ollama service is running
- Check firewall settings

### Logs and Support

- Logs location: 
  - Windows: `%APPDATA%\curriculum-curator\logs`
  - macOS: `~/Library/Application Support/curriculum-curator/logs`
  - Linux: `~/.config/curriculum-curator/logs`

- Report issues: [GitHub Issues](https://github.com/michael-borck/curriculum-curator/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Tauri](https://tauri.app/) - A framework for building native apps
- UI powered by [React](https://reactjs.org/)
- AI integrations via various LLM providers
- Icons and design elements from various open-source projects

## Roadmap

- [ ] Cloud sync capabilities
- [ ] Collaborative editing features
- [ ] Template marketplace
- [ ] Mobile companion app
- [ ] Advanced analytics dashboard
- [ ] Plugin system for extensions
- [ ] Multi-language UI support

---

**Note**: This is an active project under development. Features and documentation may change. For the latest updates, check the [GitHub repository](https://github.com/michael-borck/curriculum-curator).