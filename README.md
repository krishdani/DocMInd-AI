# DocMInd AI

An intelligent document management and analysis system powered by AI to extract insights, summarize content, and intelligently organize documentation.

## Overview

DocMInd AI is a sophisticated TypeScript-based application that combines document management capabilities with artificial intelligence to provide intelligent document processing, analysis, and retrieval. It leverages advanced NLP and machine learning models to understand document content and provide meaningful insights.

## Features

- 📄 **Smart Document Upload**: Seamless document ingestion and processing
- 🤖 **AI-Powered Analysis**: Intelligent extraction of key information
- 📝 **Auto-Summarization**: Generate concise summaries from lengthy documents
- 🔍 **Semantic Search**: Find documents based on meaning, not just keywords
- 🏷️ **Auto-Tagging**: Automatic categorization and tagging
- 💡 **Insight Generation**: Extract actionable insights from documents
- 🔐 **Secure Storage**: Encrypted document storage and retrieval
- 🚀 **API-First Design**: RESTful API for seamless integration

## Tech Stack

- **Frontend**: TypeScript, React/Next.js, TailwindCSS
- **Backend**: TypeScript, Node.js, Express
- **Database**: MongoDB / PostgreSQL
- **AI/ML**: OpenAI API, Langchain, Vector databases
- **Package Manager**: npm / yarn

## Installation

### Prerequisites
- Node.js >= 16
- npm or yarn
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/krishdani/DocMInd-AI.git
cd DocMInd-AI
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

4. Configure AI services:
```bash
# Add your API keys for:
# - OpenAI or similar LLM provider
# - Database credentials
# - Storage service (if using cloud)
```

5. Start the development server:
```bash
npm run dev
# or
yarn dev
```

6. Open your browser and navigate to `http://localhost:3000`

## Usage

### Basic Workflow

1. **Upload Documents**: Upload PDF, DOCX, TXT, or other supported formats
2. **Automatic Processing**: AI automatically processes and indexes documents
3. **Search & Retrieve**: Use semantic search to find relevant documents
4. **Extract Insights**: Generate summaries and extract key information
5. **Export Results**: Download processed data or summaries

### API Usage

```bash
# Upload a document
curl -X POST http://localhost:3000/api/documents/upload \
  -F "file=@document.pdf" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Analyze document
curl -X POST http://localhost:3000/api/documents/{id}/analyze \
  -H "Authorization: Bearer YOUR_API_KEY"

# Search documents
curl -X GET "http://localhost:3000/api/documents/search?q=your+query" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Project Structure

```
DocMInd-AI/
├── frontend/           # React/Next.js frontend
├── backend/            # Express backend
├── shared/             # Shared types and utilities
├── docs/               # Documentation
├── package.json        # Root dependencies
└── README.md           # This file
```

## Configuration

### Environment Variables

```env
# API Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database
DATABASE_URL=postgresql://user:password@localhost/docmind
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/docmind

# Server
PORT=3000
NODE_ENV=development
JWT_SECRET=your_jwt_secret

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:3000
```

## Development

### Running Tests

```bash
npm run test
```

### Building for Production

```bash
npm run build
npm run start
```

### Linting and Formatting

```bash
npm run lint
npm run format
```

## Database Setup

```bash
# Run migrations
npm run migrate

# Seed database (optional)
npm run seed
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your API keys are correctly set in `.env.local`
2. **Database Connection**: Verify database URL and credentials
3. **Build Errors**: Clear node_modules and reinstall: `rm -rf node_modules && npm install`
4. **Port Already in Use**: Change PORT in .env or kill the process using the port

## Performance Optimization

- Document indexing is performed asynchronously
- Vector embeddings are cached for faster searches
- Database queries are optimized with proper indexing
- Frontend code is split and lazy-loaded for better performance

## Security

- All API endpoints require authentication
- Documents are encrypted at rest
- API keys are securely managed
- CORS is configured for authorized domains only
- Input validation on all endpoints

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For issues, questions, or feature requests, please:
- Open an issue on [GitHub Issues](https://github.com/krishdani/DocMInd-AI/issues)
- Check existing documentation in the `/docs` folder
- Contact the maintainers

## Roadmap

- [ ] Advanced document versioning
- [ ] Collaborative document editing
- [ ] Multi-language support
- [ ] Advanced visualization tools
- [ ] Mobile application
- [ ] Enterprise deployment guides

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with TypeScript for type safety
- Powered by state-of-the-art AI models
- Community contributions and feedback

## Author

**krishdani** - [GitHub Profile](https://github.com/krishdani)

---

**Last Updated**: 2026-05-22
