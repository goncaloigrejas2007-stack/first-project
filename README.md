# 💰 FinanceFlow - Personal Finance Dashboard

A modern, interactive personal finance dashboard built with Python and Streamlit. Track your expenses, manage budgets, set savings goals, and visualize your financial data with beautiful charts.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

---

## ✨ Features

### 📊 Dashboard & Analytics
- **Real-time Overview** - See your total income, spending, net balance, and average transactions at a glance
- **Interactive Charts** - Beautiful visualizations using Altair
  - Spending by category (bar chart)
  - Category distribution (pie chart)
  - Daily spending trends (line chart)
  - Monthly comparison (bar chart)
- **Monthly Reports** - Track spending patterns month over month

### 💳 Budget Management
- **Budget Setup** - Define monthly budgets for each category
- **Real-time Tracking** - Compare actual spending vs. budget
- **Smart Alerts**
  - 🟡 Warning when you reach 75% of budget
  - 🔴 Alert when budget is exceeded
  - 🟢 All good when spending is within limits

### 💼 Savings Goals
- **Goal Creation** - Set financial targets (travel, emergency fund, new laptop, etc.)
- **Progress Tracking** - Visual progress bars showing how close you are to your goals
- **Goal Management** - Add contributions and delete goals as needed
- **Achievement Milestones** - Celebrate when you reach 75% and 100% of your goal

### 📝 Transaction Management
- **Quick Add** - Add transactions from the sidebar with date, amount, category, and description
- **Edit & Delete** - Full control over your transaction history
- **Advanced Filtering**
  - Filter by category (single or multiple)
  - Filter by date range
  - Sort by date or amount
- **Export Data** - Download filtered transactions as CSV

### 🗄️ Data Persistence
- **SQLite Database** - All data is saved locally and persists between sessions
- **No Cloud** - Your financial data stays on your computer
- **Automatic Backup** - Database is created automatically on first run

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/goncaloigrejas2007-stack/first-project.git
cd first-project
```

2. **Create a virtual environment** (recommended)
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
streamlit run streamlit_app.py
```

5. **Open in browser**
The app will automatically open at `http://localhost:8501`

---

## 📖 How to Use

### Adding a Transaction
1. Open the sidebar (left side)
2. Fill in the transaction details:
   - **Amount** - How much you spent or earned
   - **Category** - Select from predefined categories or add custom ones
   - **Description** - Optional note about the transaction
   - **Date** - When the transaction occurred
3. Click "💾 Save Transaction"

### Managing Budget
1. Go to the **🎯 Budget** tab
2. Set your monthly limits for each category
3. Click "💾 Save Budget" to apply changes
4. View **Budget vs Actual Spending** to track progress
5. Color indicators show your status:
   - 🟢 Within budget
   - 🟡 75% of budget reached (warning)
   - 🔴 Budget exceeded

### Setting Savings Goals
1. Go to the **💼 Savings** tab
2. Click "Add Goal" section
3. Enter:
   - **Goal name** - What you're saving for
   - **Target amount** - How much you want to save
   - **Description** - Optional details
4. Click "Add Goal"
5. Track progress with visual progress bars
6. Add contributions using "Add Contribution" section

### Viewing Analytics
1. Go to the **📈 Analytics** tab
2. See spending breakdown by category
3. View 30-day spending trends
4. Compare spending across months
5. Identify spending patterns and trends

### Exporting Data
1. Go to the **📋 Transactions** tab
2. Apply filters (category, date range, sort order)
3. Click "📤 Export filtered CSV"
4. Use the data in Excel, Google Sheets, or other tools

---

## 📊 Project Structure

```
first-project/
├── streamlit_app.py          # Main application
├── auth_manager.py           # User authentication and settings
├── requirements.txt          # Python dependencies
├── finance_data.db          # SQLite database (auto-generated)
├── README.md                # Documentation
├── .gitignore               # Git ignore rules
└── .github/                 # GitHub configuration
    └── ISSUE_TEMPLATE/      # Issue templates
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.8+** | Programming language |
| **Streamlit** | Web framework for data apps |
| **Pandas** | Data manipulation and analysis |
| **SQLite3** | Local database |
| **Altair** | Interactive data visualizations |
| **bcrypt** | Password hashing |

---

## 📝 Default Categories

The app comes with these default expense categories:
- 🍔 **Food** - €500/month
- 🚗 **Transport** - €150/month
- 🎬 **Entertainment** - €300/month
- 💡 **Utilities** - €200/month
- 🛍️ **Other** - €200/month
- 💵 **Income** - Special category for earnings

You can customize these budgets in the Budget tab.

---

## 💾 Data Storage

All your financial data is stored in a local SQLite database (`finance_data.db`). 

**Key tables:**
- `transactions` - All your income and expenses
- `budgets` - Your monthly budget limits
- `savings_goals` - Your financial goals and progress

**Backup your data:**
```bash
cp finance_data.db finance_data.db.backup
```

---

## 🎨 UI/UX Highlights

- ✅ Clean, modern interface
- ✅ Responsive design that works on desktop
- ✅ Color-coded budget status (🟢🟡🔴)
- ✅ Interactive charts with tooltips
- ✅ Real-time calculations
- ✅ Sidebar for easy navigation
- ✅ Emoji indicators for quick visual reference

---

## 🔐 Privacy & Security

- 🔒 **No cloud storage** - Everything stays on your computer
- 🔒 **No internet required** - Works completely offline
- 🔒 **No data sharing** - Your financial data is yours alone
- 🔒 **Open source** - You can review the code anytime

---

## 📈 Future Enhancements

Planned features for upcoming versions:
- [ ] Dark mode / Theme customization
- [ ] Recurring transaction templates
- [ ] Custom categories
- [ ] CSV import for historical data
- [ ] Advanced financial reports (PDF export)
- [ ] Multi-currency support
- [ ] Budget alerts via email/SMS
- [ ] Mobile-friendly version

---

## 🐛 Known Issues

Currently known limitations:
- Data is stored in browser session memory unless explicitly saved
- Limited to single-currency (EUR)
- No built-in password protection

---

## 💬 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Support

If you find this project helpful, please:
- ⭐ Star the repository on GitHub
- 🐛 Report issues if you find any
- 💡 Suggest improvements and features
- 📢 Share it with friends

---

## 👨‍💻 Author

Created by **Gonçalo Igrejas**

---

## 📞 Contact & Social

- GitHub: [@goncaloigrejas2007-stack](https://github.com/goncaloigrejas2007-stack)
- Email: goncalo.igrejas2007@gmail.com

---

## 🎯 Roadmap

### Version 1.0 ✅
- Basic transaction tracking
- Budget management
- Analytics dashboard

### Version 1.1 (Current)
- Savings goals
- Monthly comparisons
- Budget alerts
- Enhanced UI

### Version 2.0 (Planned)
- Dark mode
- Custom categories
- Recurring transactions
- Advanced reports
- Data import/export

---

## 📚 Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Altair Documentation](https://altair-viz.github.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

Made with ❤️ using Streamlit



































































































































































































































































































a
b
c
