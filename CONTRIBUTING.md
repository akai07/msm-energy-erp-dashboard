# Contributing to MSM Energy ERP Dashboard

Thank you for your interest in contributing to the MSM Energy ERP Dashboard! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information** including:
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Screenshots or error logs if applicable

### Submitting Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the coding standards** outlined below
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Ensure all tests pass** before submitting
6. **Create a clear pull request** with:
   - Descriptive title and summary
   - Reference to related issues
   - Screenshots for UI changes

## 🛠 Development Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+ (for production testing)
- Redis (for caching and task queue)
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Local Development

1. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/msm-energy-erp.git
   cd msm-energy-erp
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Load sample data**
   ```bash
   python manage.py process_steel_data
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

## 📝 Coding Standards

### Python Code Style

- **Follow PEP 8** for Python code formatting
- **Use Black** for automatic code formatting
- **Use flake8** for linting
- **Use mypy** for type checking
- **Maximum line length**: 88 characters (Black default)

### Code Quality Tools

```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy .

# Run all quality checks
pre-commit run --all-files
```

### Django Best Practices

- **Use Django's built-in features** when possible
- **Follow Django naming conventions**
- **Use class-based views** for complex logic
- **Implement proper error handling**
- **Use Django's security features** (CSRF, XSS protection, etc.)
- **Write efficient database queries** (use select_related, prefetch_related)

### API Development

- **Use Django REST Framework** for API endpoints
- **Implement proper serializers** for data validation
- **Use appropriate HTTP status codes**
- **Include comprehensive API documentation**
- **Implement proper authentication and permissions**

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test energy_dashboard

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML coverage report
```

### Writing Tests

- **Write tests for all new functionality**
- **Use Django's TestCase** for database-related tests
- **Use unittest.mock** for external dependencies
- **Follow the AAA pattern** (Arrange, Act, Assert)
- **Use descriptive test names** that explain what is being tested

### Test Structure

```python
class EnergyDashboardTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_energy_consumption_calculation(self):
        """Test that energy consumption is calculated correctly"""
        # Arrange
        energy_reading = EnergyReading.objects.create(
            usage_kwh=100.5,
            timestamp=timezone.now()
        )
        
        # Act
        result = energy_reading.calculate_daily_consumption()
        
        # Assert
        self.assertEqual(result, 100.5)
```

## 📚 Documentation

### Code Documentation

- **Use docstrings** for all classes, methods, and functions
- **Follow Google docstring format**
- **Include type hints** for function parameters and return values
- **Document complex algorithms** and business logic

### Example Docstring

```python
def calculate_energy_efficiency(usage_kwh: float, production_output: float) -> float:
    """
    Calculate energy efficiency ratio for production.
    
    Args:
        usage_kwh: Energy consumption in kilowatt-hours
        production_output: Production output in units
        
    Returns:
        Energy efficiency ratio (kWh per unit produced)
        
    Raises:
        ValueError: If production_output is zero or negative
    """
    if production_output <= 0:
        raise ValueError("Production output must be positive")
    
    return usage_kwh / production_output
```

## 🔒 Security Guidelines

### Security Best Practices

- **Never commit sensitive information** (API keys, passwords, secrets)
- **Use environment variables** for configuration
- **Validate all user inputs**
- **Use Django's built-in security features**
- **Keep dependencies up to date**
- **Follow OWASP security guidelines**

### Reporting Security Issues

Please report security vulnerabilities privately to [security@yourproject.com](mailto:security@yourproject.com). Do not create public issues for security vulnerabilities.

## 🌟 Areas for Contribution

### High Priority

- 🐛 **Bug fixes** and stability improvements
- 📊 **Energy analytics** enhancements
- 🔧 **Performance optimizations**
- 🧪 **Test coverage** improvements

### Medium Priority

- ✨ **New ERP features** (advanced reporting, workflow automation)
- 🎨 **UI/UX improvements**
- 📱 **Mobile responsiveness**
- 🌐 **Internationalization** (i18n)

### Low Priority

- 📚 **Documentation** improvements
- 🔄 **Code refactoring**
- 🎯 **Developer experience** enhancements

## 📋 Commit Message Guidelines

Use clear and descriptive commit messages following this format:

```
type(scope): brief description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(energy): add real-time energy monitoring dashboard

fix(api): resolve authentication token expiration issue

docs(readme): update installation instructions

test(energy): add unit tests for energy calculation functions
```

## 🏷 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Version number is bumped
- [ ] Security review completed
- [ ] Performance testing completed

## 🤔 Questions and Support

### Getting Help

- 📖 **Documentation**: Check the README and inline documentation
- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Issues**: Create an issue for bugs or feature requests
- 📧 **Email**: Contact [contributors@yourproject.com](mailto:contributors@yourproject.com)

### Community Guidelines

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Provide constructive feedback**
- **Follow the code of conduct**

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to MSM Energy ERP Dashboard! Together, we're building better tools for the manufacturing industry. 🚀**