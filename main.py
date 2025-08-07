from datetime import datetime
import pytz
import os

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout


class ExpenseManager:  # backend
    def __init__(self, file_path):
        self.file_path = file_path
        self.istanbul = pytz.timezone("Europe/Istanbul")
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            open(self.file_path, 'w').close()

    def add_expense(self, expense_type, amount, explanation, card_name="", date=None):
        try:
            amount = float(amount)
        except ValueError:
            return False, "Amount must be a number."

        if date is None:
            tarih = datetime.now(self.istanbul).date()
        else:
            try:
                tarih = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return False, "Invalid date format. Use YYYY-MM-DD."

        with open(self.file_path, "a", encoding="utf-8") as f:
            if expense_type.lower() == "cash":
                f.write(f"{tarih} - {amount} - {explanation} - cash\n")
            elif expense_type.lower() == "card":
                f.write(f"{tarih} - {amount} - {explanation} - card: {card_name}\n")
            else:
                return False, "Invalid expense type."

        return True, "Expense recorded successfully."

    def read_expenses(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.readlines()

    def get_today_expenses(self):
        today = str(datetime.now(self.istanbul).date())
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [line for line in lines if today in line]

    def delete_line(self, target_line):
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(self.file_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line != target_line:
                    f.write(line)

    def get_total_expenses_by_type(self, expense_type):
        total = 0.0
        expense_type = expense_type.lower()
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            parts = line.strip().split(' - ')
            if len(parts) < 4:
                continue
            _, amount_str, _, payment_type = parts
            if expense_type in payment_type.lower():
                try:
                    total += float(amount_str)
                except ValueError:
                    pass
        return total

    def get_total_expenses_by_card(self, card_name):
        total = 0.0
        card_name = card_name.lower()
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            if f"card: {card_name}" in line.lower():
                parts = line.strip().split(' - ')
                if len(parts) < 4:
                    continue
                _, amount_str, _, _ = parts
                try:
                    total += float(amount_str)
                except ValueError:
                    pass
        return total

    def get_expenses_by_date(self, date_str):
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        filtered_lines = []
        for line in lines:
            parts = line.strip().split(' - ')
            if len(parts) > 0 and parts[0].strip() == date_str:
                filtered_lines.append(line)
        return filtered_lines


class ExpenseForm(BoxLayout):  # frontend
    status_text = StringProperty("")
    all_expenses_text = StringProperty("")
    today_expenses = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = ExpenseManager("D:/Masaüstü/kivy/my_kivy/expenses_kivy/expenses_kivy.txt")

    def submit_expense(self):
        expense_type = self.ids.expense_type.text
        amount = self.ids.amount.text
        explanation = self.ids.explanation.text
        card_name = self.ids.card_name.text

        success, message = self.manager.add_expense(expense_type, amount, explanation, card_name)
        self.status_text = message

        if success:
            self.ids.amount.text = ""
            self.ids.explanation.text = ""
            self.ids.card_name.text = ""

    def show_all_expenses(self):
        lines = self.manager.read_expenses()
        self.all_expenses_text = "".join(lines)
        layout = FloatLayout()

        # ScrollView oluştur
        scroll = ScrollView(size_hint=(0.9, 0.9), pos_hint={'x': 0.05, 'y': 0.05})

        label = Label(
            text=self.all_expenses_text,
            size_hint=(1,None),
            text_size=(self.width*0.9, None),
            halign='left',
            valign='top'
        )
        label.bind(texture_size=lambda instance, value: setattr(instance, 'height',value[1]))

        scroll.bind(width=lambda instance, value: setattr(label, 'text_size', (value, None)))

        scroll.add_widget(label)

        close_button = Button(
            text='X',
            size_hint=(None, None),
            size=(40, 40),
            pos_hint={'right': 1, 'top': 1},
            background_color=(1, 0, 0, 1),
            color=(1, 1, 1, 1),
            font_size=30
        )

        popup = Popup(
            title="All Expenses",
            content=layout,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )

        close_button.bind(on_release=popup.dismiss)

        layout.add_widget(scroll)
        layout.add_widget(close_button)

        popup.open()

    def show_today_expenses(self):
        self.today_expenses = self.manager.get_today_expenses()

        layout = FloatLayout()

        grid_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid_layout.bind(minimum_height=grid_layout.setter('height'))

        for line in self.today_expenses:
            row = BoxLayout(size_hint_y=None, height=40)
            lbl = Label(text=line.strip(), halign='left', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            row.add_widget(lbl)
            btn = Button(text="Delete", size_hint_x=0.2)
            btn.bind(on_release=lambda btn, l=line: self.delete_today_expense_line(l))
            row.add_widget(btn)
            grid_layout.add_widget(row)

        scroll = ScrollView(
            size_hint=(1, 0.85),
            pos_hint={'x': 0.0, 'y': 0.05}
        )
        scroll.add_widget(grid_layout)

        close_button = Button(
            text='X',
            size_hint=(None, None),
            size=(40, 40),
            pos_hint={'right': 1, 'top': 1},
            background_color=(1, 0, 0, 1),
            color=(1, 1, 1, 1),
            font_size=30
        )

        self.popup = Popup(title="Today's Expenses", content=layout, size_hint=(0.95, 0.95), auto_dismiss=False)

        close_button.bind(on_release=self.popup.dismiss)

        layout.add_widget(scroll)
        layout.add_widget(close_button)

        self.popup.open()

    def delete_today_expense_line(self, line):
        self.manager.delete_line(line)
        self.popup.dismiss()
        self.show_today_expenses()

    def show_total_expenses_by_type(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        input_type = TextInput(hint_text="Enter expense type: cash or card", multiline=False)
        btn_show = Button(text="Show Total", size_hint_y=None, height=40)
        popup_content = BoxLayout(orientation='vertical', spacing=10)
        popup = Popup(title="Total Expenses By Type", content=content, size_hint=(0.8, 0.4))

        def show_total(instance):
            expense_type = input_type.text.strip().lower()
            if expense_type not in ['cash', 'card']:
                self.status_text = "Please enter 'cash' or 'card'"
                return
            total = self.manager.get_total_expenses_by_type(expense_type)
            popup_content.clear_widgets()
            popup_content.add_widget(Label(text=f"Total expenses for '{expense_type}': {total}"))
            btn_close = Button(text="Close", size_hint_y=None, height=40)
            btn_close.bind(on_release=popup.dismiss)
            popup_content.add_widget(btn_close)
        input_type.bind(on_text_validate=lambda instance: btn_show.trigger_action(duration=0.1))
        btn_show.bind(on_release=show_total)
        content.add_widget(input_type)
        content.add_widget(btn_show)
        content.add_widget(popup_content)

        popup.open()

    def show_total_expenses_by_card(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        input_card = TextInput(hint_text="Enter card name", multiline=False)
        btn_show = Button(text="Show Total", size_hint_y=None, height=40)
        popup_content = BoxLayout(orientation='vertical', spacing=10)

        popup = Popup(title="Total Expenses By Card", content=content, size_hint=(0.8, 0.4))

        def show_total(instance):
            card_name = input_card.text.strip().lower()
            if not card_name:
                self.status_text = "Please enter a card name"
                return
            total = self.manager.get_total_expenses_by_card(card_name)
            popup_content.clear_widgets()
            popup_content.add_widget(Label(text=f"Total expenses for card '{card_name}': {total}"))
            btn_close = Button(text="Close", size_hint_y=None, height=40)
            btn_close.bind(on_release=popup.dismiss)
            popup_content.add_widget(btn_close)
        input_card.bind(on_text_validate=lambda instance: btn_show.trigger_action(duration=0.1))
        btn_show.bind(on_release=show_total)
        content.add_widget(input_card)
        content.add_widget(btn_show)
        content.add_widget(popup_content)

        popup.open()

    def show_expenses_by_date(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        date_input = TextInput(hint_text="Enter date (YYYY-MM-DD)", multiline=False)
        show_button = Button(text="Show", size_hint_y=None, height=40)

        scroll_view = ScrollView(size_hint=(1, 1))
        list_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        list_layout.bind(minimum_height=list_layout.setter('height'))

        scroll_view.add_widget(list_layout)

        def show_expenses(instance):
            date_str = date_input.text.strip()
            expenses = self.manager.get_expenses_by_date(date_str)
            list_layout.clear_widgets()

            if not expenses:
                list_layout.add_widget(Label(text="No expenses found for that date."))
            else:
                for line in expenses:
                    label = Label(
                        text=line.strip(),
                        size_hint_y=None,
                        height=30,
                        halign='left',
                        valign='middle'
                    )
                    label.bind(size=label.setter('text_size'))
                    list_layout.add_widget(label)

        date_input.bind(on_text_validate=lambda instance: show_button.trigger_action(duration=0.1))
        show_button.bind(on_release=show_expenses)

        close_button = Button(text="Close", size_hint_y=None, height=40)
        close_button.bind(on_release=lambda x: popup.dismiss())

        content.add_widget(date_input)
        content.add_widget(show_button)
        content.add_widget(scroll_view)
        content.add_widget(close_button)

        popup = Popup(title="Expenses By Date", content=content, size_hint=(0.9, 0.9), auto_dismiss=False)
        popup.open()

    def add_expense_by_date_popup(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        date_input = TextInput(hint_text="Enter date (YYYY-MM-DD)", multiline=False)
        expense_type_input = TextInput(hint_text="Expense Type (cash/card)", multiline=False)
        amount_input = TextInput(hint_text="Amount", multiline=False, input_filter='float')
        explanation_input = TextInput(hint_text="Explanation", multiline=False)
        card_name_input = TextInput(hint_text="Card Name (if card used)", multiline=False)

        submit_button = Button(text="Add Expense", size_hint_y=None, height=40)
        status_label = Label(text="", size_hint_y=None, height=30)
        close_button = Button(text="Close", size_hint_y=None, height=40)

        content.add_widget(date_input)
        content.add_widget(expense_type_input)
        content.add_widget(amount_input)
        content.add_widget(explanation_input)
        content.add_widget(card_name_input)
        content.add_widget(submit_button)
        content.add_widget(status_label)
        content.add_widget(close_button)

        popup = Popup(title="Add Expense By Date", content=content, size_hint=(0.9, 0.9), auto_dismiss=False)

        # Burada Enter'a basınca focus diğer inputa geçecek şekilde eventler ekleniyor
        date_input.bind(on_text_validate=lambda instance: setattr(expense_type_input, 'focus', True))
        expense_type_input.bind(on_text_validate=lambda instance: setattr(amount_input, 'focus', True))
        amount_input.bind(on_text_validate=lambda instance: setattr(explanation_input, 'focus', True))
        explanation_input.bind(on_text_validate=lambda instance: setattr(card_name_input, 'focus', True))

        # Son inputta enter'a basınca submit tetiklenebilir:
        card_name_input.bind(on_text_validate=lambda instance: submit_button.trigger_action(duration=0.1))

        def submit_expense(instance):
            date_val = date_input.text.strip()
            expense_type_val = expense_type_input.text.strip()
            amount_val = amount_input.text.strip()
            explanation_val = explanation_input.text.strip()
            card_name_val = card_name_input.text.strip()

            success, message = self.manager.add_expense(
                expense_type_val,
                amount_val,
                explanation_val,
                card_name_val,
                date_val
            )
            status_label.text = message

            if success:
                date_input.text = ""
                expense_type_input.text = ""
                amount_input.text = ""
                explanation_input.text = ""
                card_name_input.text = ""

        submit_button.bind(on_release=submit_expense)
        close_button.bind(on_release=popup.dismiss)

        popup.open()

    # Buraya ekliyoruz: yeni butonla tarihli ekleme popup'ını açar
    def show_add_expense_by_date_popup(self):
        self.add_expense_by_date_popup()

    # Ve buraya ekliyoruz: bugünün harcamasını gösteren buton işlevi
    def show_today_expenses_button(self):
        self.show_today_expenses()


class ExpenseApp(App):
    def build(self):
        Builder.load_file("expenses_kivy.kv")
        return ExpenseForm()


if __name__ == "__main__":
    ExpenseApp().run()
