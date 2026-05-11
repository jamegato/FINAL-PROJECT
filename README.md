# Small Business Inventory Manager - Phase 2 Final Project

A professional small business inventory management system built with **Streamlit**, **Python OOP**, and **OpenAI integration**. This is a complete Phase 2 refactoring with proper layering, OOP design, and an AI assistant.

## 🏗️ Architecture

The application is organized into **four distinct layers**:

### 1. **UI Layer** (`app.py`)
- Streamlit interface with improved design
- Login/registration pages with test account information
- Separate dashboards for Owner and Employee roles
- Role-based page access control
- Beautiful gradient headers and styled components

### 2. **Data Layer** (`data_layer.py`)
- JSON file persistence with file locking
- Concurrent access protection
- Type-safe data loading with model conversion
- Clean separation of data concerns
- Methods for loading/saving each entity type

### 3. **Service Layer** (`service_layer.py`)
- Business logic and validation
- Services: Authentication, Inventory, Sales, Flags
- Consistent error handling
- Transaction-like behavior for complex operations
- No direct database access (uses models)

### 4. **Models Layer** (`models.py`)
- **Dataclasses**: `User`, `Product`, `Sale`, `Flag`
- **Manager Classes**: `UserManager`, `InventoryManager`, `SalesManager`, `FlagManager`
- Factory methods for creating entities
- Business methods (e.g., `Product.is_low_stock()`, `Sale.get_revenue()`)
- Type hints and docstrings throughout

## 🤖 AI Assistant (`ai_assistant.py`)

- **OpenAI Integration**: Connects to GPT-3.5-turbo for intelligent responses
- **Contextual Awareness**: Uses live inventory data for AI responses
- **Fallback Mode**: Pattern-based responses when API is unavailable or unconfigured
- **Natural Conversation**: Maintains chat history across sessions
- Can answer questions about:
  - Low stock alerts
  - Sales performance
  - Inventory value
  - Operational guidance

## 👥 User Roles

### Owner Account
- **Email**: `owner@test.com`
- **Password**: `owner123`
- **Features**:
  - Dashboard with business metrics
  - Inventory management (CRUD)
  - Sales reports
  - Low-stock flag monitoring
  - AI Assistant access

### Employee Account
- **Email**: `employee@test.com`
- **Password**: `employee123`
- **Features**:
  - Dashboard with personal metrics
  - Product catalog browsing
  - Sales recording
  - Low-stock flag submission
  - AI Assistant access

## 📦 Project Structure

```
FINAL PROJECT/
├── app.py                    # UI Layer (Streamlit app)
├── data_layer.py             # Data Access Layer
├── service_layer.py          # Business Logic Layer
├── models.py                 # Data Models & Managers
├── ai_assistant.py           # OpenAI Integration
├── data_access.py            # Legacy (kept for compatibility)
├── users.json                # User database
├── inventory.json            # Product inventory
├── sales.json                # Sales transactions
├── flags.json                # Low-stock alerts
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Configure OpenAI API

To enable the AI Assistant with real OpenAI responses:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

On Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

### 3. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## ✨ Key Features

### Phase 1 Issues Addressed
- ✅ Improved layout with sidebars, tabs, and proper spacing
- ✅ Better validation with clear error messages
- ✅ Proper session state management
- ✅ OOP design instead of procedural code
- ✅ Separated concerns into clear layers
- ✅ Test accounts with sample data visible on login

### Phase 2 Enhancements
- ✅ Multi-layer architecture (UI, Service, Data, Models)
- ✅ Object-oriented design with dataclasses and manager classes
- ✅ OpenAI-powered AI Assistant
- ✅ Improved UI with gradient headers and badges
- ✅ Business methods on models (e.g., `product.is_low_stock()`)
- ✅ Service layer for all business logic
- ✅ Factory methods for creating entities
- ✅ Comprehensive type hints and docstrings

### CRUD Operations
- **Create**: Add new products, register users, record sales, submit flags
- **Read**: View inventory, sales history, flags, reports
- **Update**: Modify product pricing/stock/thresholds
- **Delete**: Soft delete via "discontinue" feature

### Reporting
- Revenue analytics
- Sales performance by employee
- Low-stock alerts
- Inventory value calculations
- Flag status tracking

## 🔐 Authentication

- User registration with role selection
- Password validation (minimum 6 characters)
- Role-based access control
- Session state persistence
- Logout functionality

## 📊 Sample Data

The app comes pre-loaded with:
- **8 Products** across Bakery, Beverages, and Snacks categories
- **5 Sales Transactions** showing employee activity
- **2 Low-Stock Flags** for demonstration
- **2 User Accounts** (Owner and Employee) for testing

All sample data is visible immediately after login.

## 💡 Design Decisions

### OOP Approach
- Models use `@dataclass` for clean, maintainable code
- Manager classes encapsulate collections
- Factory methods (`create()`) for object creation
- Methods on entities for business logic

### Service Layer
- All validation logic centralized
- Services coordinate between UI and models
- Consistent error handling pattern
- Stateless, testable design

### Data Persistence
- JSON files with file locking to prevent corruption
- Type-safe conversion to model objects
- Automatic directory creation
- Error recovery mechanisms

### UI/UX
- Consistent color scheme (purple gradient headers)
- Icons for visual clarity
- Responsive layout with columns
- Form-based input for data entry
- Clear error and success messages

## 🔗 Dependencies

- **streamlit**: Web framework for building the UI
- **openai**: Integration with GPT-3.5-turbo (optional)
- **Python 3.8+**: Standard library only for core functionality

## 📝 Example Usage

### As Owner:
1. Login with `owner@test.com` / `owner123`
2. View dashboard with business metrics
3. Add a new product: "Sourdough Bread" ($6.99, 20 stock, threshold 8)
4. Check revenue reports
5. Review low-stock flags from employees

### As Employee:
1. Login with `employee@test.com` / `employee123`
2. Browse product catalog
3. Record a sale: "Espresso Shot × 3"
4. See stock update automatically
5. Flag low-stock items for owner review

## 🎯 Future Enhancements

Possible improvements:
- Database migration (SQLite/PostgreSQL)
- User profile management
- Export/import functionality
- Inventory forecasting with AI
- Multi-location support
- Mobile app
- Advanced analytics dashboards
- Email notifications

## 📄 License

Educational project - Phase 2 Final Project

## 👨‍💻 Development Notes

- All code follows PEP 8 style guidelines
- Comprehensive docstrings and type hints
- Clean separation of concerns
- No hardcoded values (configuration ready)
- Error handling throughout
- Idiomatic Python throughout
