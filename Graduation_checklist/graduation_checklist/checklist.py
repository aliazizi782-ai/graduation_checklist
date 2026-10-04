import os
import sys
import shutil
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
from PIL import Image, ImageTk
from dataclasses import dataclass
from typing import List
from datetime import datetime

DB_NAME = "graduation_checklist.db"
APP_TITLE = "سامانه چک‌لیست فارغ‌التحصیلی -کارشناسی پیوسته مهندسی کامپیوتر"
APP_VERSION = "1.0.0"
def get_resource_path(relative_path):
    """
    دریافت مسیر مطلق یک فایل منابع (مثل آیکون)
   
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def set_window_icon(window, icon_name="icon.JPG"):
  
    icon_path = get_resource_path(icon_name)
    if not os.path.exists(icon_path):
        return

    try:
        img = Image.open(icon_path)

        # چند اندازه‌ی رایج می‌سازیم تا ویندوز بهترین را انتخاب کند
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        photos = []
        for size in sizes:
            resized = img.resize(size, Image.LANCZOS)
            photos.append(ImageTk.PhotoImage(resized))

        # اعمال روی پنجره (True یعنی روی همه‌ی پنجره‌های بعدی هم اعمال شود)
        window.iconphoto(True, *photos)


        window._icon_photos = photos

    except Exception as e:
        # اگر خطایی رخ داد، فقط چاپ کن (برای دیباگ)
        print(f"خطا در تنظیم آیکون: {e}")

# ======================================================================
# قوانین چارت 1403
# ======================================================================

CATEGORY_ORDER = [
    "تخصصی الزامی",
    "تخصصی الزامی - انتخابی",
    "پایه",
    "مهارتی-اشتغال پذیری",
    "دانشگاه آزاد",
    "جبرانی",
    "پروژه",
    "تخصصی اختیاری",
    "عمومی",
]

CATEGORY_DISPLAY = {
    "تخصصی الزامی": "تخصصی الزامی (59 واحد)",
    "تخصصی الزامی - انتخابی": "تخصصی الزامی - انتخابی (21 واحد)",
    "پایه": "دروس پایه (20 واحد)",
    "مهارتی-اشتغال پذیری": "مهارتی - اشتغال پذیری (5 واحد)",
    "دانشگاه آزاد": "دروس الزامی دانشگاه آزاد (6 واحد)",
    "جبرانی": "دروس جبرانی (2 واحد)",
    "پروژه": "پروژه (3 واحد)" ,
    "تخصصی اختیاری": "تخصصی اختیاری (10 واحد)",
    "عمومی": "دروس عمومی (22 واحد)",
}

CATEGORY_COLORS = {
    "تخصصی الزامی": "#DBEAFE",
    "تخصصی الزامی - انتخابی": "#FEF3C7",
    "پایه": "#DCFCE7",
    "مهارتی-اشتغال پذیری": "#EDE9FE",
    "دانشگاه آزاد": "#FFEDD5",
    "جبرانی": "#F3F4F6",
    "پروژه": "#E0E7FF",  
    "تخصصی اختیاری": "#CCFBF1",
    "عمومی": "#FCE7F3",
}

REQUIRED_UNITS = {
    "تخصصی الزامی": 59,
    "تخصصی الزامی - انتخابی": 21,
    "پایه": 20,
    "مهارتی-اشتغال پذیری": 5,
    "دانشگاه آزاد": 6,
    "جبرانی": 2,
    "پروژه" : 3,
    "تخصصی اختیاری": 10,
    "عمومی": 22,
}

TOTAL_REQUIRED = 148
MAX_UNITS_LOW_GPA = 14
MAX_UNITS_MID_GPA = 20
MAX_UNITS_HIGH_GPA = 24
MAX_UNITS_SUMMER = 8
COMPENSATORY_UNITS_MAX = 8

GENERAL_ALTERNATIVE_GROUPS = {
    "G_ISLAMIC1": {"GE101", "GE101B", "GE101C"},
    "G_ISLAMIC2": {"GE102", "GE102B", "GE102C"},
    "G_ETHICS":   {"GE103", "GE103B", "GE103C", "GE103D"},
    "G_REVOLUTION": {"GE104", "GE104B"},
    "G_HISTORY":  {"GE105", "GE105B"},
    "G_QURAN":    {"GE106", "GE106B"},
}

# دروس تخصصی اختیاری که آزمایشگاه/کارگاه هستند
ELECTIVE_LAB_CODES = {
    "EL126",  # آزمایشگاه مهندسی نرم افزار
    "EL127",  # آزمایشگاه سخت افزار
    "EL128",  # آزمایشگاه مدارهای مجتمع پرتوان
    "EL129",  # آزمایشگاه کنترل کامپیوتری
    "EL130",  # کارگاه رباتیک
    "EL131",  # کارگاه ساخت بازی های رایانه ای
}

# دروسی که پیش‌نیازشان «گذراندن حداقل ۱۰۰ واحد» است
COURSES_REQUIRING_100_UNITS = {"PR101", "SK103"}
MIN_UNITS_FOR_PROJECT_INTERNSHIP = 100

@dataclass
class Course:
    code: str
    name: str
    units: int
    category: str
    prerequisite: str = ""
    co_requisite: str = ""
    package: str = ""
    lab_or_workshop: bool = False
    alt_group: str = ""


# ======================================================================
# دروس چارت 1403
# ======================================================================

COURSES: List[Course] = [
    Course("CS101", "مبانی کامپیوتر و برنامه سازی", 3, "تخصصی الزامی"),
    Course("CS102", "کارگاه کامپیوتر", 1, "تخصصی الزامی",lab_or_workshop=True),
    Course("CS103", "مدارهای الکتریکی و الکترونیکی", 3, "تخصصی الزامی","معادلات دیفرانسیل، فیزیک 2 "),
    Course("CS104", "ریاضیات گسسته", 3, "تخصصی الزامی"),
    Course("CS105", "داده ساختارها و الگوریتم ها", 3, "تخصصی الزامی","ریاضیات گسسته"),
    Course("CS106", "مدارهای منطقی", 3, "تخصصی الزامی"),
    Course("CS107", "برنامه سازی پیشرفته", 3, "تخصصی الزامی","مبانی کامپیوتر و برنامه سازی"),
    Course("CS108", "نظریه زبان ها و ماشین ها", 3, "تخصصی الزامی", "داده ساختارها و الگوریتم ها"),
    Course("CS109", "زبان تخصصی کامپیوتر", 2, "تخصصی الزامی","زبان انگلیسی عمومی ترکیبی 3، کارگاه کامپیوتر"),
    Course("CS110", "روش پژوهش و ارائه", 3, "تخصصی الزامی","زبان تخصصی کامپیوتر"),
    Course("CS111", "جبر خطی", 3, "تخصصی الزامی", "ریاضی عمومی 2"),
    Course("CS112", "معماری کامپیوتر", 3, "تخصصی الزامی", "مدارهای منطقی"),
    Course("CS113", "سیستم های عامل", 3, "تخصصی الزامی","داده ساختارها و الگوریتم ها"),
    Course("CS114", "تحلیل و طراحی نرم افزار", 3, "تخصصی الزامی","داده ساختارها و الگوریتم ها"),
    Course("CS115", "طراحی سیستم های دیجیتال", 3, "تخصصی الزامی","معماری کامپیوتر"),
    Course("CS116", "سیستم های نهفته و بی درنگ", 3, "تخصصی الزامی","معماری کامپیوتر"),
    Course("CS117", "امنیت سیستم های کامپیوتری", 3, "تخصصی الزامی","شبکه های کامپیوتری"),
    Course("CS118", "شبکه های کامپیوتری", 3, "تخصصی الزامی","سیستم های عامل"),
    Course("CS119", "هوش مصنوعی", 3, "تخصصی الزامی","داده ساختارها و الگوریتم ها"),
    Course("CS120", "آزمایشگاه معماری کامپیوتر", 1, "تخصصی الزامی","معماری کامپیوتر، آزمایشگاه مدارهای منطقی",
           lab_or_workshop=True),
    Course("CS121", "آزمایشگاه سیستم های عامل", 1, "تخصصی الزامی","سیستم های عامل", lab_or_workshop=True),
    Course("CS122", "آزمایشگاه مدارهای منطقی", 1, "تخصصی الزامی","مدارهای منطقی", lab_or_workshop=True),
    Course("CS123", "آزمایشگاه مدارهای الکتریکی و الکترونیکی", 1,"تخصصی الزامی", "مدارهای الکتریکی و الکترونیکی",
           lab_or_workshop=True),
    Course("CS124", "آزمایشگاه شبکه های کامپیوتری", 1, "تخصصی الزامی","شبکه های کامپیوتری", lab_or_workshop=True),

    Course("CS125", "طراحی الگوریتم ها", 3, "تخصصی الزامی - انتخابی","داده ساختارها و الگوریتم ها"),
    Course("CS126", "سیگنال ها و سیستم ها", 3, "تخصصی الزامی - انتخابی","مدارهای الکتریکی و الکترونیکی"),
    Course("CS127", "طراحی پایگاه داده ها", 3, "تخصصی الزامی - انتخابی","داده ساختارها و الگوریتم ها"),
    Course("CS128", "طراحی کامپایلرها", 3, "تخصصی الزامی - انتخابی","نظریه زبان ها و ماشین ها، معماری کامپیوتر"),
    Course("CS129", "بازیابی اطلاعات", 3, "تخصصی الزامی - انتخابی","داده ساختارها و الگوریتم ها"),
    Course("CS130", "رایانش چندرسانه ای", 3, "تخصصی الزامی - انتخابی","برنامه سازی پیشرفته، معماری کامپیوتر"),
    Course("CS131", "داده کاوی", 3, "تخصصی الزامی - انتخابی","داده ساختارها و الگوریتم ها، آمار و احتمال مهندسی"),
    Course("CS132", "محاسبات عددی", 3, "تخصصی الزامی - انتخابی","معادلات دیفرانسیل"),
    Course("CS133", "شبیه سازی کامپیوتری", 3, "تخصصی الزامی - انتخابی","آمار و احتمال مهندسی"),
    Course("CS134", "مهندسی نرم افزار", 3, "تخصصی الزامی - انتخابی","تحلیل و طراحی نرم افزار"),
    Course("CS135", "طراحی زبان های برنامه سازی", 3,"تخصصی الزامی - انتخابی", "برنامه سازی پیشرفته"),
    Course("CS136", "طراحی مدارهای مجتمع پرتوان", 3,"تخصصی الزامی - انتخابی", "طراحی سیستم های دیجیتال"),
    Course("CS137", "مدیریت پروژه های فناوری اطلاعات", 3,"تخصصی الزامی - انتخابی", "تحلیل و طراحی نرم افزار"),
    Course("CS138", "طراحی در سطح سیستم", 3, "تخصصی الزامی - انتخابی","طراحی سیستم های دیجیتال، معماری کامپیوتر"),

    Course("BA101", "ریاضی عمومی 1", 3, "پایه"),
    Course("BA102", "ریاضی عمومی 2", 3, "پایه", "ریاضی عمومی 1"),
    Course("BA103", "فیزیک 1", 3, "پایه"),
    Course("BA104", "فیزیک 2 ", 3, "پایه", "فیزیک 1"),
    Course("BA105", "آمار و احتمال مهندسی", 3, "پایه","ریاضی عمومی 1"),
    Course("BA106", "معادلات دیفرانسیل", 3, "پایه"),
    Course("BA107", "کارگاه عمومی", 1, "پایه", lab_or_workshop=True),
    Course("BA108", "آزمایشگاه فیزیک 2 ", 1, "پایه", "فیزیک 2 ",lab_or_workshop=True),

    Course("SK101", "آشنایی با صنعت کامپیوتر (کاربینی)", 1,"مهارتی-اشتغال پذیری"),
    Course("SK102", "مهارت های نرم شغلی", 2, "مهارتی-اشتغال پذیری","برنامه سازی پیشرفته"),
    Course("SK103", "کارآموزی", 2, "مهارتی-اشتغال پذیری","روش پژوهش و ارائه"),
    Course("PR101", "پروژه پایانی", 3, "پروژه"),
    Course("AZ101", "انس با قرآن کریم", 1, "دانشگاه آزاد"),
    Course("AZ102", "وصیت نامه امام خمینی (ره)", 1, "دانشگاه آزاد"),
    Course("AZ103", "آشنایی با مبانی دفاع مقدس", 2, "دانشگاه آزاد"),
    Course("AZ104", "تاریخ فرهنگ و تمدن اسلام و ایران", 2, "دانشگاه آزاد"),

    Course("RM101", "زبان انگلیسی پیش دانشگاهی ترکیبی", 2, "جبرانی"),
    Course("RM102", "ریاضی پیش دانشگاهی", 2, "جبرانی"),
    Course("RM103", "فیزیک پیش دانشگاهی", 2, "جبرانی"),
    Course("RM104", "فارسی پیش دانشگاهی", 2, "جبرانی"),

    Course("EL101", "گرافیک کامپیوتری", 3, "تخصصی اختیاری","داده ساختارها و الگوریتم ها"),
    Course("EL102", "سیستم های چندرسانه ای", 3, "تخصصی اختیاری","سیگنال ها و سیستم ها"),
    Course("EL103", "ایجاد جابک نرم افزار", 3, "تخصصی اختیاری","تحلیل و طراحی نرم افزار"),
    Course("EL104", "آزمون نرم افزار", 3, "تخصصی اختیاری","تحلیل و طراحی نرم افزار"),
    Course("EL105", "مبانی هوش محاسباتی", 3, "تخصصی اختیاری","هوش مصنوعی"),
    Course("EL106", "مبانی ساخت بازی های رایانه ای", 3,"تخصصی اختیاری"),
    Course("EL107", "انتقال داده ها", 3, "تخصصی اختیاری","سیگنال ها و سیستم ها"),
    Course("EL108", "برنامه سازی وب", 3, "تخصصی اختیاری","طراحی پایگاه داده ها"),
    Course("EL109", "برنامه سازی موبایل", 3, "تخصصی اختیاری","داده ساختارها و الگوریتم ها"),
    Course("EL110", "مبانی رایانش ابری", 3, "تخصصی اختیاری","شبکه های کامپیوتری"),
    Course("EL111", "مبانی اینترنت اشیاء", 3, "تخصصی اختیاری","شبکه های کامپیوتری"),
    Course("EL112", "تعامل انسان و کامپیوتر", 3, "تخصصی اختیاری","داده ساختارها و الگوریتم ها"),
    Course("EL113", "مدارهای منطقی پیشرفته", 3, "تخصصی اختیاری","مدارهای منطقی"),
    Course("EL114", "آداب فناوری اطلاعات", 3, "تخصصی اختیاری"),
    Course("EL115", "تجارت الکترونیکی", 3, "تخصصی اختیاری"),
    Course("EL116", "مدیریت و برنامه ریزی راهبردی", 3, "تخصصی اختیاری"),
    Course("EL117", "اندازه گیری و کنترل کامپیوتری", 3, "تخصصی اختیاری","سیگنال ها و سیستم ها"),
    Course("EL118", "زبان های توصیف سخت افزار", 3, "تخصصی اختیاری","طراحی سیستم های دیجیتال"),
    Course("EL119", "نظریه محاسبات", 3, "تخصصی اختیاری","داده ساختارها و الگوریتم ها"),
    Course("EL120", "مبانی نظریه بازی ها", 3, "تخصصی اختیاری","داده ساختارها و الگوریتم ها، آمار و احتمال مهندسی"),
    Course("EL121", "مبانی رمزنگاری", 3, "تخصصی اختیاری","ریاضیات گسسته"),
    Course("EL122", "سیستم های کنترل خطی", 3, "تخصصی اختیاری","سیگنال ها و سیستم ها"),
    Course("EL123", "مقدمه ای بر رباتیک", 3, "تخصصی اختیاری","سیگنال ها و سیستم ها"),
    Course("EL124", "مقدمه ای بر بیوانفورماتیک", 3, "تخصصی اختیاری","داده ساختارها و الگوریتم ها، آمار و احتمال مهندسی"),
    Course("EL125", "کارآفرینی", 3, "تخصصی اختیاری"),
    Course("EL126", "آزمایشگاه مهندسی نرم افزار", 1, "تخصصی اختیاری","تحلیل و طراحی نرم افزار", lab_or_workshop=True),
    Course("EL127", "آزمایشگاه سخت افزار", 1, "تخصصی اختیاری","معماری کامپیوتر", lab_or_workshop=True),
    Course("EL128", "آزمایشگاه مدارهای مجتمع پرتوان", 1, "تخصصی اختیاری","طراحی مدارهای مجتمع پرتوان", lab_or_workshop=True),
    Course("EL129", "آزمایشگاه کنترل کامپیوتری", 1, "تخصصی اختیاری","اندازه گیری و کنترل کامپیوتری", lab_or_workshop=True),
    Course("EL130", "کارگاه رباتیک", 1, "تخصصی اختیاری","مقدمه ای بر رباتیک", lab_or_workshop=True),
    Course("EL131", "کارگاه ساخت بازی های رایانه ای", 1,"تخصصی اختیاری", "مبانی ساخت بازی های رایانه ای",lab_or_workshop=True),

    Course("GE101", "اندیشه اسلامی 1 (مبدأ و معاد)", 2, "عمومی",alt_group="G_ISLAMIC1"),
    Course("GE101B", "انسان در اسلام (جایگزین اندیشه 1)", 2, "عمومی",alt_group="G_ISLAMIC1"),
    Course("GE101C", "حقوق اجتماعی و سیاسی در اسلام (جایگزین اندیشه 1)",2, "عمومی", alt_group="G_ISLAMIC1"),

    Course("GE102", "اندیشه اسلامی 2 (نبوت و امامت)", 2, "عمومی","اندیشه اسلامی 1 (مبدأ و معاد)", alt_group="G_ISLAMIC2"),
    Course("GE102B", "انسان در اسلام (جایگزین اندیشه 2)", 2, "عمومی",alt_group="G_ISLAMIC2"),
    Course("GE102C","(حقوق اجتماعی و سیاسی در اسلام (جایگزین اندیشه 2",2  ,"عمومی", alt_group="G_ISLAMIC2"),

    Course("GE103", "اخلاق اسلامی (مبانی و مفاهیم)", 2, "عمومی",alt_group="G_ETHICS"),
    Course("GE103B", "فلسفه اخلاق (جایگزین اخلاق)", 2, "عمومی",alt_group="G_ETHICS"),
    Course("GE103C", "آیین زندگی (جایگزین اخلاق)", 2, "عمومی",alt_group="G_ETHICS"),
    Course("GE103D", "اخلاق کاربردی (جایگزین اخلاق)", 2, "عمومی",alt_group="G_ETHICS"),

    Course("GE104", "انقلاب اسلامی ایران", 2, "عمومی",alt_group="G_REVOLUTION"),
    Course("GE104B","آشنایی با قانون اساسی جمهوری اسلامی ایران (جایگزین انقلاب)",2, "عمومی", alt_group="G_REVOLUTION"),

    Course("GE105", "تاریخ تحلیلی صدر اسلام", 2, "عمومی",alt_group="G_HISTORY"),
    Course("GE105B", "  تاریخ امامت (جایگزین تاریخ تحلیلی صدر اسلام)", 2, "عمومی", alt_group="G_HISTORY"),

    Course("GE106", "تفسیر موضوعی قرآن", 2, "عمومی",alt_group="G_QURAN"),
    Course("GE106B", "تفسیر موضوعی نهج البلاغه (جایگزین تفسیر)", 2,"عمومی", alt_group="G_QURAN"),

    Course("GE107", "زبان فارسی", 3, "عمومی"),
    Course("GE108", "زبان انگلیسی عمومی ترکیبی 1", 1, "عمومی"),
    Course("GE109", "زبان انگلیسی عمومی ترکیبی 2", 1, "عمومی","زبان انگلیسی عمومی ترکیبی 1"),
    Course("GE110", "زبان انگلیسی عمومی ترکیبی 3", 1, "عمومی","زبان انگلیسی عمومی ترکیبی 2"),
    Course("GE111", "تربیت بدنی 1", 1, "عمومی"),
    Course("GE112", "ورزش 1", 1, "عمومی"),
    Course("GE113", "دانش خانواده و جمعیت", 2, "عمومی"),
]


CO_REQUISITES = {
    "CS105": "برنامه سازی پیشرفته",
    "CS106": "ریاضیات گسسته",
    "CS115": "معماری کامپیوتر",
    "CS118": "سیستم های عامل",
    "BA106": "ریاضی عمومی 2",
}

PACKAGES = {
    "CS104": "الگوریتم ها و محاسبات",
    "CS105": "الگوریتم ها و محاسبات - علم داده",
    "CS107": "بازی های رایانه ای",
    "CS108": "الگوریتم ها و محاسبات",
    "CS111": "هوش مصنوعی - رباتیک",
    "CS112": "معماری کامپیوتر",
    "CS113": "رایانش امن - اینترنت اشیاء - سیستم های نرم افزاری",
    "CS114": "مهندسی نرم افزار - فناوری اطلاعات",
    "CS115": "خودکارسازی طراحی - معماری کامپیوتر",
    "CS116": "اینترنت اشیاء - معماری کامپیوتر - شبکه های کامپیوتری",
    "CS117": "رایانش امن - شبکه های کامپیوتری",
    "CS118": "اینترنت اشیاء - رایانش امن - شبکه های کامپیوتری",
    "CS119": "هوش مصنوعی - بیوانفورماتیک - بازی های رایانه ای",
    "BA105": "علم داده - هوش مصنوعی - بیوانفورماتیک - رباتیک",
    "EL101": "بازی های رایانه ای - گرافیک",
    "EL102": "هوش مصنوعی - رباتیک",
    "EL103": "مهندسی نرم افزار - فناوری اطلاعات",
    "EL104": "مهندسی نرم افزار",
    "EL105": "هوش مصنوعی",
    "EL106": "بازی های رایانه ای",
    "EL107": "شبکه های کامپیوتری",
    "EL108": "فناوری اطلاعات",
    "EL109": "بازی های رایانه ای - فناوری اطلاعات",
    "EL110": "اینترنت اشیاء",
    "EL111": "اینترنت اشیاء",
    "EL112": "فناوری اطلاعات",
    "EL113": "معماری کامپیوتر",
    "EL114": "فناوری اطلاعات",
    "EL115": "فناوری اطلاعات",
    "EL116": "فناوری اطلاعات",
    "EL117": "رباتیک - معماری کامپیوتر",
    "EL118": "معماری کامپیوتر",
    "EL119": "الگوریتم ها و محاسبات",
    "EL120": "هوش مصنوعی",
    "EL121": "رایانش امن",
    "EL122": "رباتیک",
    "EL123": "رباتیک",
    "EL124": "بیوانفورماتیک",
}


def course_package(course):
    return PACKAGES.get(course.code, course.package or "")


# ======================================================================
# Database
# ======================================================================

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            entry_year TEXT DEFAULT '',
            current_gpa REAL DEFAULT 0,
            is_last_semester INTEGER DEFAULT 0,
            is_summer INTEGER DEFAULT 0,
            needs_compensatory INTEGER DEFAULT 0,
            compensatory_units INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            units INTEGER NOT NULL,
            category TEXT NOT NULL,
            prerequisite TEXT DEFAULT '',
            co_requisite TEXT DEFAULT '',
            package TEXT DEFAULT '',
            lab_or_workshop INTEGER DEFAULT 0,
            alt_group TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_code TEXT NOT NULL,
            grade REAL,
            UNIQUE(student_id, course_code),
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(course_code) REFERENCES courses(code)
        )
    """)

    cur.execute("PRAGMA table_info(students)")
    student_cols = {row[1] for row in cur.fetchall()}
    for col, ddl in [
        ("current_gpa", "REAL DEFAULT 0"),
        ("is_last_semester", "INTEGER DEFAULT 0"),
        ("is_summer", "INTEGER DEFAULT 0"),
        ("needs_compensatory", "INTEGER DEFAULT 0"),
        ("compensatory_units", "INTEGER DEFAULT 0"),
    ]:
        if col not in student_cols:
            cur.execute(f"ALTER TABLE students ADD COLUMN {col} {ddl}")

    # مهاجرت اطلاعات نسخه‌های قدیمی: اگر فقط پرچم جبرانی وجود داشته باشد،
    # مقدار پیش‌فرض ۲ واحد جبرانی برای حفظ سازگاری داده‌های قبلی ثبت می‌شود.
    if "compensatory_units" not in student_cols:
        cur.execute("""
            UPDATE students
            SET compensatory_units = CASE
                WHEN needs_compensatory = 1 THEN 2 ELSE 0 END
        """)

    cur.execute("PRAGMA table_info(courses)")
    course_columns = {row[1] for row in cur.fetchall()}
    if "package" not in course_columns:
        cur.execute("ALTER TABLE courses ADD COLUMN package TEXT DEFAULT ''")
    if "alt_group" not in course_columns:
        cur.execute("ALTER TABLE courses ADD COLUMN alt_group TEXT DEFAULT ''")

    for c in COURSES:
        cur.execute("""
            INSERT INTO courses (code, name, units, category, prerequisite,
                                 co_requisite, package, lab_or_workshop,
                                 alt_group)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name=excluded.name,
                units=excluded.units,
                category=excluded.category,
                prerequisite=excluded.prerequisite,
                co_requisite=excluded.co_requisite,
                package=excluded.package,
                lab_or_workshop=excluded.lab_or_workshop,
                alt_group=excluded.alt_group
        """, (c.code, c.name, c.units, c.category, c.prerequisite,
              CO_REQUISITES.get(c.code, ""), course_package(c),
              int(c.lab_or_workshop), c.alt_group))

    conn.commit()
    conn.close()


# ======================================================================
# Business Logic
# ======================================================================

def passed_grade(grade):
    return grade is not None and grade >= 10


def compute_gpa(rows, only_passed=True):
    total_points = 0.0
    total_units = 0
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if grade is None:
            continue
        if only_passed and not passed_grade(grade):
            continue
        # «انس با قرآن» و «وصیت‌نامه» طبق چارت در انتخاب بار اول
        # واحد مؤثر ترمی محسوب نمی‌شوند؛ این قاعده به محاسبه GPA تعمیم داده نمی‌شود.
        total_points += grade * units
        total_units += units
    return round(total_points / total_units, 2) if total_units > 0 else 0.0


def get_max_units(student):
    _, _, _, _, current_gpa, is_last, is_summer, _, _ = student
    if is_summer:
        return MAX_UNITS_SUMMER
    if is_last:
        return MAX_UNITS_HIGH_GPA
    if current_gpa > 17:
        return MAX_UNITS_HIGH_GPA
    if current_gpa > 12:
        return MAX_UNITS_MID_GPA
    return MAX_UNITS_LOW_GPA


def normalize_course_name(text):
    """یکسان‌سازی فاصله و حروف عربی/فارسی برای تطبیق نام درس‌ها."""
    return " ".join(text.replace("ي", "ی").replace("ك", "ک").split())


def split_prerequisites(text, name_to_code):
    if not text:
        return []
    text = text.replace("ي", "ی").replace("ك", "ک").strip()
    # «و» را جداکننده در نظر نمی‌گیریم؛ چون در نام بسیاری از دروس
    # مانند «داده ساختارها و الگوریتم ها» و «آمار و احتمال مهندسی» وجود دارد.
    parts = []
    for chunk in text.replace("،", "|").split("|"):
        chunk = normalize_course_name(chunk.strip(" ()"))
        if chunk:
            parts.append(chunk)
    return parts


def resolve_names_to_codes(name, name_to_code):
    """تطبیق دقیق نام (بدون تطبیق زیررشته‌ای خطرناک)"""
    name = name.strip()
    
    # تطبیق دقیق
    if name in name_to_code:
        return [name_to_code[name]]
    
    # تطبیق با حذف پرانتز و فاصله
    import re
    def normalize(text):
        text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
        text = re.sub(r"[()（）]", "", text)
        return " ".join(text.split())
    
    name_norm = normalize(name)
    matches = []
    for full_name, code in name_to_code.items():
        if normalize(full_name) == name_norm:
            matches.append(code)
    
    return matches


def is_passed(cur, student_id, course_code):
    cur.execute(
        "SELECT grade FROM grades WHERE student_id=? AND course_code=?",
        (student_id, course_code)
    )
    row = cur.fetchone()
    return bool(row and row[0] is not None and row[0] >= 10)


def check_prerequisites(student_id, course_code):
    warnings = []
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT prerequisite, co_requisite FROM courses WHERE code=?",
        (course_code,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return []
    prereq_text, co_text = row
    cur.execute("SELECT code, name FROM courses")
    name_to_code = {name: code for code, name in cur.fetchall()}

    def check_requirement(text, label):
        if not text:
            return
        for part in split_prerequisites(text, name_to_code):
            codes = resolve_names_to_codes(part, name_to_code)
            if not codes:
                warnings.append(
                    f"{label} «{part}» در فهرست دروس قابل تطبیق خودکار نیست")
                continue
            if len(codes) > 1:
                warnings.append(
                    f"{label} «{part}» چند تطبیق دارد و نیاز به بررسی دستی دارد")
                continue
            if not is_passed(cur, student_id, codes[0]):
                warnings.append(f"{label} «{part}» گذرانده نشده است")

    check_requirement(prereq_text, "پیش‌نیاز")
    check_requirement(co_text, "هم‌نیاز")
    conn.close()
    return warnings


def category_summary(rows, compensatory_required_units=0):
    summary = {}
    for category in CATEGORY_ORDER:
        required = REQUIRED_UNITS[category]
        summary[category] = {
            "required": required,
            "passed": 0,
            "raw_passed": 0,
            "remaining": required,
            "lab_passed": False,
            "extra_courses": [],
            "extra_units": 0,
            "alternative_extras": [],
        }

    general_passed = {}
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if category != "عمومی" or not passed_grade(grade):
            continue
        general_passed[code] = (name, units, alt)

    chosen_general = {}
    extra_general = []
    counted_general_units = 0
    counted_general_codes = set()

    groups = {}
    singles = []
    for code, (name, units, alt) in general_passed.items():
        if alt:
            groups.setdefault(alt, []).append((code, name, units))
        else:
            singles.append((code, name, units))

    for alt, items in groups.items():
        chosen_code, chosen_name, chosen_units = items[0]
        chosen_general[alt] = chosen_code
        counted_general_codes.add(chosen_code)
        counted_general_units += chosen_units
        for code, name, units in items[1:]:
            extra_general.append((code, name, units))

    for code, name, units in singles:
        counted_general_codes.add(code)
        counted_general_units += units

    general_required = REQUIRED_UNITS["عمومی"]
    if counted_general_units > general_required:
        overflow = counted_general_units - general_required
        summary["عمومی"]["extra_units"] += overflow
        cumulative = 0
        for code, name, units in reversed(singles):
            if cumulative + units <= general_required:
                cumulative += units
                continue
            summary["عمومی"]["extra_courses"].append((code, name, units))
        for code, name, units in extra_general:
            summary["عمومی"]["extra_courses"].append((code, name, units))
        summary["عمومی"]["passed"] = general_required
        summary["عمومی"]["raw_passed"] = counted_general_units
        summary["عمومی"]["remaining"] = 0
        summary["عمومی"]["alternative_extras"] = extra_general
    else:
        summary["عمومی"]["passed"] = counted_general_units
        summary["عمومی"]["raw_passed"] = counted_general_units
        summary["عمومی"]["remaining"] = general_required - counted_general_units
        if extra_general:
            summary["عمومی"]["extra_units"] = sum(
                u for _, _, u in extra_general)
            summary["عمومی"]["extra_courses"] = list(extra_general)
            summary["عمومی"]["alternative_extras"] = extra_general

    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if not passed_grade(grade):
            continue
        if category == "عمومی":
            continue
        if category not in summary:
            continue
        summary[category]["raw_passed"] += units
        if lab:
            summary[category]["lab_passed"] = True

    for category in CATEGORY_ORDER:
        if category in ("عمومی",):
            continue
        s = summary[category]
        required = REQUIRED_UNITS[category]

        if category == "جبرانی":
            required = max(0, min(int(compensatory_required_units), COMPENSATORY_UNITS_MAX))
            s["required"] = required
            s["passed"] = min(s["raw_passed"], required)
            s["remaining"] = max(0, required - s["passed"])
            if s["raw_passed"] > required:
                s["extra_units"] = s["raw_passed"] - required
            continue

        if s["raw_passed"] > required:
            s["extra_units"] = s["raw_passed"] - required
            s["passed"] = required
            s["remaining"] = 0
            cumulative = 0
            extras = []
            for row in reversed(rows):
                code, name, units, cat, lab, alt, grade = row
                if cat != category or not passed_grade(grade):
                    continue
                if cumulative + units <= required:
                    cumulative += units
                    continue
                extras.append((code, name, units))
            s["extra_courses"] = list(reversed(extras))
        else:
            s["passed"] = s["raw_passed"]
            s["remaining"] = required - s["passed"]

    return summary


def calculate_status(student_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, student_no, name, entry_year, current_gpa,
               is_last_semester, is_summer, needs_compensatory,
               compensatory_units
        FROM students WHERE id=?
    """, (student_id,))
    student = cur.fetchone()
    if not student:
        conn.close()
        return None

    case_parts = " ".join(
        f"WHEN '{cat}' THEN {i}" for i, cat in enumerate(CATEGORY_ORDER)
    )
    cur.execute(f"""
        SELECT c.code, c.name, c.units, c.category, c.lab_or_workshop,
               c.alt_group, g.grade
        FROM courses c
        LEFT JOIN grades g
          ON g.course_code = c.code AND g.student_id = ?
        ORDER BY
            CASE c.category {case_parts} ELSE 99 END,
            c.code
    """, (student_id,))
    rows = cur.fetchall()

    prereq_warnings = []
    for row in rows:
        code, name = row[0], row[1]
        grade = row[6]
        if grade is None:
            continue
        for w in check_prerequisites(student_id, code):
            prereq_warnings.append(f"{name}: {w}")

    conn.close()

    summary = category_summary(rows, compensatory_required_units=student[8])
    gpa = compute_gpa(rows)
    max_units = get_max_units(student)
    problems = []
    extra_warnings = []
        # ============================================================
    # چک پیش‌نیاز واحد-محور برای پروژه و کارآموزی
    # ============================================================
    # محاسبه‌ی واحدهای گذرانده‌شده تا کنون (بدون احتساب خود پروژه و کارآموزی)
    passed_units_excluding_project = 0
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if passed_grade(grade) and code not in COURSES_REQUIRING_100_UNITS:
            passed_units_excluding_project += units
    
    # چک برای هر درس نیازمند ۱۰۰ واحد
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if code not in COURSES_REQUIRING_100_UNITS:
            continue
        # فقط اگر درس مردود یا ثبت‌نشده باشد، پیش‌نیاز را چک کن
        if grade is not None and passed_grade(grade):
            continue  # اگر پاس شده، نیازی به چک نیست
        # اگر ثبت‌نشده یا مردود است، باید ۱۰۰ واحد گذرانده باشد
        if passed_units_excluding_project < MIN_UNITS_FOR_PROJECT_INTERNSHIP:
            problems.append(
                f"{name}: پیش‌نیاز اخذ این درس، گذراندن حداقل "
                f"{MIN_UNITS_FOR_PROJECT_INTERNSHIP} واحد از دروس دیگر است "
                f"شما تا کنون {passed_units_excluding_project} واحد گذرانده‌اید")
    

    for category in CATEGORY_ORDER:
        s = summary[category]

        if category == "جبرانی":
            if s["remaining"] > 0:
                problems.append(
                    f"{category}: "
                    f"{s['remaining']} "
                    f".واحد جبرانی باقی‌مانده است")
            continue

        if s["remaining"] > 0:
            problems.append(
                f"{category}: {s['remaining']} واحد دیگر لازم است "
                f"(تکمیل‌شده: {s['passed']} از {s['required']})")

        if s["extra_units"] > 0:
            names = ", ".join(n for _, n, _ in s["extra_courses"][:5])
            if len(s["extra_courses"]) > 5:
                names += " و ..."
            extra_warnings.append(
                f"{category}: {s['extra_units']} واحد مازاد بر سقف "
                f"{s['required']} واحد ({names}). این واحدها در مجموع "
                f"واحد موردنیاز محاسبه نمی‌شوند.")

    alt_extras = summary["عمومی"].get("alternative_extras", [])
    if alt_extras:
        names = ", ".join(n for _, n, _ in alt_extras)
        extra_warnings.append(
            f".دروس عمومی: از گروه‌های «جایگزین»  فقط یکی باید گذرانده شود"
            f"دروس اضافه: {names}")

    elective = summary["تخصصی اختیاری"]
    if elective["passed"] >= 10 and not elective["lab_passed"]:
        problems.append( ".از 10 واحد دروس اختیاری باید حداقل یک واحد آن آزمایشگاه یا کارگاه باشد"
        ) 

        # ============================================================
    # تشخیص گروه‌های جایگزین پاس‌شده (قبل از محاسبه‌ی مردودی‌ها)
    # ============================================================
    passed_alt_groups = set()
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if alt and passed_grade(grade):
            passed_alt_groups.add(alt)

    # ============================================================
    # محاسبه‌ی دروس مردود واقعی
    # ============================================================
    failed = []
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if grade is None or passed_grade(grade):
            continue
        # اگر درس از گروه جایگزین است و گروهش پاس شده → نادیده بگیر
        if alt and alt in passed_alt_groups:
            continue
        failed.append((code, name, units, category, grade))
    for code, name, units, category, grade in failed:
        problems.append(f"درس مردود: {name} ({units} واحد) - نمره {grade:g}")

    # ============================================================
    # محاسبه‌ی دروس باقی‌مانده با منطق هوشمند
    # ============================================================
    remaining_courses = []

    # ۱. دروس مردود واقعی (نه از گروه‌های جایگزین پاس‌شده)
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if grade is None or passed_grade(grade):
            continue
        if alt and alt in passed_alt_groups:
            continue
        remaining_courses.append(
            (code, name, units, category, lab, "مردود", grade))

    # ۲. دروس عمومی: ابتدا گروه‌های جایگزین
    general_passed = {}
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if category == "عمومی" and passed_grade(grade):
            general_passed[code] = (name, units, alt)

    # گروه‌های جایگزین که یک درسشان پاس شده
    passed_groups = set()
    for code, (name, units, alt) in general_passed.items():
        if alt:
            passed_groups.add(alt)

    # دروس عمومی ثبت‌نشده
    general_remaining = []
    general_missing_groups = {}
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if category != "عمومی" or grade is not None:
            continue
        # اگر این درس جزء گروه جایگزین است و گروهش پاس شده → نادیده بگیر
        if alt and alt in passed_groups:
            continue
        # اگر این درس جزء گروه جایگزین است → در لیست گروه قرار بگیر
        if alt:
            general_missing_groups.setdefault(alt, []).append(
                (code, name, units, lab))
        else:
            general_remaining.append((code, name, units, lab))

    # برای هر گروه جایگزین پاس‌نشده، فقط یک درس نمایش بده
    for alt, items in general_missing_groups.items():
        code, name, units, lab = items[0]
        general_remaining.append((code, name, units, lab))

    # بررسی سقف عمومی
    general_needed = summary["عمومی"]["remaining"]
    if general_needed > 0:
        cumulative = 0
        for code, name, units, lab in general_remaining:
            if cumulative >= general_needed:
                break
            remaining_courses.append(
                (code, name, units, "عمومی", lab, "باقی‌مانده", None))
            cumulative += units

       # ۳. دروس سایر دسته‌ها (به‌جز عمومی و جبرانی)
    for category in CATEGORY_ORDER:
        if category in ("عمومی", "جبرانی"):
            continue

        s = summary[category]

        # ✅ استثنا: تخصصی اختیاری با کمبود آزمایشگاه (حتی اگر remaining = 0 باشد)
        is_elective_lab_missing = (
            category == "تخصصی اختیاری"
            and not s["lab_passed"]
            and s["passed"] >= 10
        )

        if s["remaining"] <= 0 and not is_elective_lab_missing:
            continue   # دسته تکمیل است و نیازی به درس اضافی نیست

        # --- حالت خاص: تخصصی اختیاری ---
        if category == "تخصصی اختیاری":
            needed = s["remaining"]

            # ابتدا اگر به آزمایشگاه نیاز دارد، یک آزمایشگاه پیشنهاد بده
            if not s["lab_passed"]:
                lab_added = False
                for row in rows:
                    code, name, units, cat, lab, alt, grade = row
                    if (cat == "تخصصی اختیاری"
                            and code in ELECTIVE_LAB_CODES
                            and grade is None):
                        remaining_courses.append(
                            (code, name, units, category, True,
                             "باقی‌مانده (آزمایشگاه الزامی)", None))
                        needed -= units
                        lab_added = True
                        break
                # اگر هیچ آزمایشگاه ثبت‌نشده‌ای نبود، آزمایشگاه مردود را نمایش بده
                if not lab_added:
                    for row in rows:
                        code, name, units, cat, lab, alt, grade = row
                        if (cat == "تخصصی اختیاری"
                                and code in ELECTIVE_LAB_CODES
                                and grade is not None
                                and not passed_grade(grade)):
                            remaining_courses.append(
                                (code, name, units, category, True,
                                 "مردود (آزمایشگاه اجباری)", grade))
                            needed = max(0, needed - units)
                            break

            # سپس دروس عادی را تا پر شدن کمبود پیشنهاد بده
            if needed > 0:
                for row in rows:
                    code, name, units, cat, lab, alt, grade = row
                    if (cat != "تخصصی اختیاری"
                            or grade is not None
                            or code in ELECTIVE_LAB_CODES):
                        continue
                    if needed <= 0:
                        break
                    remaining_courses.append(
                        (code, name, units, category, lab,
                         "باقی‌مانده", None))
                    needed -= units
            continue

        # --- سایر دسته‌ها ---
        cat_remaining = []
        for row in rows:
            code, name, units, cat, lab, alt, grade = row
            if cat != category or grade is not None:
                continue
            cat_remaining.append((code, name, units, lab))

        cumulative = 0
        for code, name, units, lab in cat_remaining:
            if cumulative >= s["remaining"]:
                break
            remaining_courses.append(
                (code, name, units, category, lab, "باقی‌مانده", None))
            cumulative += units

    # ۴. دروس جبرانی
    if student[7]:
        s = summary["جبرانی"]
        if s["remaining"] > 0:
            cumulative = 0
            for row in rows:
                code, name, units, category, lab, alt, grade = row
                if category != "جبرانی" or grade is not None:
                    continue
                if cumulative >= s["remaining"]:
                    break
                remaining_courses.append(
                    (code, name, units, category, lab,
                     "باقی‌مانده", None))
                cumulative += units
    # ۵. دروس نیازمند ۱۰۰ واحد (اگر پیش‌نیازشان برقرار نیست)
    for row in rows:
        code, name, units, category, lab, alt, grade = row
        if code not in COURSES_REQUIRING_100_UNITS:
            continue
        if grade is not None and passed_grade(grade):
            continue  # پاس شده
        if passed_units_excluding_project < MIN_UNITS_FOR_PROJECT_INTERNSHIP:
            # اگر هنوز در remaining_courses نیست، اضافه کن
            already_in = any(rc[0] == code for rc in remaining_courses)
            if not already_in:
                remaining_courses.append(
                    (code, name, units, category, lab, 
                     f"نیازمند {MIN_UNITS_FOR_PROJECT_INTERNSHIP} واحد", None))
    # ============================================================
    # محاسبه‌ی مجموع‌ها
    # ============================================================
    total_passed = sum(s["passed"] for s in summary.values())
    total_raw = sum(s["raw_passed"] for s in summary.values())
    total_extra = sum(s["extra_units"] for s in summary.values())

    effective_total_required = TOTAL_REQUIRED - REQUIRED_UNITS["جبرانی"] + summary["جبرانی"]["required"]

    # هشدار پیش‌نیاز/هم‌نیاز یک شرط واقعی برای بررسی نهایی است؛
    # قبلاً این هشدارها نمایش داده می‌شدند اما مانع اعلام فارغ‌التحصیلی نمی‌شدند.
    for warning in prereq_warnings:
        if "گذرانده نشده است" in warning and warning not in problems:
            problems.append(warning)

    is_graduated = len(problems) == 0
    progress = min(100.0,
                   round((total_passed / effective_total_required) * 100, 1)) \
        if effective_total_required else 0

    return {
        "student": student,
        "rows": rows,
        "summary": summary,
        "failed": failed,
        "remaining_courses": remaining_courses,
        "problems": problems,
        "extra_warnings": extra_warnings,
        "prereq_warnings": prereq_warnings,
        "total_passed": total_passed,
        "total_raw": total_raw,
        "total_extra": total_extra,
        "total_required": effective_total_required,
        "gpa": gpa,
        "max_units": max_units,
        "is_graduated": is_graduated,
        "progress": progress,
    }
# ======================================================================
# Backup / Restore
# ======================================================================

def export_database(parent):
    if not os.path.exists(DB_NAME):
        messagebox.showwarning("پشتیبان‌گیری", ".فایل دیتابیس یافت نشد")
        return
    path = filedialog.asksaveasfilename(
        parent=parent, title="ذخیره پشتیبان",
        defaultextension=".db",
        filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")],
        initialfile=f"backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    if not path:
        return
    try:
        shutil.copy2(DB_NAME, path)
        messagebox.showinfo("پشتیبان‌گیری",
                            f".پشتیبان با موفقیت ذخیره شد\n{path}")
    except Exception as e:
        messagebox.showerror("خطا", str(e))


def import_database(parent):
    path = filedialog.askopenfilename(
        parent=parent, title="انتخاب فایل پشتیبان",
        filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")])
    if not path:
        return
    if not messagebox.askyesno(
            "بازیابی",
            "با بازیابی، اطلاعات فعلی جایگزین می‌شود. ادامه؟"):
        return
    try:
        shutil.copy2(path, DB_NAME)
        messagebox.showinfo("بازیابی",
                            "بازیابی انجام شد. برنامه را دوباره اجرا کنید.")
    except Exception as e:
        messagebox.showerror("خطا", str(e))


# ======================================================================
# GUI
# ======================================================================

class GraduationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        set_window_icon(self)   #  آیکون پنجره‌ی اصلی
        self.setup_auto_geometry(self, width_ratio=0.92, height_ratio=0.85,
                                 min_width=1100, min_height=650, center=True)
        self.minsize(1000, 600)

        self.student_id = None
        self.course_rows = []

        self.setup_style()
        self.build_ui()
        self.load_courses()
        self.after(300, self.show_welcome)

    # ------------------------------------------------------------------
    def setup_auto_geometry(self, win, width_ratio=0.85, height_ratio=0.85,
                        min_width=900, min_height=600, center=True):
        """تنظیم خودکار اندازه و موقعیت پنجره — وسط‌چین و بدون بیرون‌زدگی"""
        win.update_idletasks()
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()

        # محاسبه‌ی ابعاد
        width = max(min_width, int(screen_w * width_ratio))
        height = max(min_height, int(screen_h * height_ratio))

       
        width = min(width, screen_w - 40)
        height = min(height, screen_h - 100)

        if center:
            x = (screen_w - width) // 2
            y = (screen_h - height) // 6
            win.geometry(f"{width}x{height}+{x}+{y}")
        else:
            win.geometry(f"{width}x{height}")
    # ------------------------------------------------------------------
    
    def show_toast(self, message, kind="success", duration=2500):
       
        colors = {
            "success": {"bg": "#16a34a", "border": "#15803d", "icon": "✓"},
            "info":    {"bg": "#2563eb", "border": "#1d4ed8", "icon": "ℹ"},
            "warning": {"bg": "#d97706", "border": "#b45309", "icon": "⚠"},
            "error":   {"bg": "#dc2626", "border": "#b91c1c", "icon": "✗"},
        }
        theme = colors.get(kind, colors["success"])

        # اگر toast قبلی وجود دارد، حذفش کن
        if hasattr(self, "_active_toast") and self._active_toast is not None:
            try:
                self._active_toast.destroy()
            except tk.TclError:
                pass
            self._active_toast = None

        # فریم اصلی toast
        toast = tk.Frame(
            self,
            bg=theme["bg"],
            highlightbackground=theme["border"],
            highlightthickness=1,
            bd=0,
        )
        inner = tk.Frame(toast, bg=theme["bg"])
        inner.pack(padx=16, pady=10)

        icon_label = tk.Label(
            inner, text=theme["icon"], bg=theme["bg"], fg="white",
            font=(self.font_family, 14, "bold"),
        )
        icon_label.pack(side="right", padx=(0, 8))

        msg_label = tk.Label(
            inner, text=message, bg=theme["bg"], fg="white",
            font=(self.font_family, 12, "bold"),
            justify="right",
        )
        msg_label.pack(side="right")

        # قرار دادن toast در بالای پنجره، وسط‌چین
        toast.place(relx=0.5, rely=0.04, anchor="n")
        self._active_toast = toast

        # انیمیشن fade out
        def fade_out(step=10):
            if step <= 0:
                try:
                    toast.destroy()
                except tk.TclError:
                    pass
                if getattr(self, "_active_toast", None) is toast:
                    self._active_toast = None
                return
            try:
                current_rely = 0.04 + (10 - step) * 0.002
                toast.place_configure(rely=current_rely)
            except tk.TclError:
                return
            self.after(30, lambda: fade_out(step - 1))

        self.after(duration, fade_out)
    
    # ------------------------------------------------------------------
    def setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.font_family = self.pick_font()

        style.configure("Title.TLabel"                  ,font=(self.font_family, 20, "bold")    ,foreground="#1e3a8a")
        style.configure("SubTitle.TLabel"               ,font=(self.font_family, 12)            ,foreground="#475569")
        style.configure("Section.TLabel"                ,font=(self.font_family, 12, "bold")    ,foreground="#1e40af")
        style.configure("Treeview",rowheight=30         ,font=(self.font_family, 12))
        style.configure("Treeview.Heading"              ,font=(self.font_family, 12, "bold")    ,background="#1e40af",foreground="white")
        style.map("Treeview.Heading"                                                            ,background=[("active", "#1e40af")])
        style.configure("TButton"                       ,font=(self.font_family, 12),padding=4)
        style.configure("Accent.TButton"                ,font=(self.font_family, 12, "bold")    ,foreground="white" ,background="#2563eb")
        style.map("Accent.TButton"                                                              ,background=[("active", "#1d4ed8")])
        style.configure("Success.TButton"               ,font=(self.font_family, 12, "bold")    ,foreground="white",background="#16a34a")
        style.map("Success.TButton"                                                             ,background=[("active", "#15803d")])
        style.configure("Danger.TButton"                ,font=(self.font_family, 12, "bold")    ,foreground="white",background="#dc2626")
        style.map("Danger.TButton"                                                              ,background=[("active", "#b91c1c")])
        style.configure("TLabelframe.Label"             ,font=(self.font_family, 12, "bold")    ,foreground="#1e40af")
        style.configure("TLabelframe"                                                           ,background="#f8fafc",borderwidth=1,relief="solid")
        style.configure("Green.TLabel"                                                          ,foreground="#166534",font=(self.font_family, 13, "bold"))
        style.configure("Red.TLabel"                                                            ,foreground="#991b1b",font=(self.font_family, 13, "bold"))
        style.configure("Info.TLabel"                                                           ,foreground="#1e3a8a",font=(self.font_family, 12, "bold"))
        style.configure("Progress.Horizontal.TProgressbar",troughcolor="#e2e8f0"                ,background="#22c55e",lightcolor="#22c55e",darkcolor="#16a34a")

    def pick_font(self):
        try:
            available = tkfont.families(self)
        except Exception:
            available = []
        for name in ["B Nazanin","Vazirmatn", "IRANSans","Arial"]:
            if name in available:
                return name
        return "Tahoma"

    # ------------------------------------------------------------------
    def build_ui(self):
        # منو
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="پشتیبان‌گیری از دیتابیس"    ,command=lambda: export_database(self))
        file_menu.add_command(label="بازیابی از پشتیبان",       command=lambda: import_database(self))
        file_menu.add_separator()
        file_menu.add_command(label="خروج",                     command=self.destroy)
        menubar.add_cascade(label="فایل", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="راهنما", command=self.show_help)
        help_menu.add_command(label="درباره", command=self.show_about)
        menubar.add_cascade(label="راهنما", menu=help_menu)
        self.config(menu=menubar)

        # هدر
        header = tk.Frame(self, bg="#1e3a8a", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text=APP_TITLE, bg="#1e3a8a", fg="white",font=(self.font_family, 18, "bold")).pack(
            anchor="e", padx=20, pady=(12, 2))
        tk.Label(header,
                 text=".مبنای دروس: چارت 1403 دانشگاه آزاد اسلامی واحد مبارکه -  طبق مصوبه جلسه شماره 179  مورخ 1403/4/10 تنظیم گردیده است",
                 bg="#1e3a8a", fg="#c7d2fe",
                 font=(self.font_family, 11)).pack(anchor="e", padx=20)

        # نوار ابزار
        toolbar = ttk.Frame(self, padding=(12, 8))
        toolbar.pack(fill="x")
        
        ttk.Button(toolbar, text="📊 بررسی وضعیت فارغ‌التحصیلی",
                style="Accent.TButton",command=self.show_graduation_status).pack(side="left", padx=2)

        # =====================================================
        # اطلاعات دانشجو - با عنوان راست‌چین و ویجت‌های راست‌چین
        # =====================================================
        student_outer = tk.Frame(self, bg="#f8fafc",highlightbackground="#1e40af",highlightthickness=1, bd=0)
        student_outer.pack(fill="x", padx=12, pady=(20, 6))

        # قاب داخلی برای عنوان + محتوا
        inner = tk.Frame(student_outer, bg="#f8fafc")
        inner.pack(fill="x", padx=12, pady=8)

        # عنوان به‌عنوان یک برچسب معمولی در بالای محتوا
        title_row = tk.Frame(inner, bg="#f8fafc")
        title_row.pack(fill="x", pady=(0, 8))
        tk.Label(title_row, text="اطلاعات دانشجو",bg="#f8fafc", fg="#1e40af",font=(self.font_family, 13, "bold")).pack(side="right")

        # محتوای اصلی
        student_frame = tk.Frame(inner, bg="#f8fafc")
        student_frame.pack(fill="x")


        # ستون کشسان در سمت چپ
        student_frame.columnconfigure(0, weight=1)

        # -------- ردیف 0 --------
        ttk.Label(student_frame, text=":نام و نام خانوادگی").grid(
            row=0, column=9, padx=5, pady=6, sticky="e")
        self.name_var = tk.StringVar()
        ttk.Entry(student_frame, textvariable=self.name_var, width=24,justify="right").grid(row=0, column=8, padx=5, pady=6)

        ttk.Label(student_frame, text=":شماره دانشجویی").grid(
            row=0, column=7, padx=5, pady=6, sticky="e")
        self.no_var = tk.StringVar()
        ttk.Entry(student_frame, textvariable=self.no_var, width=15,justify="right").grid(row=0, column=6, padx=5, pady=6)

        ttk.Label(student_frame, text=":سال ورود").grid(
            row=0, column=5, padx=5, pady=6, sticky="w")
        self.year_var = tk.StringVar()
        ttk.Entry(student_frame, textvariable=self.year_var, width=10,justify="right").grid(row=0, column=4, padx=5, pady=6)

        ttk.Button(student_frame, text="ثبت / به‌روزرسانی",
                style="Accent.TButton",
                command=self.save_student).grid(row=0, column=3,padx=10, pady=6)
        ttk.Button(student_frame, text="دانشجویان قبلی",
                command=self.choose_student).grid(row=0, column=2,padx=5, pady=6)

        ttk.Button(student_frame, text="🗑 حذف دانشجو",
                command=self.delete_student).grid(row=0, column=1,padx=5, pady=6)

        # -------- ردیف 1 --------
        ttk.Label(student_frame, text=":معدل ترم قبل").grid(
            row=1, column=9, padx=5, pady=6, sticky="e")
        self.gpa_var = tk.StringVar(value="0")
        ttk.Entry(student_frame, textvariable=self.gpa_var, width=10,justify="right").grid(row=1, column=8, padx=5, pady=6 ,sticky="e")

        self.is_last_var = tk.BooleanVar()
        ttk.Checkbutton(student_frame, text="ترم آخر",
                        variable=self.is_last_var).grid(
            row=1, column=7, padx=10, pady=6, sticky="e")

        self.is_summer_var = tk.BooleanVar()
        ttk.Checkbutton(student_frame, text="ترم تابستان",variable=self.is_summer_var).grid(
            row=1, column=6, padx=10, pady=6, sticky="e")

        ttk.Label(student_frame, text=":واحد جبرانی موردنیاز").grid(
            row=1, column=5, padx=5, pady=6, sticky="e")
        self.comp_units_var = tk.StringVar(value="0")
        ttk.Spinbox(student_frame, from_=0, to=COMPENSATORY_UNITS_MAX,
                    increment=2, textvariable=self.comp_units_var,
                    width=8, justify="right").grid(
            row=1, column=4, padx=5, pady=6, sticky="e")


        # نوار فیلتر و جستجو
        filter_frame = ttk.Frame(self, padding=(12, 8))
        filter_frame.pack(fill="x")

        ttk.Label(filter_frame, text=":جستجو").pack(side="right", padx=4)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var,width=28, justify="right")
        search_entry.pack(side="right", padx=4)
        search_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        ttk.Label(filter_frame, text=":دسته").pack(side="right", padx=4)
        self.category_var = tk.StringVar(value="همه")
        categories = ["همه"] + [CATEGORY_DISPLAY[c] for c in CATEGORY_ORDER]
        self.category_combo = ttk.Combobox(
            filter_frame, textvariable=self.category_var,
            values=categories, state="readonly", width=38,justify="center")
        self.category_combo.pack(side="right")
        self.category_combo.bind("<<ComboboxSelected>>",lambda e: self.apply_filter())

        ttk.Button(filter_frame, text="حذف نمره",
                   style="Danger.TButton",command=self.delete_grade).pack(side="left", padx=2)
        ttk.Button(filter_frame, text="پاک کردن همه نمرات",
                   style="Danger.TButton",command=self.delete_all_grades).pack(side="left", padx=2)

        # جدول
        table_frame = ttk.Frame(self, padding=12)
        table_frame.pack(fill="both", expand=True)

        columns = ("category", "status", "grade", "package", "co","pre", "units", "name")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            selectmode="browse")

        headings = {
            "category": "دسته", "status": "وضعیت", "grade": "نمره",
            "package": "بسته", "co": "هم نیاز", "pre": "پیش نیاز",
            "units": "تعداد واحد", "name": "نام درس"
        }
        widths = {
            "category": 180, "status": 90, "grade": 65, "package": 170,
            "co": 150, "pre": 180, "units": 80, "name": 280
        }
        for col in columns:
            self.tree.heading(col, text=headings[col], anchor="center")
            self.tree.column(col, width=widths[col], anchor="center",stretch=False)

        self.tree.tag_configure("passed", background="#dcfce7")
        self.tree.tag_configure("failed", background="#fee2e2")

        for cat, color in CATEGORY_COLORS.items():
            self.tree.tag_configure(f"cat_{cat}", background=color)

        yscroll = ttk.Scrollbar(table_frame, orient="vertical",command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal",command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set,xscrollcommand=xscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.edit_grade)


        # نوار وضعیت
        status_frame = tk.Frame(self, bg="#f1f5f9", height=44)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            status_frame, variable=self.progress_var,
            style="Progress.Horizontal.TProgressbar",
            length=300, maximum=100)
        self.progress.pack(side="left", padx=15, pady=10)

        self.progress_label = tk.Label(
            status_frame, text="0%", bg="#f1f5f9",
            font=(self.font_family, 12, "bold"), fg="#1e40af")
        self.progress_label.pack(side="left")

        self.status_var = tk.StringVar(
            value=".ابتدا دانشجو را ثبت یا انتخاب کنید")
        tk.Label(status_frame, textvariable=self.status_var,
                 bg="#f1f5f9", font=(self.font_family, 12),
                 fg="#334155", anchor="e").pack(
            side="right", padx=15, fill="x", expand=True)

    # ------------------------------------------------------------------
    def show_welcome(self):
        """ صفحه ی خوش آمدگویی  """
        win = tk.Toplevel(self)
        win.title("خوش آمدید")
        set_window_icon(win)
        self.setup_auto_geometry(win, width_ratio=0.50, height_ratio=0.87,
                                min_width=600, min_height=580, center=True)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        win.configure(bg="#FFFFFF")

        # نوار رنگی بالای پنجره
        tk.Frame(win, bg="#1E3A8A", height=4).pack(fill="x")

        # آیکون
        tk.Label(win, text="🎓", font=(self.font_family, 50),
                bg="#FFFFFF", fg="#1E3A8A").pack(pady=(15, 2))

        # عنوان
        tk.Label(win, text="به سامانه چک‌لیست فارغ‌التحصیلی خوش آمدید",
                font=(self.font_family, 16, "bold"),
                bg="#FFFFFF", fg="#1E293B").pack()

        tk.Label(win,
                text="کارشناسی پیوسته مهندسی کامپیوتر — دانشگاه آزاد اسلامی واحد مبارکه",
                font=(self.font_family, 13),
                bg="#FFFFFF", fg="#64748B").pack(pady=(2, 10))

        # کارت اطلاعات
        info_card = tk.Frame(win, bg="#F8FAFC",
                            highlightbackground="#E2E8F0",
                            highlightthickness=1)
        info_card.pack(fill="x", padx=24, pady=4)

        info = (
            "📌 مبنای برنامه: چارت 1403/4/10 وزارت علوم، تحقیقات و فناوری\n"
            "🎯 مجموع واحدهای لازم: 146 واحد پایه + واحدهای جبرانی\n\n"
            "📚 :دسته‌بندی دروس\n"
            " تخصصی الزامی: 59 واحد• \n"
            " تخصصی الزامی - انتخابی: 21 واحد•\n"
            " پایه: 20 واحد•\n"
            " مهارتی - اشتغال پذیری: 5 واحد•\n"
            " دانشگاه آزاد: 6 واحد•\n"
            " جبرانی: طبق نظر گروه آموزشی (۰ تا ۸)•\n"
            " تخصصی اختیاری: 10 واحد•\n"
            " عمومی: 22 واحد•"
        )
        tk.Label(info_card, text=info, justify="right",
                bg="#F8FAFC", fg="#1E293B",
                font=(self.font_family, 13)).pack(padx=16, pady=12, anchor="e")

        # پیام شروع
        tk.Label(win, text="برای شروع، اطلاعات دانشجو را در فرم اصلی وارد کنید.",
                font=(self.font_family, 13),
                bg="#FFFFFF", fg="#64748B").pack(pady=(10, 6))

        # ✅ دکمه شروع (در پایین پنجره)
        btn_frame = tk.Frame(win, bg="#FFFFFF")
        btn_frame.pack(pady=(4, 12))
        ttk.Button(btn_frame, text="شروع", style="Accent.TButton",
                command=win.destroy).pack()

    def show_help(self):
        messagebox.showinfo(
            "راهنما",
            " .برای ثبت یا ویرایش نمره، روی ردیف درس دوبار کلیک کنید\n\n"
            " .برای حذف نمره، درس را انتخاب و دکمه «حذف نمره» را بزنید\n\n"
            " .رنگ هر دسته در جدول متفاوت است\n\n"
            
            " دروس مازاد بر سقف هر دسته\n"
            " .در مجموع 148 واحد محسوب نمی شوند و هشدار داده می شود\n\n"
            
            " شرط آزمایشگاه: از 10 واحد تخصصی اختیاری،\n"
            " .حداقل 1 واحد باید آزمایشگاه یا کارگاه باشد\n\n"
            " اگر دانشجو نیاز به دروس جبرانی نداشته باشد،\n"
            " .مجموع واحدهای لازم 146 واحد می شود"
           
        )

    def show_about(self):
        messagebox.showinfo(
            "درباره",
            f"{APP_TITLE}\n"
            f"نسخه: {APP_VERSION}\n"
            f"مبنای دروس: چارت 1403 دانشگاه آزاد اسلامی واحد مبارکه\n"
            f"Python + Tkinter ساخته‌شده با "
        )

    # ------------------------------------------------------------------
    def save_student(self):
        name = self.name_var    .get().strip()
        no = self.no_var        .get().strip()
        year = self.year_var    .get().strip()

        if not name or len(name) < 3:
            self.show_toast("نام باید حداقل ۳ کاراکتر باشد", kind="warning")
            return
        if not no or not no.isdigit() or len(no) < 5:
            self.show_toast("شماره دانشجویی باید عددی و حداقل ۵ رقم باشد",
                            kind="warning")
            return
        if year and (not year.isdigit() or len(year) != 4):
            self.show_toast("سال ورود باید ۴ رقمی باشد", kind="warning")
            return

        try:
            gpa = float(self.gpa_var.get().strip().replace(",", ".") or 0)
            if gpa < 0 or gpa > 20:
                raise ValueError
        except ValueError:
            self.show_toast("معدل باید عددی بین ۰ و ۲۰ باشد", kind="warning")
            return

        try:
            comp_text = self.comp_units_var.get().strip().replace(",", ".") or "0"
            comp_float = float(comp_text)
            if comp_float < 0 or comp_float > COMPENSATORY_UNITS_MAX or comp_float % 2 != 0:
                raise ValueError
            comp_units = int(comp_float)
        except ValueError:
            self.show_toast("واحد جبرانی باید یکی از مقادیر ۰، ۲، ۴، ۶ یا ۸ باشد",
                            kind="warning")
            return

        conn = get_conn()
        cur = conn.cursor()
        try:
                
            cur.execute("SELECT id FROM students WHERE student_no=?", (no,))
            existing = cur.fetchone()
            is_new = existing is None

            cur.execute("""
                INSERT INTO students(student_no, name, entry_year,
                    current_gpa, is_last_semester, is_summer,
                    needs_compensatory, compensatory_units)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_no) DO UPDATE SET
                    name=excluded.name,
                    entry_year=excluded.entry_year,
                    current_gpa=excluded.current_gpa,
                    is_last_semester=excluded.is_last_semester,
                    is_summer=excluded.is_summer,
                    needs_compensatory=excluded.needs_compensatory,
                    compensatory_units=excluded.compensatory_units
            """, (no, name, year, gpa,
                int(self.is_last_var.get()),
                int(self.is_summer_var.get()),
                int(comp_units > 0), comp_units))
            conn.commit()

            cur.execute("SELECT id FROM students WHERE student_no=?", (no,))
            self.student_id = cur.fetchone()[0]
            self.status_var.set(f"دانشجو: {name} - {no}")
            self.update_progress()

            
            if is_new:
                self.show_toast(
                    f"دانشجوی «{name}» با موفقیت ثبت شد",
                    kind="success"
                )
            else:
                self.show_toast(
                    f"اطلاعات دانشجوی «{name}» به‌روزرسانی شد",
                    kind="success"
                )

        except sqlite3.Error as e:
            self.show_toast(f"خطای پایگاه داده: {e}", kind="error")
            return
        finally:
            conn.close()

        self.load_courses()
    
    def choose_student(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, student_no, name, entry_year FROM students "
                    "ORDER BY id DESC")
        students = cur.fetchall()
        conn.close()

        if not students:
            messagebox.showinfo("دانشجو", ".هنوز دانشجویی ثبت نشده است")
            return

        win = tk.Toplevel(self)
        win.title("انتخاب دانشجو")
        set_window_icon(win)
        self.setup_auto_geometry(win, width_ratio=0.55, height_ratio=0.60,
                                min_width=600, min_height=400, center=True)
        win.transient(self)

        search_frame = ttk.Frame(win, padding=8)
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text=":جستجو").pack(side="right")
        search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=search_var,
                width=30).pack(side="right", padx=5)

        tree = ttk.Treeview(win, columns=( "year", "no", "name","row_num"),
                            show="headings", height=15)
        for c, h, w in [
            ("year", "سال ورود", 100),
            ("no", "شماره دانشجویی", 150),
            ("name", "نام", 280),
            ("row_num", "شماره ردیف", 90),
        ]:
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="center")

        
        row_to_db_id = {}

        def refresh_list(*args):
            for i in tree.get_children():
                tree.delete(i)
            row_to_db_id.clear()

            term = search_var.get().strip()
            display_index = 0
            for s in students:
                sid, sno, sname, syear = s
                if term and term not in str(sno) and term not in str(sname):
                    continue
                display_index += 1
                tree.insert("", "end",
                            values=(syear, sno, sname,display_index))
                row_to_db_id[display_index] = sid

        search_var.trace("w", refresh_list)
        refresh_list()
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def select(event=None):
            item = tree.selection()
            if not item:
                return
            values = tree.item(item[0], "values")
            display_index = int(values[3])
            
            sid = row_to_db_id.get(display_index)
            if sid is None:
                return

            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT student_no, name, entry_year, current_gpa,
                    is_last_semester, is_summer, needs_compensatory,
                    compensatory_units
                FROM students WHERE id=?
            """, (sid,))
            row = cur.fetchone()
            conn.close()

            self.student_id = sid
            self.no_var.set(row[0])
            self.name_var.set(row[1])
            self.year_var.set(row[2])
            self.gpa_var.set(str(row[3] or 0))
            self.is_last_var.set(bool(row[4]))
            self.is_summer_var.set(bool(row[5]))
            self.comp_units_var.set(str(row[7] or 0))

            self.status_var.set(f":دانشجو انتخاب شد {row[1]}")
            self.load_courses()
            self.update_progress()
            win.destroy()

        tree.bind("<Double-1>", select)
        ttk.Button(win, text="انتخاب", style="Accent.TButton",
                command=select).pack(pady=5)

    def delete_student(self):
        if not self.student_id:
            messagebox.showwarning("حذف دانشجو",
                                   ".ابتدا دانشجو را انتخاب کنید")
            return

        name = self.name_var.get()
        no = self.no_var.get()

        if not messagebox.askyesno(
                "حذف دانشجو",
                f"دانشجو «{name} - {no}» و تمام نمراتش حذف شود؟"):
            return

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id=?", (self.student_id,))
        conn.commit()
        conn.close()

        self.student_id = None
        self.name_var.set("")
        self.no_var.set("")
        self.year_var.set("")
        self.gpa_var.set("0")
        self.is_last_var.set(False)
        self.is_summer_var.set(False)
        self.comp_units_var.set("0")
        self.status_var.set("دانشجو حذف شد")
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.load_courses()

    # ------------------------------------------------------------------
    def load_courses(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = get_conn()
        cur = conn.cursor()

        case_parts = " ".join(
            f"WHEN '{cat}' THEN {i}"
            for i, cat in enumerate(CATEGORY_ORDER)
        )
        cur.execute(f"""
            SELECT c.code, c.name, c.units, c.category,
                   c.prerequisite, c.co_requisite, c.package,
                   c.alt_group, g.grade
            FROM courses c
            LEFT JOIN grades g
              ON c.code=g.course_code AND g.student_id=?
            ORDER BY
                CASE c.category {case_parts} ELSE 99 END,
                c.code
        """, (self.student_id or -1,))
        self.course_rows = cur.fetchall()
        conn.close()

        self.apply_filter()

    def apply_filter(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        term = self.search_var.get().strip().lower()
        cat_display = self.category_var.get()

        cat_key = None
        if cat_display != "همه":
            for k, v in CATEGORY_DISPLAY.items():
                if v == cat_display:
                    cat_key = k
                    break

        for row in self.course_rows:
            (code, name, units, category, pre, co, package,
             alt_group, grade) = row
            if cat_key and category != cat_key:
                continue
            if term and term not in name.lower() and term not in code.lower():
                continue

            if grade is None:
                status = "ثبت نشده"
                grade_text = ""
                tag = f"cat_{category}"
            elif grade >= 10:
                status = "قبول"
                grade_text = f"{grade:g}"
                tag = "passed"
            else:
                status = "مردود"
                grade_text = f"{grade:g}"
                tag = "failed"

            self.tree.insert(
                "", "end",
                values=(category,
                        status, grade_text, package or "-",
                        co or "-", pre or "-", units, name),tags=(tag,))

    def update_progress(self):
        if not self.student_id:
            self.progress_var.set(0)
            self.progress_label.config(text="0%")
            return
        result = calculate_status(self.student_id)
        if result is None:
            return
        self.progress_var.set(result["progress"])
        self.progress_label.config(text=f"{result['progress']}%")

    # ------------------------------------------------------------------
    def edit_grade(self, event=None):
        if not self.student_id:
            messagebox.showwarning("دانشجو",
                                   ".ابتدا دانشجو را ثبت یا انتخاب کنید")
            return
        item = self.tree.selection()
        if not item:
            return

        values = self.tree.item(item[0], "values")
        category, status, current, package, co, pre, units, name = values
        units = int(units)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT code FROM courses
            WHERE name=? AND category=?
            LIMIT 1
        """, (name, category))
        code_row = cur.fetchone()
        code = code_row[0] if code_row else ""

        warnings = check_prerequisites(self.student_id, code)

        cur.execute("SELECT alt_group FROM courses WHERE code=?", (code,))
        alt_row = cur.fetchone()
        alt_group = alt_row[0] if alt_row else ""

        if alt_group:
            group_codes = GENERAL_ALTERNATIVE_GROUPS.get(alt_group, set())
            placeholders = ",".join("?" * len(group_codes))
            cur.execute(f"""
                SELECT c.name, g.grade
                FROM grades g
                JOIN courses c ON c.code = g.course_code
                WHERE g.student_id=? AND g.course_code IN ({placeholders})
                  AND g.course_code != ? AND g.grade >= 10
            """, (self.student_id, *group_codes, code))
            others = cur.fetchall()
            for oname, ograde in others:
                warnings.append(
                    f"از گروه « جایگزین » قبلاً درس «{oname}» با نمره "
                    f"{ograde:g} گذرانده‌اید. فقط یکی از این‌ها جزء "
                    f"22 .واحد محاسبه می‌شود")
        conn.close()

        win = tk.Toplevel(self)
        win.title(f"ثبت نمره - {name}")
        set_window_icon(win)
        self.setup_auto_geometry(win, width_ratio=0.40, height_ratio=0.58,
                                 min_width=500, min_height=380, center=True)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        tk.Label(win, text=f"درس: {name}",font=(self.font_family, 14, "bold"),fg="#1e3a8a", wraplength=500).pack(pady=(12, 4))
        tk.Label(win, text=f" تعداد واحد: {units}",font=(self.font_family, 12)).pack()
        tk.Label(win, text=f"دسته: {category}",font=(self.font_family, 11),fg="#475569").pack(pady=2)
        
        if pre and pre != "-":
            tk.Label(win, text=f"پیش‌نیاز: {pre}",fg="#2563eb", wraplength=500,font=(self.font_family, 11)).pack(pady=2)
        
        if co and co != "-":
            tk.Label(win, text=f"هم‌نیاز: {co}",fg="#7c3aed", wraplength=500,font=(self.font_family, 11)).pack(pady=2)

        if warnings:
            tk.Label(win, text=":⚠ هشدار\n" + "\n".join(warnings),fg="#dc2626", wraplength=500, justify="right",font=(self.font_family, 11)).pack(pady=6)

        tk.Label(win, text=":نمره (خالی = حذف نمره)",font=(self.font_family, 10)).pack(pady=(10, 2))
        grade_var = tk.StringVar(value=current)
        entry = ttk.Entry(win, textvariable=grade_var, width=15,justify="center",font=(self.font_family, 14))
        entry.pack(pady=5)
        entry.focus()

        def save():
            text = grade_var.get().strip().replace(",", ".")
            if text == "":
                grade = None
            else:
                try:
                    grade = float(text)
                except ValueError:
                    messagebox.showerror("نمره نامعتبر",
                                         ".نمره باید عددی باشد")
                    return
                if grade < 0 or grade > 20:
                    messagebox.showerror("نمره نامعتبر",
                                         ".نمره باید بین 0 و 20 باشد")
                    return

            conn = get_conn()
            cur = conn.cursor()
            if grade is None:
                cur.execute("""
                    DELETE FROM grades WHERE student_id=? AND course_code=?
                """, (self.student_id, code))
            else:
                cur.execute("""
                    INSERT INTO grades(student_id, course_code, grade)
                    VALUES (?, ?, ?)
                    ON CONFLICT(student_id, course_code)
                    DO UPDATE SET grade=excluded.grade
                """, (self.student_id, code, grade))
            conn.commit()
            conn.close()

            self.load_courses()
            self.update_progress()
            win.destroy()

        ttk.Button(win, text="ذخیره", style="Success.TButton",
                   command=save).pack(pady=10)

    def delete_grade(self):
        if not self.student_id:
            messagebox.showwarning("دانشجو",
                                   ".ابتدا دانشجو را ثبت یا انتخاب کنید")
            return
        item = self.tree.selection()
        if not item:
            messagebox.showinfo("حذف نمره", ".یک درس را انتخاب کنید")
            return

        values = self.tree.item(item[0], "values")
        name = values[7]
        category = values[0]

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT code FROM courses
            WHERE name=? AND category=?
            LIMIT 1
        """, (name, category))
        code_row = cur.fetchone()
        code = code_row[0] if code_row else ""

        if not messagebox.askyesno("حذف نمره",
                                   f"نمره درس «{name}» حذف شود؟"):
            conn.close()
            return

        cur.execute("DELETE FROM grades WHERE student_id=? AND course_code=?",
                    (self.student_id, code))
        conn.commit()
        conn.close()
        self.load_courses()
        self.update_progress()
        self.status_var.set(f"نمره «{name}» .حذف شد")

    def delete_all_grades(self):
        if not self.student_id:
            messagebox.showwarning("دانشجو",
                                   ".ابتدا دانشجو را ثبت یا انتخاب کنید")
            return
        if not messagebox.askyesno(
                "پاک کردن همه نمرات",
                "تمام نمرات ثبت‌شده‌ی این دانشجو حذف شود؟"):
            return

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM grades WHERE student_id=?",
                    (self.student_id,))
        conn.commit()
        conn.close()
        self.load_courses()
        self.update_progress()
        self.status_var.set(".تمام نمرات این دانشجو حذف شد")

    # ------------------------------------------------------------------
    def show_graduation_status(self):
        if not self.student_id:
            messagebox.showwarning("دانشجو",
                                ".ابتدا دانشجو را ثبت یا انتخاب کنید")
            return
        result = calculate_status(self.student_id)
        if result is None:
            messagebox.showerror("خطا", ".دانشجو یافت نشد")
            return

        win = tk.Toplevel(self)
        win.title("بررسی وضعیت فارغ‌التحصیلی")
        set_window_icon(win)
        self.setup_auto_geometry(win, width_ratio=0.80, height_ratio=0.88,
                                min_width=850, min_height=620, center=True)
        win.transient(self)

        if result["is_graduated"]:
            title = "🎉 تبریک! شرایط فارغ‌التحصیلی تکمیل شده است"
            color = "Green.TLabel"
        else:
            title = "شرایط فارغ‌التحصیلی هنوز تکمیل نشده است"
            color = "Red.TLabel"

        ttk.Label(win, text=title, style=color,
                font=(self.font_family, 16, "bold")).pack(pady=10)

        ttk.Label(
            win,
            text=f"واحد مؤثر :{result['total_passed']} از "
                f"{result['total_required']}  |  "
                f"مازاد :{result['total_extra']}  |  "
                f"پیشرفت :{result['progress']}%  |  "
                f"معدل :{result['gpa']}  |  "
                f"حداکثر واحد مجاز :{result['max_units']}",
            font=(self.font_family, 12)
        ).pack(pady=5)

        pb = ttk.Progressbar(win, maximum=100,
                            style="Progress.Horizontal.TProgressbar",
                            value=result["progress"])
        pb.pack(pady=5, fill="x", padx=30)

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        text = tk.Text(frame, wrap="word",
                    font=(self.font_family, 13),
                    padx=10, pady=10, bg="#f8fafc",spacing1=3,spacing3=3)
        text.tag_configure("rtl", justify="right")
        text.tag_configure("heading", font=(self.font_family, 12, "bold"),
                        foreground="#1e40af" ,justify="right")
        text.tag_configure("red", foreground="#991b1b",justify="right")
        text.tag_configure("green", foreground="#166534",justify="right")
        text.tag_configure("orange", foreground="#d97706",justify="right")
        text.pack(fill="both", expand=True)

        # ---- مجموع واحدها ----
        text.insert(
            "end",
            f"\nمجموع واحد مؤثر: {result['total_passed']} | "
            f"مجموع خام: {result['total_raw']} | "
            f"مازاد: {result['total_extra']}\n", "rtl")

        # ---- وضعیت تفصیلی دسته‌ها ----
        text.insert("end", "وضعیت تفصیلی دروس\n", "heading")
        text.insert("end", "-" * 90 + "\n", "rtl")

        for category in CATEGORY_ORDER:
            s = result["summary"][category]
            display = CATEGORY_DISPLAY[category]

            # --- جبرانی ---
            if category == "جبرانی":
                if s["required"] == 0:
                    line = f" {display}: نیاز نیست\n"
                else:
                    line = f" {display}: {s['passed']} از {s['required']} واحد گذرانده شده (باقی‌مانده: {s['remaining']})\n"
                text.insert("end", line ,"rtl")
                continue

            # --- دسته‌های عادی ---
            mark = "✓" if s["remaining"] == 0 else "✗"
            line = (f"{mark} {display}: {s['passed']} از {s['required']} "
                    f"(باقی‌مانده: {s['remaining']})\n")
            if s["remaining"] == 0:
                text.insert("end", line, "green")
            else:
                text.insert("end", line, "red")

            # دروس مازاد این دسته
            if s["extra_units"] > 0:
                names = ", ".join(n for _, n, _ in s["extra_courses"][:5])
                if len(s["extra_courses"]) > 5:
                    names += " و ..."
                text.insert(
                    "end",
                    f"    ⚠ مازاد: {s['extra_units']} واحد ({names})\n",
                    "orange")

            # دروس مردود این دسته
            failed_in_cat = [f for f in result["failed"] if f[3] == category]
            for code, name, units, cat, grade in failed_in_cat:
                text.insert(
                    "end",
                    f"    ✗ مردود: {name} ({units} واحد) - نمره {grade:g}\n",
                    "red")

        # ---- دروس عمومی جایگزین مازاد ----
        alt_extras = result["summary"]["عمومی"].get("alternative_extras", [])
        if alt_extras:
            names = ", ".join(n for _, n, _ in alt_extras)
            text.insert(
                "end",
                f"\n:⚠ دروس عمومی جایگزین اضافه {names}\n",
                "orange")
            text.insert(
                "end",
                "  (از هر گروه « جایگزین » فقط یکی جزء ۲۲ واحد محاسبه می‌شود)\n",
                "orange")
        
       
        # ---- هشدارهای پیش‌نیاز ----
        if result["prereq_warnings"]:
            text.insert("end", "\n⚠ هشدارهای پیش‌نیاز / هم‌نیاز\n", "heading")
            text.insert("end", "-" * 90 + "\n", "rtl")
            for w in result["prereq_warnings"]:
                text.insert("end", " " + w + "\n", "red")

      
        # ---- نتیجه نهایی ----
        text.insert("end", "\n" + "=" * 90 + "\n", "rtl")
        if result["problems"]:
            text.insert(
                "end",
                f"\n✗ :شما هنوز فارغ‌التحصیل نیستید. موارد زیر باید بررسی شوند\n",
                "red")
            text.insert("end", "-" * 90 + "\n", "rtl")
            for p in result["problems"]:
                text.insert("end", f"{p}\n\n", "red")
        else:
            text.insert("end", "\n✓ تمام شروط برقرار است\n", "green")

        # ---- دروس باقی‌مانده ----
        text.insert("end", "\nدروس باقی‌مانده\n", "heading")
        text.insert("end", "-" * 90 + "\n", "rtl")

        if result["remaining_courses"]:
            for item in result["remaining_courses"]:
                code, name, units, category, lab, status, grade = item
                lab_mark = " [آزمایشگاه/کارگاه]" if lab else ""
                if "مردود" in status:
                    text.insert(
                        "end",
                        f"✗ {name}{lab_mark} | {units} واحد | "
                        f"{CATEGORY_DISPLAY.get(category, category)} | "
                        f"مردود با نمره {grade:g}\n", "red")
                elif "آزمایشگاه اجباری" in status:
                    text.insert(
                        "end",
                        f"• {name}{lab_mark} | {units} واحد | "
                        f"{CATEGORY_DISPLAY.get(category, category)} | "
                        f"⚠ الزامی (آزمایشگاه/کارگاه)\n", "orange")
                else:
                    text.insert(
                        "end",
                        f"• {name}{lab_mark} | {units} واحد | "
                        f"{CATEGORY_DISPLAY.get(category, category)}\n", "rtl")
        else:
            text.insert("end", ".موردی باقی نمانده است\n", "green")

        text.config(state="disabled")
        ttk.Button(win, text="بستن", style="Accent.TButton",
                command=win.destroy).pack(pady=10)


# ======================================================================
# Entry Point
# ======================================================================

if __name__ == "__main__":
    init_db()
    app = GraduationApp()
    app.mainloop()