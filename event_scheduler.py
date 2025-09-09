import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import re

class EventSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("برنامه‌ریز رویداد")
        self.root.geometry("800x600")
        
        # اتصال به پایگاه داده
        self.conn = sqlite3.connect("events.db")
        self.create_table()
        
        # لیست دسته‌بندی رویدادها
        self.event_types = ["امتحان", "تمرین", "کلاس", "جلسه", "تحقیق", "ارائه", "سایر"]
        
        # رابط کاربری
        self.create_gui()
        
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                description TEXT
            )
        ''')
        self.conn.commit()
    
    def validate_date(self, date_str):
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, date_str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    def validate_time(self, time_str):
        pattern = r"^\d{2}:\d{2}$"
        if not re.match(pattern, time_str):
            return False
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    def create_gui(self):
        # فریم برای افزودن رویداد
        add_frame = ttk.LabelFrame(self.root, text="افزودن رویداد جدید")
        add_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(add_frame, text="عنوان:").grid(row=0, column=0, padx=5, pady=5)
        self.title_entry = ttk.Entry(add_frame)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="نوع رویداد:").grid(row=1, column=0, padx=5, pady=5)
        self.event_type_combo = ttk.Combobox(add_frame, values=self.event_types)
        self.event_type_combo.grid(row=1, column=1, padx=5, pady=5)
        self.event_type_combo.set("سایر")
        
        ttk.Label(add_frame, text="تاریخ (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5)
        self.date_entry = ttk.Entry(add_frame)
        self.date_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="ساعت (HH:MM):").grid(row=3, column=0, padx=5, pady=5)
        self.time_entry = ttk.Entry(add_frame)
        self.time_entry.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="توضیحات:").grid(row=4, column=0, padx=5, pady=5)
        self.desc_entry = ttk.Entry(add_frame)
        self.desc_entry.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Button(add_frame, text="افزودن رویداد", command=self.add_event).grid(row=5, column=0, columnspan=2, pady=10)
        
        # فریم برای نمایش رویدادها
        self.event_frame = ttk.LabelFrame(self.root, text="لیست رویدادها")
        self.event_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.tree = ttk.Treeview(self.event_frame, columns=("ID", "Title", "Type", "Date", "Time", "Description"), show="headings")
        self.tree.heading("ID", text="شناسه")
        self.tree.heading("Title", text="عنوان")
        self.tree.heading("Type", text="نوع")
        self.tree.heading("Date", text="تاریخ")
        self.tree.heading("Time", text="ساعت")
        self.tree.heading("Description", text="توضیحات")
        self.tree.grid(row=0, column=0, padx=5, pady=5)
        
        # تنظیم عرض ستون‌ها
        for col in self.tree["columns"]:
            self.tree.column(col, width=100)
        
        # دکمه‌های ویرایش و حذف
        ttk.Button(self.event_frame, text="ویرایش رویداد", command=self.edit_event).grid(row=1, column=0, pady=5)
        ttk.Button(self.event_frame, text="حذف رویداد", command=self.delete_event).grid(row=2, column=0, pady=5)
        
        # فریم برای جستجوی نزدیک‌ترین رویداد
        search_frame = ttk.LabelFrame(self.root, text="جستجوی نزدیک‌ترین رویداد")
        search_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(search_frame, text="تاریخ (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
        self.search_date_entry = ttk.Entry(search_frame)
        self.search_date_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(search_frame, text="جستجو", command=self.find_nearest_event).grid(row=1, column=0, columnspan=2, pady=5)
        
        # نمایش رویدادها
        self.load_events()
    
    def add_event(self):
        title = self.title_entry.get()
        event_type = self.event_type_combo.get()
        date = self.date_entry.get()
        time = self.time_entry.get()
        description = self.desc_entry.get()
        
        if not title or not event_type or not date or not time:
            messagebox.showerror("خطا", "لطفاً تمام فیلدها را پر کنید!")
            return
        
        if not self.validate_date(date):
            messagebox.showerror("خطا", "فرمت تاریخ نامعتبر است! از فرمت YYYY-MM-DD استفاده کنید.")
            return
        
        if not self.validate_time(time):
            messagebox.showerror("خطا", "فرمت ساعت نامعتبر است! از فرمت HH:MM استفاده کنید.")
            return
        
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO events (title, event_type, date, time, description) VALUES (?, ?, ?, ?, ?)",
                      (title, event_type, date, time, description))
        self.conn.commit()
        
        self.title_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.event_type_combo.set("سایر")
        
        self.load_events()
        messagebox.showinfo("موفقیت", "رویداد با موفقیت اضافه شد!")
    
    def load_events(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events")
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, values=row)
    
    def edit_event(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("خطا", "لطفاً یک رویداد را انتخاب کنید!")
            return
        
        item = self.tree.item(selected_item)
        event_id = item["values"][0]
        
        # پنجره ویرایش
        edit_window = tk.Toplevel(self.root)
        edit_window.title("ویرایش رویداد")
        edit_window.geometry("400x300")
        
        ttk.Label(edit_window, text="عنوان:").grid(row=0, column=0, padx=5, pady=5)
        title_entry = ttk.Entry(edit_window)
        title_entry.grid(row=0, column=1, padx=5, pady=5)
        title_entry.insert(0, item["values"][1])
        
        ttk.Label(edit_window, text="نوع رویداد:").grid(row=1, column=0, padx=5, pady=5)
        event_type_combo = ttk.Combobox(edit_window, values=self.event_types)
        event_type_combo.grid(row=1, column=1, padx=5, pady=5)
        event_type_combo.set(item["values"][2])
        
        ttk.Label(edit_window, text="تاریخ (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5)
        date_entry = ttk.Entry(edit_window)
        date_entry.grid(row=2, column=1, padx=5, pady=5)
        date_entry.insert(0, item["values"][3])
        
        ttk.Label(edit_window, text="ساعت (HH:MM):").grid(row=3, column=0, padx=5, pady=5)
        time_entry = ttk.Entry(edit_window)
        time_entry.grid(row=3, column=1, padx=5, pady=5)
        time_entry.insert(0, item["values"][4])
        
        ttk.Label(edit_window, text="توضیحات:").grid(row=4, column=0, padx=5, pady=5)
        desc_entry = ttk.Entry(edit_window)
        desc_entry.grid(row=4, column=1, padx=5, pady=5)
        desc_entry.insert(0, item["values"][5] or "")
        
        def save_changes():
            title = title_entry.get()
            event_type = event_type_combo.get()
            date = date_entry.get()
            time = time_entry.get()
            description = desc_entry.get()
            
            if not title or not event_type or not date or not time:
                messagebox.showerror("خطا", "لطفاً تمام فیلدها را پر کنید!")
                return
            
            if not self.validate_date(date):
                messagebox.showerror("خطا", "فرمت تاریخ نامعتبر است! از فرمت YYYY-MM-DD استفاده کنید.")
                return
            
            if not self.validate_time(time):
                messagebox.showerror("خطا", "فرمت ساعت نامعتبر است! از فرمت HH:MM استفاده کنید.")
                return
            
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE events 
                SET title = ?, event_type = ?, date = ?, time = ?, description = ?
                WHERE id = ?
            ''', (title, event_type, date, time, description, event_id))
            self.conn.commit()
            
            self.load_events()
            edit_window.destroy()
            messagebox.showinfo("موفقیت", "رویداد با موفقیت ویرایش شد!")
        
        ttk.Button(edit_window, text="ذخیره تغییرات", command=save_changes).grid(row=5, column=0, columnspan=2, pady=10)
    
    def delete_event(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("خطا", "لطفاً یک رویداد را انتخاب کنید!")
            return
        
        item = self.tree.item(selected_item)
        event_id = item["values"][0]
        
        if messagebox.askyesno("تأیید", "آیا مطمئن هستید که می‌خواهید این رویداد را حذف کنید؟"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            self.conn.commit()
            self.load_events()
            messagebox.showinfo("موفقیت", "رویداد با موفقیت حذف شد!")
    
    def find_nearest_event(self):
        search_date = self.search_date_entry.get()
        if not self.validate_date(search_date):
            messagebox.showerror("خطا", "فرمت تاریخ نامعتبر است! از فرمت YYYY-MM-DD استفاده کنید.")
            return
        
        search_datetime = datetime.strptime(search_date, "%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events WHERE date >= ?", (search_date,))
        events = cursor.fetchall()
        
        if not events:
            messagebox.showinfo("نتیجه", "هیچ رویدادی در آینده یافت نشد!")
            return
        
        nearest_event = None
        min_diff = float("inf")
        
        for event in events:
            event_datetime = datetime.strptime(f"{event[3]} {event[4]}", "%Y-%m-%d %H:%M")
            diff = (event_datetime - search_datetime).total_seconds()
            if diff >= 0 and diff < min_diff:
                min_diff = diff
                nearest_event = event
        
        if nearest_event:
            messagebox.showinfo("نزدیک‌ترین رویداد", f"عنوان: {nearest_event[1]}\nنوع: {nearest_event[2]}\nتاریخ: {nearest_event[3]}\nساعت: {nearest_event[4]}\nتوضیحات: {nearest_event[5] or 'بدون توضیحات'}")
        else:
            messagebox.showinfo("نتیجه", "هیچ رویدادی در آینده یافت نشد!")
    
    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = EventSchedulerApp(root)
    root.mainloop()