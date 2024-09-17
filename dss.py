#Allameh University Educational Expert System


import sqlite3


class EducationExpertSystem:
    def __init__(self):
        self.conn = sqlite3.connect('allameh_education_system.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.majors = {1: "علوم کامپیوتر", 2: "مهندسی کامپیوتر", 3: "آمار و احتمال", 4: "ریاضی کاربردی"}
        self.education_levels = {1: "دیپلم", 2: "کارشناسی", 3: "کارشناسی ارشد", 4: "دکترا"}




    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT,
                gender INTEGER,
                education_level INTEGER,
                military_service INTEGER,
                gpa REAL,
                credits INTEGER,
                major TEXT,
                status TEXT
            )
        ''')
            
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY,
                name TEXT,
                credits INTEGER,
                prerequisite INTEGER,
                major TEXT
            )
        ''')
        
        
        
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                student_id TEXT,
                course_id INTEGER,
                grade REAL,
                semester INTEGER,
                year INTEGER,
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS degree_requirements (
                education_level INTEGER,
                major TEXT,
                required_credits INTEGER,
                minimum_gpa REAL,
                PRIMARY KEY (education_level, major)
            )
        ''')
        self.conn.commit()






    def add_student(self, name, gender, education_level, military_service, gpa, credits, major):
        student_id = self.generate_student_id()
        
        self.cursor.execute('''
            INSERT INTO students (id, name, gender, education_level, military_service, gpa, credits, major, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, name, gender, education_level, military_service, gpa, credits, major, "فعال"))
        self.conn.commit()
        
        return student_id







    def generate_student_id(self):
        self.cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM students")
        max_id = self.cursor.fetchone()[0]
        return str(int(max_id) + 1) if max_id else "40313141001"






    def add_course(self, name, credits, prerequisite, major):
        self.cursor.execute('''
            INSERT INTO courses (name, credits, prerequisite, major)
            VALUES (?, ?, ?, ?)
        ''', (name, credits, prerequisite, major))
        self.conn.commit()
        return self.cursor.lastrowid




    def enroll_student(self, student_id, course_id, semester, year):
        if self.check_prerequisite(student_id, course_id):
            self.cursor.execute('''
                INSERT INTO enrollments (student_id, course_id, semester, year)
                VALUES (?, ?, ?, ?)
            ''', (student_id, course_id, semester, year))
            self.conn.commit()
            return True
        return False






    def check_prerequisite(self, student_id, course_id):
        self.cursor.execute("SELECT prerequisite FROM courses WHERE id = ?", (course_id,))
        prerequisite = self.cursor.fetchone()[0]
        if prerequisite is None:
            return True
        self.cursor.execute('''
            SELECT COUNT(*) FROM enrollments
            WHERE student_id = ? AND course_id = ? AND grade >= 10
        ''', (student_id, prerequisite))
        return self.cursor.fetchone()[0] > 0





    def update_grade(self, student_id, course_id, grade, semester, year):
        self.cursor.execute('''
            UPDATE enrollments
            SET grade = ?
            WHERE student_id = ? AND course_id = ? AND semester = ? AND year = ?
        ''', (grade, student_id, course_id, semester, year))
        self.conn.commit()
        self.update_student_gpa(student_id)






    def update_student_gpa(self, student_id):
        self.cursor.execute('''
            SELECT AVG(grade), SUM(c.credits)
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.student_id = ? AND e.grade IS NOT NULL
        ''', (student_id,))
        avg_grade, total_credits = self.cursor.fetchone()
        if avg_grade is not None:
            self.cursor.execute('''
                UPDATE students
                SET gpa = ?, credits = ?
                WHERE id = ?
            ''', (avg_grade, total_credits, student_id))
            self.conn.commit()





    def get_gpa_label(self, gpa):
        if gpa >= 18:
            return "A"
        elif gpa >= 16:
            return "B"
        elif gpa >= 14:
            return "C"
        elif gpa >= 12:
            return "D"
        else:
            return "F"




    def check_graduation_eligibility(self, student_id):
        self.cursor.execute('''
            SELECT education_level, credits, gpa, major FROM students WHERE id = ?
        ''', (student_id,))
        
        education_level, credits, gpa, major = self.cursor.fetchone()
        
        self.cursor.execute('''
            SELECT required_credits, minimum_gpa
            FROM degree_requirements
            WHERE education_level = ? AND major = ?
        ''', (education_level, major))
        
        requirements = self.cursor.fetchone()
        
        if not requirements:
            return False, "ابتدا الزامات فارغ التحصیلی برای این مقطع و رشته را تعریف کنید."
        
        required_credits, minimum_gpa = requirements
        
        if credits < required_credits:
            return False, f"تعداد واحدهای گذرانده کافی نیست. نیاز به {required_credits} واحد است"
            
        if gpa < minimum_gpa:
            return False, f"معدل کل کمتر از حد نصاب ({minimum_gpa}) است."
        return True, "واجد شرایط فارغ التحصیلی است."






    def generate_report(self, student_id):
        self.cursor.execute("SELECT name, gender, education_level, military_service, gpa, credits, major, status FROM students WHERE id = ?", (student_id,))
        student = self.cursor.fetchone()
        
        
        if student:
            name, gender, education_level, military_service, gpa, credits, major, status = student
            gender_str = "مرد" if gender == 1 else "زن"
            
            military_service_str = "انجام شده" if military_service == 1 else "انجام نشده" if gender == 1 else "اعمال نمیشود"
            
            gpa_label = self.get_gpa_label(gpa)
            
            eligible, reason = self.check_graduation_eligibility(student_id)
            
            report = f"""
            گزارش دانشجو برای: {name}
            شماره دانشجویی: {student_id}
            جنسیت: {gender_str}
            مقطع تحصیلی: {self.education_levels.get(education_level, "نامشخص")}
            وضعیت خدمت سربازی: {military_service_str}
            معدل کل: {gpa:.2f} ({gpa_label})
            تعداد واحدهای گذرانده: {credits}
            رشته تحصیلی: {major}
            وضعیت: {status}
            واجد شرایط فارغ التحصیلی: {"بله" if eligible else "خیر"} - {reason}
            
            نمرات دروس:
            """
            
            self.cursor.execute("""
                SELECT c.name, e.grade, e.semester, e.year
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id
                WHERE e.student_id = ?
                ORDER BY e.year DESC, e.semester DESC
            """, (student_id,))
            courses = self.cursor.fetchall()
            
            for course in courses:
                course_name, grade, semester, year = course
                grade_label = self.get_gpa_label(grade) if grade is not None else "ثبت نشده"
                report += f"{course_name}: {grade:.2f if grade is not None else 'N/A'} ({grade_label}) (ترم {semester}، سال {year})\n"
            
            return report
        return "دانشجو یافت نشد."






    def confirm_graduation(self, student_id):
        eligible, reason = self.check_graduation_eligibility(student_id)
        if eligible:
            if self.update_education_level(student_id):
                return "فارغ التحصیلی تایید شد. مقطع تحصیلی به روز شد."
            else:
                return "فارغ التحصیلی تایید شد. مقطع تحصیلی در بالاترین سطح است."
        else:
            return f"امکان تایید فارغ التحصیلی وجود ندارد. {reason}"





    def update_education_level(self, student_id):
        self.cursor.execute("SELECT education_level FROM students WHERE id = ?", (student_id,))
        current_level = self.cursor.fetchone()[0]
        if current_level < 4:  
            self.cursor.execute("UPDATE students SET education_level = ? WHERE id = ?", (current_level + 1, student_id))
            self.conn.commit()
            return True
        return False






    def update_student_status(self, student_id, new_status):
        self.cursor.execute("UPDATE students SET status = ? WHERE id = ?", (new_status, student_id))
        self.conn.commit()





    def add_degree_requirement(self, education_level, major, required_credits, minimum_gpa):
        self.cursor.execute('''
            INSERT OR REPLACE INTO degree_requirements (education_level, major, required_credits, minimum_gpa)
            VALUES (?, ?, ?, ?)
        ''', (education_level, major, required_credits, minimum_gpa))
        self.conn.commit()






    def list_students(self):
        self.cursor.execute("SELECT id, name, major, education_level, gpa FROM students\n")
        students = self.cursor.fetchall()
        if students:
            print("\nلیست دانشجویان:")
            print("\n-----------------------------")
            for student in students:
                student_id, name, major, education_level, gpa = student
                print(f"\nنام: {name} \nشماره دانشجویی: {student_id} \nرشته: {major} \nمقطع: {self.education_levels[education_level]} \nمعدل: {gpa:.2f}")
                print("\n-----------------------------")
        else:
            print("\nهیچ دانشجویی یافت نشد.")






    def list_courses(self):
        self.cursor.execute("SELECT id, name, credits, major FROM courses\n")
        courses = self.cursor.fetchall()
        if courses:
            print("\nلیست دروس:")
            print("\n-----------------------------")
            for course in courses:
                course_id, name, credits, major = course
                print(f"\nکد درس: {course_id} \nنام: {name} \nتعداد واحد: {credits} \nرشته: {major}")
                print("\n-----------------------------")
        else:
            print("\nهیچ درسی یافت نشد.")
            
            
            
            
            
            
            
def get_user_input(prompt):
    while True:
        try:
            user_input = input(prompt)
            if not user_input.strip():
                raise ValueError("\nورودی نمیتواند خالی باشد")
            return user_input
        except Exception as e:
            print(f"خطا: {e}")
            print("\nلطفا دوباره تلاش کنید.")





            
def main():
    expert_system = EducationExpertSystem()

    print("\n" + "=" * 48)
    print("سیستم جامع مقررات آموزشی دانشگاه علامه طباطبایی".center(48))
    print("=" * 48 + "\n")

    while True:
        print("\n" + "╔" + "═" * 46 + "╗")
        print("║" + " سیستم خبره مقررات آموزشی ".center(46) + "║")
        print("╠" + "═" * 46 + "╣")
        
        menu_items = [
            "افزودن دانشجو",
            "افزودن درس",
            "ثبت نام دانشجو در درس",
            "ثبت نمره",
            "بررسی امکان فارغ التحصیلی",
            "تایید فارغ التحصیلی",
            "تولید گزارش دانشجو",
            "به روزرسانی وضعیت دانشجو",
            "افزودن الزامات درجه تحصیلی",
            "نمایش لیست دانشجویان",
            "نمایش لیست دروس",
            "خروج"
        ]

        for i, item in enumerate(menu_items):
            if i == len(menu_items) - 1:
                print("║" + f" 0. {item}".ljust(46) + "║")
            else:
                print("║" + f" {i+1}. {item}".ljust(46) + "║")

        print("╚" + "═" * 46 + "╝")

        choice = get_user_input("\nگزینه مورد نظر را انتخاب کنید: ")

            


        try:
            if choice == "1":
                name = get_user_input("نام دانشجو: ")
                gender = int(get_user_input("جنسیت (1 برای مرد، 2 برای زن): "))
                education_level = int(get_user_input("مقطع تحصیلی (1: دیپلم، 2: کارشناسی، 3: کارشناسی ارشد، 4: دکترا): "))
                if gender == 1:  
                    military_service = int(get_user_input("وضعیت خدمت سربازی (1: انجام شده یا معاف، 0: انجام نشده): "))
                else:  
                    military_service = 1 
                gpa = float(get_user_input("معدل: "))
                credits = int(get_user_input("تعداد واحدهای گذرانده: "))
                major = get_user_input("رشته تحصیلی: ")
                student_id = expert_system.add_student(name, gender, education_level, military_service, gpa, credits, major)
                print(f"دانشجو با شماره دانشجویی {student_id} اضافه شد.")


            elif choice == "2":
                name = get_user_input("نام درس: ")
                credits = int(get_user_input("تعداد واحد: "))
                prerequisite = get_user_input("کد درس پیش نیاز (اگر ندارد، خالی بگذارید): ")
                prerequisite = int(prerequisite) if prerequisite else None
                major = get_user_input("رشته مربوطه: ")
                course_id = expert_system.add_course(name, credits, prerequisite, major)
                print(f"درس با کد {course_id} اضافه شد.")


            elif choice == "3":
                student_id = get_user_input("شماره دانشجویی: ")
                course_id = int(get_user_input("کد درس: "))
                semester = int(get_user_input("شماره ترم: "))
                year = int(get_user_input("سال تحصیلی: "))
                if expert_system.enroll_student(student_id, course_id, semester, year):
                    print("دانشجو با موفقیت در درس ثبت نام شد.")
                else:
                    print("ثبت نام ناموفق بود. لطفا پیش نیازها را بررسی کنید.")


            elif choice == "4":
                student_id = get_user_input("شماره دانشجویی: ")
                course_id = int(get_user_input("کد درس: "))
                grade = float(get_user_input("نمره: "))
                semester = int(get_user_input("شماره ترم: "))
                year = int(get_user_input("سال تحصیلی: "))
                expert_system.update_grade(student_id, course_id, grade, semester, year)
                print("نمره با موفقیت ثبت شد.")


            elif choice == "5":
                student_id = get_user_input("شماره دانشجویی: ")
                eligible, reason = expert_system.check_graduation_eligibility(student_id)
                print(f"وضعیت فارغ التحصیلی: {'واجد شرایط' if eligible else 'غیر واجد شرایط'}")
                print(f"دلیل: {reason}")


            elif choice == "6":
                student_id = get_user_input("شماره دانشجویی: ")
                result = expert_system.confirm_graduation(student_id)
                print(result)


            elif choice == "7":
                student_id = get_user_input("شماره دانشجویی: ")
                report = expert_system.generate_report(student_id)
                print(report)


            elif choice == "8":
                student_id = get_user_input("شماره دانشجویی: ")
                new_status = get_user_input("وضعیت جدید (فعال، مرخصی، اخراج، فارغ التحصیل): ")
                expert_system.update_student_status(student_id, new_status)
                print("وضعیت دانشجو با موفقیت به روز شد.")


            elif choice == "9":
                education_level = int(get_user_input("مقطع تحصیلی (1: دیپلم، 2: کارشناسی، 3: کارشناسی ارشد، 4: دکترا): "))
                major = get_user_input("رشته تحصیلی: ")
                required_credits = int(get_user_input("تعداد واحد مورد نیاز: "))
                minimum_gpa = float(get_user_input("حداقل معدل مورد نیاز: "))
                expert_system.add_degree_requirement(education_level, major, required_credits, minimum_gpa)
                print("الزامات درجه تحصیلی با موفقیت اضافه شد.")


            elif choice == "10":
                expert_system.list_students()


            elif choice == "11":
                expert_system.list_courses()


            elif choice == "0":
                print("خروج از برنامه.")
                break


            else:
                print("گزینه نامعتبر. لطفا دوباره امتحان کنید.")


        except ValueError as e:
            print(f"خطا در ورودی: {e}")
            
            
        except sqlite3.Error as e:
            print(f"خطا در پایگاه داده: {e}")


if __name__ == "__main__":
    main()
    
#Allameh University Educational Expert System