"""
GUI-интерфейс для настройки парсера Ozon.

Запуск: python main.py setup-gui

Окно позволяет ввести:
- Номер телефона для входа на data.ozon.ru
- Email Gmail для чтения кода подтверждения
- App Password от Gmail
- Список SKU для парсинга

Данные сохраняются в .env файл.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional


class SetupGUI:
    """Графический интерфейс для настройки парсера."""

    def __init__(self):
        """Инициализация GUI."""
        self.root = tk.Tk()
        self.root.title("Ozon Parser — Настройка")
        self.root.geometry("550x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # Определяем путь к .env файлу
        self.env_path = Path(__file__).parent / ".env"

        # Загружаем текущие значения из .env
        self.current_values = self._load_env()

        # Создаём интерфейс
        self._create_ui()

    def _load_env(self) -> dict:
        """Чтение текущих значений из .env файла."""
        values = {}
        if self.env_path.exists():
            with open(self.env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        values[key.strip()] = value.strip()
        return values

    def _create_ui(self):
        """Создание элементов интерфейса."""
        # Заголовок
        header_frame = tk.Frame(self.root, bg="#1a73e8", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="Ozon Parser — Настройка",
            font=("Segoe UI", 16, "bold"),
            bg="#1a73e8",
            fg="white",
        )
        title_label.pack(pady=12)

        # Основной контент
        content_frame = tk.Frame(self.root, bg="#f0f0f0", padx=30, pady=20)
        content_frame.pack(fill="both", expand=True)

        # --- Поле: Номер телефона ---
        self._create_field(
            content_frame,
            row=0,
            label="Номер телефона",
            key="PHONE_NUMBER",
            placeholder="+79991234567",
            hint="Для входа на data.ozon.ru",
        )

        # --- Поле: Gmail Email ---
        self._create_field(
            content_frame,
            row=1,
            label="Gmail Email",
            key="GMAIL_EMAIL",
            placeholder="your@gmail.com",
            hint="Для чтения кодов подтверждения",
        )

        # --- Поле: Gmail App Password ---
        self._create_field(
            content_frame,
            row=2,
            label="Gmail App Password",
            key="GMAIL_APP_PASSWORD",
            placeholder="xxxx xxxx xxxx xxxx",
            hint="App Password из Google Account → Security",
            show="•",
        )

        # --- Поле: Список SKU ---
        self._create_field(
            content_frame,
            row=3,
            label="Список SKU",
            key="SKU_LIST",
            placeholder="2359066702,2829800382",
            hint="Артикулы товаров через запятую",
        )

        # --- Кнопки ---
        button_frame = tk.Frame(self.root, bg="#f0f0f0", pady=20)
        button_frame.pack(fill="x")

        save_btn = tk.Button(
            button_frame,
            text="💾 Сохранить",
            command=self._save,
            font=("Segoe UI", 11, "bold"),
            bg="#1a73e8",
            fg="white",
            activebackground="#1557b0",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=8,
        )
        save_btn.pack(side="left", padx=(30, 10))

        reset_btn = tk.Button(
            button_frame,
            text="🔄 Сбросить",
            command=self._reset,
            font=("Segoe UI", 11),
            bg="#e8e8e8",
            fg="#333",
            activebackground="#d0d0d0",
            activeforeground="#333",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
        )
        reset_btn.pack(side="left", padx=5)

        close_btn = tk.Button(
            button_frame,
            text="✕ Закрыть",
            command=self.root.destroy,
            font=("Segoe UI", 11),
            bg="#e8e8e8",
            fg="#333",
            activebackground="#d0d0d0",
            activeforeground="#333",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
        )
        close_btn.pack(side="right", padx=(10, 30))

        # --- Подсказка внизу ---
        hint_label = tk.Label(
            self.root,
            text=(
                "ℹ️ Как создать App Password: "
                "Google Account → Security → 2-Step Verification → App Passwords"
            ),
            font=("Segoe UI", 8),
            bg="#f0f0f0",
            fg="#666",
            wraplength=500,
        )
        hint_label.pack(pady=(0, 10))

    def _create_field(
        self,
        parent: tk.Frame,
        row: int,
        label: str,
        key: str,
        placeholder: str,
        hint: str,
        show: Optional[str] = None,
    ):
        """Создание поля ввода с подписью и подсказкой."""
        row_frame = tk.Frame(parent, bg="#f0f0f0")
        row_frame.pack(fill="x", pady=4)

        # Метка
        tk.Label(
            row_frame,
            text=label,
            font=("Segoe UI", 10, "bold"),
            bg="#f0f0f0",
            fg="#333",
            width=20,
            anchor="w",
        ).pack(side="left", padx=(0, 10))

        # Поле ввода
        entry = tk.Entry(
            row_frame,
            font=("Segoe UI", 10),
            bg="white",
            relief="solid",
            borderwidth=1,
            show=show,
            width=35,
        )
        entry.pack(side="left", fill="x", expand=True)

        # Заполняем текущим значением или placeholder
        value = self.current_values.get(key, "")
        if value:
            entry.insert(0, value)
        else:
            entry.insert(0, placeholder)
            entry.config(fg="#999")

        # Подсказка под полем
        tk.Label(
            row_frame,
            text=hint,
            font=("Segoe UI", 8),
            bg="#f0f0f0",
            fg="#888",
        ).pack(side="left", padx=(15, 0), pady=(18, 0))

        # Сохраняем ссылку на entry
        setattr(self, f"entry_{key}", entry)

    def _get_value(self, key: str, default: str) -> str:
        """Получить значение из поля ввода."""
        entry = getattr(self, f"entry_{key}", None)
        if entry:
            value = entry.get().strip()
            return value if value else default
        return default

    def _save(self):
        """Сохранение данных в .env файл."""
        # Собираем значения
        data = {
            "PHONE_NUMBER": self._get_value("PHONE_NUMBER", "+79991234567"),
            "GMAIL_EMAIL": self._get_value("GMAIL_EMAIL", "your@gmail.com"),
            "GMAIL_APP_PASSWORD": self._get_value("GMAIL_APP_PASSWORD", ""),
            "SKU_LIST": self._get_value("SKU_LIST", "2359066702,2829800382"),
        }

        # Валидация
        if not data["PHONE_NUMBER"].strip():
            messagebox.showerror("Ошибка", "Номер телефона не может быть пустым!")
            return

        if "@" not in data["GMAIL_EMAIL"]:
            messagebox.showerror("Ошибка", "Введите корректный Gmail email!")
            return

        if not data["GMAIL_APP_PASSWORD"].strip():
            messagebox.showwarning(
                "Внимание",
                "App Password не заполнен. Без него не получится "
                "получить код подтверждения из Gmail.\n\n"
                "Продолжить без пароля?",
                icon="warning",
            )
            # Пользователь нажал "Отмена" — не сохраняем
            return

        # Записываем в .env
        with open(self.env_path, "w", encoding="utf-8") as f:
            f.write("# Номер телефона для входа на data.ozon.ru\n")
            f.write(f"PHONE_NUMBER={data['PHONE_NUMBER']}\n\n")
            f.write("# Данные Gmail для чтения кода подтверждения\n")
            f.write(f"GMAIL_EMAIL={data['GMAIL_EMAIL']}\n")
            f.write(f"GMAIL_APP_PASSWORD={data['GMAIL_APP_PASSWORD']}\n\n")
            f.write("# Список SKU через запятую\n")
            f.write(f"SKU_LIST={data['SKU_LIST']}\n")

        messagebox.showinfo(
            "Успех",
            f"Настройки сохранены в .env файл!\n\n"
            f"Телефон: {data['PHONE_NUMBER']}\n"
            f"Gmail: {data['GMAIL_EMAIL']}\n"
            f"SKU: {data['SKU_LIST']}\n\n"
            f"Теперь можно запускать парсер.",
        )
        self.root.destroy()

    def _reset(self):
        """Сброс всех полей к значениям по умолчанию."""
        result = messagebox.askyesno(
            "Сброс",
            "Сбросить все поля к значениям по умолчанию?",
        )
        if not result:
            return

        # Очищаем поля
        for key in ["PHONE_NUMBER", "GMAIL_EMAIL", "GMAIL_APP_PASSWORD", "SKU_LIST"]:
            entry = getattr(self, f"entry_{key}")
            entry.delete(0, tk.END)

    def run(self):
        """Запуск GUI."""
        self.root.mainloop()


def main():
    """Точка входа для GUI."""
    gui = SetupGUI()
    gui.run()


if __name__ == "__main__":
    main()
