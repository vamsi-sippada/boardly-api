# Boardly API

A Trello-inspired project management REST API built with Django and Django REST Framework.

## Live URL
https://boardly-api-hfay.onrender.com

## Tech Stack
- **Backend:** Django, Django REST Framework
- **Auth:** JWT (djangorestframework-simplejwt)
- **Database:** PostgreSQL
- **Async Tasks:** Celery + Redis
- **Deployment:** Render

## Features
- Board, List, Card nested resource hierarchy
- Per-board role permissions (Owner / Member / Viewer)
- Django signals for automatic activity logging
- Celery background tasks for due date reminders
- Notification system with fanout to board members

## Local Setup

```bash
git clone https://github.com/vamsi-sippada/boardly-api
cd boardly-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
CELERY_BROKER_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1

Run:
```bash
python manage.py migrate
python manage.py runserver
```


## API Endpoints

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/auth/register/ | Register a new user | No |
| POST | /api/auth/login/ | Get JWT tokens | No |
| POST | /api/auth/token/refresh/ | Refresh access token | No |
| GET | /api/auth/profile/ | Get current user profile | Yes |
| PUT | /api/auth/profile/ | Update current user profile | Yes |

### Boards
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/boards/ | List all boards you're a member of | Yes |
| POST | /api/boards/ | Create a new board | Yes |
| GET | /api/boards/{id}/ | Get board detail with members and lists | Yes |
| PUT | /api/boards/{id}/ | Update board (owner only) | Yes |
| DELETE | /api/boards/{id}/ | Delete board (owner only) | Yes |
| POST | /api/boards/{id}/add_member/ | Add a member with role | Yes |
| DELETE | /api/boards/{id}/remove_member/{user_id}/ | Remove a member | Yes |

### Lists
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/boards/{board_id}/lists/ | Get all lists in a board | Yes |
| POST | /api/boards/{board_id}/lists/ | Create a list (member/owner only) | Yes |
| GET | /api/boards/{board_id}/lists/{id}/ | Get list detail | Yes |
| PUT | /api/boards/{board_id}/lists/{id}/ | Update list (member/owner only) | Yes |
| DELETE | /api/boards/{board_id}/lists/{id}/ | Delete list (member/owner only) | Yes |

### Cards
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/boards/{board_id}/lists/{list_id}/cards/ | Get all cards in a list | Yes |
| POST | /api/boards/{board_id}/lists/{list_id}/cards/ | Create a card (member/owner only) | Yes |
| GET | /api/boards/{board_id}/lists/{list_id}/cards/{id}/ | Get card detail | Yes |
| PUT | /api/boards/{board_id}/lists/{list_id}/cards/{id}/ | Update card | Yes |
| DELETE | /api/boards/{board_id}/lists/{list_id}/cards/{id}/ | Delete card | Yes |
| POST | /api/boards/{board_id}/lists/{list_id}/cards/{id}/assign/ | Assign member to card | Yes |
| DELETE | /api/boards/{board_id}/lists/{list_id}/cards/{id}/unassign/{user_id}/ | Unassign member | Yes |

### Comments
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/boards/{board_id}/lists/{list_id}/cards/{card_id}/comments/ | Get all comments | Yes |
| POST | /api/boards/{board_id}/lists/{list_id}/cards/{card_id}/comments/ | Add a comment | Yes |
| DELETE | /api/boards/{board_id}/lists/{list_id}/cards/{card_id}/comments/{id}/ | Delete comment (author/owner only) | Yes |

### Activity Log
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/boards/{board_id}/lists/{list_id}/cards/{card_id}/activity/ | Get card activity log | Yes |

### Notifications
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/notifications/ | Get all your notifications | Yes |
| POST | /api/notifications/{id}/mark_read/ | Mark notification as read | Yes |
| POST | /api/notifications/mark_all_read/ | Mark all notifications as read | Yes |

## Permission Matrix

| Action | Owner | Member | Viewer |
|--------|-------|--------|--------|
| View board/lists/cards | ✅ | ✅ | ✅ |
| Create/edit cards | ✅ | ✅ | ✗ |
| Add comments | ✅ | ✅ | ✗ |
| Create/edit lists | ✅ | ✅ | ✗ |
| Delete own comments | ✅ | ✅ | ✗ |
| Delete any comment | ✅ | ✗ | ✗ |
| Manage board members | ✅ | ✗ | ✗ |
| Edit board settings | ✅ | ✗ | ✗ |
| Delete board | ✅ | ✗ | ✗ |

## Background Tasks
Celery handles due date reminders:
- **8:00 AM UTC daily** — notifies assigned members of cards due in 24 hours
- **9:00 AM UTC daily** — notifies assigned members of overdue cards

## Running Tests
```bash
python manage.py test
```
23 tests covering authentication, board permissions, card CRUD, and signal side effects.