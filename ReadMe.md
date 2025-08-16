# MSM Energy ERP Dashboard

![MSM Energy ERP](https://img.shields.io/badge/MSM%20Energy-ERP%20Dashboard-blue?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-4.2.7-green?style=flat-square&logo=django)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=flat-square&logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

**A comprehensive Enterprise Resource Planning (ERP) system designed specifically for steel and manufacturing industries, featuring advanced energy monitoring, production management, and real-time analytics.**

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/msm-energy-erp.git
cd msm-energy-erp

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Process steel industry data
python manage.py process_steel_data

# Start the development server
python manage.py runserver
```

## 📋 Table of Contents

- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Docker Deployment](#-docker-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🔋 ForgeForward Energy Dashboard
- **Real-time Energy Monitoring**: Track energy consumption with live data visualization
- **Energy Correlation Analysis**: Analyze relationships between usage patterns and operational factors
- **CO2 Emissions Tracking**: Monitor environmental impact with automated calculations
- **Power Quality Monitoring**: Track power factor, reactive power, and efficiency metrics
- **Cost Analysis**: Correlate energy usage with operational costs
- **Predictive Analytics**: Identify energy optimization opportunities

### 🏭 Core ERP Modules
- **Sales Management**: Customer relationship management, order tracking, and invoicing
- **Inventory Control**: Real-time stock management with automated reorder points
- **Production Planning**: Work order management, scheduling, and resource allocation
- **Quality Assurance**: Comprehensive quality control with inspection workflows
- **Human Resources**: Employee management, payroll, and performance tracking
- **Financial Management**: Accounting, budgeting, and financial reporting

### 📊 Advanced Analytics
- **Interactive Dashboards**: Chart.js powered visualizations
- **Real-time Monitoring**: Live data updates and alerts
- **Custom Reports**: Flexible reporting engine
- **Data Export**: CSV, Excel, and PDF export capabilities

## 🛠 Technology Stack

### Backend
- **Django 4.2.7**: Web framework with REST API capabilities
- **Django REST Framework**: API development and serialization
- **PostgreSQL**: Primary database for production
- **SQLite**: Development database
- **Celery**: Asynchronous task processing
- **Redis**: Cache and message broker

### Frontend
- **HTML5/CSS3**: Modern responsive design
- **JavaScript (ES6+)**: Interactive functionality
- **Chart.js**: Data visualization and analytics
- **Bootstrap**: UI framework

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **SciPy**: Statistical analysis
- **Scikit-learn**: Machine learning capabilities

### DevOps & Deployment
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration
- **Nginx**: Web server and reverse proxy
- **Gunicorn**: WSGI HTTP Server
- **GitHub Actions**: CI/CD pipeline

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 15+ (for production)
- Redis (for caching and task queue)
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/msm-energy-erp.git
   cd msm-energy-erp
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Database setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Load sample data**
   ```bash
   python manage.py process_steel_data
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

   Visit `http://localhost:8000` to access the application.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
DJANGO_ENVIRONMENT=development
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/msm_energy_erp

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Configuration

For PostgreSQL production setup:

```sql
CREATE DATABASE msm_energy_erp;
CREATE USER msm_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE msm_energy_erp TO msm_user;
```

## 📚 API Documentation

### Authentication

The API uses token-based authentication. Include the token in the Authorization header:

```bash
Authorization: Token your-api-token-here
```

### Core Endpoints

#### Energy Dashboard

```bash
# Get energy dashboard statistics
GET /api/energy/dashboard-stats/

# Get energy consumption trends
GET /api/energy/consumption-trends/

# Process steel industry data
POST /api/energy/steel-industry-process/

# Get energy correlations
GET /api/energy/energy-correlations/
```

#### ERP Modules

```bash
# Sales Management
GET /api/sales/orders/
POST /api/sales/orders/
GET /api/sales/customers/

# Inventory Management
GET /api/inventory/items/
POST /api/inventory/items/
GET /api/inventory/suppliers/

# Production Management
GET /api/production/work-orders/
POST /api/production/work-orders/
GET /api/production/schedules/

# Quality Assurance
GET /api/quality/inspections/
POST /api/quality/inspections/
GET /api/quality/reports/
```

### Sample API Response

```json
{
  "energy_stats": {
    "total_consumption": 125847.5,
    "avg_daily_usage": 3.58,
    "co2_emissions": 0.0,
    "efficiency_score": 85.2
  },
  "correlations": {
    "usage_co2": 0.988,
    "power_factor_efficiency": 0.202
  },
  "peak_hours": [9, 10, 11, 14, 15, 16]
}
```

## 🐳 Docker Deployment

### Quick Start with Docker Compose

1. **Clone and configure**
   ```bash
   git clone https://github.com/yourusername/msm-energy-erp.git
   cd msm-energy-erp
   cp .env.example .env
   # Edit .env with your production settings
   ```

2. **Build and start services**
   ```bash
   docker-compose up -d
   ```

3. **Initialize database**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   docker-compose exec web python manage.py process_steel_data
   ```

4. **Access the application**
   - Web Application: `http://localhost`
   - Admin Panel: `http://localhost/admin`
   - API Documentation: `http://localhost/api/docs`

### Production Deployment

For production deployment with SSL and domain configuration:

```bash
# Update environment variables
export DJANGO_ENVIRONMENT=production
export ALLOWED_HOSTS=yourdomain.com
export SECRET_KEY=your-production-secret-key

# Deploy with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test energy_dashboard

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```
## 📁 Project Structure

```
msm-energy-erp/
├── msm_energy_erp/           # Main Django project
│   ├── settings/             # Environment-specific settings
│   │   ├── __init__.py
│   │   ├── base.py          # Base settings
│   │   └── production.py    # Production settings
│   ├── urls.py
│   └── wsgi.py
├── energy_dashboard/         # Energy monitoring app
│   ├── models.py            # Energy data models
│   ├── views.py             # API views
│   ├── serializers.py       # DRF serializers
│   └── management/commands/ # Custom management commands
├── core/                     # Core functionality
├── sales/                    # Sales management
├── inventory/                # Inventory control
├── production/               # Production planning
├── quality_assurance/        # Quality control
├── hr/                       # Human resources
├── finance/                  # Financial management
├── static/                   # Static files
├── templates/                # HTML templates
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Multi-service setup
├── nginx.conf               # Nginx configuration
└── .env.example             # Environment variables template
```

## 🤝 Contributing

We welcome contributions from developers, industry experts, and anyone passionate about improving manufacturing efficiency!

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests for new functionality**
5. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
6. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Development Guidelines

- **Code Style**: Follow PEP 8 for Python code
- **Testing**: Write tests for new features and ensure existing tests pass
- **Documentation**: Update documentation for any new features or changes
- **Commit Messages**: Use clear and descriptive commit messages
- **Security**: Never commit sensitive information like API keys or passwords

### Areas for Contribution

- 🐛 Bug fixes and improvements
- ✨ New features and enhancements
- 📚 Documentation improvements
- 🧪 Test coverage expansion
- 🌐 Internationalization and localization
- 🎨 UI/UX improvements
- 📊 New analytics and reporting features

## 📊 Data Sources

This project utilizes real-world datasets:

- **Steel Industry Energy Data**: Time-series energy consumption data from steel manufacturing operations
- **ERP Sample Data**: Comprehensive business data including customers, suppliers, products, and transactions

## 🔒 Security

Security is a top priority. Please report security vulnerabilities privately to [security@yourproject.com](mailto:security@yourproject.com).

### Security Features

- Token-based API authentication
- CSRF protection
- SQL injection prevention
- XSS protection
- Secure headers configuration
- Rate limiting
- Input validation and sanitization

## 📈 Performance

- **Database Optimization**: Efficient queries with proper indexing
- **Caching**: Redis-based caching for improved response times
- **Async Processing**: Celery for background tasks
- **Static File Optimization**: Compressed and minified assets
- **Database Connection Pooling**: Optimized database connections

## 🌍 Roadmap

### Phase 1 (Current)
- ✅ Core ERP modules
- ✅ Energy dashboard
- ✅ Real-time monitoring
- ✅ Docker deployment

### Phase 2 (Upcoming)
- 🔄 Mobile application
- 🔄 Advanced analytics and ML
- 🔄 IoT device integration
- 🔄 Multi-tenant support

### Phase 3 (Future)
- 📋 Industry-specific modules
- 📋 Third-party integrations
- 📋 Advanced reporting engine
- 📋 Workflow automation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to the open-source community for the amazing tools and libraries
- Steel industry professionals who provided real-world insights
- Contributors who help improve this project
- Django and Python communities for excellent documentation and support

## 📞 Support

Need help? Here's how to get support:

- 📖 **Documentation**: Check this README and inline documentation
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/msm-energy-erp/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/msm-energy-erp/discussions)
- 📧 **Email**: [support@yourproject.com](mailto:support@yourproject.com)

---

**Built with ❤️ for the manufacturing industry. Let's build a more efficient and sustainable future together! 🚀**

---

*Keywords: ERP, Manufacturing, Steel Industry, Energy Monitoring, Django, Python, PostgreSQL, Docker, Real-time Analytics, Production Management, Quality Assurance*
