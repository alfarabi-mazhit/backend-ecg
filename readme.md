# Backend for Heart Disease Prediction App

This repository contains the backend implementation for a heart disease prediction app. The backend is built using **FastAPI** and integrates with a **MongoDB** database for storage. It also handles user management, predictions, and machine learning model management.

---

## **Features**
- User authentication and authorization (JWT-based).
- Role-based access control (user and admin roles).
- ECG image upload and prediction processing.
- Machine Learning model management (add, update, delete models).
- User management (list, block, delete users).
- Prediction management (list, view, delete predictions).
- RESTful APIs for frontend integration.

---

## **Technologies Used**
- **FastAPI**: For building the RESTful APIs.
- **MongoDB**: Database for storing users, predictions, and ML models.
- **Pydantic**: Data validation and serialization.
- **TensorFlow**: For integrating ML models (future integration planned).
- **Python**: Programming language.
- **JWT**: For secure authentication.

---

## **Setup Instructions**

### **1. Clone the Repository**
```bash
git clone https://github.com/<your-username>/<your-repository-name>.git
cd backend
```
## **2. Set Up Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate 
```
3. Install Dependencies
bash
Копировать код
pip install -r requirements.txt
4. Configure Environment Variables
Create a .env file in the root directory and add the following variables:

env
Копировать код
MONGODB_URI=mongodb://localhost:27017/heart-disease-db
JWT_SECRET=your-super-secret-key
JWT_EXPIRES_IN=24  # Token expiration time in hours
PORT=8000
UPLOAD_DIRECTORY=uploaded_images  # Directory for storing uploaded files
5. Run the Application
Start the development server:

bash
Копировать код
uvicorn app.main:app --reload
API Documentation
The API documentation is available at:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
Folder Structure
bash
Копировать код
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/    # API route handlers
│   │   └── routes.py     # Main API router
│   ├── core/
│   │   ├── config.py     # App configuration
│   │   └── security.py   # JWT and security utilities
│   ├── db/
│   │   ├── crud/         # CRUD operations
│   │   └── mongodb.py    # MongoDB connection
│   ├── models/           # Pydantic schemas and data models
│   ├── services/         # Business logic and utility services
│   └── main.py           # Application entry point
├── .env                  # Environment variables
├── requirements.txt      # Project dependencies
└── README.md             # Project README
Future Enhancements
Integrate TensorFlow model for ECG image prediction.
Add file upload support for ML model management.
Implement role-based access control for specific API routes.
Expand data visualization for prediction and user statistics.
License
This project is licensed under the MIT License. See the LICENSE file for details.

Contributing
Contributions are welcome! Please follow these steps:

Fork the repository.
Create a feature branch (git checkout -b feature-name).
Commit your changes (git commit -m "Add feature-name").
Push to the branch (git push origin feature-name).
Create a pull request.
Contact
For questions or support, contact:

Email: your-email@example.com
GitHub: https://github.com/your-username
yaml
Копировать код
