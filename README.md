# VidID - Video Identification System

[![Videntify CI](https://github.com/KristsPutans/Videntify/actions/workflows/ci.yml/badge.svg)](https://github.com/KristsPutans/Videntify/actions/workflows/ci.yml)

> Last tested: May 8, 2025

## Overview
VidID is a sophisticated video identification system similar to Shazam but for videos. It allows users to identify videos from short clips, providing accurate matches with detailed metadata.

## System Architecture

### Core Components
- **Video Acquisition Module**: Handles video acquisition from multiple sources
- **Feature Extraction Engine**: Extracts features and generates fingerprints
- **Content Database**: Manages raw videos, features, and metadata
- **Indexing System**: Creates searchable indexes for fast retrieval
- **Matching Engine**: Processes user video clips and returns matches
- **API Layer**: Provides interfaces for mobile apps and third-party integrations

### Technical Stack
- **Cloud Infrastructure**: AWS/GCP/Azure with auto-scaling capabilities
- **Processing Frameworks**: Apache Spark for batch, Ray for near real-time
- **Databases**:
  - Vector DB: Milvus or Pinecone for embeddings
  - Metadata DB: PostgreSQL with TimescaleDB extension
  - Object Storage: S3-compatible with lifecycle policies
- **ML Framework**: PyTorch for video understanding models
- **Orchestration**: Kubernetes for orchestration

## Features

### Data Acquisition
- Multi-tiered content sources from popular streaming platforms, television, YouTube, and archives
- Legal framework for content usage and attribution
- Multiple ingestion methods including APIs, recording, web crawling, and partnerships

## Development & Deployment

### CI/CD Pipeline
This project uses GitHub Actions for continuous integration and deployment. The workflow automatically tests, builds, and deploys the application when changes are pushed to the repository.

#### Workflow Steps
1. **Test**: Runs unit and integration tests for both UI and backend components
2. **Build**: Creates optimized builds for production deployment
3. **Deploy**: Automatically deploys to staging (develop branch) or production (main branch)

#### Environment Configuration
To set up the CI/CD pipeline, the following secrets need to be configured in the GitHub repository settings:
- `NETLIFY_SITE_ID`: Production site ID from Netlify
- `NETLIFY_STAGING_SITE_ID`: Staging site ID from Netlify
- `NETLIFY_AUTH_TOKEN`: Authentication token for Netlify deployment

### Testing
The project includes comprehensive testing across all components:

#### UI Testing
- Unit tests for individual components using Jest and React Testing Library
- Integration tests for complete application flows
- Run tests with: `cd ui && npm test`
- Run CI tests: `cd ui && npm run test:ci`

#### Backend Testing
- Unit tests for API endpoints and core functions
- Integration tests for end-to-end workflows
- Run tests with: `pytest --cov=src/`

A dedicated shell script `test.sh` is available in the root directory to simplify running tests.

### Feature Engineering
- Advanced video feature extraction with scene detection, perceptual hashing, and CNN models
- Audio feature extraction including spectrograms and transcription
- Rich metadata enrichment for enhanced search capabilities

### Indexing & Storage
- Multi-modal index design with hierarchical structure
- Intelligent sharding strategy for optimized performance
- Sophisticated caching architecture for frequent queries

### Query Processing
- Efficient query workflow from preprocessing to result delivery
- Performance optimization with GPU acceleration
- Enhanced results with temporal alignment and context extraction

### User Applications
- Mobile application with video capture and result visualization
- Comprehensive API services for third-party integration
- Admin dashboard for system monitoring and analytics

## Getting Started

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- GPU support for optimal performance

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/vidid.git
cd vidid

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start the services
docker-compose up -d
```

## License
Propriety - All Rights Reserved

## Contact
For inquiries, please contact: support@vidid.com
