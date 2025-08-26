from logic import *

def main():
    app = QApplication([])
    window = Logic()
    window.show()
    window.setFixedSize(700, 600)
    app.exec()

if __name__ == "__main__":
    main()