import sys
import os
import mysql.connector
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTabWidget, QTableWidget, QTableWidgetItem,
                             QComboBox, QHeaderView, QMessageBox, QGroupBox, QTimeEdit, QTextEdit, QDialog,
                             QFileDialog, QGridLayout, QCheckBox, QScrollArea, QAbstractItemView, QFormLayout,
                             QDateEdit, QCalendarWidget)
from PyQt5.QtCore import Qt, QDate, QRegExp, QTime
from PyQt5.QtGui import QColor, QIntValidator, QRegExpValidator, QPalette, QIcon


class DatabaseConnection:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host="127.0.0.1",
            port="3306",
            user="admin",
            password="admin",
            database="stomat"
        )
        self.cursor = self.connection.cursor(dictionary=True)


class AddEditServiceDialog(QDialog):
    def __init__(self, service_data=None, parent=None):
        super().__init__(parent)
        self.service_data = service_data
        self.db = DatabaseConnection()
        self.doctors = []
        self.initUI()
        self.load_doctors()

    def load_doctors(self):
        try:
            self.db.cursor.execute("SELECT dent_id, surname_d, name_d, patron_d FROM dentists")
            self.doctors = self.db.cursor.fetchall()
            for doctor in self.doctors:
                doctor_name = f"{doctor['surname_d']} {doctor['name_d']} {doctor['patron_d']}"
                self.doctor_input.addItem(doctor_name, doctor['dent_id'])
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке списка врачей: {str(e)}')

    def initUI(self):
        layout = QGridLayout()
        self.name_input = QLineEdit()
        self.price_input = QLineEdit()
        self.doctor_input = QComboBox()
        self.time_input = QLineEdit()
        price_validator = QIntValidator(1, 99999999)
        self.price_input.setValidator(price_validator)
        time_validator = QIntValidator(1, 999)
        self.time_input.setValidator(time_validator)
        if self.service_data:
            self.name_input.setText(self.service_data['name_serv'])
            self.price_input.setText(str(int(self.service_data['price'])))
            self.time_input.setText(str(self.service_data['exec_time']))
            self.setWindowTitle('Редактировать услугу')
        else:
            self.setWindowTitle('Добавить услугу')
        layout.addWidget(QLabel('Название услуги:'), 0, 0)
        layout.addWidget(self.name_input, 0, 1)
        layout.addWidget(QLabel('Цена:'), 1, 0)
        layout.addWidget(self.price_input, 1, 1)
        layout.addWidget(QLabel('Врач:'), 2, 0)
        layout.addWidget(self.doctor_input, 2, 1)
        layout.addWidget(QLabel('Время выполнения (мин.):'), 3, 0)
        layout.addWidget(self.time_input, 3, 1)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('Сохранить')
        cancel_btn = QPushButton('Отмена')
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 4, 0, 1, 2)
        self.setLayout(layout)

    def validate_and_accept(self):
        if not all([self.name_input.text(), self.price_input.text(), self.time_input.text()]):
            QMessageBox.warning(self, 'Ошибка', 'Заполните все обязательные поля')
            return
        try:
            price = int(self.price_input.text())
            time = int(self.time_input.text())
            if not (1 <= price <= 999999):
                raise ValueError("Invalid price range")
            if not (1 <= time <= 999):
                raise ValueError("Invalid time range")
        except ValueError:
            QMessageBox.warning(self, 'Ошибка', 'Проверьте правильность ввода числовых значений')
            return
        self.accept()

    def get_service_data(self):
        return {
            'name_serv': self.name_input.text().strip(),
            'price': int(self.price_input.text()),
            'dent': self.doctor_input.currentData(),
            'exec_time': int(self.time_input.text())
        }

    def closeEvent(self, event):
        self.db.connection.close()
        super().closeEvent(event)


class ServiceManagementTab(QWidget):
    def __init__(self, doctors, parent=None):
        super().__init__(parent)
        self.doctors = doctors
        self.db = DatabaseConnection()
        self.initUI()
        self.load_services()

    def initUI(self):
        layout = QVBoxLayout()
        self.service_table = QTableWidget()
        self.service_table.setColumnCount(4)
        self.service_table.setHorizontalHeaderLabels(['Наименование', 'Цена', 'Врач', 'Время выполнения (мин.)'])
        header = self.service_table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.service_table.setColumnWidth(1, 100)
        self.service_table.setColumnWidth(3, 150)
        self.service_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.service_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton('Добавить')
        edit_btn = QPushButton('Редактировать')
        delete_btn = QPushButton('Удалить')
        add_btn.clicked.connect(self.add_service)
        edit_btn.clicked.connect(self.edit_service)
        delete_btn.clicked.connect(self.delete_service)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        layout.addWidget(QLabel('Список услуг'))
        layout.addWidget(self.service_table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_services(self):
        try:
            self.db.cursor.execute("""
                SELECT s.serv_id, s.name_serv, s.price, s.exec_time, 
                       d.surname_d, d.name_d, d.patron_d, s.dent
                FROM services s
                JOIN dentists d ON s.dent = d.dent_id
                ORDER BY s.name_serv
            """)
            services = self.db.cursor.fetchall()
            self.service_table.setRowCount(len(services))
            for row, service in enumerate(services):
                doctor_name = f"{service['surname_d']} {service['name_d']} {service['patron_d']}"
                self.service_table.setItem(row, 0, QTableWidgetItem(service['name_serv']))
                self.service_table.setItem(row, 1, QTableWidgetItem(str(service['price'])))
                self.service_table.setItem(row, 2, QTableWidgetItem(doctor_name))
                self.service_table.setItem(row, 3, QTableWidgetItem(str(service['exec_time'])))

                self.service_table.item(row, 0).setData(Qt.UserRole, {
                    'serv_id': service['serv_id'],
                    'dent': service['dent']
                })
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке услуг: {str(e)}')

    def add_service(self):
        dialog = AddEditServiceDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            service_data = dialog.get_service_data()
            if service_data:
                try:
                    self.db.cursor.execute("""
                        INSERT INTO services (name_serv, dent, price, exec_time)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        service_data['name_serv'],
                        service_data['dent'],
                        service_data['price'],
                        service_data['exec_time']
                    ))
                    self.db.connection.commit()
                    self.load_services()
                except Exception as e:
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка при добавлении услуги: {str(e)}')

    def edit_service(self):
        current_row = self.service_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите услугу для редактирования')
            return
        service_data = self.service_table.item(current_row, 0).data(Qt.UserRole)
        service_data.update({
            'name_serv': self.service_table.item(current_row, 0).text(),
            'price': float(self.service_table.item(current_row, 1).text()),
            'exec_time': int(self.service_table.item(current_row, 3).text())
        })
        dialog = AddEditServiceDialog(service_data, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_service_data()
            if updated_data:
                try:
                    self.db.cursor.execute("""
                        UPDATE services 
                        SET name_serv = %s, dent = %s, price = %s, exec_time = %s
                        WHERE serv_id = %s
                    """, (
                        updated_data['name_serv'],
                        updated_data['dent'],
                        updated_data['price'],
                        updated_data['exec_time'],
                        service_data['serv_id']
                    ))
                    self.db.connection.commit()
                    self.load_services()
                except Exception as e:
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка при обновлении услуги: {str(e)}')

    def delete_service(self):
        current_row = self.service_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите услугу для удаления')
            return
        service_data = self.service_table.item(current_row, 0).data(Qt.UserRole)
        service_name = self.service_table.item(current_row, 0).text()
        reply = QMessageBox.question(
            self, 'Подтверждение',
            f'Вы уверены, что хотите удалить услугу "{service_name}"?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.db.cursor.execute("DELETE FROM services WHERE serv_id = %s", (service_data['serv_id'],))
                self.db.connection.commit()
                self.load_services()
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при удалении услуги: {str(e)}')


class AddEditDoctorDialog(QDialog):
    def __init__(self, doctor_data=None, parent=None):
        super().__init__(parent)
        self.doctor_data = doctor_data
        self.db = DatabaseConnection()
        self.specialties = {}
        self.initUI()

    def load_specialties(self):
        try:
            self.db.cursor.execute("SELECT id_special, name_sp FROM Special")
            specialties = self.db.cursor.fetchall()
            self.specialties = {spec['name_sp']: spec['id_special'] for spec in specialties}
            self.special_input.clear()
            self.special_input.addItems(self.specialties.keys())
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке специальностей: {str(e)}')

    def initUI(self):
        layout = QGridLayout()
        self.surname_d_input = QLineEdit()
        self.name_d_input = QLineEdit()
        self.patron_d_input = QLineEdit()
        self.special_input = QComboBox()
        self.exper_input = QLineEdit()
        self.num_cab_input = QLineEdit()
        self.load_specialties()
        name_validator = QRegExpValidator(QRegExp("[А-Яа-яЁё-]+"))
        self.surname_d_input.setValidator(name_validator)
        self.name_d_input.setValidator(name_validator)
        self.patron_d_input.setValidator(name_validator)
        exper_validator = QIntValidator(0, 99)
        self.exper_input.setValidator(exper_validator)
        cab_validator = QIntValidator(1, 999)
        self.num_cab_input.setValidator(cab_validator)
        if self.doctor_data:
            self.surname_d_input.setText(self.doctor_data['surname_d'])
            self.name_d_input.setText(self.doctor_data['name_d'])
            self.patron_d_input.setText(self.doctor_data['patron_d'])
            try:
                specialty_name = self.doctor_data.get('specialty_name')
                if specialty_name:
                    index = self.special_input.findText(specialty_name)
                    if index >= 0:
                        self.special_input.setCurrentIndex(index)
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке специальности врача: {str(e)}')
            self.exper_input.setText(str(self.doctor_data['exper']))
            self.num_cab_input.setText(str(self.doctor_data['num_cab']))
            self.setWindowTitle('Редактировать врача')
        else:
            self.setWindowTitle('Добавить врача')
        layout.addWidget(QLabel('Фамилия:'), 0, 0)
        layout.addWidget(self.surname_d_input, 0, 1)
        layout.addWidget(QLabel('Имя:'), 1, 0)
        layout.addWidget(self.name_d_input, 1, 1)
        layout.addWidget(QLabel('Отчество:'), 2, 0)
        layout.addWidget(self.patron_d_input, 2, 1)
        layout.addWidget(QLabel('Специальность:'), 3, 0)
        layout.addWidget(self.special_input, 3, 1)
        layout.addWidget(QLabel('Стаж (лет):'), 4, 0)
        layout.addWidget(self.exper_input, 4, 1)
        layout.addWidget(QLabel('Кабинет:'), 5, 0)
        layout.addWidget(self.num_cab_input, 5, 1)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('Сохранить')
        cancel_btn = QPushButton('Отмена')
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 6, 0, 1, 2)
        self.setLayout(layout)

    def validate_and_accept(self):
        if not all([
            self.surname_d_input.text(),
            self.name_d_input.text(),
            self.special_input.currentText(),
            self.exper_input.text(),
            self.num_cab_input.text()
        ]):
            QMessageBox.warning(self, 'Ошибка', 'Заполните все обязательные поля')
            return
        try:
            exper = int(self.exper_input.text())
            num_cab = int(self.num_cab_input.text())
            if not (0 <= exper <= 99):
                raise ValueError("Invalid experience range")
            if not (1 <= num_cab <= 999):
                raise ValueError("Invalid cabinet number range")
        except ValueError:
            QMessageBox.warning(self, 'Ошибка', 'Проверьте правильность ввода числовых значений')
            return
        self.accept()

    def get_doctor_data(self):
        specialty_name = self.special_input.currentText()
        specialty_id = self.specialties.get(specialty_name)
        return {
            'surname_d': self.surname_d_input.text(),
            'name_d': self.name_d_input.text(),
            'patron_d': self.patron_d_input.text(),
            'special': specialty_id,
            'exper': int(self.exper_input.text()),
            'num_cab': int(self.num_cab_input.text())
        }


class DoctorManagementTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.doctors = []
        self.setupUI()
        self.load_doctors()

    def setupUI(self):
        main_layout = QVBoxLayout(self)
        self.doctor_table = QTableWidget()
        self.doctor_table.setColumnCount(6)
        self.doctor_table.setHorizontalHeaderLabels(['Фамилия', 'Имя', 'Отчество', 'Специальность', 'Стаж (лет)',
                                                     'Кабинет'])
        self.doctor_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.doctor_table.setSelectionMode(QTableWidget.SingleSelection)
        self.doctor_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.doctor_table.hideColumn(6)
        header = self.doctor_table.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        button_layout = QHBoxLayout()
        add_button = QPushButton('Добавить')
        edit_button = QPushButton('Редактировать')
        delete_button = QPushButton('Удалить')
        add_button.clicked.connect(self.add_doctor)
        edit_button.clicked.connect(self.edit_doctor)
        delete_button.clicked.connect(self.delete_doctor)
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        main_layout.addWidget(QLabel('Список врачей'))
        main_layout.addWidget(self.doctor_table)
        main_layout.addLayout(button_layout)

    def load_doctors(self):
        try:
            self.doctor_table.setRowCount(0)
            query = """
            SELECT d.*, s.name_sp as specialty_name 
            FROM Dentists d
            JOIN Special s ON d.special = s.id_special
            ORDER BY d.surname_d, d.name_d
            """
            self.db.cursor.execute(query)
            self.doctors = self.db.cursor.fetchall()
            for row, doctor in enumerate(self.doctors):
                self.doctor_table.insertRow(row)
                self.doctor_table.setItem(row, 0, QTableWidgetItem(str(doctor['surname_d'])))
                self.doctor_table.setItem(row, 1, QTableWidgetItem(str(doctor['name_d'])))
                self.doctor_table.setItem(row, 2, QTableWidgetItem(str(doctor['patron_d'])))
                self.doctor_table.setItem(row, 3, QTableWidgetItem(str(doctor['specialty_name'])))
                self.doctor_table.setItem(row, 4, QTableWidgetItem(str(doctor['exper'])))
                self.doctor_table.setItem(row, 5, QTableWidgetItem(str(doctor['num_cab'])))
                self.doctor_table.setItem(row, 6, QTableWidgetItem(str(doctor['dent_id'])))
        except Exception as e:
            print(f"Ошибка при загрузке данных: {str(e)}")
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке данных: {str(e)}')

    def add_doctor(self):
        dialog = AddEditDoctorDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                doctor_data = dialog.get_doctor_data()
                query = """
                INSERT INTO Dentists (surname_d, name_d, patron_d, special, exper, num_cab)
                VALUES (%(surname_d)s, %(name_d)s, %(patron_d)s, %(special)s, %(exper)s, %(num_cab)s)
                """
                self.db.cursor.execute(query, doctor_data)
                self.db.connection.commit()
                self.load_doctors()
            except Exception as e:
                self.db.connection.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при добавлении врача: {str(e)}')

    def edit_doctor(self):
        current_row = self.doctor_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите врача для редактирования')
            return
        dialog = AddEditDoctorDialog(self.doctors[current_row], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                doctor_data = dialog.get_doctor_data()
                doctor_data['dent_id'] = self.doctors[current_row]['dent_id']
                query = """
                UPDATE Dentists
                SET surname_d=%(surname_d)s, name_d=%(name_d)s, patron_d=%(patron_d)s,
                    special=%(special)s, exper=%(exper)s, num_cab=%(num_cab)s
                WHERE dent_id=%(dent_id)s
                """
                self.db.cursor.execute(query, doctor_data)
                self.db.connection.commit()
                self.load_doctors()
                QMessageBox.information(self, 'Успех', 'Данные врача успешно обновлены')
            except Exception as e:
                self.db.connection.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при обновлении данных врача: {str(e)}')

    def delete_doctor(self):
        current_row = self.doctor_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите врача для удаления')
            return
        doctor = self.doctors[current_row]
        reply = QMessageBox.question(
            self, 'Подтверждение',
            f'Вы уверены, что хотите удалить врача "{doctor["surname_d"]} {doctor["name_d"]} {doctor["patron_d"]}"?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.db.cursor.execute("DELETE FROM Dentists WHERE dent_id = %s", (doctor['dent_id'],))
                self.db.connection.commit()
                self.load_doctors()
            except Exception as e:
                self.db.connection.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при удалении врача: {str(e)}')

    def closeEvent(self, event):
        if hasattr(self, 'db'):
            self.db.connection.close()
        super().closeEvent(event)


class DoctorScheduleCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.selected_doctor = None
        self.appointments_by_date = {}
        self.clicked.connect(self.show_day_appointments)

    def set_doctor(self, doctor_id, appointments):
        self.selected_doctor = doctor_id
        self.appointments_by_date = appointments if appointments else {}
        self.updateCells()

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        if self.selected_doctor:
            date_str = date.toString(Qt.ISODate)
            if date_str in self.appointments_by_date:
                painter.save()
                painter.setPen(Qt.blue)
                painter.setBrush(QColor(200, 220, 255, 100))
                painter.drawRect(rect.adjusted(1, 1, -1, -1))
                painter.restore()

    def show_day_appointments(self, date):
        date_str = date.toString(Qt.ISODate)
        if not self.selected_doctor:
            QMessageBox.warning(self, "Ошибка", "Врач не выбран")
            return
        if date_str not in self.appointments_by_date:
            QMessageBox.information(self, "Расписание", "Нет записей на эту дату")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Записи на {date.toString('dd.MM.yyyy')}")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout()
        appointments_list = QTextEdit()
        appointments_list.setReadOnly(True)
        text = ""
        for i, appointment in enumerate(self.appointments_by_date[date_str], 1):
            text += f"Запись {i}:\n"
            text += f"Время: {appointment['time']}\n"
            text += f"Пациент: {appointment['patient']}\n"
            text += f"Услуги: {appointment['services']}\n\n"
        appointments_list.setText(text)
        layout.addWidget(appointments_list)
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        dialog.setLayout(layout)
        dialog.exec_()


class AppointmentTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.selected_date = None
        self.selected_patient = None
        self.selected_services = []
        self.selected_doctor = None
        self.selected_appointment_id = None
        self.initUI()
        self.load_initial_data()

    def initUI(self):
        main_layout = QHBoxLayout()
        calendar_widget = QWidget()
        calendar_layout = QVBoxLayout()
        calendar_layout.setContentsMargins(0, 0, 10, 0)
        appointment_calendar_label = QLabel("Календарь записей")
        calendar_layout.addWidget(appointment_calendar_label)
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.clicked.connect(self.update_appointments_table)
        calendar_layout.addWidget(self.calendar)
        doctor_schedule_label = QLabel("Расписание врача")
        calendar_layout.addWidget(doctor_schedule_label)
        self.doctor_schedule_calendar = DoctorScheduleCalendar()
        calendar_layout.addWidget(self.doctor_schedule_calendar)
        calendar_widget.setLayout(calendar_layout)
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        form_widget = QWidget()
        form_layout = QFormLayout()
        self.patient_combo = QComboBox()
        form_layout.addRow("Выберите пациента:", self.patient_combo)
        services_group = QGroupBox("Выберите услуги:")
        services_layout = QVBoxLayout()
        services_scroll = QScrollArea()
        services_scroll.setWidgetResizable(True)
        services_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        services_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.services_container = QWidget()
        self.services_layout = QVBoxLayout(self.services_container)
        self.services_layout.setSpacing(5)
        self.services_layout.setContentsMargins(5, 5, 5, 5)
        self.services_checkboxes = []
        self.service_data = {}
        services_scroll.setWidget(self.services_container)
        services_scroll.setMinimumHeight(150)
        services_layout.addWidget(services_scroll)
        services_group.setLayout(services_layout)
        form_layout.addRow(services_group)
        self.doctor_combo = QComboBox()
        form_layout.addRow("Выберите врача:", self.doctor_combo)
        time_widget = QWidget()
        time_layout = QHBoxLayout()
        self.start_time = QTimeEdit()
        self.end_time = QTimeEdit()
        min_time = QTime(8, 0)
        max_time = QTime(20, 0)
        self.start_time.setTimeRange(min_time, max_time)
        self.end_time.setTimeRange(min_time, max_time)
        self.start_time.setDisplayFormat("HH:mm")
        self.end_time.setDisplayFormat("HH:mm")
        self.start_time.setTime(min_time)
        self.end_time.setTime(max_time)
        time_layout.addWidget(QLabel("Начало:"))
        time_layout.addWidget(self.start_time)
        time_layout.addWidget(QLabel("Конец:"))
        time_layout.addWidget(self.end_time)
        time_widget.setLayout(time_layout)
        form_layout.addRow("Выберите время:", time_widget)
        form_widget.setLayout(form_layout)
        right_layout.addWidget(form_widget)
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(7)
        self.appointments_table.setHorizontalHeaderLabels(['Пациент', 'Врач', 'Кабинет', 'Услуги', 'Время начала',
                                                           'Время конца', 'Итоговая сумма'])
        self.appointments_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.appointments_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.appointments_table.itemClicked.connect(self.select_appointment)
        right_layout.addWidget(QLabel("Записи на выбранную дату:"))
        right_layout.addWidget(self.appointments_table)
        button_layout = QHBoxLayout()
        self.book_btn = QPushButton("Записать")
        self.cancel_btn = QPushButton("Отменить")
        self.change_btn = QPushButton("Изменить")
        self.book_btn.clicked.connect(self.book_appointment)
        self.cancel_btn.clicked.connect(self.cancel_appointment)
        self.change_btn.clicked.connect(self.change_appointment)
        button_layout.addWidget(self.book_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.change_btn)
        right_layout.addLayout(button_layout)
        right_widget.setLayout(right_layout)
        main_layout.addWidget(calendar_widget, 1)
        main_layout.addWidget(right_widget, 2)
        self.setLayout(main_layout)

    def load_initial_data(self):
        self.load_patients()
        self.load_doctors()
        self.load_services()
        self.update_appointments_table()

    def load_patients(self):
        try:
            self.patient_combo.clear()
            query = """
                SELECT snils_id, CONCAT(surname_p, ' ', name_p, ' ', patron_p, ' (', snils_id, ')') as full_name
                FROM patients
                ORDER BY surname_p, name_p
            """
            self.db.cursor.execute(query)
            patients = self.db.cursor.fetchall()
            self.patient_data = {}
            for patient in patients:
                self.patient_combo.addItem(patient['full_name'])
                self.patient_data[patient['full_name']] = patient['snils_id']
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки пациентов: {str(e)}")

    def on_doctor_changed(self, index):
        doctor_name = self.doctor_combo.currentText()
        if doctor_name in self.doctor_data:
            doctor_id = self.doctor_data[doctor_name]
            try:
                query = """
                    SELECT 
                        a.date,
                        TIME_FORMAT(a.time_s, '%H:%i') as start_time,
                        TIME_FORMAT(a.time_e, '%H:%i') as end_time,
                        CONCAT(p.surname_p, ' ', p.name_p) as patient_name,
                        GROUP_CONCAT(s.name_serv SEPARATOR ', ') as services
                    FROM Appointment a
                    JOIN patients p ON a.snils = p.snils_id
                    JOIN App_serv aps ON a.appoint_id = aps.Appoint_id
                    JOIN services s ON aps.Serv_id = s.serv_id
                    WHERE a.dent_id = %s
                    GROUP BY a.appoint_id, a.date, a.time_s, a.time_e, p.surname_p, p.name_p
                    ORDER BY a.date, a.time_s
                """
                self.db.cursor.execute(query, (doctor_id,))
                appointments = self.db.cursor.fetchall()
                appointments_by_date = {}
                for appointment in appointments:
                    date_str = appointment['date'].strftime('%Y-%m-%d')
                    if date_str not in appointments_by_date:
                        appointments_by_date[date_str] = []
                    appointments_by_date[date_str].append({
                        'time': f"{appointment['start_time']} - {appointment['end_time']}",
                        'patient': appointment['patient_name'],
                        'services': appointment['services']
                    })

                self.doctor_schedule_calendar.set_doctor(doctor_id, appointments_by_date)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки расписания: {str(e)}")
                self.doctor_schedule_calendar.set_doctor(None, {})

    def load_doctors(self):
        try:
            self.doctor_combo.clear()
            query = """
                SELECT dent_id, CONCAT(surname_d, ' ', name_d, ' ', patron_d) as full_name
                FROM dentists
                ORDER BY surname_d, name_d
            """
            self.db.cursor.execute(query)
            doctors = self.db.cursor.fetchall()
            self.doctor_data = {}
            for doctor in doctors:
                self.doctor_combo.addItem(doctor['full_name'])
                self.doctor_data[doctor['full_name']] = doctor['dent_id']
            if self.doctor_combo.count() > 0:
                self.doctor_combo.setCurrentIndex(0)
                self.on_doctor_changed(0)
            self.doctor_combo.currentIndexChanged.connect(self.on_doctor_changed)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки врачей: {str(e)}")

    def load_services(self):
        try:
            query = """
                SELECT serv_id, name_serv
                FROM services
                ORDER BY name_serv
            """
            self.db.cursor.execute(query)
            services = self.db.cursor.fetchall()
            for checkbox in self.services_checkboxes:
                self.services_layout.removeWidget(checkbox)
                checkbox.deleteLater()
            self.services_checkboxes.clear()
            self.service_data.clear()
            for service in services:
                checkbox = QCheckBox(service['name_serv'])
                self.services_checkboxes.append(checkbox)
                self.services_layout.addWidget(checkbox)
                self.service_data[service['name_serv']] = service['serv_id']
            self.services_layout.addStretch()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки услуг: {str(e)}")

    def get_selected_services(self):
        return [cb.text() for cb in self.services_checkboxes if cb.isChecked()]

    def validate_services(self):
        selected_services = self.get_selected_services()
        if not selected_services:
            QMessageBox.warning(self, "Ошибка", "Необходимо выбрать хотя бы одну услугу")
            return False, 0

        total_sum = self.calculate_total_sum(selected_services)
        if total_sum <= 0:
            QMessageBox.warning(self, "Ошибка", "Ошибка расчета суммы услуг")
            return False, 0

        return True, total_sum

    def update_appointments_table(self):
        try:
            self.selected_date = self.calendar.selectedDate().toString(Qt.ISODate)
            self.appointments_table.setRowCount(0)
            query = """
                   SELECT 
                       CONCAT(p.surname_p, ' ', p.name_p, ' ', p.patron_p) as patient_name,
                       CONCAT(d.surname_d, ' ', d.name_d, ' ', d.patron_d) as doctor_name,
                       d.num_cab as cabinet,
                       GROUP_CONCAT(s.name_serv SEPARATOR ', ') as services,
                       TIME_FORMAT(a.time_s, '%H:%i') as start_time,
                       TIME_FORMAT(a.time_e, '%H:%i') as end_time,
                       a.sum as total_sum,
                       a.appoint_id
                   FROM Appointment a
                   JOIN patients p ON a.snils = p.snils_id
                   JOIN dentists d ON a.dent_id = d.dent_id
                   JOIN App_serv aps ON a.appoint_id = aps.Appoint_id
                   JOIN services s ON aps.Serv_id = s.serv_id
                   WHERE a.date = %s
                   GROUP BY a.appoint_id, p.surname_p, p.name_p, p.patron_p,
                            d.surname_d, d.name_d, d.patron_d, d.num_cab, a.time_s, a.time_e, a.sum
                   ORDER BY a.time_s
               """
            self.db.cursor.execute(query, (self.selected_date,))
            appointments = self.db.cursor.fetchall()
            self.appointment_ids = {}
            for row, appointment in enumerate(appointments):
                self.appointments_table.insertRow(row)
                self.appointments_table.setItem(row, 0, QTableWidgetItem(appointment['patient_name']))
                self.appointments_table.setItem(row, 1, QTableWidgetItem(appointment['doctor_name']))
                self.appointments_table.setItem(row, 2, QTableWidgetItem(str(appointment['cabinet'])))
                self.appointments_table.setItem(row, 3, QTableWidgetItem(appointment['services']))
                self.appointments_table.setItem(row, 4, QTableWidgetItem(appointment['start_time']))
                self.appointments_table.setItem(row, 5, QTableWidgetItem(appointment['end_time']))
                self.appointments_table.setItem(row, 6, QTableWidgetItem(str(appointment['total_sum'])))
                self.appointment_ids[row] = appointment['appoint_id']
            self.appointments_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления таблицы записей: {str(e)}")

    def calculate_total_sum(self, selected_services):
        try:
            services_list = ', '.join(['%s' for _ in selected_services])
            query = f"""
                SELECT SUM(price) as total
                FROM services
                WHERE name_serv IN ({services_list})
            """
            self.db.cursor.execute(query, selected_services)
            result = self.db.cursor.fetchone()
            return result['total'] if result['total'] else 0
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка расчета суммы: {str(e)}")
            return 0

    def get_doctor_cabinet(self, doctor_name):
        try:
            query = "SELECT num_cab FROM dentists WHERE dent_id = %s"
            self.db.cursor.execute(query, (self.doctor_data[doctor_name],))
            result = self.db.cursor.fetchone()
            return result['num_cab'] if result else None
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка получения кабинета: {str(e)}")
            return None

    def book_appointment(self):
        try:
            # Validate services first
            is_valid, total_sum = self.validate_services()
            if not is_valid:
                return

            current_patient = self.patient_combo.currentText()
            current_doctor = self.doctor_combo.currentText()
            selected_services = self.get_selected_services()
            start_time = self.start_time.time().toString("HH:mm")
            end_time = self.end_time.time().toString("HH:mm")
            cabinet = self.get_doctor_cabinet(current_doctor)

            query = """
                SELECT COUNT(*) as count
                FROM Appointment
                WHERE dent_id = %s AND date = %s AND (
                    (time_s < %s AND time_e > %s) OR
                    (time_s >= %s AND time_s < %s)
                )
            """
            self.db.cursor.execute(query, (
                self.doctor_data[current_doctor],
                self.selected_date,
                end_time, start_time,
                start_time, end_time
            ))
            conflict_result = self.db.cursor.fetchone()
            if conflict_result['count'] > 0:
                QMessageBox.warning(self, "Ошибка", "На это время уже есть запись для выбранного врача.")
                return

            query = """
                INSERT INTO Appointment (dent_id, snils, time_s, time_e, num_cab, date, sum)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.db.cursor.execute(query, (
                self.doctor_data[current_doctor],
                self.patient_data[current_patient],
                start_time,
                end_time,
                cabinet,
                self.selected_date,
                total_sum
            ))
            appointment_id = self.db.cursor.lastrowid

            for service_name in selected_services:
                query = """
                    INSERT INTO App_serv (Serv_id, Appoint_id)
                    VALUES (%s, %s)
                """
                self.db.cursor.execute(query, (self.service_data[service_name], appointment_id))

            self.db.connection.commit()
            self.update_appointments_table()
            QMessageBox.information(self, "Успех", "Запись успешно создана")

        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка создания записи: {str(e)}")

    def change_appointment(self):
        try:
            if not self.selected_appointment_id:
                QMessageBox.warning(self, "Ошибка", "Выберите запись для изменения")
                return

            # Validate services first
            is_valid, total_sum = self.validate_services()
            if not is_valid:
                return

            current_patient = self.patient_combo.currentText()
            current_doctor = self.doctor_combo.currentText()
            selected_services = self.get_selected_services()
            start_time = self.start_time.time().toString("HH:mm")
            end_time = self.end_time.time().toString("HH:mm")
            cabinet = self.get_doctor_cabinet(current_doctor)

            # Check for time conflicts with other appointments
            query = """
                SELECT COUNT(*) as count
                FROM Appointment
                WHERE dent_id = %s 
                AND date = %s 
                AND appoint_id != %s 
                AND (
                    (time_s < %s AND time_e > %s) OR
                    (time_s >= %s AND time_s < %s)
                )
            """
            self.db.cursor.execute(query, (
                self.doctor_data[current_doctor],
                self.selected_date,
                self.selected_appointment_id,
                end_time, start_time,
                start_time, end_time
            ))
            conflict_result = self.db.cursor.fetchone()
            if conflict_result['count'] > 0:
                QMessageBox.warning(self, "Ошибка", "На это время уже есть запись для выбранного врача.")
                return

            query = """
                UPDATE Appointment 
                SET dent_id = %s,
                    snils = %s,
                    time_s = %s,
                    time_e = %s,
                    num_cab = %s,
                    date = %s,
                    sum = %s
                WHERE appoint_id = %s
            """
            self.db.cursor.execute(query, (
                self.doctor_data[current_doctor],
                self.patient_data[current_patient],
                start_time,
                end_time,
                cabinet,
                self.selected_date,
                total_sum,
                self.selected_appointment_id
            ))

            self.db.cursor.execute("DELETE FROM App_serv WHERE Appoint_id = %s",
                                   (self.selected_appointment_id,))

            for service_name in selected_services:
                query = """
                    INSERT INTO App_serv (Serv_id, Appoint_id)
                    VALUES (%s, %s)
                """
                self.db.cursor.execute(query, (self.service_data[service_name], self.selected_appointment_id))

            self.db.connection.commit()
            self.update_appointments_table()
            self.selected_appointment_id = None
            QMessageBox.information(self, "Успех", "Запись успешно изменена")

        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка изменения записи: {str(e)}")

    def cancel_appointment(self):
        try:
            if not self.selected_appointment_id:
                QMessageBox.warning(self, "Ошибка", "Выберите запись для отмены")
                return
            reply = QMessageBox.question(self, 'Подтверждение',
                                         'Вы уверены, что хотите отменить эту запись?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                query = "DELETE FROM App_serv WHERE Appoint_id = %s"
                self.db.cursor.execute(query, (self.selected_appointment_id,))
                query = "DELETE FROM Appointment WHERE appoint_id = %s"
                self.db.cursor.execute(query, (self.selected_appointment_id,))
                self.db.connection.commit()
                self.update_appointments_table()
                self.selected_appointment_id = None
                QMessageBox.information(self, "Успех", "Запись успешно отменена")
        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка отмены записи: {str(e)}")

    def select_appointment(self, item):
        row = item.row()
        self.selected_appointment_id = self.appointment_ids.get(row)
        if self.selected_appointment_id is None:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить ID записи")


class PatientDialog(QDialog):
    def __init__(self, patient_data=None, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.setWindowTitle("Пациент")
        self.setModal(True)
        layout = QGridLayout()
        self.snils_input = QLineEdit()
        self.surname_input = QLineEdit()
        self.name_input = QLineEdit()
        self.patronymic_input = QLineEdit()
        self.birthdate_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.gender_input = QComboBox()
        self.gender_input.addItems(['М', 'Ж'])
        snils_validator = QRegExpValidator(QRegExp(r'\d{3}-\d{3}-\d{3} \d{2}'))
        self.snils_input.setValidator(snils_validator)
        self.snils_input.setInputMask("999-999-999 99")
        self.birthdate_input.setInputMask("99.99.9999")
        self.phone_input.setInputMask("+7 (999) 999-99-99")
        if patient_data:
            self.snils_input.setText(patient_data['snils_id'])
            self.surname_input.setText(patient_data['surname_p'])
            self.name_input.setText(patient_data['name_p'])
            self.patronymic_input.setText(patient_data['patron_p'])
            self.birthdate_input.setText(patient_data['birthday'])
            self.phone_input.setText(patient_data['phone'])
            self.gender_input.setCurrentText(patient_data['gender'])
        layout.addWidget(QLabel("СНИЛС:"), 0, 0)
        layout.addWidget(self.snils_input, 0, 1)
        layout.addWidget(QLabel("Фамилия:"), 1, 0)
        layout.addWidget(self.surname_input, 1, 1)
        layout.addWidget(QLabel("Имя:"), 2, 0)
        layout.addWidget(self.name_input, 2, 1)
        layout.addWidget(QLabel("Отчество:"), 3, 0)
        layout.addWidget(self.patronymic_input, 3, 1)
        layout.addWidget(QLabel("Дата рождения:"), 4, 0)
        layout.addWidget(self.birthdate_input, 4, 1)
        layout.addWidget(QLabel("Телефон:"), 5, 0)
        layout.addWidget(self.phone_input, 5, 1)
        layout.addWidget(QLabel("Пол:"), 6, 0)
        layout.addWidget(self.gender_input, 6, 1)
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.validate_and_accept)
        cancel_button = QPushButton("Отменить")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout, 7, 0, 1, 3)
        self.setLayout(layout)

    def validate_and_accept(self):
        if not all([self.snils_input.text().strip(),
                    self.surname_input.text().strip(),
                    self.name_input.text().strip(),
                    self.birthdate_input.text().strip(),
                    self.phone_input.text().strip()]):
            QMessageBox.warning(self, "Ошибка", "Все поля, кроме отчества, обязательны для заполнения!")
            return
        snils = self.snils_input.text().replace(" ", "").replace("-", "")
        if len(snils) != 11:
            QMessageBox.warning(self, "Ошибка", "Неверный формат СНИЛС!")
            return
        try:
            day, month, year = map(int, self.birthdate_input.text().split('.'))
            if not (1900 <= year <= 2024 and 1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Неверная дата рождения!")
            return
        self.accept()

    def get_patient_data(self):
        return {
            'snils_id': self.snils_input.text(),
            'surname_p': self.surname_input.text(),
            'name_p': self.name_input.text(),
            'patron_p': self.patronymic_input.text(),
            'birthday': self.birthdate_input.text(),
            'phone': self.phone_input.text(),
            'gender': self.gender_input.currentText()
        }


class PatientManagementTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
        self.initUI()
        self.load_patients()

    def initUI(self):
        layout = QVBoxLayout()
        self.patient_table = QTableWidget(0, 7)
        self.patient_table.setHorizontalHeaderLabels(['СНИЛС', 'Фамилия', 'Имя', 'Отчество', 'Дата рождения', 'Телефон',
                                                      'Пол'])
        self.patient_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.patient_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.patient_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        add_patient_button = QPushButton('Добавить пациента')
        add_patient_button.clicked.connect(self.add_patient)
        edit_patient_button = QPushButton('Редактировать пациента')
        edit_patient_button.clicked.connect(self.edit_patient)
        remove_patient_button = QPushButton('Удалить пациента')
        remove_patient_button.clicked.connect(self.remove_patient)
        layout.addWidget(QLabel('Список пациентов'))
        layout.addWidget(self.patient_table)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(add_patient_button)
        buttons_layout.addWidget(edit_patient_button)
        buttons_layout.addWidget(remove_patient_button)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def load_patients(self):
        try:
            self.db.cursor.execute("""
                SELECT snils_id, surname_p, name_p, patron_p, 
                       DATE_FORMAT(birthday, '%d.%m.%Y') as birthday, 
                       phone, gender 
                FROM Patients
            """)
            patients = self.db.cursor.fetchall()
            self.patient_table.setRowCount(0)
            for patient in patients:
                row = self.patient_table.rowCount()
                self.patient_table.insertRow(row)
                self.patient_table.setItem(row, 0, QTableWidgetItem(patient['snils_id']))
                self.patient_table.setItem(row, 1, QTableWidgetItem(patient['surname_p']))
                self.patient_table.setItem(row, 2, QTableWidgetItem(patient['name_p']))
                self.patient_table.setItem(row, 3, QTableWidgetItem(patient['patron_p']))
                self.patient_table.setItem(row, 4, QTableWidgetItem(patient['birthday']))
                self.patient_table.setItem(row, 5, QTableWidgetItem(patient['phone']))
                self.patient_table.setItem(row, 6, QTableWidgetItem(patient['gender']))
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке данных: {str(e)}')

    def add_patient(self):
        dialog = PatientDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            patient_data = dialog.get_patient_data()
            try:
                self.db.cursor.execute("""
                    INSERT INTO Patients (snils_id, surname_p, name_p, patron_p, birthday, phone, gender)
                    VALUES (%s, %s, %s, %s, STR_TO_DATE(%s, '%d.%m.%Y'), %s, %s)
                """, (
                    patient_data['snils_id'],
                    patient_data['surname_p'],
                    patient_data['name_p'],
                    patient_data['patron_p'],
                    patient_data['birthday'],
                    patient_data['phone'],
                    patient_data['gender']
                ))
                self.db.connection.commit()
                self.load_patients()
            except Exception as e:
                self.db.connection.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при добавлении пациента: {str(e)}')

    def edit_patient(self):
        current_row = self.patient_table.currentRow()
        if current_row >= 0:
            patient_data = {
                'snils_id': self.patient_table.item(current_row, 0).text(),
                'surname_p': self.patient_table.item(current_row, 1).text(),
                'name_p': self.patient_table.item(current_row, 2).text(),
                'patron_p': self.patient_table.item(current_row, 3).text(),
                'birthday': self.patient_table.item(current_row, 4).text(),
                'phone': self.patient_table.item(current_row, 5).text(),
                'gender': 'М'
            }
            dialog = PatientDialog(patient_data, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                new_patient_data = dialog.get_patient_data()
                try:
                    self.db.cursor.execute("""
                        UPDATE Patients 
                        SET surname_p = %s, name_p = %s, patron_p = %s, birthday = STR_TO_DATE(%s, '%d.%m.%Y'),
                            phone = %s, gender = %s
                        WHERE snils_id = %s
                    """, (
                        new_patient_data['surname_p'],
                        new_patient_data['name_p'],
                        new_patient_data['patron_p'],
                        new_patient_data['birthday'],
                        new_patient_data['phone'],
                        new_patient_data['gender'],
                        new_patient_data['snils_id']
                    ))
                    self.db.connection.commit()
                    self.load_patients()
                except Exception as e:
                    self.db.connection.rollback()
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка при обновлении данных пациента: {str(e)}')
        else:
            QMessageBox.warning(self, 'Предупреждение', 'Пожалуйста, выберите пациента для редактирования.')

    def remove_patient(self):
        current_row = self.patient_table.currentRow()
        if current_row >= 0:
            snils = self.patient_table.item(current_row, 0).text()
            reply = QMessageBox.question(self, 'Подтверждение',
                                         f'Вы хотите удалить пациента с СНИЛС {snils}?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    self.db.cursor.execute("DELETE FROM Patients WHERE snils_id = %s", (snils,))
                    self.db.connection.commit()
                    self.load_patients()
                except Exception as e:
                    self.db.connection.rollback()
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка при удалении пациента: {str(e)}')
        else:
            QMessageBox.warning(self, 'Предупреждение', 'Пожалуйста, выберите пациента для удаления.')


class ReportingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        period_group = QGroupBox("Отчетный период")
        period_layout = QHBoxLayout()
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.end_date_edit.setDate(QDate.currentDate())
        period_layout.addWidget(QLabel('Период:'))
        period_layout.addWidget(self.start_date_edit)
        period_layout.addWidget(QLabel('-'))
        period_layout.addWidget(self.end_date_edit)
        period_group.setLayout(period_layout)
        report_type_group = QGroupBox("Тип отчета")
        report_type_layout = QVBoxLayout()
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Общий отчет",
            "Отчет по врачам",
            "Отчет по услугам",
            "Отчет по пациентам"
        ])
        report_type_layout.addWidget(self.report_type_combo)
        report_type_group.setLayout(report_type_layout)
        button_layout = QHBoxLayout()
        generate_report_btn = QPushButton('Сформировать отчет')
        generate_report_btn.clicked.connect(self.generate_report)
        save_report_btn = QPushButton('Сохранить отчет')
        save_report_btn.clicked.connect(self.save_report)
        button_layout.addWidget(generate_report_btn)
        button_layout.addWidget(save_report_btn)
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(period_group)
        layout.addWidget(report_type_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel('Результат:'))
        layout.addWidget(self.report_text)
        self.setLayout(layout)

    def generate_report(self):
        try:
            start_date = self.start_date_edit.date().toString(Qt.ISODate)
            end_date = self.end_date_edit.date().toString(Qt.ISODate)
            report_type = self.report_type_combo.currentText()
            if report_type == "Общий отчет":
                report_text = self.generate_general_report(start_date, end_date)
            elif report_type == "Отчет по врачам":
                report_text = self.generate_doctors_report(start_date, end_date)
            elif report_type == "Отчет по услугам":
                report_text = self.generate_services_report(start_date, end_date)
            else:
                report_text = self.generate_patients_report(start_date, end_date)
            self.report_text.setText(report_text)
            self.show_info_message("Отчет успешно сформирован!")
        except Exception as e:
            self.show_error_message(f"Ошибка при формировании отчета: {str(e)}")

    def generate_general_report(self, start_date, end_date):
        try:
            query = """
                SELECT 
                    COUNT(DISTINCT a.appoint_id) as total_appointments,
                    COUNT(DISTINCT a.snils) as total_patients,
                    COUNT(DISTINCT a.dent_id) as total_doctors,
                    SUM(a.sum) as total_revenue
                FROM Appointment a
                WHERE a.date BETWEEN %s AND %s
            """
            self.db.cursor.execute(query, (start_date, end_date))
            stats = self.db.cursor.fetchone()

            query = """
                SELECT 
                    s.name_serv,
                    COUNT(*) as count,
                    SUM(s.price) as total
                FROM Appointment a
                JOIN App_serv aps ON a.appoint_id = aps.appoint_id
                JOIN Services s ON aps.serv_id = s.serv_id
                WHERE a.date BETWEEN %s AND %s
                GROUP BY s.name_serv
                ORDER BY count DESC
                LIMIT 5
            """
            self.db.cursor.execute(query, (start_date, end_date))
            top_services = self.db.cursor.fetchall()

            report = f"""ОБЩИЙ ОТЧЕТ
Период: {start_date} - {end_date}

ОСНОВНЫЕ ПОКАЗАТЕЛИ:
Всего приемов: {stats['total_appointments']}
Всего пациентов: {stats['total_patients']}
Работало врачей: {stats['total_doctors']}
Общая выручка: {stats['total_revenue']:,} руб.

ТОП-5 ПОПУЛЯРНЫХ УСЛУГ:
"""
            for service in top_services:
                report += f"{service['name_serv']}: {service['count']} раз - {service['total']:,} руб.\n"

            return report
        except Exception as e:
            raise Exception(f"Ошибка формирования общего отчета: {str(e)}")

    def generate_doctors_report(self, start_date, end_date):
        try:
            query = """
                SELECT 
                    CONCAT(d.surname_d, ' ', d.name_d, ' ', d.patron_d) as doctor_name,
                    sp.name_sp as specialization,
                    COUNT(DISTINCT a.appoint_id) as total_appointments,
                    COUNT(DISTINCT a.snils) as unique_patients,
                    SUM(a.sum) as total_revenue
                FROM Dentists d
                LEFT JOIN Appointment a ON d.dent_id = a.dent
                LEFT JOIN Special sp ON d.special = sp.id_special
                WHERE a.date BETWEEN %s AND %s
                GROUP BY d.dent_id, doctor_name, sp.name_sp
                ORDER BY total_revenue DESC
            """
            self.db.cursor.execute(query, (start_date, end_date))
            doctors_stats = self.db.cursor.fetchall()

            report = f"""ОТЧЕТ ПО ВРАЧАМ
Период: {start_date} - {end_date}

СТАТИСТИКА ПО ВРАЧАМ:
"""
            for doc in doctors_stats:
                report += f"""
Врач: {doc['doctor_name']}
Специализация: {doc['specialization']}
Количество приемов: {doc['total_appointments']}
Уникальных пациентов: {doc['unique_patients']}
Общая выручка: {doc['total_revenue']:,} руб.
----------------------------------------"""

            return report
        except Exception as e:
            raise Exception(f"Ошибка формирования отчета по врачам: {str(e)}")

    def generate_services_report(self, start_date, end_date):
        try:
            query = """
                SELECT 
                    s.name_serv,
                    COUNT(*) as usage_count,
                    MIN(s.price) as min_price,
                    MAX(s.price) as max_price,
                    SUM(s.price) as total_revenue
                FROM Services s
                JOIN App_serv aps ON s.serv_id = aps.serv_id
                JOIN Appointment a ON aps.appoint_id = a.appoint_id
                WHERE a.date BETWEEN %s AND %s
                GROUP BY s.serv_id, s.name_serv
                ORDER BY usage_count DESC
            """
            self.db.cursor.execute(query, (start_date, end_date))
            services_stats = self.db.cursor.fetchall()

            report = f"""ОТЧЕТ ПО УСЛУГАМ
Период: {start_date} - {end_date}

СТАТИСТИКА ПО УСЛУГАМ:
"""
            for service in services_stats:
                report += f"""
Услуга: {service['name_serv']}
Количество оказаний: {service['usage_count']}
Минимальная цена: {service['min_price']:,} руб.
Максимальная цена: {service['max_price']:,} руб.
Общая выручка: {service['total_revenue']:,} руб.
----------------------------------------"""

            return report
        except Exception as e:
            raise Exception(f"Ошибка формирования отчета по услугам: {str(e)}")

    def generate_patients_report(self, start_date, end_date):
        try:
            query = """
                SELECT 
                    CONCAT(p.surname_p, ' ', p.name_p, ' ', p.patron_p) as patient_name,
                    p.birthday,
                    p.phone,
                    COUNT(DISTINCT a.appoint_id) as visit_count,
                    SUM(a.sum) as total_spent
                FROM Patients p
                JOIN Appointment a ON p.snils_id = a.snils
                WHERE a.date BETWEEN %s AND %s
                GROUP BY p.snils_id, patient_name, p.birthday, p.phone
                ORDER BY total_spent DESC
            """
            self.db.cursor.execute(query, (start_date, end_date))
            patients_stats = self.db.cursor.fetchall()

            report = f"""ОТЧЕТ ПО ПАЦИЕНТАМ
Период: {start_date} - {end_date}

СТАТИСТИКА ПО ПАЦИЕНТАМ:
"""
            for patient in patients_stats:
                report += f"""
Пациент: {patient['patient_name']}
Дата рождения: {patient['birthday'].strftime('%d.%m.%Y')}
Телефон: {patient['phone']}
Количество визитов: {patient['visit_count']}
Общая сумма: {patient['total_spent']:,} руб.
----------------------------------------"""

            return report
        except Exception as e:
            raise Exception(f"Ошибка формирования отчета по пациентам: {str(e)}")

    def save_report(self):
        try:
            if not self.report_text.toPlainText():
                self.show_error_message("Сначала сформируйте отчет!")
                return
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчет",
                os.path.join(os.path.expanduser("~"), "report.pdf"),
                "PDF Files (*.pdf)"
            )
            if file_name:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                try:
                    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
                except:
                    pass
                doc = SimpleDocTemplate(file_name, pagesize=A4)
                styles = getSampleStyleSheet()
                styles.add(ParagraphStyle(
                    name='CustomStyle',
                    fontName='Arial' if 'Arial' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
                    fontSize=10,
                    leading=12,
                ))
                elements = []
                text = self.report_text.toPlainText()
                for line in text.split('\n'):
                    if line.strip():
                        elements.append(Paragraph(line, styles['CustomStyle']))
                        elements.append(Spacer(1, 6))
                doc.build(elements)
                self.show_info_message("Отчет успешно сохранен!")
        except Exception as e:
            self.show_error_message(f"Ошибка при сохранении отчета: {str(e)}")

    def show_info_message(self, message):
        QMessageBox.information(self, "Информация", message)

    def show_error_message(self, message):
        QMessageBox.warning(self, "Ошибка", message)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Дентал Плюс')
        self.setGeometry(100, 100, 1200, 650)
        self.setWindowIcon(QIcon('icon.ico'))
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        self.setPalette(palette)
        self.main_widget = self.create_main_widget()
        self.setCentralWidget(self.main_widget)

    def create_main_widget(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        main_widget.setStyleSheet("background-color: #B0C4DE;")  # Светлый фон для основного виджета
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
                    QTabWidget::pane {
                        background: #5F9EA0;  /* Белый фон вкладок */
                        border: 2px solid #F0FFFF;  /* Голубая обводка вкладок */
                    }
                    QTabBar::tab {
                        background: #e6f7ff;  /* Светло-голубой цвет вкладки */
                        color: #333333;  /* Темный цвет текста */
                        padding: 7px;
                        border: 1px solid #4a90e2; /* Голубая обводка вкладки */
                    }
                    QTabBar::tab:selected {
                        background: #4a90e2;  /* Голубой цвет выбранной вкладки */
                        color: #ffffff;  /* Белый цвет текста выбранной вкладки */
                    }
                    QTabBar::tab:hover {
                        background: #b3e0ff;  /* Светло-голубой цвет вкладки при наведении */
                    }
                """)
        self.doctor_tab = DoctorManagementTab()
        tab_widget.addTab(self.doctor_tab, 'Врачи')
        tab_widget.addTab(ServiceManagementTab(self.doctor_tab.doctors), 'Услуги')
        self.appointment_tab = AppointmentTab(self.doctor_tab)
        tab_widget.addTab(self.appointment_tab, 'Запись на прием')
        tab_widget.addTab(PatientManagementTab(), 'Пациенты')
        tab_widget.addTab(ReportingTab(), 'Отчетность')
        main_layout.addWidget(tab_widget)
        return main_widget

    def closeEvent(self, event):
        if hasattr(self, 'db'):
            self.db.connection.close()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

