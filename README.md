# CyberShield Academy

CyberShield Academy is a web-based cybersecurity training platform designed to help students and young professionals build real-world digital defence skills. The platform tackles the problem of inaccessible, overly theoretical cybersecurity education by combining structured course modules, hands-on hacking labs, timed live events, and a dual-portal system — all wrapped in a sleek, professional interface.

# How It Works

When a user visits the platform, they are prompted to choose a role: **Student** or **Admin**. Based on the selected role they are taken to a dedicated login form, and once authenticated, they are granted access to their respective portal. Students can browse and enrol in courses, launch lab environments, join live events, and contact the team. Admins get a full management dashboard to control courses, labs, events, users, and incoming messages.

---

# App Features

## Student Portal

### 1. The Home Page (Landing)

The public-facing landing page introduces CyberShield Academy with a hero section, platform highlights, and call-to-action buttons directing visitors to register or explore courses. It communicates the platform's mission and gives an overview of available training tracks before the user even logs in.

<center><img width="867" height="366" alt="image" style="padding: 10px;" src="https://github.com/user-attachments/assets/4b58bc3e-a7ad-4e3c-8980-be405f9e6a2d" />
</center>

### 2. The Login & Registration System

The portal selector screen prompts every user — student or admin — to choose their role before proceeding. Students who don't have an account can register with their first name, last name, email, and password (with confirmation). Validation is enforced on both the frontend and backend, including duplicate-email detection and minimum password length. After successful registration, the student is redirected to log in and begin their training.

<center><img width="831" height="392" alt="image" style="padding: 10px;" src="https://github.com/user-attachments/assets/57318274-9a8e-4667-b672-eca1b24ccc53" />
</center>

### 3. The Student Dashboard

Once logged in, students land on their personal dashboard displaying a welcome message and a summary of their enrolled courses with live progress bars showing how far along each course they are. The dashboard also shows enrollment dates and last active timestamps, giving students a clear picture of their training momentum.

<center><img width="932" height="386" alt="image" style="padding: 10px;" src="https://github.com/user-attachments/assets/43ebe1f7-cb71-4f3d-aa12-00081a29c6bd" />
</center>

### 4. The Courses Page

The courses listing page displays all available training modules published by the admin. Students can filter courses by **difficulty level** (Beginner, Intermediate, Advanced, Expert) or **topic** (Network Security, Web Security, Malware Analysis, Cryptography, Forensics, Cloud Security, OSINT, Penetration Testing, Incident Response, Social Engineering), and search by keyword. Each course card shows the title, topic, level, estimated duration, number of modules, and enrollment count. Students can enrol in a course directly from the listing page with one click. Pagination is implemented for large catalogues.

<center><img width="835" height="410" alt="image" style="padding: 10px;" src="https://github.com/user-attachments/assets/4212fc64-cf23-4888-8048-86f0aa305366" />
</center>

### 5. The Labs Page

The labs section gives students access to hands-on hacking environments. Each lab card displays its category (Web, Network, Forensics, Crypto, Malware, Cloud, OSINT, Reversing, Exploit, Social Engineering), difficulty (Novice → Elite), XP reward, estimated duration, tags, and a custom icon. Students can launch a lab environment with a single button — progress is tracked automatically, and returning students pick up where they left off. A live XP counter motivates completion.

<center><img width="823" height="392" alt="image" style="padding: 10px;" src="https://github.com/user-attachments/assets/b60ea36b-ae0b-4258-b6c8-a3c15783f686" /></center>

### 6. The Contact Page

Students and visitors can reach the CyberShield team through a contact form that captures their name, email, subject (selected from a dropdown), and a message. All submissions are stored in the database and surfaced in the admin inbox with read/unread status tracking and the sender's IP address for security logging.

<center><img width="803" height="412" alt="image" style="padding: 10px;" src="https://github.com/user-attachments/assets/623aa115-64c7-4729-afd7-e629a7958630" />
</center>

---

## Admin Portal

Admins log in through the same role-selector screen using hardcoded credentials. Once authenticated, they gain access to a full management panel with a persistent sidebar for navigation.

### 1. The Admin Dashboard

The central command panel displays four stat cards — **Total Students**, **Active Users**, **Total Enrollments**, and **Unread Messages** — all pulled live from the database. Below the stats, a student accounts table shows every registered student with their enrollment count, join date, status badge, and a one-click activate/deactivate toggle. A quick-actions panel on the right provides shortcuts to all management pages. Recent messages are previewed at the bottom with unread indicators.

### 2. Student Management

The dedicated students page (`/admin/students`) shows every registered student in a full-featured table with live client-side search (by name or email), a read/unread status filter, sortable columns, and enrollment progress bars. Stats at the top summarise total, active, deactivated, and total enrollment counts. Pagination handles large user bases (25 per page).

### 3. Course Management

Admins can create, edit, and delete courses through a polished form. Fields include course title, full description, topic, difficulty level, estimated duration, number of modules, and an optional cover image URL. The form supports both create mode (blank) and edit mode (pre-filled with existing data), and a delete button with confirmation is available in edit mode.

### 4. Lab Management

The lab creation and editing form allows admins to configure every aspect of a lab: title, description, category, difficulty, XP reward, estimated duration, environment URL (external), comma-separated tags, and an emoji icon (with a visual picker). Labs can be deactivated (soft-deleted) from the edit form, preserving their progress records.

### 5. Live Event Management

Admins can launch timed live events with a title, description, XP pool, and an end datetime. The form includes a live XP preview that updates as the admin types. Events can be edited after creation (to extend time or adjust XP) and ended early via a soft-delete. Active events appear automatically as banners on the student-facing labs page.

### 6. Inbox (Messages)

The admin messages page presents a two-pane email-style inbox. The left pane lists all messages with sender name, subject preview, timestamp, and an unread indicator dot. Clicking any message opens the full detail in the right pane — showing the sender's full name, email, IP address, received timestamp, complete message body, and a read/unread status badge. A **Reply** button opens the user's mail client pre-addressed to the sender. Messages can be permanently deleted with a confirmation prompt. Live search and a read/unread filter are available in the toolbar.

<center><img width="941" height="408" alt="image" style="padding: 10px;" src="https://github.com/user-attachments/assets/31084ecf-44a1-4c1b-afce-46a6bc3587af" />
</center>

---

# Project Structure

```
CyberShield-Academy/
│
├── app.py                  # Flask application factory, all routes and auth logic
├── models.py               # SQLAlchemy database models
├── requirements.txt        # Python dependencies
├── cybershield.db          # SQLite database (auto-created on first run)
│
├── migrations/             # Flask-Migrate database migration files
│
├── templates/              # Jinja2 HTML templates
│   ├── index.html          # Public landing page
│   ├── about.html          # About page
│   ├── login_signup.html   # Dual-mode login & registration page
│   ├── dashboard.html      # Student dashboard
│   ├── training.html       # Courses listing page
│   ├── course_detail.html  # Individual course page
│   ├── course_form.html    # Admin: create course form
│   ├── lab_form.html       # Admin: create / edit lab form
│   ├── event_form.html     # Admin: create / edit live event form
│   ├── labs.html           # Labs listing + live event banner
│   ├── labs_briefing.html  # Event briefing detail page
│   ├── contact.html        # Public contact form
│   ├── admin_dashboard.html    # Admin overview dashboard
│   ├── admin_messages.html     # Admin inbox (two-pane)
│   ├── admin_students.html     # Admin student registry
│   └── admin/
│       └── course_form.html    # Admin: edit existing course form
│
└── static/                 # CSS, JS, and image assets
```

---


# Database Models

| Model            | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `User`           | Student accounts with hashed passwords, active status, and enrollment links |
| `Course`         | Training modules with title, topic, level, duration, and module count       |
| `Enrollment`     | Links a student to a course with a progress percentage and timestamps        |
| `Lab`            | Hands-on lab environments with XP, difficulty, tags, and optional env URL   |
| `LabProgress`    | Tracks per-student lab progress, completion status, and XP awarded           |
| `LiveEvent`      | Timed group CTF events with XP pool, end datetime, and participant list      |
| `ContactMessage` | Inbound contact form submissions with read status and IP logging             |

---


# Conclusion

So far the complete frontend of CyberShield Academy has been built using **Flask + Jinja2**, along with the full authentication system (student registration, login, session management, and admin access control). The database schema covering users, courses, enrollments, labs, lab progress, live events, and contact messages is fully implemented and migrated.

The objective for the next phase is to complete the remaining admin management features (certificates, analytics, settings) and to build out the full interactive lab environment — including real-time progress updates from within lab sessions and automatic XP awarding upon completion.
