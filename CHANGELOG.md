# Changelog

All notable changes to the Daotomata Hotel Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Standalone repository structure
- Comprehensive documentation for independent deployment
- Enhanced CI/CD workflow for isolated development

### Changed
- Migrated from dao-hotel monorepo to standalone repository
- Updated dependencies and project structure
- Improved documentation with migration context

## [1.0.0] - 2025-01-05

### Added
- Initial release as standalone repository
- Multi-agent AI concierge system with triage agent
- Specialized agents for booking, concierge, guest services, and activities
- OpenAI Agents SDK integration with GPT-4o
- FastAPI async API framework
- Supabase multi-tenant database support with RLS
- Pydantic data validation and serialization
- Docker containerization support
- Comprehensive test suite
- API documentation with Swagger UI and ReDoc
- Health check endpoints
- Session management capabilities
- Hotel-specific context detection
- Custom tools for hotel operations (PMS integration ready)

### Technical Features
- **Triage Agent**: Intelligent conversation routing
- **Booking Specialist**: Room reservations and availability checks
- **Hotel Concierge**: Local recommendations and area information
- **Guest Services**: Hotel services and maintenance requests
- **Activities Coordinator**: Entertainment and spa services

### Infrastructure
- Multi-tenant architecture with domain-based detection
- Row Level Security (RLS) for data isolation
- Environment-based configuration
- Production-ready Docker setup
- Comprehensive error handling and logging

### Migration Notes
- Extracted from [dao-hotel monorepo](https://github.com/mkiradani/dao-hotel)
- Maintained backward compatibility with existing hotel system
- Preserved all existing functionality and tools
- Updated documentation for standalone deployment

## Repository History

This repository was created by extracting the `/services/bot` directory from the main [dao-hotel monorepo](https://github.com/mkiradani/dao-hotel) to enable:

1. **Independent Development**: Dedicated team focus on AI agent features
2. **Separate Deployment**: Independent scaling and deployment cycles
3. **Faster CI/CD**: Reduced build times and focused testing
4. **Specialized Tooling**: AI-specific development and testing tools

### Integration with Main System

This service maintains integration with the main hotel system through:
- Shared Supabase database with multi-tenant RLS
- Standardized REST API patterns
- Common environment configuration
- Unified authentication and session management

---

For the complete development history prior to extraction, see the [dao-hotel repository](https://github.com/mkiradani/dao-hotel/commits/main/services/bot).
