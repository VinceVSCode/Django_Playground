# Django Playground

A Django learning playground project for exploring Django web framework concepts and features. This repository serves as a sandbox for experimenting with Django development patterns, authentication, REST APIs, and web application functionality.

## 🎯 Purpose

This project is designed for learning Django and has no specific end goal. It's an evolving playground where new Django concepts and features are implemented and tested. Future expansions may include additional Django apps, advanced features, or integrations with other technologies.

## 🚀 Current Features

### Web Application
- **User Authentication**: Login/logout functionality with Django's built-in authentication system
- **Note Management**: Create, view, and manage personal notes
- **User-specific Content**: Each user can only access their own notes
- **Responsive Templates**: Clean HTML templates for web interface

### REST API
- **Token-based Authentication**: API endpoints require authentication
- **Notes API**: Full CRUD operations for notes via RESTful endpoints
- **JSON Responses**: Structured API responses using Django REST Framework

### Technical Implementation
- **Django 5.2.4**: Latest Django framework
- **SQLite Database**: Simple file-based database for development
- **Django REST Framework**: API development toolkit
- **Model-View-Template (MVT)**: Standard Django architecture pattern

## 📁 Project Structure

```
Django_Playground/
├── DjangoPlayground/           # Main Django project
│   ├── DjangoPlayground/       # Project configuration
│   │   ├── settings.py         # Django settings
│   │   ├── urls.py            # Main URL configuration
│   │   └── wsgi.py            # WSGI configuration
│   ├── firstsite/             # Main Django app
│   │   ├── models.py          # Data models (Note)
│   │   ├── views.py           # View functions (web + API)
│   │   ├── urls.py            # App URL patterns
│   │   ├── forms.py           # Django forms
│   │   ├── serializers.py     # DRF serializers
│   │   └── templates/         # HTML templates
│   ├── db.sqlite3             # SQLite database
│   └── manage.py              # Django management script
└── README.md                  # This file
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/VinceVSCode/Django_Playground.git
   cd Django_Playground
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or manually install:
   ```bash
   pip install django djangorestframework
   ```

3. **Navigate to the Django project**
   ```bash
   cd DjangoPlayground
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Web interface: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/

## 🌐 Available Endpoints

### Web Views
- `/hello/` - Hello world page with authentication status
- `/notes/` - View user's notes (requires login)
- `/notes/create/` - Create a new note (requires login)
- `/accounts/login/` - Login page
- `/accounts/logout/` - Logout page
- `/admin/` - Django admin interface

### API Endpoints
- `GET/POST /api/notes/` - List user notes or create new note
- `GET/PUT/DELETE /api/notes/<id>/` - Retrieve, update, or delete specific note

All API endpoints require authentication.

## 📋 Models

### Note Model
- `title` (CharField): Note title (max 200 characters)
- `content` (TextField): Note content
- `created_at` (DateTimeField): Auto-generated creation timestamp
- `owner` (ForeignKey): Reference to the User who created the note

## 🔧 Technologies Used

- **Backend**: Django 5.2.4, Django REST Framework
- **Database**: SQLite (development)
- **Frontend**: HTML templates, Django template system
- **Authentication**: Django's built-in authentication system

## 🚧 Development Status

This is an active learning project. Current areas of exploration include:
- User authentication and authorization
- Django models and database relationships
- REST API development with Django REST Framework
- Template rendering and forms
- Django admin interface

## 🤝 Contributing

This is a personal learning project, but feel free to:
- Fork the repository for your own learning
- Suggest improvements or new features to explore
- Share learning resources or Django best practices

## 📝 Learning Notes

### Key Django Concepts Implemented
- **Models**: Database models with relationships
- **Views**: Function-based views for both web and API
- **Templates**: HTML rendering with Django template language
- **Forms**: Django forms for user input
- **Authentication**: User login/logout and permission decorators
- **URL Routing**: URL patterns and namespacing
- **Admin Interface**: Django admin for model management

### Django REST Framework Features
- **Serializers**: Data serialization for API responses
- **API Views**: Function-based API views with decorators
- **Permissions**: Authentication and permission classes
- **Response**: Structured JSON responses

## 📚 Future Learning Areas

Potential areas for future exploration:
- Class-based views
- Advanced authentication (OAuth, JWT)
- Database optimization and complex queries
- File uploads and media handling
- Caching strategies
- Testing frameworks
- Deployment configurations
- Additional Django apps and packages

---

*This project is part of a Django learning journey. Code quality and architecture may vary as different concepts are explored and implemented.*