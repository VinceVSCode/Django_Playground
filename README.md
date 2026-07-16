# Django Playground
![tests](https://github.com/VinceVSCode/Django_Playground/actions/workflows/tests.yml/badge.svg)
<img width="1536" height="1024" alt="DjangoPlayground" src="https://github.com/user-attachments/assets/ada6156a-efe2-4180-8052-0623e1bf04ac" />

A Django learning project designed for exploring Django framework concepts and features. This repository serves as a practical playground for understanding Django development, including models, views, templates, authentication, and REST APIs.

## 🎯 Project Purpose

This project is primarily a learning resource with no specific end goal. It's designed to:
- Explore Django fundamentals
- Practice Django best practices
- Experiment with different Django features
- Serve as a reference for Django development patterns

## 🚀 Features

### Core Features
- **User Authentication**: Login/logout functionality with user session management
- **Notes Management**: CRUD operations for personal notes
- **Web Interface**: HTML templates for user interaction
- **REST API**: RESTful endpoints for programmatic access
- **Database Integration**: SQLite database with Django ORM

### Technical Highlights
- Django 5.2.4 framework
- Django REST Framework for API endpoints
- User-based data isolation (notes are user-specific)
- Form handling with Django Forms
- Template rendering with context data
- Authentication decorators for protected views

## 📁 Project Structure

```
Django_Playground/
├── DjangoPlayground/              # Main Django project directory
│   ├── DjangoPlayground/          # Project configuration
│   │   ├── __init__.py
│   │   ├── settings.py            # Django settings
│   │   ├── urls.py               # Main URL configuration
│   │   ├── wsgi.py               # WSGI configuration
│   │   └── asgi.py               # ASGI configuration
│   ├── firstsite/                # Main Django app
│   │   ├── models.py             # Note model definition
│   │   ├── views.py              # Views (both web and API)
│   │   ├── urls.py               # App URL patterns
│   │   ├── forms.py              # Django forms
│   │   ├── serializers.py        # DRF serializers
│   │   ├── admin.py              # Django admin configuration
│   │   ├── migrations/           # Database migrations
│   │   └── templates/            # HTML templates
│   │       ├── firstsite/        # App-specific templates
│   │       └── registration/     # Authentication templates
│   ├── manage.py                 # Django management script
│   └── db.sqlite3               # SQLite database (created after setup)
├── .gitignore                   # Git ignore file
└── README.md                    # This file
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/VinceVSCode/Django_Playground.git
   cd Django_Playground
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv django_env
   source django_env/bin/activate  # On Windows: django_env\Scripts\activate
   ```

3. **Install dependencies** (from the repository root, where `requirements.txt` lives)
   ```bash
   pip install -r requirements.txt
   ```
   This installs Django, Django REST Framework, and the test tooling (pytest, pytest-django, factory_boy, Faker).

4. **Navigate to the Django project directory**
   ```bash
   cd DjangoPlayground
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional, for admin access)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main application: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/

## 🎮 Usage

### Web Interface

#### Authentication
- **Login**: http://127.0.0.1:8000/accounts/login/
- **Logout**: http://127.0.0.1:8000/accounts/logout/

#### Main Features
- **Hello Page**: http://127.0.0.1:8000/hello/
  - Displays a personalized greeting
  - Shows different messages for authenticated vs. anonymous users

- **Notes Management**:
  - **View Notes**: http://127.0.0.1:8000/notes/ (requires login)
  - **Create Note**: http://127.0.0.1:8000/notes/create/ (requires login)

### REST API Endpoints

All API endpoints require authentication (token or session) and return JSON responses.

#### Notes API
- **GET /api/notes/**: Retrieve all notes for the authenticated user (supports `?tag=`, `?untagged=1`, `?search=`, `?pinned=`, `?archived=`)
- **POST /api/notes/**: Create a new note
- **GET /api/notes/{id}/**: Retrieve a specific note
- **PUT /api/notes/{id}/**: Update a specific note (snapshots a version first)
- **DELETE /api/notes/{id}/**: Delete a specific note
- **POST /api/notes/{id}/send/**: Send a copy to another user (`{"recipient_username": "bob"}`)
- **GET/POST/DELETE /api/notes/{id}/versions/**, **POST .../versions/{vid}/restore/**: version history
- **GET /api/inbox/**, **GET /api/sent/**: send history
- **GET/POST /api/tags/**, **GET /api/analytics/notes/**

#### Authentication (token)

Generate a token for a user, then send it as an `Authorization: Token <key>` header:
```bash
python manage.py drf_create_token <username>
```

#### API Usage Examples

**Create a note** (POST /api/notes/):
```bash
curl -X POST http://127.0.0.1:8000/api/notes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your-token>" \
  -d '{"title": "My Note", "content": "This is my note content"}'
```

**Retrieve notes** (GET /api/notes/):
```bash
curl -X GET http://127.0.0.1:8000/api/notes/ \
  -H "Authorization: Token <your-token>"
```

## 📊 Database Schema

### Note Model
```python
class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    tags = models.ManyToManyField('Tag', blank=True)
```

**Fields:**
- `title`: Note title (max 100 characters)
- `content`: Note content (unlimited text)
- `created_at` / `updated_at`: Automatic timestamps
- `owner`: Foreign key to Django's built-in User model
- `is_pinned` / `is_archived`: Boolean flags used by the list filters
- `tags`: Many-to-many link to per-user `Tag` records

**Related models:** `Tag` (per-user, unique name), `NoteVersion` (edit-history snapshots),
`NoteSend` (log of a note copied to another user), and `NoteEvent` (create/update/delete/send
audit trail powering analytics).

## 🔧 Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Django Shell
```bash
python manage.py shell
```

### Collecting Static Files (for production)
```bash
python manage.py collectstatic
```

## 🎯 Learning Objectives

This project demonstrates:

1. **Django Fundamentals**
   - Project and app structure
   - Models, Views, Templates (MVT) pattern
   - URL routing and configuration

2. **Database Operations**
   - Model definition and relationships
   - Database migrations
   - ORM queries and filtering

3. **Authentication & Authorization**
   - User authentication system
   - Login required decorators
   - User-specific data access

4. **Forms & Templates**
   - Django Forms for data input
   - HTML template rendering
   - Context data passing

5. **REST API Development**
   - Django REST Framework integration
   - Serializers for data transformation
   - API views and permissions

6. **Best Practices**
   - Separation of concerns
   - DRY (Don't Repeat Yourself) principle
   - Security considerations

## 🚀 Future Possibilities

This playground project could be extended with:

- **Enhanced User Features**
  - User registration
  - Password reset functionality
  - User profiles

- **Advanced Note Features**
  - Note categories/tags
  - Note sharing between users
  - Rich text editing
  - File attachments

- **Technical Enhancements**
  - PostgreSQL database
  - Redis caching
  - Celery task queue
  - Docker containerization

- **UI/UX Improvements**
  - CSS framework integration (Bootstrap, Tailwind)
  - JavaScript frontend (React, Vue)
  - Progressive Web App (PWA) features

- **Additional Django Features**
  - Django signals
  - Custom middleware
  - Management commands
  - Internationalization (i18n)

## 📝 Contributing

This is a learning project, but contributions are welcome! Feel free to:
- Suggest improvements
- Add new features
- Fix bugs
- Improve documentation

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Acknowledgments

- Django documentation and community
- Django REST Framework documentation
- Python community for excellent learning resources

---

**Happy Learning! 🎉**

This project is designed to be a hands-on learning experience. Don't hesitate to break things, experiment, and learn from the process!
