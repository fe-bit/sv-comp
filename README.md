# SV-COMP Django Web Application

This is a Django-based web application for managing and analyzing software verification competition (SV-COMP) benchmarks. The application provides tools to compare different software verifiers on verification tasks, evaluate their performance, and run various analysis strategies.

## Project Overview

The SV-COMP web application manages verification tasks, verifiers, and benchmarks from software verification competitions. It allows users to:

1. Browse verification tasks by category
2. View detailed benchmark results for each verification task
3. Compare verifier performance across different categories
4. Run various analysis strategies (virtually best verifier, category-based, k-nearest neighbors)
5. Generate embedding vectors for verification tasks to find similar tasks

## Project Structure

The project consists of several main components:

- **verification_tasks**: Core app managing verification tasks and categories
- **verifiers**: App for tracking different software verification tools
- **benchmarks**: App for storing and analyzing benchmark results
- **utils**: Helper utilities for various tasks

### Key Features

- **Task Browsing**: View and filter verification tasks by category
- **Detailed Task View**: Examine how different verifiers perform on specific tasks
- **Embedding Analysis**: Use code embeddings to find similar verification tasks
- **Strategy Evaluation**: Compare different selection strategies:
  - Virtually Best Verifier
  - Category Best Verifier 
  - KNN-based strategies for selecting optimal verifiers

## Technical Details

- **Code Embeddings**: Uses Microsoft's CodeBERT to generate embeddings for C code
- **Vector Database**: Uses ChromaDB to store and query code embeddings
- **Django Web Framework**: Django 5.2 for the web application
- **Templating**: Uses Django templates with Bootstrap 5

## Main Views

- `verification_task_list`: Displays all verification tasks with filtering capabilities
- `verification_task_detail`: Shows detailed information about a specific verification task and how different verifiers perform on it

## Management Commands

The project includes several management commands for setup and analysis:

- `setup_sv_comp`: Initializes the database with SV-COMP data
- `embed`: Generates embeddings for verification tasks
- `eval_strategy`: Evaluates different verifier selection strategies
- `virtually_best_analysis`: Analyzes the performance of the virtually best verifier
- `categorical_best_analysis`: Analyzes category-based verifier selection strategy

## Getting Started

1. Install dependencies 
2. Configure the database in settings.py
3. Run migrations: `python manage.py migrate`
4. Load SV-COMP data: `python manage.py setup_sv_comp`
5. Generate embeddings: `python manage.py embed`
6. Start the development server: `python manage.py runserver`

## Requirements

- Python 3.9+
- Django 5.2+
- PyTorch
- Transformers (Hugging Face)
- ChromaDB
- pandas

## Project Status

This appears to be a research/academic project for analyzing software verification competition results and developing strategies for optimal verifier selection.