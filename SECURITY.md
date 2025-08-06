# Security Guidelines

## 🔐 Environment Variables

This project uses environment variables for sensitive configuration. **Never commit actual secrets to the repository.**

### Required Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Database Configuration
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_USER=bitcoin_user
POSTGRES_DB=bitcoin_backtesting

# API Configuration
DATABASE_URL=postgresql://bitcoin_user:your_secure_password_here@postgres-bitcoin:5432/bitcoin_backtesting
POSTGRES_HOST=postgres-bitcoin
POSTGRES_PORT=5432

# Braiins Pool Token (optional)
BRAIINS_TOKEN=your_braiins_token_here
```

### Security Best Practices

1. **Never commit `.env` files** - They are automatically ignored by `.gitignore`
2. **Use strong passwords** - Generate secure passwords for production
3. **Rotate tokens regularly** - Update Braiins tokens periodically
4. **Use different passwords** for development and production
5. **Limit database access** - Only expose necessary ports

### Production Deployment

For production deployment:

1. Use environment variables or secrets management
2. Change default passwords
3. Use HTTPS for all connections
4. Implement proper authentication
5. Regular security audits

### Token Management

- Braiins Pool tokens are stored in the database
- Tokens are encrypted in transit
- Tokens are optional (fallback to public data)
- Tokens can be updated via the web interface

## 🛡️ Security Features

- **Input validation** on all API endpoints
- **SQL injection protection** via SQLAlchemy ORM
- **XSS protection** via proper HTML encoding
- **CSRF protection** via proper form handling
- **Environment variable validation**

## 🔍 Security Audit

This repository has been audited for:
- ✅ No hardcoded passwords
- ✅ No API keys in code
- ✅ Proper environment variable usage
- ✅ Secure database configuration
- ✅ Input validation implemented 