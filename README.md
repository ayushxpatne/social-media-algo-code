# Social Media Algorithm: From Basic to ML-Powered

A comprehensive project that demystifies how social media algorithms work by building them from scratch. Starting from a simple rule-based system and evolving to a sophisticated machine learning-powered recommendation engine using embeddings and vector similarity search.

## 🎯 Project Overview

This project answers the fundamental question: **"How do social media algorithms know what content to show you?"** Through hands-on implementation, we explore the evolution from basic scoring systems to advanced ML-powered recommendation engines that power platforms like TikTok, Instagram, and YouTube.

## 🚀 Key Features

### 📊 Three Progressive Implementations

1. **Basic Algorithm** (`basic_algorithm.ipynb`)
   - Simple like/dislike scoring system
   - Rule-based content categorization
   - Cold start problem handling
   - Basic personalization using mean preference scores

2. **Comprehensive Algorithm** (`comprehensive_algo/`)
   - Multi-dimensional interaction tracking (view time, likes, comments, shares, saves)
   - Complex content categorization with 8 main categories and 50+ subcategories
   - Advanced scoring system with weighted interactions
   - Web interface for real-time interaction simulation

3. **ML-Powered Algorithm** (`ml_algo/`)
   - Google Gemini embeddings for content vectorization (3072 dimensions)
   - FAISS vector similarity search for content retrieval
   - User embedding generation using weighted averages
   - Intelligent content recommendation with exploration/exploitation balance
   - Real-time learning from user interactions

### 🧠 Core Concepts Demonstrated

- **Cold Start Problem**: How algorithms handle new users
- **Exploration vs Exploitation**: Balancing known preferences vs discovering new content
- **Embeddings**: Converting content into mathematical vectors
- **Vector Similarity**: Finding similar content using mathematical operations
- **User Profiling**: Building comprehensive user preference models
- **Real-time Learning**: Continuously updating recommendations based on interactions

## 🏗️ Architecture & Technology Stack

### Backend Technologies
- **Python 3.10+**: Core implementation language
- **Flask**: Web framework for interactive demos
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations
- **FAISS**: Facebook AI Similarity Search for vector operations
- **Google Gemini API**: Content embeddings generation

### Frontend Technologies
- **HTML5/CSS3**: Responsive web interface
- **JavaScript**: Real-time interaction handling
- **Bootstrap**: UI framework for clean design

### Data Storage
- **JSON**: Content and interaction data storage
- **CSV**: Content metadata and embeddings
- **FAISS Index**: Pre-computed content embeddings for fast similarity search

## 📁 Project Structure
```
social-media-algo-code/
├── basic_algorithm.ipynb          # Simple rule-based algorithm
├── comprehensive_algo/            # Advanced rule-based system
│   ├── app.py                    # Flask web application
│   ├── comprehensive_algo.ipynb  # Jupyter notebook implementation
│   ├── data.json                 # Content database
│   ├── history.json              # User interaction history
│   └── templates/
│       └── index.html            # Web interface
├── ml_algo/                      # ML-powered recommendation system
│   ├── app.py                    # Flask web application
│   ├── ml_algo.ipynb             # Jupyter notebook implementation
│   ├── data.json                 # Content database
│   ├── data2.json                # Enhanced content with embeddings
│   ├── content.csv               # Content metadata
│   ├── index.faiss               # FAISS vector index
│   ├── index_v2.faiss            # Enhanced FAISS index
│   ├── faiss.ipynb               # Vector similarity implementation
│   └── templates/
│       └── index.html            # Interactive web interface
├── history.json                  #interaction history for basic algo 
```