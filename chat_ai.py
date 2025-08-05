import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QMovie, QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from openai import OpenAI
from text_to_speech import TTS

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",  # Thay bằng API key của bạn
)

def svg_to_icon(svg_path, size=(24, 24)):
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(*size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

class TypingIndicator(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.label = QLabel()
        self.loading_label = QLabel()
        self.movie = QMovie("loading.gif")
        self.movie.setScaledSize(QSize(70, 70))
        self.loading_label.setMovie(self.movie)
        self.loading_label.setFixedSize(70, 70)
        self.movie.start()

        layout.addWidget(self.loading_label, alignment=Qt.AlignLeft)

        layout.addWidget(self.label, alignment=Qt.AlignLeft)  # Căn trái
        layout.setContentsMargins(10, 4, 0, 4)
        self.setLayout(layout)

class ChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat AI")
        self.setMinimumSize(500, 600)
        self.is_dark_mode = False  # Cờ kiểm tra chế độ hiện tại

        # Nút quay lại (ẩn mặc định)
        self.back_button = QPushButton()
        self.back_button.setIcon(svg_to_icon("icons/arrow-left.svg", (24, 24)))
        self.back_button.setIconSize(QSize(24, 24))
        self.back_button.setFixedSize(36, 36)
        self.back_button.setStyleSheet("border: none; background-color: transparent;")
        self.back_button.clicked.connect(self.show_chat_view)
        self.back_button.hide()  # Ẩn mặc định

        # Nút chuyển đổi chế độ sáng/tối
        self.theme_button = QPushButton()
        self.theme_button.setIcon(svg_to_icon("icons/moon.svg", (24, 24)))
        self.theme_button.setIconSize(QSize(24, 24))
        self.theme_button.setFixedSize(36, 36)
        self.theme_button.setStyleSheet("border: none; background-color: transparent;")
        self.theme_button.clicked.connect(self.toggle_theme)

        # Nút setting
        self.setting_button = QPushButton()
        self.setting_button.setIcon(svg_to_icon("icons/setting.svg", (24, 24)))
        self.setting_button.setIconSize(QSize(24, 24))
        self.setting_button.setFixedSize(36, 36)
        self.setting_button.setStyleSheet("border: none; background-color: transparent;")
        self.setting_button.clicked.connect(self.show_settings)

        # Layout top bar
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(self.back_button)
        top_bar_layout.addStretch()
        
        top_bar_layout.addWidget(self.setting_button)
        top_bar_layout.setContentsMargins(4, 4, 6, 4)

        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("background-color: #E6F0FA; border-radius: 10px;")

        # input + send button
        self.input_box = QTextEdit()
        self.input_box.setStyleSheet("""
            QTextEdit {
                background-color: #CCCCCC;
                border: 1px solid #CCC;
                border-radius: 10px;
                padding: 6px;
                font-family: 'Segoe UI';
                font-size: 15px;
            }
        """)
        self.input_box.setFixedHeight(40)
        self.input_box.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_box.setPlaceholderText("Nhập tin nhắn...")
        self.input_box.installEventFilter(self)

        self.send_button = QPushButton()
        self.send_button.setIcon(svg_to_icon("icons/send_white.svg", (24, 24)))
        self.send_button.setIconSize(QSize(24, 24))
        self.send_button.setFixedSize(40, 40)
        self.send_button.setStyleSheet("border: none; background-color: #CCCCCC; border-radius: 8px;")
        self.send_button.clicked.connect(self.send_message)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(top_bar_layout)
        self.main_layout.addWidget(self.chat_list)
        self.main_layout.addLayout(input_layout)
        self.setLayout(self.main_layout)

        self.typing_item = None
        self.typing_widget = None

        self.add_bot_message("Chào bạn! 😊\nMình có thể giúp gì cho bạn hôm nay?")

    def eventFilter(self, source, event):
        if source is self.input_box and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers():
                self.send_message()
                return True
        return super().eventFilter(source, event)

    def send_message(self):
        user_text = self.input_box.toPlainText().strip()
        if not user_text:
            return
        self.input_box.clear()
        self.add_user_message(user_text)

        self.show_typing_indicator()
        QTimer.singleShot(500, lambda: self.get_bot_response(user_text))  # mô phỏng độ trễ

    def add_user_message(self, text):
        item = QListWidgetItem()

        label = QLabel(text)
        label.setStyleSheet("""
            background-color: #DCF8C6;
            border-radius: 10px;
            padding: 8px;
            font-family: 'Segoe UI';
            font-size: 15px;
        """)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignRight)

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)  # khoảng cách giữa các bong bóng
        layout.addWidget(label, alignment=Qt.AlignRight)
        container.setLayout(layout)

        item.setSizeHint(container.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, container)
        self.chat_list.scrollToBottom()

    def add_bot_message(self, text):
        item = QListWidgetItem()

        # Tạo nhãn tin nhắn bot
        label = QLabel(text)
        label.setStyleSheet("""
            background-color: #FF9999;
            color: white;
            border-radius: 10px;
            padding: 8px;
            font-family: 'Segoe UI';
            font-size: 15px;
        """)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignLeft)

        # Tạo nút icon loa
        speaker_button = QPushButton()
        speaker_button.setIcon(svg_to_icon("icons/speaker_on.svg", (20, 20)))
        speaker_button.setIconSize(QSize(20, 20))
        speaker_button.setFixedSize(30, 30)
        speaker_button.setStyleSheet("border: none; background-color: transparent;")
        speaker_button.clicked.connect(lambda: TTS(text))  # Đọc nội dung tin nhắn

        # Tạo layout chứa icon + label
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.addWidget(label)
        msg_layout.addWidget(speaker_button)
        msg_layout.setAlignment(Qt.AlignLeft)

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)
        layout.addLayout(msg_layout)
        container.setLayout(layout)

        item.setSizeHint(container.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, container)
        self.chat_list.scrollToBottom()

    def show_typing_indicator(self):
        self.typing_item = QListWidgetItem()
        self.typing_widget = TypingIndicator()
        self.typing_item.setSizeHint(self.typing_widget.sizeHint())
        self.chat_list.addItem(self.typing_item)
        self.chat_list.setItemWidget(self.typing_item, self.typing_widget)
        self.chat_list.scrollToBottom()

    def hide_typing_indicator(self):
        if self.typing_item:
            row = self.chat_list.row(self.typing_item)
            self.chat_list.takeItem(row)
            self.typing_item = None
            self.typing_widget = None

    def get_bot_response(self, user_input):
        try:
            response = client.chat.completions.create(
                model="google/gemma-3n-e2b-it:free",
                messages=[
                            {"role": "user", "content": user_input}
                        ],
            )
            bot_reply = response.choices[0].message.content.strip()
            print("Bot:", bot_reply)
        except Exception as e:
            bot_reply = "❌ Có lỗi xảy ra khi gọi API: " + str(e)
            print(bot_reply)

        self.hide_typing_indicator()
        self.add_bot_message(bot_reply)

    def show_settings(self):
        self.chat_list.clear()
        self.input_box.hide()
        self.send_button.hide()
        self.back_button.show()

        # ----- Dòng tiêu đề "Cài đặt" -----
        item1 = QListWidgetItem()
        label1 = QLabel("🔧 Cài đặt")
        label1.setStyleSheet("""
            font-size: 18px;
            color: #333;
            padding: 16px;
            font-weight: bold;
            font-family: 'Segoe UI';
        """)
        label1.setAlignment(Qt.AlignCenter)
        container1 = QWidget()
        layout1 = QVBoxLayout()
        layout1.addWidget(label1)
        layout1.setAlignment(Qt.AlignCenter)
        container1.setLayout(layout1)
        item1.setSizeHint(container1.sizeHint())
        self.chat_list.addItem(item1)
        self.chat_list.setItemWidget(item1, container1)

        # ----- Dòng chuyển đổi sáng/tối -----
        item2 = QListWidgetItem()
        label2 = QLabel("Chế độ giao diện:")
        label2.setStyleSheet("font-size: 15px; padding: 8px;")
        label2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        theme_toggle_btn = QPushButton()
        icon_path = "icons/sun.svg" if self.is_dark_mode else "icons/moon.svg"
        theme_toggle_btn.setIcon(svg_to_icon(icon_path, (24, 24)))
        theme_toggle_btn.setIconSize(QSize(24, 24))
        theme_toggle_btn.setFixedSize(40, 40)
        theme_toggle_btn.setStyleSheet("border: none; background-color: transparent;")
        theme_toggle_btn.clicked.connect(lambda: [self.toggle_theme(), self.show_settings()])  # refresh lại icon sau khi toggle

        container2 = QWidget()
        layout2 = QHBoxLayout()
        layout2.addWidget(label2)
        layout2.addStretch()
        layout2.addWidget(theme_toggle_btn)
        layout2.setContentsMargins(12, 6, 12, 6)
        container2.setLayout(layout2)

        item2.setSizeHint(container2.sizeHint())
        self.chat_list.addItem(item2)
        self.chat_list.setItemWidget(item2, container2)

        # Bạn có thể thêm các tùy chọn cài đặt khác ở đây tương tự

    def show_chat_view(self):
        self.back_button.hide()
        self.input_box.show()
        self.send_button.show()
        self.chat_list.clear()
        self.add_bot_message("Chào bạn! 😊\nMình có thể giúp gì cho bạn hôm nay?")

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode

        if self.is_dark_mode:
            self.setStyleSheet("background-color: #1e1e1e; color: white;")
            self.chat_list.setStyleSheet("background-color: #2e2e2e; border-radius: 10px;")
            self.input_box.setStyleSheet("""
                QTextEdit {
                    background-color: #444444;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 10px;
                    padding: 6px;
                    font-family: 'Segoe UI';
                    font-size: 15px;
                }
            """)
            self.theme_button.setIcon(svg_to_icon("icons/sun.svg", (24, 24)))
        else:
            self.setStyleSheet("")  # trở về mặc định
            self.chat_list.setStyleSheet("background-color: #E6F0FA; border-radius: 10px;")
            self.input_box.setStyleSheet("""
                QTextEdit {
                    background-color: #CCCCCC;
                    border: 1px solid #CCC;
                    border-radius: 10px;
                    padding: 6px;
                    font-family: 'Segoe UI';
                    font-size: 15px;
                }
            """)
            self.theme_button.setIcon(svg_to_icon("icons/moon.svg", (24, 24)))

# ------------------ Hàm chính ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())

