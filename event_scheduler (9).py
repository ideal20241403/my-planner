import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import re
import jdatetime

class EventSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("برنامه‌ریز رویداد")
        self.root.geometry("1200x800")
        
        # اتصال به پایگاه داده
        self.conn = sqlite3.connect("events.db")
        self.create_table()
        
        # لیست دسته‌بندی رویدادها
        self.event_types = ["امتحان", "تمرین", "کلاس", "جلسه", "تحقیق", "ارائه", "سایر"]
        
        # روزهای هفته
        self.weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
        
        # تاریخ و زمان فعلی سیستم
        self.update_current_datetime()
        
        # حالت نمایش: 0=نزدیک‌ترین، 1=آینده، 2=همه، 3=جدول هفتگی
        self.display_mode = 0
        
        # رابط کاربری
        self.create_gui()
        
        # به‌روزرسانی تاریخ و ساعت
        self.update_current_time()
        
        # نمایش اولیه: نزدیک‌ترین رویداد
        self.load_events()
        self.load_future_tasks()
        self.load_weekly_schedule()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL,
                date TEXT,
                time TEXT,
                description TEXT,
                is_recurring INTEGER DEFAULT 0,
                recurring_day INTEGER DEFAULT -1,
                end_date TEXT
            )
        ''')
        self.conn.commit()
    
    def update_current_datetime(self):
        self.current_datetime = datetime.now()
        self.current_jalali = jdatetime.datetime.fromgregorian(date=self.current_datetime)
    
    def get_weekday_name(self, jalali_date_str):
        year, month, day = map(int, jalali_date_str.split("-"))
        jalali_date = jdatetime.date(year, month, day)
        weekday_num = jalali_date.weekday()
        return self.weekdays[weekday_num]
    
    def get_jalali_weekday_num(self, jalali_date_str):
        year, month, day = map(int, jalali_date_str.split("-"))
        jalali_date = jdatetime.date(year, month, day)
        return jalali_date.weekday()
    
    def validate_jalali_date(self, date_str):
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, date_str):
            return False
        try:
            year, month, day = map(int, date_str.split("-"))
            jdatetime.date(year, month, day)
            return True
        except ValueError:
            return False
    
    def validate_time(self, time_str):
        if not time_str:
            return True
        pattern = r"^\d{2}:\d{2}$"
        if not re.match(pattern, time_str):
            return False
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    def jalali_to_gregorian(self, jalali_date):
        year, month, day = map(int, jalali_date.split("-"))
        gregorian_date = jdatetime.date(year, month, day).togregorian()
        return gregorian_date.strftime("%Y-%m-%d")
    
    def gregorian_to_jalali(self, gregorian_date):
        gregorian = datetime.strptime(gregorian_date, "%Y-%m-%d")
        jalali = jdatetime.date.fromgregorian(date=gregorian)
        return jalali.strftime("%Y-%m-%d")
    
    def create_gui(self):
        # نمایش تاریخ و ساعت فعلی
        self.current_time_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.current_time_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # فریم برای افزودن رویداد
        add_frame = ttk.LabelFrame(self.root, text="افزودن رویداد جدید")
        add_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # گزینه تکراری
        self.recurring_var = tk.BooleanVar()
        ttk.Checkbutton(add_frame, text="رویداد تکراری هفتگی", variable=self.recurring_var).grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Label(add_frame, text="عنوان:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.title_entry = ttk.Entry(add_frame, width=25)
        self.title_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="نوع رویداد:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.event_type_combo = ttk.Combobox(add_frame, values=self.event_types, width=23)
        self.event_type_combo.grid(row=2, column=1, padx=5, pady=5)
        self.event_type_combo.set("سایر")
        
        # فریم برای تاریخ
        date_frame = ttk.Frame(add_frame)
        date_frame.grid(row=3, column=0, columnspan=2, pady=5)
        
        ttk.Label(date_frame, text="تاریخ شمسی (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        self.date_entry = ttk.Entry(date_frame, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        
        # روز تکراری
        self.recurring_day_combo = ttk.Combobox(date_frame, values=self.weekdays, width=10, state="disabled")
        self.recurring_day_combo.pack(side=tk.LEFT, padx=5)
        self.recurring_day_combo.set("شنبه")
        
        # تاریخ پایان
        ttk.Label(date_frame, text="تا تاریخ (اختیاری):").pack(side=tk.LEFT, padx=5)
        self.end_date_entry = ttk.Entry(date_frame, width=15)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(add_frame, text="ساعت (HH:MM، اختیاری):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.time_entry = ttk.Entry(add_frame, width=25)
        self.time_entry.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="توضیحات:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = ttk.Entry(add_frame, width=25)
        self.desc_entry.grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Button(add_frame, text="افزودن رویداد", command=self.add_event).grid(row=6, column=0, columnspan=2, pady=10)
        
        # دکمه‌های تغییر حالت نمایش
        mode_frame = ttk.Frame(self.root)
        mode_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Button(mode_frame, text="نمایش نزدیک‌ترین رویداد", command=lambda: self.set_display_mode(0)).pack(side=tk.LEFT, padx=5)
        ttk.Button(mode_frame, text="نمایش رویدادهای آینده", command=lambda: self.set_display_mode(1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(mode_frame, text="نمایش همه رویدادها", command=lambda: self.set_display_mode(2)).pack(side=tk.LEFT, padx=5)
        ttk.Button(mode_frame, text="جدول برنامه هفتگی", command=lambda: self.set_display_mode(3)).pack(side=tk.LEFT, padx=5)
        
        # فریم برای نمایش رویدادها
        self.event_frame = ttk.LabelFrame(self.root, text="لیست رویدادها / نزدیک‌ترین رویداد")
        self.event_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        
        # لیبل برای نمایش نزدیک‌ترین رویداد
        self.nearest_label = ttk.Label(self.event_frame, text="", font=("Arial", 10), justify=tk.LEFT)
        self.nearest_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Treeview برای لیست رویدادها
        self.tree = ttk.Treeview(self.event_frame, columns=("ID", "Title", "Type", "Date", "Time", "Description"), show="headings")
        self.tree.heading("ID", text="شناسه")
        self.tree.heading("Title", text="عنوان")
        self.tree.heading("Type", text="نوع")
        self.tree.heading("Date", text="تاریخ شمسی (روز)")
        self.tree.heading("Time", text="ساعت")
        self.tree.heading("Description", text="توضیحات")
        self.tree.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # تنظیم عرض ستون‌ها
        self.tree.column("ID", width=50)
        self.tree.column("Title", width=150)
        self.tree.column("Type", width=80)
        self.tree.column("Date", width=120)
        self.tree.column("Time", width=80)
        self.tree.column("Description", width=200)
        
        # اسکرول‌بار
        scrollbar = ttk.Scrollbar(self.event_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # دکمه‌های ویرایش و حذف
        button_frame = ttk.Frame(self.event_frame)
        button_frame.grid(row=2, column=0, pady=5)
        ttk.Button(button_frame, text="ویرایش رویداد", command=self.edit_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="حذف رویداد", command=self.delete_event).pack(side=tk.LEFT, padx=5)
        
        # بخش کارهای آینده
        tasks_frame = ttk.LabelFrame(self.root, text="کارهای آینده (بدون زمان مشخص)")
        tasks_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        
        self.tasks_tree = ttk.Treeview(tasks_frame, columns=("ID", "Title", "Type", "Date", "Description"), show="headings")
        self.tasks_tree.heading("ID", text="شناسه")
        self.tasks_tree.heading("Title", text="عنوان")
        self.tasks_tree.heading("Type", text="نوع")
        self.tasks_tree.heading("Date", text="تاریخ شمسی (روز)")
        self.tasks_tree.heading("Description", text="توضیحات")
        self.tasks_tree.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.tasks_tree.column("ID", width=50)
        self.tasks_tree.column("Title", width=150)
        self.tasks_tree.column("Type", width=80)
        self.tasks_tree.column("Date", width=120)
        self.tasks_tree.column("Description", width=200)
        
        tasks_scrollbar = ttk.Scrollbar(tasks_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        tasks_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tasks_tree.configure(yscrollcommand=tasks_scrollbar.set)
        
        # جدول برنامه هفتگی
        self.schedule_frame = ttk.LabelFrame(self.root, text="جدول برنامه هفتگی")
        self.schedule_frame.grid(row=3, column=1, rowspan=3, padx=10, pady=10, sticky="nsew")
        
        # Treeview برای جدول هفتگی
        self.schedule_tree = ttk.Treeview(self.schedule_frame, columns=self.weekdays, show="headings")
        for day in self.weekdays:
            self.schedule_tree.heading(day, text=day)
            self.schedule_tree.column(day, width=150)
        self.schedule_tree.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        schedule_scrollbar = ttk.Scrollbar(self.schedule_frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        schedule_scrollbar.grid(row=0, column=1, sticky="ns")
        self.schedule_tree.configure(yscrollcommand=schedule_scrollbar.set)
        
        self.schedule_frame.columnconfigure(0, weight=1)
        self.schedule_frame.rowconfigure(0, weight=1)
        
        # فریم جستجو
        search_frame = ttk.LabelFrame(self.root, text="جستجوی نزدیک‌ترین رویداد")
        search_frame.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        ttk.Label(search_frame, text="تاریخ شمسی (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
        self.search_date_entry = ttk.Entry(search_frame, width=30)
        self.search_date_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(search_frame, text="جستجو", command=self.find_nearest_event).grid(row=1, column=0, columnspan=2, pady=5)
        
        # تنظیم grid weights
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(3, weight=1)
        self.root.rowconfigure(4, weight=1)
        self.event_frame.columnconfigure(0, weight=1)
        self.event_frame.rowconfigure(1, weight=1)
        tasks_frame.columnconfigure(0, weight=1)
        tasks_frame.rowconfigure(0, weight=1)
        add_frame.columnconfigure(1, weight=1)
    
    def update_current_time(self):
        self.update_current_datetime()
        current_time_text = f"تاریخ و ساعت فعلی: {self.current_jalali.strftime('%Y/%m/%d %H:%M:%S')} - {self.get_weekday_name(self.current_jalali.strftime('%Y-%m-%d'))}"
        self.current_time_label.config(text=current_time_text)
        self.root.after(1000, self.update_current_time)
    
    def set_display_mode(self, mode):
        self.display_mode = mode
        self.load_events()
        if mode == 3:
            self.load_weekly_schedule()
    
    def toggle_recurring(self):
        if self.recurring_var.get():
            self.date_entry.config(state="disabled")
            self.recurring_day_combo.config(state="readonly")
            self.end_date_entry.config(state="normal")
        else:
            self.date_entry.config(state="normal")
            self.recurring_day_combo.config(state="disabled")
            self.end_date_entry.config(state="disabled")
    
    def add_event(self):
        title = self.title_entry.get().strip()
        event_type = self.event_type_combo.get()
        jalali_date = self.date_entry.get().strip()
        time = self.time_entry.get().strip()
        description = self.desc_entry.get().strip()
        is_recurring = self.recurring_var.get()
        recurring_day_str = self.recurring_day_combo.get()
        end_jalali_date = self.end_date_entry.get().strip()
        
        if not title or not event_type:
            messagebox.showerror("خطا", "لطفاً عنوان و نوع را پر کنید!")
            return
        
        if is_recurring:
            if not recurring_day_str or recurring_day_str == "":
                messagebox.showerror("خطا", "لطفاً روز تکرار را انتخاب کنید!")
                return
            recurring_day = self.weekdays.index(recurring_day_str)
            if end_jalali_date and not self.validate_jalali_date(end_jalali_date):
                messagebox.showerror("خطا", "فرمت تاریخ پایان نامعتبر است!")
                return
            gregorian_end_date = self.jalali_to_gregorian(end_jalali_date) if end_jalali_date else None
            gregorian_date = None  # برای تکراری، تاریخ شروع لازم نیست
        else:
            if not jalali_date or not self.validate_jalali_date(jalali_date):
                messagebox.showerror("خطا", "فرمت تاریخ نامعتبر است!")
                return
            gregorian_date = self.jalali_to_gregorian(jalali_date)
            recurring_day = -1
            gregorian_end_date = None
        
        if time and not self.validate_time(time):
            messagebox.showerror("خطا", "فرمت ساعت نامعتبر است!")
            return
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO events (title, event_type, date, time, description, is_recurring, recurring_day, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, event_type, gregorian_date, time if time else None, description, int(is_recurring), recurring_day, gregorian_end_date))
        self.conn.commit()
        
        self.clear_entries()
        self.load_events()
        self.load_future_tasks()
        self.load_weekly_schedule()
        messagebox.showinfo("موفقیت", "رویداد با موفقیت اضافه شد!")
    
    def clear_entries(self):
        self.title_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.event_type_combo.set("سایر")
        self.recurring_var.set(False)
        self.date_entry.config(state="normal")
        self.recurring_day_combo.config(state="disabled")
        self.end_date_entry.config(state="disabled")
    
    def load_events(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.nearest_label.config(text="")
        
        cursor = self.conn.cursor()
        events = []
        
        if self.display_mode == 0:  # نزدیک‌ترین
            nearest_event = self.get_nearest_event()
            if nearest_event:
                self.display_nearest_event(nearest_event)
            else:
                self.nearest_label.config(text="هیچ رویدادی در آینده یافت نشد!")
            return
        
        elif self.display_mode == 1:  # آینده
            # رویدادهای یک‌باره
            cursor.execute('''
                SELECT * FROM events 
                WHERE is_recurring = 0 AND date >= ? OR (date = ? AND (time >= ? OR time IS NULL))
                ORDER BY date, time
            ''', (self.current_datetime.strftime("%Y-%m-%d"),
                  self.current_datetime.strftime("%Y-%m-%d"),
                  self.current_datetime.strftime("%H:%M")))
            single_events = cursor.fetchall()
            
            # رویدادهای تکراری در آینده
            recurring_events = self.get_future_recurring_events()
            
            events = single_events + recurring_events
        elif self.display_mode == 2:  # همه
            cursor.execute('''
                SELECT * FROM events ORDER BY 
                CASE WHEN is_recurring = 1 THEN 0 ELSE 1 END, date, time
            ''')
            all_events = cursor.fetchall()
            
            # برای تکراری‌ها، فقط الگو نمایش بده
            events = all_events
        elif self.display_mode == 3:  # جدول هفتگی
            return  # جداگانه لود می‌شود
        
        for row in events:
            if row[6] == 1:  # تکراری
                jalali_date = f"هر {self.weekdays[row[7]]}"
                date_with_day = f"تکراری ({self.weekdays[row[7]]})"
            else:
                jalali_date = self.gregorian_to_jalali(row[3]) if row[3] else ""
                date_with_day = f"{jalali_date} ({self.get_weekday_name(jalali_date)})" if jalali_date else ""
            display_time = row[4] if row[4] else "بدون زمان"
            self.tree.insert("", tk.END, values=(row[0], row[1], row[2], date_with_day, display_time, row[5] or ""))
    
    def get_nearest_event(self):
        cursor = self.conn.cursor()
        # یک‌باره
        cursor.execute('''
            SELECT * FROM events 
            WHERE is_recurring = 0 AND (date > ? OR (date = ? AND time > ?))
            ORDER BY date, time LIMIT 1
        ''', (self.current_datetime.strftime("%Y-%m-%d"),
              self.current_datetime.strftime("%Y-%m-%d"),
              self.current_datetime.strftime("%H:%M")))
        single = cursor.fetchone()
        
        # تکراری
        cursor.execute('''
            SELECT * FROM events 
            WHERE is_recurring = 1 AND (end_date IS NULL OR end_date >= ?) 
            AND recurring_day = ? 
            ORDER BY recurring_day LIMIT 1
        ''', (self.current_datetime.strftime("%Y-%m-%d"),
              self.get_jalali_weekday_num(self.current_jalali.strftime("%Y-%m-%d"))))
        recurring = cursor.fetchone()
        
        # مقایسه و انتخاب نزدیک‌ترین
        candidates = [single] if single else []
        if recurring:
            candidates.append(recurring)
        if not candidates:
            return None
        # ساده: اولین را برگردان
        return candidates[0]
    
    def display_nearest_event(self, event):
        if not event:
            return
        if event[6] == 1:  # تکراری
            day_name = self.weekdays[event[7]]
            date_text = f"هر {day_name}"
            time_text = f"{event[4]} " if event[4] else "بدون زمان "
        else:
            jalali_date = self.gregorian_to_jalali(event[3])
            date_with_day = f"{jalali_date} ({self.get_weekday_name(jalali_date)})"
            time_text = f"{event[4]} " if event[4] else "بدون زمان "
            date_text = date_with_day
        self.nearest_label.config(text=f"نزدیک‌ترین رویداد:\nعنوان: {event[1]}\nنوع: {event[2]}\nتاریخ: {date_text}\nساعت: {time_text}\nتوضیحات: {event[5] or 'بدون توضیحات'}")
    
    def get_future_recurring_events(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM events 
            WHERE is_recurring = 1 AND (end_date IS NULL OR end_date >= ?)
            ORDER BY recurring_day
        ''', (self.current_datetime.strftime("%Y-%m-%d"),))
        return cursor.fetchall()
    
    def load_future_tasks(self):
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM events 
            WHERE time IS NULL AND is_recurring = 0 AND date >= ?
            ORDER BY date
        ''', (self.current_datetime.strftime("%Y-%m-%d"),))
        tasks = cursor.fetchall()
        
        for row in tasks:
            jalali_date = self.gregorian_to_jalali(row[3])
            date_with_day = f"{jalali_date} ({self.get_weekday_name(jalali_date)})"
            self.tasks_tree.insert("", tk.END, values=(row[0], row[1], row[2], date_with_day, row[5] or ""))
    
    def load_weekly_schedule(self):
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # پاک کردن تگ‌ها
        for tag in self.schedule_tree.get_tags():
            self.schedule_tree.tag_configure(tag, foreground='black')
        
        # رویدادهای تکراری (الگو هفتگی)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM events 
            WHERE is_recurring = 1 AND (end_date IS NULL OR end_date >= ?)
        ''', (self.current_datetime.strftime("%Y-%m-%d"),))
        recurring_events = cursor.fetchall()
        
        # رویدادهای یک‌باره در هفته جاری
        current_greg_date = self.current_datetime.strftime("%Y-%m-%d")
        start_of_week = (self.current_datetime - timedelta(days=self.current_datetime.weekday())).strftime("%Y-%m-%d")
        end_of_week = (self.current_datetime + timedelta(days=6 - self.current_datetime.weekday())).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT * FROM events 
            WHERE is_recurring = 0 AND date >= ? AND date <= ?
        ''', (start_of_week, end_of_week))
        single_events_this_week = cursor.fetchall()
        
        # برای هر روز هفته
        for day_idx, day_name in enumerate(self.weekdays):
            day_events = []
            
            # رویدادهای تکراری برای این روز
            for event in recurring_events:
                if event[7] == day_idx:  # recurring_day
                    event_text = f"{event[1]} ({event[2]}) - {event[4] or 'بدون زمان'}"
                    day_events.append((event_text, 'recurring'))  # آبی
            
            # رویدادهای یک‌باره برای این روز (محاسبه روز هفته)
            for event in single_events_this_week:
                event_greg_date = event[3]
                event_jalali = self.gregorian_to_jalali(event_greg_date)
                event_weekday = self.get_jalali_weekday_num(event_jalali)
                if event_weekday == day_idx:
                    event_text = f"{event[1]} ({event[2]}) - {event[4] or 'بدون زمان'}"
                    day_events.append((event_text, 'single'))  # قرمز
            
            # اضافه به جدول
            if day_events:
                # چند سطر اگر چند رویداد
                for i, (text, event_type) in enumerate(day_events):
                    if i == 0:
                        self.schedule_tree.insert("", tk.END, values=('',) * day_idx + (text,) + ('',) * (6 - day_idx))
                        iid = self.schedule_tree.get_children()[-1]
                        if event_type == 'single':
                            self.schedule_tree.set(iid, day_name, text)
                            self.schedule_tree.item(iid, tags=('single',))
                        else:
                            self.schedule_tree.item(iid, tags=('recurring',))
                    else:
                        self.schedule_tree.insert("", tk.END, values=('',) * day_idx + (text,) + ('',) * (6 - day_idx))
                        iid = self.schedule_tree.get_children()[-1]
                        if event_type == 'single':
                            self.schedule_tree.item(iid, tags=('single',))
                        else:
                            self.schedule_tree.item(iid, tags=('recurring',))
            else:
                self.schedule_tree.insert("", tk.END, values=('',) * day_idx + ('بدون رویداد',) + ('',) * (6 - day_idx))
        
        # رنگ‌بندی
        self.schedule_tree.tag_configure('recurring', foreground='blue', font=('Arial', 9, 'bold'))
        self.schedule_tree.tag_configure('single', foreground='red', font=('Arial', 9, 'bold'))
    
    def edit_event(self):
        # مشابه قبل، اما با فیلدهای جدید
        selected_item = self.tree.selection()
        if not selected_item and self.display_mode != 0:
            messagebox.showerror("خطا", "لطفاً یک رویداد را انتخاب کنید!")
            return
        
        if self.display_mode == 0:
            nearest = self.get_nearest_event()
            if not nearest:
                return
            event_id = nearest[0]
            item_values = self.get_item_values(nearest)
        else:
            item = self.tree.item(selected_item)
            event_id = item["values"][0]
            item_values = item["values"]
        
        self.open_edit_window(event_id, item_values)
    
    def get_item_values(self, row):
        if row[6] == 1:
            date_with_day = f"تکراری ({self.weekdays[row[7]]})"
            time_text = row[4] if row[4] else "بدون زمان"
        else:
            jalali_date = self.gregorian_to_jalali(row[3]) if row[3] else ""
            date_with_day = f"{jalali_date} ({self.get_weekday_name(jalali_date)})" if jalali_date else ""
            time_text = row[4] if row[4] else "بدون زمان"
        return (row[0], row[1], row[2], date_with_day, time_text, row[5] or "")
    
    def open_edit_window(self, event_id, item_values):
        # بارگیری رویداد از دیتابیس
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        event = cursor.fetchone()
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title("ویرایش رویداد")
        edit_window.geometry("450x450")
        
        recurring_var = tk.BooleanVar(value=bool(event[6]))
        
        ttk.Checkbutton(edit_window, text="رویداد تکراری هفتگی", variable=recurring_var).grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Label(edit_window, text="عنوان:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        title_entry = ttk.Entry(edit_window, width=30)
        title_entry.grid(row=1, column=1, padx=5, pady=5)
        title_entry.insert(0, event[1])
        
        ttk.Label(edit_window, text="نوع رویداد:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        event_type_combo = ttk.Combobox(edit_window, values=self.event_types, width=28)
        event_type_combo.grid(row=2, column=1, padx=5, pady=5)
        event_type_combo.set(event[2])
        
        # فریم تاریخ
        date_frame = ttk.Frame(edit_window)
        date_frame.grid(row=3, column=0, columnspan=2, pady=5)
        
        ttk.Label(date_frame, text="تاریخ شمسی (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        date_entry = ttk.Entry(date_frame, width=15)
        date_entry.pack(side=tk.LEFT, padx=5)
        if not event[6]:
            date_entry.insert(0, self.gregorian_to_jalali(event[3]) if event[3] else "")
        
        recurring_day_combo = ttk.Combobox(date_frame, values=self.weekdays, width=10, state="readonly")
        recurring_day_combo.pack(side=tk.LEFT, padx=5)
        if event[6]:
            recurring_day_combo.set(self.weekdays[event[7]])
            recurring_day_combo.config(state="readonly")
        
        ttk.Label(date_frame, text="تا تاریخ (اختیاری):").pack(side=tk.LEFT, padx=5)
        end_date_entry = ttk.Entry(date_frame, width=15)
        end_date_entry.pack(side=tk.LEFT, padx=5)
        if event[6] and event[8]:
            end_date_entry.insert(0, self.gregorian_to_jalali(event[8]))
        
        def toggle_recurring_edit():
            if recurring_var.get():
                date_entry.config(state="disabled")
                recurring_day_combo.config(state="readonly")
                end_date_entry.config(state="normal")
            else:
                date_entry.config(state="normal")
                recurring_day_combo.config(state="disabled")
                end_date_entry.config(state="disabled")
        
        recurring_var.trace('w', lambda *args: toggle_recurring_edit())
        toggle_recurring_edit()
        
        ttk.Label(edit_window, text="ساعت (HH:MM، اختیاری):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        time_entry = ttk.Entry(edit_window, width=30)
        time_entry.grid(row=4, column=1, padx=5, pady=5)
        time_entry.insert(0, event[4] or "")
        
        ttk.Label(edit_window, text="توضیحات:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        desc_entry = ttk.Entry(edit_window, width=30)
        desc_entry.grid(row=5, column=1, padx=5, pady=5)
        desc_entry.insert(0, event[5] or "")
        
        def save_changes():
            title = title_entry.get().strip()
            event_type = event_type_combo.get()
            jalali_date = date_entry.get().strip()
            time = time_entry.get().strip()
            description = desc_entry.get().strip()
            is_recurring = recurring_var.get()
            
            if not title or not event_type:
                messagebox.showerror("خطا", "عنوان و نوع را پر کنید!")
                return
            
            if is_recurring:
                recurring_day_str = recurring_day_combo.get()
                if not recurring_day_str:
                    messagebox.showerror("خطا", "روز تکرار را انتخاب کنید!")
                    return
                recurring_day = self.weekdays.index(recurring_day_str)
                end_jalali = end_date_entry.get().strip()
                if end_jalali and not self.validate_jalali_date(end_jalali):
                    messagebox.showerror("خطا", "فرمت تاریخ پایان نامعتبر!")
                    return
                greg_end = self.jalali_to_gregorian(end_jalali) if end_jalali else None
                greg_date = None
            else:
                if not jalali_date or not self.validate_jalali_date(jalali_date):
                    messagebox.showerror("خطا", "فرمت تاریخ نامعتبر!")
                    return
                greg_date = self.jalali_to_gregorian(jalali_date)
                recurring_day = -1
                greg_end = None
            
            if time and not self.validate_time(time):
                messagebox.showerror("خطا", "فرمت ساعت نامعتبر!")
                return
            
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE events 
                SET title = ?, event_type = ?, date = ?, time = ?, description = ?, 
                    is_recurring = ?, recurring_day = ?, end_date = ?
                WHERE id = ?
            ''', (title, event_type, greg_date, time if time else None, description, 
                  int(is_recurring), recurring_day, greg_end, event_id))
            self.conn.commit()
            
            self.load_events()
            self.load_future_tasks()
            self.load_weekly_schedule()
            edit_window.destroy()
            messagebox.showinfo("موفقیت", "رویداد ویرایش شد!")
        
        ttk.Button(edit_window, text="ذخیره تغییرات", command=save_changes).grid(row=6, column=0, columnspan=2, pady=10)
    
    def delete_event(self):
        selected_item = self.tree.selection()
        if not selected_item and self.display_mode != 0:
            messagebox.showerror("خطا", "لطفاً یک رویداد را انتخاب کنید!")
            return
        
        if self.display_mode == 0:
            nearest = self.get_nearest_event()
            if not nearest:
                return
            event_id = nearest[0]
        else:
            item = self.tree.item(selected_item)
            event_id = item["values"][0]
        
        if messagebox.askyesno("تأیید", "آیا مطمئن هستید؟"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            self.conn.commit()
            self.load_events()
            self.load_future_tasks()
            self.load_weekly_schedule()
            messagebox.showinfo("موفقیت", "رویداد حذف شد!")
    
    def find_nearest_event(self):
        jalali_search_date = self.search_date_entry.get().strip()
        if not self.validate_jalali_date(jalali_search_date):
            messagebox.showerror("خطا", "فرمت تاریخ شمسی نامعتبر!")
            return
        
        gregorian_search_date = self.jalali_to_gregorian(jalali_search_date)
        search_datetime = datetime.strptime(gregorian_search_date, "%Y-%m-%d")
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM events 
            WHERE is_recurring = 0 AND date >= ? 
            ORDER BY date, time LIMIT 1
        ''', (search_datetime.strftime("%Y-%m-%d"),))
        nearest = cursor.fetchone()
        
        if nearest:
            jalali_date = self.gregorian_to_jalali(nearest[3])
            date_with_day = f"{jalali_date} ({self.get_weekday_name(jalali_date)})"
            time_text = f"{nearest[4]} " if nearest[4] else "بدون زمان "
            messagebox.showinfo("نزدیک‌ترین رویداد", 
                               f"عنوان: {nearest[1]}\nنوع: {nearest[2]}\nتاریخ: {date_with_day}\nساعت: {time_text}\nتوضیحات: {nearest[5] or 'بدون توضیحات'}")
        else:
            messagebox.showinfo("نتیجه", "هیچ رویدادی یافت نشد!")
    
    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = EventSchedulerApp(root)
    root.mainloop()