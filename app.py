import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import date, datetime
from config import DB_CONFIG

# Словарь таблиц с их русскими названиями и полями
TABLES = {
    'services': {
        'name': 'Службы',
        'columns': ['service_id', 'name', 'phone', 'created_at'],
        'column_names': ['ID', 'Название', 'Телефон', 'Дата создания'],
        'editable': ['name', 'phone'],
        'pk': 'service_id'
    },
    'departments': {
        'name': 'Отделы',
        'columns': ['department_id', 'service_id', 'name', 'address', 'phone', 'created_at'],
        'column_names': ['ID', 'ID службы', 'Название', 'Адрес', 'Телефон', 'Дата создания'],
        'editable': ['service_id', 'name', 'address', 'phone'],
        'pk': 'department_id'
    },
    'sections': {
        'name': 'Участки',
        'columns': ['section_id', 'department_id', 'name', 'manager', 'created_at'],
        'column_names': ['ID', 'ID отдела', 'Название', 'Управляющий', 'Дата создания'],
        'editable': ['department_id', 'name', 'manager'],
        'pk': 'section_id'
    },
    'houses': {
        'name': 'Дома',
        'columns': ['house_id', 'service_id', 'department_id', 'section_id', 'street',
                    'house_number', 'building', 'year_built', 'total_apartments', 'resident_count', 'created_at'],
        'column_names': ['ID', 'ID службы', 'ID отдела', 'ID участка', 'Улица',
                         'Номер дома', 'Корпус', 'Год постройки', 'Всего квартир', 'Жильцов', 'Дата создания'],
        'editable': ['service_id', 'department_id', 'section_id', 'street', 'house_number', 'building', 'year_built'],
        'pk': 'house_id'
    },
    'apartments': {
        'name': 'Квартиры',
        'columns': ['apartment_id', 'house_id', 'apt_number', 'floor', 'living_area',
                    'total_area', 'privatized', 'cold_water', 'hot_water', 'garbage_chute',
                    'elevator', 'current_residents', 'created_at'],
        'column_names': ['ID', 'ID дома', 'Номер кв.', 'Этаж', 'Жилая пл.',
                         'Общая пл.', 'Приватиз.', 'Хол. вода', 'Гор. вода', 'Мусоропровод',
                         'Лифт', 'Жильцов', 'Дата создания'],
        'editable': ['house_id', 'apt_number', 'floor', 'living_area', 'total_area',
                     'privatized', 'cold_water', 'hot_water', 'garbage_chute', 'elevator'],
        'pk': 'apartment_id'
    },
    'tenants': {
        'name': 'Жильцы',
        'columns': ['tenant_id', 'apartment_id', 'full_name', 'inn', 'passport',
                    'birth_date', 'is_responsible', 'payer_code_id', 'moved_in', 'moved_out', 'created_at'],
        'column_names': ['ID', 'ID квартиры', 'ФИО', 'ИНН', 'Паспорт',
                         'Дата рожд.', 'Ответственный', 'ID шифра', 'Дата вселения', 'Дата выселения', 'Дата создания'],
        'editable': ['apartment_id', 'full_name', 'inn', 'passport', 'birth_date',
                     'is_responsible', 'payer_code_id', 'moved_in', 'moved_out'],
        'pk': 'tenant_id'
    },
    'payer_codes': {
        'name': 'Шифры плательщиков',
        'columns': ['payer_code_id', 'code', 'name', 'percent_share', 'created_at'],
        'column_names': ['ID', 'Код', 'Название', 'Процент', 'Дата создания'],
        'editable': ['code', 'name', 'percent_share'],
        'pk': 'payer_code_id'
    },
    'tariffs': {
        'name': 'Тарифы',
        'columns': ['tariff_id', 'service_type', 'has_service', 'tariff', 'valid_from', 'valid_to', 'created_at'],
        'column_names': ['ID', 'Тип услуги', 'Есть услуга', 'Тариф', 'Действует с', 'Действует до', 'Дата создания'],
        'editable': ['service_type', 'has_service', 'tariff', 'valid_from', 'valid_to'],
        'pk': 'tariff_id'
    }
}

# Операторы сравнения для фильтра
FILTER_OPERATORS = [
    ('=', 'Равно'),
    ('!=', 'Не равно'),
    ('>', 'Больше'),
    ('<', 'Меньше'),
    ('>=', 'Больше или равно'),
    ('<=', 'Меньше или равно'),
    ('LIKE', 'Содержит'),
    ('NOT LIKE', 'Не содержит'),
    ('IS NULL', 'Пусто'),
    ('IS NOT NULL', 'Не пусто')
]


class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ГЖУ - Система управления жилищным фондом")
        self.root.state('zoomed')
        self.root.minsize(900, 500)

        self.conn = None
        self.current_table = None
        self.sort_column = None
        self.sort_reverse = False
        self.current_filter = None
        self.toast_window = None

        self.create_widgets()
        self.connect_db()

    def show_toast(self, message, duration=2500, toast_type="info"):
        # Показать всплывающее уведомление
        if self.toast_window:
            try:
                self.toast_window.destroy()
            except:
                pass
        accent_colors = {
            "success": "#28a745",  # Зеленый
            "error": "#dc3545",  # Красный
            "info": "#17a2b8",  # Голубой
            "warning": "#ffc107"  # Желтый
        }
        bg_colors = {
            "success": "#d4edda",  # Светло-зеленый
            "error": "#f8d7da",  # Светло-красный
            "info": "#d1ecf1",  # Светло-голубой
            "warning": "#fff3cd"  # Светло-желтый
        }
        accent_color = accent_colors.get(toast_type, accent_colors["info"])
        bg_color = bg_colors.get(toast_type, bg_colors["info"])

        self.toast_window = tk.Toplevel(self.root)
        self.toast_window.overrideredirect(True)
        self.toast_window.attributes('-topmost', True)
        outer_frame = tk.Frame(self.toast_window, bg=accent_color, padx=1, pady=1)
        outer_frame.pack(fill=tk.BOTH, expand=True)
        main_frame = tk.Frame(outer_frame, bg=bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)
        accent_bar = tk.Frame(main_frame, bg=accent_color, width=5)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y)
        content_frame = tk.Frame(main_frame, bg=bg_color, padx=12, pady=10)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        label = tk.Label(content_frame, text=message, fg='#333333', bg=bg_color,
                         font=('Segoe UI', 10), wraplength=300, justify=tk.LEFT)
        label.pack()
        self.toast_window.update_idletasks()
        width = self.toast_window.winfo_width()
        height = self.toast_window.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - width - 15
        y = screen_height - height - 70
        self.toast_window.geometry(f'+{x}+{y}')
        self.toast_window.after(duration, self.close_toast)

    def close_toast(self):
        # Закрыть уведомление
        if self.toast_window:
            try:
                self.toast_window.destroy()
            except:
                pass
            self.toast_window = None

    def connect_db(self):
        # Подключение к базе данных
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.show_toast("Подключено к базе данных", toast_type="success")
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к БД:\n{e}")
            self.show_toast("Ошибка подключения к БД", toast_type="error")

    def create_widgets(self):
        # Создание виджетов интерфейса
        left_frame = ttk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        tables_frame = ttk.LabelFrame(left_frame, text="Таблицы", padding=5)
        tables_frame.pack(fill=tk.X, pady=(0, 10))
        for table_key, table_info in TABLES.items():
            btn = ttk.Button(tables_frame, text=table_info['name'], width=20,
                             command=lambda t=table_key: self.load_table(t))
            btn.pack(pady=2)
        forms_frame = ttk.LabelFrame(left_frame, text="Формы", padding=5)
        forms_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(forms_frame, text="Квартира + Жильцы", width=20,
                   command=self.open_apartment_tenants_form).pack(pady=2)
        reports_frame = ttk.LabelFrame(left_frame, text="Отчеты", padding=5)
        reports_frame.pack(fill=tk.X)
        ttk.Button(reports_frame, text="Квартплата", width=20,
                   command=self.report_rent).pack(pady=2)
        ttk.Button(reports_frame, text="Жильцы по участкам", width=20,
                   command=self.report_tenants_by_section).pack(pady=2)
        ttk.Button(reports_frame, text="Статистика жилфонда", width=20,
                   command=self.report_housing_stats).pack(pady=2)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        search_frame = ttk.LabelFrame(main_frame, text="Поиск (по подстроке)", padding=5)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text="Поле:").pack(side=tk.LEFT, padx=2)
        self.search_field = ttk.Combobox(search_frame, state="readonly", width=15)
        self.search_field.pack(side=tk.LEFT, padx=2)
        ttk.Label(search_frame, text="Значение:").pack(side=tk.LEFT, padx=2)
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=2)
        self.search_entry.bind('<Return>', lambda e: self.search_records())
        ttk.Button(search_frame, text="Найти", command=self.search_records).pack(side=tk.LEFT, padx=2)
        filter_frame = ttk.LabelFrame(main_frame, text="Фильтр", padding=5)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(filter_frame, text="Поле:").pack(side=tk.LEFT, padx=2)
        self.filter_field = ttk.Combobox(filter_frame, state="readonly", width=15)
        self.filter_field.pack(side=tk.LEFT, padx=2)
        ttk.Label(filter_frame, text="Оператор:").pack(side=tk.LEFT, padx=2)
        self.filter_operator = ttk.Combobox(filter_frame, state="readonly", width=15)
        self.filter_operator['values'] = [op[1] for op in FILTER_OPERATORS]
        self.filter_operator.current(0)
        self.filter_operator.pack(side=tk.LEFT, padx=2)
        self.filter_operator.bind('<<ComboboxSelected>>', self.on_operator_change)
        ttk.Label(filter_frame, text="Значение:").pack(side=tk.LEFT, padx=2)
        self.filter_entry = ttk.Entry(filter_frame, width=15)
        self.filter_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Применить", command=self.apply_filter).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Сброс фильтра", command=self.reset_filter).pack(side=tk.LEFT, padx=2)
        sort_frame = ttk.LabelFrame(main_frame, text="Сортировка", padding=5)
        sort_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(sort_frame, text="Поле:").pack(side=tk.LEFT, padx=2)
        self.sort_field = ttk.Combobox(sort_frame, state="readonly", width=15)
        self.sort_field.pack(side=tk.LEFT, padx=2)
        ttk.Label(sort_frame, text="Направление:").pack(side=tk.LEFT, padx=2)
        self.sort_direction = ttk.Combobox(sort_frame, state="readonly", width=12)
        self.sort_direction['values'] = ['По возрастанию', 'По убыванию']
        self.sort_direction.current(0)
        self.sort_direction.pack(side=tk.LEFT, padx=2)
        ttk.Button(sort_frame, text="Сортировать", command=self.apply_sort).pack(side=tk.LEFT, padx=2)
        ttk.Button(sort_frame, text="Сброс сортировки", command=self.reset_sort).pack(side=tk.LEFT, padx=2)
        self.sort_label_var = tk.StringVar(value="")
        ttk.Label(sort_frame, textvariable=self.sort_label_var, foreground="blue").pack(side=tk.LEFT, padx=10)
        data_frame = ttk.Frame(main_frame)
        data_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(data_frame, show="headings")
        vsb = ttk.Scrollbar(data_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(data_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        data_frame.grid_rowconfigure(0, weight=1)
        data_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-1>", self.on_header_click)
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=5)
        ttk.Button(actions_frame, text="Добавить", command=self.add_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Редактировать", command=self.edit_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Удалить", command=self.delete_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Обновить", command=self.load_data()).pack(side=tk.LEFT, padx=2)
        self.filter_label_var = tk.StringVar(value="")
        ttk.Label(actions_frame, textvariable=self.filter_label_var, foreground="green").pack(side=tk.LEFT, padx=20)

    def on_operator_change(self, event=None):
        # Обработка изменения оператора фильтра
        operator_index = self.filter_operator.current()
        operator = FILTER_OPERATORS[operator_index][0]
        # Для IS NULL и IS NOT NULL скрываем поле ввода
        if operator in ('IS NULL', 'IS NOT NULL'):
            self.filter_entry.configure(state='disabled')
            self.filter_entry.delete(0, tk.END)
        else:
            self.filter_entry.configure(state='normal')

    def load_table(self, table_name):
        # Загрузка данных таблицы
        if not self.conn:
            self.show_toast("Нет подключения к БД", toast_type="warning")
            return
        self.current_table = table_name
        table_info = TABLES[table_name]
        # Сброс фильтра и сортировки при смене таблицы
        self.current_filter = None
        self.sort_column = None
        self.sort_reverse = False
        self.filter_label_var.set("")
        self.sort_label_var.set("")
        # Очистка и настройка Treeview
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = table_info['columns']
        for i, col in enumerate(table_info['columns']):
            self.tree.heading(col, text=table_info['column_names'][i])
            self.tree.column(col, width=100, minwidth=50)
        # Обновление комбобоксов
        self.search_field['values'] = table_info['column_names']
        self.filter_field['values'] = table_info['column_names']
        self.sort_field['values'] = table_info['column_names']
        if table_info['column_names']:
            self.search_field.current(0)
            self.filter_field.current(0)
            self.sort_field.current(0)
        self.load_data()

    def load_data(self):
        # Загрузка данных из текущей таблицы
        if not self.current_table or not self.conn:
            return
        try:
            cursor = self.conn.cursor()
            query = f"SELECT * FROM {self.current_table}"
            params = []

            # Применение фильтра
            if self.current_filter:
                field, operator, value = self.current_filter
                if operator in ('IS NULL', 'IS NOT NULL'):
                    query += f" WHERE {field} {operator}"
                elif operator in ('LIKE', 'NOT LIKE'):
                    query += f" WHERE CAST({field} AS TEXT) {operator} %s"
                    params.append(f"%{value}%")
                else:
                    query += f" WHERE {field} {operator} %s"
                    params.append(value)

            # Применение сортировки
            if self.sort_column:
                order = "DESC" if self.sort_reverse else "ASC"
                query += f" ORDER BY {self.sort_column} {order}"

            cursor.execute(query, params if params else None)
            rows = cursor.fetchall()

            # Очистка таблицы
            self.tree.delete(*self.tree.get_children())

            # Добавление данных
            for row in rows:
                # Преобразование данных для отображения
                display_row = []
                for val in row:
                    if val is None:
                        display_row.append("")
                    elif isinstance(val, bool):
                        display_row.append("Да" if val else "Нет")
                    elif isinstance(val, (date, datetime)):
                        display_row.append(str(val))
                    else:
                        display_row.append(val)
                self.tree.insert("", tk.END, values=display_row)
            cursor.close()
            table_name = TABLES[self.current_table]['name']
            self.show_toast(f"{table_name}: загружено {len(rows)} записей", toast_type="success")
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Ошибка", f"Ошибка загрузки данных:\n{e}")

    def on_header_click(self, event):
        # Обработка клика по заголовку для быстрой сортировки
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            column = self.tree.identify_column(event.x)
            col_index = int(column[1:]) - 1
            if self.current_table:
                table_info = TABLES[self.current_table]
                col_name = table_info['columns'][col_index]
                col_display = table_info['column_names'][col_index]

                if self.sort_column == col_name:
                    self.sort_reverse = not self.sort_reverse
                else:
                    self.sort_column = col_name
                    self.sort_reverse = False

                self.sort_field.current(col_index)
                self.sort_direction.current(1 if self.sort_reverse else 0)

                direction = "убыв." if self.sort_reverse else "возр."
                self.sort_label_var.set(f"Сортировка: {col_display} ({direction})")

                self.load_data()

    def search_records(self):
        # Поиск записей
        if not self.current_table:
            self.show_toast("Сначала выберите таблицу", toast_type="warning")
            return

        field_index = self.search_field.current()
        if field_index < 0:
            return

        table_info = TABLES[self.current_table]
        field_name = table_info['columns'][field_index]
        field_display = table_info['column_names'][field_index]
        search_value = self.search_entry.get()

        if not search_value:
            self.current_filter = None
            self.filter_label_var.set("")
        else:
            self.current_filter = (field_name, 'LIKE', search_value)
            self.filter_label_var.set(f"Поиск: {field_display} содержит '{search_value}'")

        self.load_data()

    def apply_filter(self):
        # Применение фильтра
        if not self.current_table:
            self.show_toast("Сначала выберите таблицу", toast_type="warning")
            return

        field_index = self.filter_field.current()
        operator_index = self.filter_operator.current()

        if field_index < 0 or operator_index < 0:
            return

        table_info = TABLES[self.current_table]
        field_name = table_info['columns'][field_index]
        field_display = table_info['column_names'][field_index]
        operator = FILTER_OPERATORS[operator_index][0]
        operator_display = FILTER_OPERATORS[operator_index][1]
        filter_value = self.filter_entry.get()

        # Проверка значения для операторов, требующих его
        if operator not in ('IS NULL', 'IS NOT NULL') and not filter_value:
            self.show_toast("Введите значение для фильтра", toast_type="warning")
            return

        self.current_filter = (field_name, operator, filter_value)

        if operator in ('IS NULL', 'IS NOT NULL'):
            self.filter_label_var.set(f"Фильтр: {field_display} {operator_display}")
        else:
            self.filter_label_var.set(f"Фильтр: {field_display} {operator_display} '{filter_value}'")

        self.load_data()

    def reset_filter(self):
        # Сброс фильтра
        self.search_entry.delete(0, tk.END)
        self.filter_entry.delete(0, tk.END)
        self.current_filter = None
        self.filter_label_var.set("")
        if self.current_table:
            self.load_data()

    def apply_sort(self):
        # Применение сортировки
        if not self.current_table:
            self.show_toast("Сначала выберите таблицу", toast_type="warning")
            return

        field_index = self.sort_field.current()
        if field_index < 0:
            return

        table_info = TABLES[self.current_table]
        self.sort_column = table_info['columns'][field_index]
        col_display = table_info['column_names'][field_index]
        self.sort_reverse = self.sort_direction.current() == 1

        direction = "убыв." if self.sort_reverse else "возр."
        self.sort_label_var.set(f"Сортировка: {col_display} ({direction})")

        self.load_data()

    def reset_sort(self):
        # Сброс сортировки
        self.sort_column = None
        self.sort_reverse = False
        self.sort_label_var.set("")
        if self.current_table:
            self.load_data()

    def add_record(self):
        # Добавление новой записи
        if not self.current_table:
            self.show_toast("Сначала выберите таблицу", toast_type="warning")
            return

        self.open_edit_dialog(None)

    def edit_record(self):
        # Редактирование выбранной записи
        if not self.current_table:
            self.show_toast("Сначала выберите таблицу", toast_type="warning")
            return

        selected = self.tree.selection()
        if not selected:
            self.show_toast("Выберите запись для редактирования", toast_type="warning")
            return

        values = self.tree.item(selected[0])['values']
        self.open_edit_dialog(values)

    def on_double_click(self, event):
        # Обработка двойного клика для редактирования
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            self.edit_record()

    def open_edit_dialog(self, values):
        # Открытие диалога редактирования
        if not self.current_table:
            return

        table_info = TABLES[self.current_table]
        is_new = values is None

        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить запись" if is_new else "Редактировать запись")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        entries = {}

        for i, col in enumerate(table_info['columns']):
            if col == table_info['pk'] and is_new:
                continue  # Пропускаем первичный ключ при добавлении
            if col == 'created_at':
                continue  # Пропускаем дату создания

            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=10, pady=2)

            label = ttk.Label(frame, text=table_info['column_names'][i] + ":", width=15)
            label.pack(side=tk.LEFT)

            # Определяем тип виджета
            col_lower = col.lower()
            if 'privatized' in col_lower or 'water' in col_lower or 'elevator' in col_lower or \
                    'garbage' in col_lower or 'responsible' in col_lower or 'has_service' in col_lower:
                var = tk.BooleanVar()
                entry = ttk.Checkbutton(frame, variable=var)
                entry.var = var
                if values and i < len(values):
                    val = values[i]
                    var.set(val == "Да" or val is True or val == "true")
            else:
                entry = ttk.Entry(frame, width=30)
                if values and i < len(values):
                    entry.insert(0, str(values[i]) if values[i] not in [None, ""] else "")

            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entries[col] = entry

            if col not in table_info['editable'] and not is_new:
                if hasattr(entry, 'configure'):
                    try:
                        entry.configure(state='disabled')
                    except:
                        pass

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        def save():
            self.save_record(entries, values, is_new)
            dialog.destroy()

        ttk.Button(btn_frame, text="Сохранить", command=save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def save_record(self, entries, old_values, is_new):
        # Сохранение записи в БД
        if not self.conn or not self.current_table:
            return
        table_info = TABLES[self.current_table]
        try:
            cursor = self.conn.cursor()
            if is_new:
                # INSERT
                columns = []
                values = []
                placeholders = []

                for col in table_info['editable']:
                    if col in entries:
                        entry = entries[col]
                        if hasattr(entry, 'var'):
                            val = entry.var.get()
                        else:
                            val = entry.get().strip()
                            if val == "":
                                val = None
                        columns.append(col)
                        values.append(val)
                        placeholders.append("%s")

                query = f"INSERT INTO {self.current_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(query, values)
            else:
                # UPDATE
                pk_col = table_info['pk']
                pk_index = table_info['columns'].index(pk_col)
                pk_value = old_values[pk_index]

                set_parts = []
                values = []

                for col in table_info['editable']:
                    if col in entries:
                        entry = entries[col]
                        if hasattr(entry, 'var'):
                            val = entry.var.get()
                        else:
                            val = entry.get().strip()
                            if val == "":
                                val = None
                        set_parts.append(f"{col} = %s")
                        values.append(val)

                values.append(pk_value)
                query = f"UPDATE {self.current_table} SET {', '.join(set_parts)} WHERE {pk_col} = %s"
                cursor.execute(query, values)

            self.conn.commit()
            cursor.close()
            self.load_data()
            messagebox.showinfo("Успех", "Запись сохранена")

        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Ошибка", f"Ошибка сохранения:\n{e}")

    def delete_record(self):
        # Удаление выбранной записи
        if not self.current_table:
            self.show_toast("Сначала выберите таблицу", toast_type="warning")
            return

        selected = self.tree.selection()
        if not selected:
            self.show_toast("Выберите запись для удаления", toast_type="warning")
            return

        if not messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            return

        try:
            table_info = TABLES[self.current_table]
            pk_col = table_info['pk']
            pk_index = table_info['columns'].index(pk_col)

            values = self.tree.item(selected[0])['values']
            pk_value = values[pk_index]

            cursor = self.conn.cursor()
            query = f"DELETE FROM {self.current_table} WHERE {pk_col} = %s"
            cursor.execute(query, (pk_value,))
            self.conn.commit()
            cursor.close()

            self.load_data()
            messagebox.showinfo("Успех", "Запись удалена")

        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Ошибка", f"Ошибка удаления:\n{e}")

    def open_apartment_tenants_form(self):
        # Открытие формы для добавления квартиры с жильцами
        if not self.conn:
            self.show_toast("Нет подключения к БД", toast_type="warning")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить квартиру с жильцами")
        dialog.geometry("1100x600")
        dialog.transient(self.root)
        dialog.grab_set()
        main_canvas = tk.Canvas(dialog)
        main_scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=main_canvas.yview)
        main_frame = ttk.Frame(main_canvas)
        main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        apt_frame = ttk.LabelFrame(main_frame, text="Данные квартиры", padding=10)
        apt_frame.pack(fill=tk.X, padx=10, pady=5)
        apt_entries = {}
        row = ttk.Frame(apt_frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Дом:", width=15).pack(side=tk.LEFT)
        houses = self.get_houses_list()
        house_combo = ttk.Combobox(row, state="readonly", width=50)
        house_combo['values'] = [f"{h[0]}: {h[1]} {h[2]}{' корп.' + h[3] if h[3] else ''}" for h in houses]
        house_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        apt_entries['house_combo'] = house_combo
        apt_entries['houses_data'] = houses

        row = ttk.Frame(apt_frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Номер квартиры:", width=15).pack(side=tk.LEFT)
        apt_number_entry = ttk.Entry(row, width=20)
        apt_number_entry.pack(side=tk.LEFT)
        apt_entries['apt_number'] = apt_number_entry

        row = ttk.Frame(apt_frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Этаж:", width=15).pack(side=tk.LEFT)
        floor_entry = ttk.Entry(row, width=20)
        floor_entry.pack(side=tk.LEFT)
        apt_entries['floor'] = floor_entry

        row = ttk.Frame(apt_frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Жилая площадь:", width=15).pack(side=tk.LEFT)
        living_area_entry = ttk.Entry(row, width=20)
        living_area_entry.pack(side=tk.LEFT)
        ttk.Label(row, text="м²").pack(side=tk.LEFT, padx=5)
        apt_entries['living_area'] = living_area_entry

        row = ttk.Frame(apt_frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Общая площадь:", width=15).pack(side=tk.LEFT)
        total_area_entry = ttk.Entry(row, width=20)
        total_area_entry.pack(side=tk.LEFT)
        ttk.Label(row, text="м²").pack(side=tk.LEFT, padx=5)
        apt_entries['total_area'] = total_area_entry

        checkboxes_frame = ttk.Frame(apt_frame)
        checkboxes_frame.pack(fill=tk.X, pady=5)

        privatized_var = tk.BooleanVar()
        ttk.Checkbutton(checkboxes_frame, text="Приватизирована", variable=privatized_var).pack(side=tk.LEFT, padx=5)
        apt_entries['privatized'] = privatized_var

        cold_water_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(checkboxes_frame, text="Хол. вода", variable=cold_water_var).pack(side=tk.LEFT, padx=5)
        apt_entries['cold_water'] = cold_water_var

        hot_water_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(checkboxes_frame, text="Гор. вода", variable=hot_water_var).pack(side=tk.LEFT, padx=5)
        apt_entries['hot_water'] = hot_water_var

        garbage_var = tk.BooleanVar()
        ttk.Checkbutton(checkboxes_frame, text="Мусоропровод", variable=garbage_var).pack(side=tk.LEFT, padx=5)
        apt_entries['garbage_chute'] = garbage_var

        elevator_var = tk.BooleanVar()
        ttk.Checkbutton(checkboxes_frame, text="Лифт", variable=elevator_var).pack(side=tk.LEFT, padx=5)
        apt_entries['elevator'] = elevator_var

        tenants_frame = ttk.LabelFrame(main_frame, text="Жильцы квартиры (можно добавить несколько)", padding=10)
        tenants_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tenants_list = []

        tenants_tree = ttk.Treeview(tenants_frame,
                                    columns=('name', 'passport', 'birth_date', 'responsible', 'moved_in'),
                                    show='headings', height=5)
        tenants_tree.heading('name', text='ФИО')
        tenants_tree.heading('passport', text='Паспорт')
        tenants_tree.heading('birth_date', text='Дата рожд.')
        tenants_tree.heading('responsible', text='Ответственный')
        tenants_tree.heading('moved_in', text='Дата вселения')

        tenants_tree.column('name', width=200)
        tenants_tree.column('passport', width=120)
        tenants_tree.column('birth_date', width=100)
        tenants_tree.column('responsible', width=100)
        tenants_tree.column('moved_in', width=100)

        tenants_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Форма добавления жильца
        add_tenant_frame = ttk.LabelFrame(tenants_frame, text="Добавить жильца", padding=5)
        add_tenant_frame.pack(fill=tk.X, pady=5)

        tenant_entries = {}

        row1 = ttk.Frame(add_tenant_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="ФИО:", width=12).pack(side=tk.LEFT)
        tenant_name = ttk.Entry(row1, width=30)
        tenant_name.pack(side=tk.LEFT, padx=5)
        tenant_entries['full_name'] = tenant_name

        ttk.Label(row1, text="Паспорт:").pack(side=tk.LEFT, padx=5)
        tenant_passport = ttk.Entry(row1, width=15)
        tenant_passport.pack(side=tk.LEFT)
        tenant_entries['passport'] = tenant_passport

        row2 = ttk.Frame(add_tenant_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Дата рожд.:", width=12).pack(side=tk.LEFT)
        tenant_birth = ttk.Entry(row2, width=12, foreground='gray')
        tenant_birth.insert(0, "ГГГГ-ММ-ДД")
        tenant_birth.pack(side=tk.LEFT, padx=5)
        tenant_entries['birth_date'] = tenant_birth

        def on_birth_focus_in(e):
            if tenant_birth.get() == "ГГГГ-ММ-ДД":
                tenant_birth.delete(0, tk.END)
                tenant_birth.configure(foreground='black')

        def on_birth_focus_out(e):
            if not tenant_birth.get():
                tenant_birth.insert(0, "ГГГГ-ММ-ДД")
                tenant_birth.configure(foreground='gray')

        def on_birth_key(e):
            val = tenant_birth.get()
            if e.char.isdigit():
                if len(val) == 4 or len(val) == 7:
                    tenant_birth.insert(tk.END, '-')

        tenant_birth.bind('<FocusIn>', on_birth_focus_in)
        tenant_birth.bind('<FocusOut>', on_birth_focus_out)
        tenant_birth.bind('<KeyRelease>', on_birth_key)

        ttk.Label(row2, text="Дата вселения:").pack(side=tk.LEFT, padx=5)
        tenant_moved = ttk.Entry(row2, width=12)
        tenant_moved.insert(0, str(date.today()))
        tenant_moved.pack(side=tk.LEFT)
        tenant_entries['moved_in'] = tenant_moved

        tenant_responsible_var = tk.BooleanVar()
        ttk.Checkbutton(row2, text="Ответственный", variable=tenant_responsible_var).pack(side=tk.LEFT, padx=10)
        tenant_entries['is_responsible'] = tenant_responsible_var

        def add_tenant_to_list():
            # Добавить жильца в список
            name = tenant_entries['full_name'].get().strip()
            if not name:
                self.show_toast("Введите ФИО жильца", toast_type="warning")
                return

            tenant_data = {
                'full_name': name,
                'passport': tenant_entries['passport'].get().strip() or None,
                'birth_date': tenant_entries['birth_date'].get().strip() if tenant_entries[
                                                                                'birth_date'].get().strip() != "ГГГГ-ММ-ДД" else None,
                'is_responsible': tenant_entries['is_responsible'].get(),
                'moved_in': tenant_entries['moved_in'].get().strip() or str(date.today())
            }

            tenants_list.append(tenant_data)

            tenants_tree.insert('', tk.END, values=(
                tenant_data['full_name'],
                tenant_data['passport'] or '',
                tenant_data['birth_date'] or '',
                'Да' if tenant_data['is_responsible'] else 'Нет',
                tenant_data['moved_in']
            ))

            tenant_entries['full_name'].delete(0, tk.END)
            tenant_entries['passport'].delete(0, tk.END)
            tenant_entries['birth_date'].delete(0, tk.END)
            tenant_entries['birth_date'].insert(0, "ГГГГ-ММ-ДД")
            tenant_entries['birth_date'].configure(foreground='gray')
            tenant_entries['is_responsible'].set(False)

        def remove_selected_tenant():
            # Удалить выбранного жильца из списка
            selected = tenants_tree.selection()
            if selected:
                idx = tenants_tree.index(selected[0])
                tenants_tree.delete(selected[0])
                if idx < len(tenants_list):
                    tenants_list.pop(idx)

        btn_row = ttk.Frame(add_tenant_frame)
        btn_row.pack(fill=tk.X, pady=5)
        ttk.Button(btn_row, text="Добавить жильца в список", command=add_tenant_to_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row, text="Удалить выбранного", command=remove_selected_tenant).pack(side=tk.LEFT, padx=5)

        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill=tk.X, pady=10)

        def save_apartment_with_tenants():
            # Сохранить квартиру и всех жильцов
            # Проверка данных квартиры
            house_idx = apt_entries['house_combo'].current()
            if house_idx < 0:
                self.show_toast("Выберите дом", toast_type="warning")
                return

            house_id = apt_entries['houses_data'][house_idx][0]
            apt_number = apt_entries['apt_number'].get().strip()

            if not apt_number:
                self.show_toast("Введите номер квартиры", toast_type="warning")
                return

            living_area = apt_entries['living_area'].get().strip()
            total_area = apt_entries['total_area'].get().strip()

            if not living_area or not total_area:
                self.show_toast("Введите площадь квартиры", toast_type="warning")
                return

            try:
                cursor = self.conn.cursor()

                # Вставляем квартиру
                cursor.execute("""
                    INSERT INTO apartments (house_id, apt_number, floor, living_area, total_area, 
                                          privatized, cold_water, hot_water, garbage_chute, elevator)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING apartment_id
                """, (
                    house_id,
                    apt_number,
                    apt_entries['floor'].get().strip() or None,
                    living_area,
                    total_area,
                    apt_entries['privatized'].get(),
                    apt_entries['cold_water'].get(),
                    apt_entries['hot_water'].get(),
                    apt_entries['garbage_chute'].get(),
                    apt_entries['elevator'].get()
                ))

                apartment_id = cursor.fetchone()[0]

                # Вставляем жильцов
                for tenant in tenants_list:
                    cursor.execute("""
                        INSERT INTO tenants (apartment_id, full_name, passport, birth_date, is_responsible, moved_in)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        apartment_id,
                        tenant['full_name'],
                        tenant['passport'],
                        tenant['birth_date'],
                        tenant['is_responsible'],
                        tenant['moved_in']
                    ))

                self.conn.commit()
                cursor.close()

                messagebox.showinfo("Успех",
                                    f"Квартира №{apt_number} создана (ID: {apartment_id})\n"
                                    f"Добавлено жильцов: {len(tenants_list)}")

                dialog.destroy()

                # Обновляем данные если открыта таблица квартир или жильцов
                if self.current_table in ('apartments', 'tenants'):
                    self.load_data()

            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Ошибка", f"Ошибка сохранения:\n{e}")

        ttk.Button(buttons_frame, text="Сохранить квартиру с жильцами",
                   command=save_apartment_with_tenants).pack(side=tk.LEFT, padx=20)
        ttk.Button(buttons_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT)

    def get_houses_list(self):
        # Получить список домов для выбора
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT house_id, street, house_number, building FROM houses ORDER BY street, house_number")
            houses = cursor.fetchall()
            cursor.close()
            return houses
        except:
            return []

    def report_rent(self):
        # Отчет: Квартплата по домам
        if not self.conn:
            self.show_toast("Нет подключения к БД", toast_type="warning")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Отчет: Квартплата")
        dialog.geometry("650x400")
        dialog.transient(self.root)
        dialog.grab_set()

        params_frame = ttk.LabelFrame(dialog, text="Параметры отчета", padding=10)
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        row = ttk.Frame(params_frame)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text="Дом:", width=20).pack(side=tk.LEFT)

        houses = self.get_houses_list()
        house_combo = ttk.Combobox(row, state="readonly", width=45)
        house_combo['values'] = ['Все дома'] + [f"{h[0]}: {h[1]} {h[2]}{' корп.' + h[3] if h[3] else ''}" for h in
                                                houses]
        house_combo.current(0)
        house_combo.pack(side=tk.LEFT)

        row2 = ttk.Frame(params_frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="Или фильтр по улице:", width=20).pack(side=tk.LEFT)
        street_entry = ttk.Entry(row2, width=30)
        street_entry.pack(side=tk.LEFT)
        ttk.Label(row2, text="(если дом не выбран)").pack(side=tk.LEFT, padx=5)

        sort_frame = ttk.LabelFrame(dialog, text="Сортировка", padding=10)
        sort_frame.pack(fill=tk.X, padx=10, pady=5)

        row = ttk.Frame(sort_frame)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text="Сортировать по:", width=20).pack(side=tk.LEFT)
        sort_field = ttk.Combobox(row, state="readonly", width=25)
        sort_field['values'] = ['Адрес', 'Номер квартиры', 'Общая площадь', 'Итого к оплате']
        sort_field.current(0)
        sort_field.pack(side=tk.LEFT)

        sort_dir = ttk.Combobox(row, state="readonly", width=15)
        sort_dir['values'] = ['По возрастанию', 'По убыванию']
        sort_dir.current(0)
        sort_dir.pack(side=tk.LEFT, padx=5)

        def generate_report():
            house_idx = house_combo.current()
            house_id = None if house_idx == 0 else houses[house_idx - 1][0]
            street_filter = street_entry.get().strip()
            sort_idx = sort_field.current()
            sort_order = "ASC" if sort_dir.current() == 0 else "DESC"

            sort_columns = ['h.street, h.house_number, a.apt_number', 'a.apt_number', 'a.total_area', 'total_rent']
            order_by = sort_columns[sort_idx]

            try:
                cursor = self.conn.cursor()

                query = """
                    SELECT 
                        h.street || ' ' || h.house_number || COALESCE(' корп.' || h.building, '') AS address,
                        a.apt_number,
                        a.total_area,
                        a.current_residents,
                        CASE WHEN a.cold_water THEN 'Да' ELSE 'Нет' END AS cold_water,
                        CASE WHEN a.hot_water THEN 'Да' ELSE 'Нет' END AS hot_water,
                        CASE WHEN a.elevator THEN 'Да' ELSE 'Нет' END AS elevator,
                        ROUND(a.total_area * 25.50, 2) AS rent_base,
                        ROUND(CASE WHEN a.cold_water THEN a.current_residents * 150.00 ELSE 0 END, 2) AS cold_water_cost,
                        ROUND(CASE WHEN a.hot_water THEN a.current_residents * 200.00 ELSE 0 END, 2) AS hot_water_cost,
                        ROUND(CASE WHEN a.elevator THEN a.total_area * 5.00 ELSE 0 END, 2) AS elevator_cost,
                        ROUND(
                            a.total_area * 25.50 + 
                            CASE WHEN a.cold_water THEN a.current_residents * 150.00 ELSE 0 END +
                            CASE WHEN a.hot_water THEN a.current_residents * 200.00 ELSE 0 END +
                            CASE WHEN a.elevator THEN a.total_area * 5.00 ELSE 0 END
                        , 2) AS total_rent
                    FROM apartments a
                    JOIN houses h ON a.house_id = h.house_id
                """

                params = []
                where_conditions = []

                if house_id:
                    where_conditions.append("h.house_id = %s")
                    params.append(house_id)
                elif street_filter:
                    where_conditions.append("h.street ILIKE %s")
                    params.append(f"%{street_filter}%")

                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)

                query += f" ORDER BY {order_by} {sort_order}"

                cursor.execute(query, params if params else None)
                rows = cursor.fetchall()

                # Итоги
                totals_query = """
                    SELECT 
                        COUNT(*) as cnt,
                        COALESCE(SUM(a.total_area), 0) as total_area,
                        COALESCE(SUM(
                            a.total_area * 25.50 + 
                            CASE WHEN a.cold_water THEN a.current_residents * 150.00 ELSE 0 END +
                            CASE WHEN a.hot_water THEN a.current_residents * 200.00 ELSE 0 END +
                            CASE WHEN a.elevator THEN a.total_area * 5.00 ELSE 0 END
                        ), 0) AS total_sum
                    FROM apartments a
                    JOIN houses h ON a.house_id = h.house_id
                """
                if where_conditions:
                    totals_query += " WHERE " + " AND ".join(where_conditions)

                cursor.execute(totals_query, params if params else None)
                totals = cursor.fetchone()
                cursor.close()

                dialog.destroy()
                self.show_report_window("Отчет: Квартплата",
                                        ['Адрес', 'Кв.', 'Площадь', 'Жильцов', 'Хол.вода', 'Гор.вода', 'Лифт',
                                         'Содерж.', 'Хол.вода₽', 'Гор.вода₽', 'Лифт₽', 'ИТОГО'],
                                        rows,
                                        f"Всего квартир: {totals[0]} | Общая площадь: {totals[1]:.2f} м² | ИТОГО К ОПЛАТЕ: {totals[2]:.2f} руб.")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка формирования отчета:\n{e}")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=20)
        ttk.Button(btn_frame, text="Сформировать отчет", command=generate_report).pack(side=tk.LEFT, padx=20)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT)

    def report_tenants_by_section(self):
        # Отчет: Жильцы по участкам (для избирательных списков)
        if not self.conn:
            self.show_toast("Нет подключения к БД", toast_type="warning")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Отчет: Жильцы по участкам")
        dialog.geometry("650x400")
        dialog.transient(self.root)
        dialog.grab_set()

        params_frame = ttk.LabelFrame(dialog, text="Параметры отчета", padding=10)
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        row = ttk.Frame(params_frame)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text="Участок:", width=20).pack(side=tk.LEFT)

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT section_id, name FROM sections ORDER BY name")
            sections = cursor.fetchall()
            cursor.close()
        except:
            sections = []

        section_combo = ttk.Combobox(row, state="readonly", width=30)
        section_combo['values'] = ['Все участки'] + [f"{s[0]}: {s[1]}" for s in sections]
        section_combo.current(0)
        section_combo.pack(side=tk.LEFT)

        adults_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="Только совершеннолетние (18+)", variable=adults_var).pack(anchor=tk.W,
                                                                                                      pady=5)

        active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="Только проживающие (не выселенные)", variable=active_var).pack(anchor=tk.W,
                                                                                                           pady=5)

        sort_frame = ttk.LabelFrame(dialog, text="Сортировка", padding=10)
        sort_frame.pack(fill=tk.X, padx=10, pady=5)

        row = ttk.Frame(sort_frame)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text="Сортировать по:", width=20).pack(side=tk.LEFT)
        sort_field = ttk.Combobox(row, state="readonly", width=25)
        sort_field['values'] = ['ФИО', 'Адрес', 'Дата рождения', 'Возраст']
        sort_field.current(0)
        sort_field.pack(side=tk.LEFT)

        sort_dir = ttk.Combobox(row, state="readonly", width=15)
        sort_dir['values'] = ['По возрастанию', 'По убыванию']
        sort_dir.current(0)
        sort_dir.pack(side=tk.LEFT, padx=5)

        def generate_report():
            section_idx = section_combo.current()
            section_id = None if section_idx == 0 else sections[section_idx - 1][0]
            only_adults = adults_var.get()
            only_active = active_var.get()
            sort_idx = sort_field.current()
            sort_order = "ASC" if sort_dir.current() == 0 else "DESC"

            sort_columns = ['t.full_name', 'h.street, h.house_number', 't.birth_date', 'age']
            order_by = sort_columns[sort_idx]

            try:
                cursor = self.conn.cursor()

                query = """
                    SELECT 
                        s.name AS section_name,
                        t.full_name,
                        h.street || ' ' || h.house_number || COALESCE(' корп.' || h.building, '') || ', кв.' || a.apt_number AS address,
                        t.birth_date,
                        CASE WHEN t.birth_date IS NOT NULL 
                             THEN EXTRACT(YEAR FROM AGE(t.birth_date))::int 
                             ELSE NULL END AS age,
                        t.passport
                    FROM tenants t
                    JOIN apartments a ON t.apartment_id = a.apartment_id
                    JOIN houses h ON a.house_id = h.house_id
                    JOIN sections s ON h.section_id = s.section_id
                    WHERE 1=1
                """

                params = []
                if section_id:
                    query += " AND s.section_id = %s"
                    params.append(section_id)
                if only_adults:
                    query += " AND t.birth_date IS NOT NULL AND t.birth_date <= CURRENT_DATE - INTERVAL '18 years'"
                if only_active:
                    query += " AND t.moved_out IS NULL"

                query += f" ORDER BY s.name, {order_by} {sort_order}"

                cursor.execute(query, params if params else None)
                rows = cursor.fetchall()

                # Итоги по участкам
                cursor.execute("""
                    SELECT s.name, COUNT(*) 
                    FROM tenants t
                    JOIN apartments a ON t.apartment_id = a.apartment_id
                    JOIN houses h ON a.house_id = h.house_id
                    JOIN sections s ON h.section_id = s.section_id
                    WHERE 1=1
                """ + (" AND s.section_id = %s" if section_id else "") +
                               (
                                   " AND t.birth_date IS NOT NULL AND t.birth_date <= CURRENT_DATE - INTERVAL '18 years'" if only_adults else "") +
                               (" AND t.moved_out IS NULL" if only_active else "") +
                               " GROUP BY s.name ORDER BY s.name",
                               params if params else None)
                group_totals = cursor.fetchall()
                cursor.close()

                dialog.destroy()

                totals_str = " | ".join([f"{g[0]}: {g[1]} чел." for g in group_totals])
                total_count = sum(g[1] for g in group_totals)

                self.show_report_window("Отчет: Жильцы по участкам",
                                        ['Участок', 'ФИО', 'Адрес', 'Дата рожд.', 'Возраст', 'Паспорт'],
                                        rows,
                                        f"ИТОГО: {total_count} чел. | {totals_str}")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка формирования отчета:\n{e}")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=20)
        ttk.Button(btn_frame, text="Сформировать отчет", command=generate_report).pack(side=tk.LEFT, padx=20)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT)

    def report_housing_stats(self):
        # Отчет: Статистика по жилфонду
        if not self.conn:
            self.show_toast("Нет подключения к БД", toast_type="warning")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Отчет: Статистика жилфонда")
        dialog.geometry("650x380")
        dialog.transient(self.root)
        dialog.grab_set()

        params_frame = ttk.LabelFrame(dialog, text="Параметры отчета", padding=10)
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        row = ttk.Frame(params_frame)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text="Группировать по:", width=20).pack(side=tk.LEFT)
        group_combo = ttk.Combobox(row, state="readonly", width=25)
        group_combo['values'] = ['Службам', 'Отделам', 'Участкам']
        group_combo.current(0)
        group_combo.pack(side=tk.LEFT)

        row = ttk.Frame(params_frame)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text="Год постройки от:", width=20).pack(side=tk.LEFT)
        year_from = ttk.Entry(row, width=10)
        year_from.pack(side=tk.LEFT)
        ttk.Label(row, text="до:").pack(side=tk.LEFT, padx=5)
        year_to = ttk.Entry(row, width=10)
        year_to.pack(side=tk.LEFT)

        sort_frame = ttk.LabelFrame(dialog, text="Сортировка", padding=10)
        sort_frame.pack(fill=tk.X, padx=10, pady=5)

        row = ttk.Frame(sort_frame)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text="Сортировать по:", width=20).pack(side=tk.LEFT)
        sort_field = ttk.Combobox(row, state="readonly", width=25)
        sort_field['values'] = ['Название', 'Кол-во домов', 'Кол-во квартир', 'Кол-во жильцов']
        sort_field.current(0)
        sort_field.pack(side=tk.LEFT)

        sort_dir = ttk.Combobox(row, state="readonly", width=15)
        sort_dir['values'] = ['По возрастанию', 'По убыванию']
        sort_dir.current(0)
        sort_dir.pack(side=tk.LEFT, padx=5)

        def generate_report():
            group_idx = group_combo.current()
            year_from_val = year_from.get().strip()
            year_to_val = year_to.get().strip()
            sort_idx = sort_field.current()
            sort_order = "ASC" if sort_dir.current() == 0 else "DESC"

            group_tables = [
                ('sv.name', 'services sv', 'h.service_id = sv.service_id'),
                ('d.name', 'departments d', 'h.department_id = d.department_id'),
                ('sec.name', 'sections sec', 'h.section_id = sec.section_id')
            ]
            group_col, group_table, group_join = group_tables[group_idx]

            sort_columns = [group_col, 'houses_count', 'apartments_count', 'residents_count']
            order_by = sort_columns[sort_idx]

            try:
                cursor = self.conn.cursor()

                where_conditions = []
                params = []

                if year_from_val:
                    where_conditions.append("h.year_built >= %s")
                    params.append(int(year_from_val))
                if year_to_val:
                    where_conditions.append("h.year_built <= %s")
                    params.append(int(year_to_val))

                where_clause = (" WHERE " + " AND ".join(where_conditions)) if where_conditions else ""

                query = f"""
                    SELECT 
                        {group_col} AS group_name,
                        COUNT(DISTINCT h.house_id) AS houses_count,
                        COUNT(DISTINCT a.apartment_id) AS apartments_count,
                        COALESCE(SUM(a.current_residents), 0)::int AS residents_count,
                        COALESCE(ROUND(AVG(a.total_area), 2), 0) AS avg_area,
                        COALESCE(ROUND(SUM(a.total_area), 2), 0) AS total_area
                    FROM houses h
                    JOIN {group_table} ON {group_join}
                    LEFT JOIN apartments a ON h.house_id = a.house_id
                    {where_clause}
                    GROUP BY {group_col} 
                    ORDER BY {order_by} {sort_order}
                """

                cursor.execute(query, params if params else None)
                rows = cursor.fetchall()

                # Общие итоги
                totals_query = f"""
                    SELECT 
                        COUNT(DISTINCT h.house_id),
                        COUNT(DISTINCT a.apartment_id),
                        COALESCE(SUM(a.current_residents), 0)::int,
                        COALESCE(ROUND(SUM(a.total_area), 2), 0)
                    FROM houses h
                    LEFT JOIN apartments a ON h.house_id = a.house_id
                    {where_clause}
                """

                cursor.execute(totals_query, params if params else None)
                totals = cursor.fetchone()
                cursor.close()

                group_names = ['Служба', 'Отдел', 'Участок']
                group_text = group_combo.get().lower()

                dialog.destroy()

                self.show_report_window(f"Отчет: Статистика жилфонда (по {group_text})",
                                        [group_names[group_idx], 'Домов', 'Квартир', 'Жильцов', 'Ср. площадь',
                                         'Общ. площадь'],
                                        rows,
                                        f"ИТОГО: домов: {totals[0]} | квартир: {totals[1]} | жильцов: {totals[2]} | площадь: {totals[3]} м²")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка формирования отчета:\n{e}")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=20)
        ttk.Button(btn_frame, text="Сформировать отчет", command=generate_report).pack(side=tk.LEFT, padx=20)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT)

    def show_report_window(self, title, columns, data, totals_text):
        # Показать окно с отчетом
        report_win = tk.Toplevel(self.root)
        report_win.title(title)
        report_win.geometry("1000x600")
        report_win.state('zoomed')

        header = ttk.Label(report_win, text=title, font=('Segoe UI', 14, 'bold'))
        header.pack(pady=10)

        tree_frame = ttk.Frame(report_win)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, minwidth=50)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        for row in data:
            display_row = [str(v) if v is not None else '' for v in row]
            tree.insert('', tk.END, values=display_row)

        # Итоги
        totals_frame = ttk.Frame(report_win)
        totals_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(totals_frame, text=totals_text, font=('Segoe UI', 11, 'bold'),
                  foreground='#0066cc').pack(side=tk.LEFT)

        ttk.Button(totals_frame, text="Закрыть", command=report_win.destroy).pack(side=tk.RIGHT, padx=10)

        self.show_toast(f"Отчет сформирован: {len(data)} записей", toast_type="success")


if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()
