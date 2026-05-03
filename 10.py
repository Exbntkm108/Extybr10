import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
import subprocess
from datetime import datetime

# --- Настройки API ---
# Получите бесплатный API-ключ на https://www.exchangerate-api.com/
API_KEY = "YOUR_API_KEY"  # Вставьте сюда ваш API-ключ
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/"

class CurrencyConverter:
    def __init__(self, master):
        self.master = master
        master.title("Currency Converter")

        self.data_file = 'conversion_history.json'
        self.conversion_history = self.load_history()

        if API_KEY == "YOUR_API_KEY":
            messagebox.showwarning("API Ключ", "Пожалуйста, замените 'YOUR_API_KEY' на ваш реальный API-ключ от exchangerate-api.com в коде.")

        # --- Интерфейс ---
        self.main_frame = ttk.Frame(master, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Выбор валют
        ttk.Label(self.main_frame, text="Из валюты:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.from_currency_var = tk.StringVar(value="USD")
        self.from_currency_combo = ttk.Combobox(self.main_frame, textvariable=self.from_currency_var, width=10)
        self.from_currency_combo.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(self.main_frame, text="В валюту:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.to_currency_var = tk.StringVar(value="EUR")
        self.to_currency_combo = ttk.Combobox(self.main_frame, textvariable=self.to_currency_var, width=10)
        self.to_currency_combo.grid(row=0, column=3, padx=5, pady=2)

        # Поле ввода суммы
        ttk.Label(self.main_frame, text="Сумма:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.amount_entry = ttk.Entry(self.main_frame, width=15)
        self.amount_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        # Кнопка конвертации
        self.convert_button = ttk.Button(self.main_frame, text="Конвертировать", command=self.convert_currency)
        self.convert_button.grid(row=2, column=0, columnspan=4, padx=5, pady=10)

        # Результат конвертации
        ttk.Label(self.main_frame, text="Результат:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.result_display = ttk.Label(self.main_frame, text="0.00")
        self.result_display.grid(row=3, column=1, columnspan=3, padx=5, pady=2, sticky="w")

        # Таблица истории
        self.history_frame = ttk.LabelFrame(master, text="История конвертаций", padding="10")
        self.history_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.tree = ttk.Treeview(self.history_frame, columns=("Timestamp", "FromCurrency", "ToCurrency", "Amount", "ConvertedAmount"), show="headings")
        self.tree.heading("Timestamp", text="Время")
        self.tree.heading("FromCurrency", text="Из")
        self.tree.heading("ToCurrency", text="В")
        self.tree.heading("Amount", text="Сумма")
        self.tree.heading("ConvertedAmount", text="Результат")

        self.tree.column("Timestamp", width=150)
        self.tree.column("FromCurrency", width=50, anchor='center')
        self.tree.column("ToCurrency", width=50, anchor='center')
        self.tree.column("Amount", width=100)
        self.tree.column("ConvertedAmount", width=100)

        self.tree.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self.history_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.load_currencies()
        self.update_history_table()

    def load_currencies(self):
        try:
            response = requests.get(BASE_URL.replace('latest/','codes/')) # Используем эндпоинт для кодов валют
            data = response.json()
            if data.get("result") == "success":
                currencies = list(data.get("supported_codes", {}).keys())
                self.from_currency_combo['values'] = currencies
                self.to_currency_combo['values'] = currencies
            else:
                messagebox.showerror("Ошибка API", f"Не удалось загрузить список валют: {data.get('error-type')}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка сети", f"Не удалось подключиться к API: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при загрузке валют: {e}")

    def load_history(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def save_history(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.password_history, f, indent=4, ensure_ascii=False)

    def convert_currency(self):
        from_currency = self.from_currency_var.get()
        to_currency = self.to_currency_var.get()
        amount_str = self.amount_entry.get()

        if not from_currency or not to_currency:
            messagebox.showwarning("Ошибка", "Выберите валюты 'Из' и 'В'.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showwarning("Некорректный ввод", "Сумма должна быть положительным числом.")
                return
        except ValueError:
            messagebox.showwarning("Некорректный ввод", "Введите корректное числовое значение для суммы.")
            return

        try:
            response = requests.get(f"{BASE_URL}{from_currency}")
            data = response.json()

            if data.get("result") == "success":
                rates = data.get("conversion_rates")
                if to_currency in rates:
                    exchange_rate = rates[to_currency]
                    converted_amount = amount * exchange_rate
                    self.result_display.config(text=f"{converted_amount:.2f} {to_currency}")

                    # Добавляем в историю
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.conversion_history.append({
                        "timestamp": timestamp,
                        "from_currency": from_currency,
                        "to_currency": to_currency,
                        "amount": amount,
                        "converted_amount": f"{converted_amount:.2f} {to_currency}"
                    })
                    self.save_history()
                    self.update_history_table()
                else:
                    messagebox.showerror("Ошибка", f"Нет данных для конвертации в {to_currency}.")
            else:
                messagebox.showerror("Ошибка API", f"Ошибка получения курса: {data.get('error-type')}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка сети", f"Не удалось подключиться к API: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при конвертации: {e}")

    def update_history_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in reversed(self.conversion_history):
            self.tree.insert("", tk.END, values=(
                record.get("timestamp"),
                record.get("from_currency"),
                record.get("to_currency"),
                record.get("amount"),
                record.get("converted_amount")
            ))

# --- Функции Git ---
def setup_git_repo(repo_path="."):
    if not os.path.exists(os.path.join(repo_path, ".git")):
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        print("Git репозиторий инициализирован.")
    else:
        print("Git репозиторий уже существует.")

def create_gitignore(repo_path="."):
    gitignore_path = os.path.join(repo_path, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write("__pycache__/\n")
            f.write("*.pyc\n")
            f.write("conversion_history.json\n") # Не добавлять файл с историей в Git
            f.write("*.lock\n") # Для pipenv/poetry
        print(".gitignore создан.")

if __name__ == "__main__":
    setup_git_repo()
    create_gitignore()

    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()
    