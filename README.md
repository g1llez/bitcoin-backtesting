# Bitcoin Mining Backtesting System

Advanced Bitcoin mining backtesting platform with multi-machine optimization and dynamic strategy testing.

## 🚀 Features

- **Multi-Machine Optimization**: Optimize mining strategies across multiple machines
- **Real-Time Market Data**: Live Bitcoin price and FPPS data integration
- **Dynamic Strategy Testing**: Backtest different mining strategies with historical data
- **Efficiency Analysis**: Detailed efficiency curves and optimization algorithms
- **Multi-Theme Interface**: Dark, light, and colorful themes
- **International Date Format**: YYYY-MM-DD format support
- **Docker Ready**: Complete containerized setup

## 🏗️ Architecture

- **Frontend**: HTML5, CSS3, JavaScript with Chart.js
- **Backend**: FastAPI (Python) with PostgreSQL
- **Database**: PostgreSQL with automated migrations
- **Containerization**: Docker Compose setup

## 🛠️ Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation
```bash
# Clone the repository
git clone git@github.com:g1llez/bitcoin-backtesting.git
cd bitcoin-backtesting

# Copy environment file and configure
cp env.example .env
# Edit .env with your secure passwords and tokens

# Start the application
docker compose up -d

# Access the application
open http://localhost:3001
```

### Security Setup
See [SECURITY.md](SECURITY.md) for detailed security guidelines and best practices.

## 📊 Current Version
- **Version**: 2.3
- **Last Update**: January 2024

## 🔧 Development

### Project Structure
```
bitcoin-backtesting/
├── frontend/          # Web interface
├── api/              # FastAPI backend
├── database/         # PostgreSQL migrations
├── docs/            # Documentation
└── docker-compose.yml
```

### Key Features
- **Backtesting Interface**: Complete backtesting workflow
- **Machine Management**: Add, edit, and optimize mining machines
- **Site Configuration**: Multi-site mining operations
- **Market Data Cache**: Efficient data caching system
- **Real-Time Updates**: Live market data every 30 seconds

## 📈 Roadmap

- [ ] Advanced backtesting algorithms
- [ ] Machine learning optimization
- [ ] Historical data analysis
- [ ] Performance benchmarking
- [ ] API documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions, please open an issue on GitHub.

---

**Built with ❤️ for Bitcoin mining optimization** 