# Contributing to SpeakEasy

Thank you for your interest in contributing to SpeakEasy! This document provides guidelines and instructions for contributing to this open-source voice-to-text application.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Code Contributions](#code-contributions)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to:

- **Be respectful**: Treat everyone with respect. Healthy debate is encouraged, but harassment is not tolerated.
- **Be constructive**: Provide constructive feedback and be open to receiving it.
- **Be inclusive**: Welcome newcomers and help them get started.
- **Focus on what's best**: Make decisions that benefit the community and users.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/speakeasy.git
   cd speakeasy
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/bitgineer/speakeasy.git
   ```
4. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

## Development Setup

### Prerequisites

- Python 3.10 - 3.12
- Node.js 18+ (LTS)
- FFmpeg in system PATH
- UV package manager (`pip install uv`)
- Git

### Backend Setup

```bash
cd backend
uv venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Frontend Setup

```bash
cd gui
npm install
```

### Running Tests

**Backend**:
```bash
cd backend
pytest
```

**Frontend**:
```bash
cd gui
npm test
```

## How to Contribute

### Reporting Bugs

Before creating a bug report, please:

1. **Check existing issues** to avoid duplicates
2. **Use the latest version** to verify the bug still exists
3. **Collect information** about the bug

When submitting a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Environment details**:
  - OS and version
  - Python version
  - Node.js version
  - GPU model (if applicable)
- **Error messages** or logs
- **Screenshots** (if applicable)

Use the [Bug Report template](https://github.com/bitgineer/speakeasy/issues/new?template=bug_report.md) when available.

### Suggesting Features

Feature requests are welcome! When suggesting a feature:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** - what problem does it solve?
3. **Explain the feature** in detail
4. **Consider alternatives** you've evaluated
5. **Be open to discussion** about implementation

Use the [Feature Request template](https://github.com/bitgineer/speakeasy/issues/new?template=feature_request.md) when available.

### Code Contributions

#### Finding Issues to Work On

- Look for issues labeled `good first issue` or `help wanted`
- Check the [project roadmap](../README.md#roadmap)
- Comment on an issue before starting work to avoid conflicts

#### Types of Contributions

- **Bug fixes**: Address issues in the codebase
- **Features**: Implement new functionality
- **Documentation**: Improve README, code comments, or guides
- **Tests**: Add test coverage
- **Performance**: Optimize existing code
- **Models**: Add support for new AI models
- **UI/UX**: Improve the user interface

## Coding Standards

### Python (Backend)

- **Follow PEP 8** style guide
- **Use type hints** where appropriate
- **Write docstrings** for functions and classes (Google style)
- **Maximum line length**: 100 characters
- **Use Black** for formatting: `black backend/`
- **Use isort** for imports: `isort backend/`

Example:
```python
def transcribe_audio(
    audio_path: str,
    model_name: str = "whisper-base",
    language: Optional[str] = None
) -> TranscriptionResult:
    """Transcribe audio file to text.
    
    Args:
        audio_path: Path to the audio file.
        model_name: Name of the model to use.
        language: Optional language code (e.g., 'en', 'es').
        
    Returns:
        TranscriptionResult containing text and metadata.
        
    Raises:
        FileNotFoundError: If audio file doesn't exist.
        ModelError: If model fails to load or process.
    """
    # Implementation
```

### JavaScript/TypeScript (Frontend)

- **Use ESLint** configuration provided
- **Use Prettier** for formatting
- **Follow React best practices**
- **Use functional components** with hooks
- **Add JSDoc comments** for complex functions

Example:
```typescript
interface TranscriptionPanelProps {
  transcription: string;
  onCopy: () => void;
  isProcessing: boolean;
}

/**
 * Displays transcription results with copy functionality.
 */
export const TranscriptionPanel: React.FC<TranscriptionPanelProps> = ({
  transcription,
  onCopy,
  isProcessing
}) => {
  // Component implementation
};
```

### General Guidelines

- **Keep functions small** and focused on a single responsibility
- **Use meaningful variable names**
- **Add comments** for complex logic, but prefer self-documenting code
- **Write tests** for new features and bug fixes
- **Update documentation** when adding or changing features
- **Don't break existing functionality** - maintain backwards compatibility

## Pull Request Process

1. **Update your branch** with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Ensure tests pass**:
   ```bash
   # Backend
   cd backend && pytest
   
   # Frontend
   cd gui && npm test
   ```

3. **Format your code**:
   ```bash
   # Backend
   black backend/
   isort backend/
   
   # Frontend
   cd gui && npm run lint
   ```

4. **Commit your changes** with clear messages:
   ```bash
   git add .
   git commit -m "feat: add support for Voxtral model
   
   - Integrate Mistral Voxtral for complex dictation
   - Add model selection UI
   - Update documentation
   
   Closes #123"
   ```

   Commit message format:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes (formatting)
   - `refactor:` Code refactoring
   - `test:` Adding or updating tests
   - `chore:` Maintenance tasks

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub:
   - Use a clear title describing the change
   - Fill out the PR template completely
   - Link related issues with `Closes #123` or `Fixes #123`
   - Request review from maintainers

7. **Address review feedback**:
   - Be responsive to comments
   - Make requested changes in new commits
   - Re-request review when ready

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/updates
- `chore/description` - Maintenance tasks

### Before Submitting

Checklist:
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main
- [ ] No merge conflicts

## Project Structure

```
speakeasy/
├── backend/              # Python FastAPI backend
│   ├── app/             # Application code
│   ├── models/          # AI model integrations
│   ├── tests/           # Test suite
│   └── pyproject.toml   # Python dependencies
├── gui/                 # Electron + React frontend
│   ├── src/             # Source code
│   ├── public/          # Static assets
│   └── package.json     # Node dependencies
├── docs/                # Documentation and images
├── scripts/             # Build and utility scripts
├── CONTRIBUTING.md      # This file
└── README.md           # Project overview
```

## Getting Help

- **Discussions**: Use [GitHub Discussions](https://github.com/bitgineer/speakeasy/discussions) for questions
- **Issues**: For bugs and feature requests

## Recognition

Contributors will be:
- Listed in the project's contributors section
- Mentioned in release notes for significant contributions
- Given credit in documentation where appropriate

Thank you for contributing to SpeakEasy!
